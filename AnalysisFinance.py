import yfinance as yf
import numpy as np

def get_stock_data(ticker: str):
    stock = yf.Ticker(ticker)
    return (
        stock.info,
        stock.history(period="1y"),
        stock.financials,
        stock.balance_sheet,
        stock.cashflow,
        stock.earnings
    )

def score_stock(ticker: str) -> float:
    info, history, financials, balance_sheet, cashflow, earnings = get_stock_data(ticker)
    score = 0.0

#---Value Formulas (30%)---#
    

    #EV/EBITDA

    if ev_ebitda := info.get("enterpriseToEbitda"):
        if ev_ebitda < 0: score += 0
        elif ev_ebitda < 5: score += 7
        elif ev_ebitda < 10: score += 10
        elif ev_ebitda < 15: score += 8
        elif ev_ebitda < 20: score += 6
        elif ev_ebitda < 25: score += 4
        elif ev_ebitda < 35: score += 2
        else: score += 1 

    #Shareholder yield

    dividend_yield = info.get("dividendYield") or 0
    market_cap = info.get("marketCap")

    try:
        buybacks = cashflow.loc["Repurchase Of Capital Stock"].iloc[0]
        buyback_yield = abs(buybacks) / market_cap if market_cap else 0
    except:
        buyback_yield = 0

    shareholder_yield = dividend_yield + buyback_yield

    if shareholder_yield > 0:
        if shareholder_yield < 0.01: score += 1   
        elif shareholder_yield < 0.02: score += 3   
        elif shareholder_yield < 0.05: score += 6   
        elif shareholder_yield < 0.08: score += 8   
        elif shareholder_yield < 0.10: score += 10  
        else: score += 7

    #Free Cash Flow

    fcf = info.get("freeCashflow")
    market_cap = info.get("marketCap")

    if fcf and market_cap:
        fcf_yield = fcf / market_cap

        if fcf_yield < 0: score += 0
        elif fcf_yield > 0.02: score += 2
        elif fcf_yield > 0.04: score += 4
        elif fcf_yield > 0.06: score += 6
        elif fcf_yield > 0.08: score += 8
        elif fcf_yield > 0.10: score += 10
        #Ranges
        else: score += 8
    
#---Profitability Formulas (30%)---#

    #-Piotroski-F Score-#

        #Profitability (4pts max)

    ROA = info.get("returnOnAssets") or 0
    OCF = info.get("operatingCashflow") or 0

    P1 = P2 = P3 = P4 = P5 = P6 = P7 = P8 = P9 = 0
    P_scores = np.array([P1, P2, P3, P4, P5, P6, P7, P8, P9])
    
    if ROA > 0:
        P1 = 1
    else: P1 = 0

    if OCF > 0:
        P2 = 1
    else: P2 = 0

    try:
        net_income = financials.loc["Net Income"] 
        total_assets = balance_sheet.loc["Total Assets"]

        ROA_current = net_income.iloc[0] / total_assets.iloc[0]
        ROA_last_year = net_income.iloc[1] / total_assets.iloc[1]

        delta_ROA = ROA_current - ROA_last_year

        if delta_ROA > 0: P3 = 1
        else: P3 = 0
    except: 
        P3 = 0
    try:
        net_income = financials.loc["Net Income"]
        P4 = 1 if OCF > net_income.iloc[0] else 0
    except:
        P4 = 0

        #Leverage, liquidity & fund source (3pts max)

    try:
        longTermDebt = balance_sheet.loc["Long Term Debt"]
        total_assets = balance_sheet.loc["Total Assets"]

        lev_current = longTermDebt.iloc[0] / total_assets.iloc[0]
        lev_previous_year = longTermDebt.iloc[1] / total_assets.iloc[1]

        delta_lev = lev_current - lev_previous_year

        if delta_lev < 0:
            P5 = 1
        else: P5 = 0
    except:
        P5 = 0

    try:
        current_liabilities = balance_sheet.loc["Current Liabilities"]
        total_assets = balance_sheet.loc["Total Assets"]

        liquid_current = total_assets.iloc[0] / current_liabilities.iloc[0]
        liquid_previous_year = total_assets.iloc[1] / current_liabilities.iloc[1]

        if liquid_current > liquid_previous_year:
            P6 = 1
        else: P6 = 0
    except: 
        P6 = 0

    try:
        shares_current = balance_sheet.loc["Ordinary Shares Number"].iloc[0]
        shares_previous_year = balance_sheet.loc["Ordinary Shares Number"].iloc[1]

        if shares_current <= shares_previous_year:
            P7 = 1
        else: P7 = 0
    except:
        P7 = 0
        
        #Operating Efficiency (2pts max)

    try:
        grossMarg_current = financials.loc["Gross Profit"].iloc[0] / financials.loc["Total Revenue"].iloc[0]
        grossMarg_prev_year = financials.loc["Gross Profit"].iloc[1] / financials.loc["Total Revenue"].iloc[1]
        
        if grossMarg_current > grossMarg_prev_year:
            P8 = 1
        else: P8 = 0

    except:
        P8 = 0
    
    try:
        revenue = financials.loc["Total Revenue"]
        total_assets = balance_sheet.loc["Total Assets"]

        AT_current = revenue.iloc[0] / total_assets.iloc[0]
        AT_prev_year = revenue.iloc[1] / total_assets.iloc[1]

        if AT_current > AT_prev_year:
            P9 = 1
        else: P9 = 0
    except:
        P9 = 0

    SumP = np.sum(P_scores)

    if SumP <= 3: score += 0
    elif SumP <= 5: score += 3
    elif SumP <= 7: score += 7
    else: score += 10



    #CROIC 

    try:
        fcf            = info.get("freeCashflow") or 0
        total_debt     = info.get("totalDebt") or 0
        total_equity   = balance_sheet.loc["Stockholders Equity"].iloc[0]
        cash           = info.get("totalCash") or 0

        invested_capital = total_equity + total_debt - cash

        if invested_capital > 0:
            CROIC = fcf / invested_capital

            if CROIC < 0.05: score += 0
            elif CROIC < 0.1: score += 3
            elif CROIC < 0.15: score += 7
            else: score += 10
    except:
        pass

    #Gross Profit Margin

    try:
         grossMargin = financials.loc["Gross Profit"].iloc[0] / financials.loc["Total Revenue"].iloc[0]

         if grossMargin < 0.1: score += 0
         elif grossMargin < 0.2: score += 3
         elif grossMargin <= 0.4: score += 7
         else: score += 10
    except: 
        pass

#---Forensic Safety (25%)---#

    #Altman Z-Score

    try:
        current_assets = balance_sheet.loc["Current Assets"].iloc[0]
        current_liabilities = balance_sheet.loc["Current Liabilities"].iloc[0]
        total_assets = balance_sheet.loc["Total Assets"].iloc[0]
        retained_earnings = balance_sheet.loc["Retained Earnings"].iloc[0]
        ebit = financials.loc["EBIT"].iloc[0]
        market_cap = info.get("marketCap")
        total_liabilities = balance_sheet.loc["Total Liabilities Net Minority Interest"].iloc[0]
        revenue = financials.loc["Total Revenue"].iloc[0]
        working_cap = current_assets - current_liabilities

        x1 = working_cap / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_cap / total_liabilities
        x5 = revenue / total_assets

        Z = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + x5

        if Z < 1.81: score += 0
        elif Z <= 2.99: score += 5
        else: score += 10
    except:
        pass

    #Beneish M-Score

    try:
        #Current year
        
        receive_c = balance_sheet.loc["Accounts Receivable"].iloc[0]
        revenue_c = financials.loc["Total Revenue"].iloc[0]
        gross_profit_c = financials.loc["Gross Profit"].iloc[0]
        total_assets_c = balance_sheet.loc["Total Assets"].iloc[0]
        ppe_c = balance_sheet.loc["Net PPE"].iloc[0]
        deprec_c = cashflow.loc["Depreciation"].iloc[0]
        sga_c = financials.loc["Selling General Administrative"].iloc[0]
        current_liabilities = balance_sheet.loc["Current Liabilities"].iloc[0]
        LTD_c = balance_sheet.loc["Long Term Debt"].iloc[0]
        net_income_c = financials.loc["Net Income"].iloc[0]
        cfo_c = info.get("operatingCashflow") or 0

        #Previous year

        receive_p = balance_sheet.loc["Accounts Receivable"].iloc[1]
        revenue_p = financials.loc["Total Revenue"].iloc[1]
        gross_profit_p = financials.loc["Gross Profit"].iloc[1]
        total_assets_p = balance_sheet.loc["Total Assets"].iloc[1]
        ppe_p = balance_sheet.loc["Net PPE"].iloc[1]
        deprec_p = cashflow.loc["Depreciation"].iloc[1]
        sga_p = financials.loc["Selling General Administrative"].iloc[1]
        current_liabilities_p = balance_sheet.loc["Current Liabilities"].iloc[1]
        LTD_p = balance_sheet.loc["Long Term Debt"].iloc[1]
        
        DSRI = (receive_c / revenue_c) / (receive_p / revenue_p)
        GMI = ((revenue_p - gross_profit_p) / revenue_p) / ((revenue_c - gross_profit_c) / revenue_c)
        AQI = (1 - (gross_profit_c + ppe_c) / total_assets_c) / (1 - (gross_profit_p + ppe_p) / total_assets_p)
        SGI = revenue_c /revenue_p 
        DEPI = (deprec_p / (ppe_p + deprec_p)) / (deprec_c / (ppe_c + deprec_c))
        SGAI = (sga_c / revenue_c) / (sga_p / revenue_p)
        TATA = (net_income_c - cfo_c) / total_assets_c
        LVGI = ((LTD_c + current_liabilities) / total_assets_c) / ((LTD_p + current_liabilities_p) / total_assets_p)

        M = -4.84 + 0.92*(DSRI) + 0.528*(GMI) + 0.404*(AQI) + 0.892*(SGI) + 0.115*(DEPI) - 0.172*(SGAI) + 4.679*(TATA) - 0.327*(LVGI)

        if M < -2.22: score += 10
        elif M <= -1.78: score += 5
        else: score += 0 
    except:
        pass

    #Sloane Ratio

    try:
        cfi = cashflow.loc["Investing Cash Flow"].iloc[0]
        ocf = info.get("operatingCashflow") or 0
        net_income = financials.loc["Net Income"].iloc[0]
        total_assets = balance_sheet.loc["Total Assets"].iloc[0]

        Sloane = (net_income - ocf - cfi) / total_assets

        if abs(Sloane) <= 0.1: score += 5
        elif abs(Sloane) <= 0.25: score += 2.5
        else: score += 0
    except:
        pass

#---Momentum & Sentiment (15%)---#

    #Sharpe Ratio

    try:
        daily_returns = history["Close"].pct_change().dropna()
        annual_return = daily_returns.mean() * 252
        annual_vol = daily_returns.std() * np.sqrt(252)
        try:
            treasury = yf.ticker("^TNX")
            RFR = treasury.info.get("regularMarketPrice") / 100
        except: 
            RFR = 0.045
        
        sharpe = (annual_return - RFR) / annual_vol

        if sharpe >= 2: score += 5
        elif sharpe >= 1: score += 2.5
        else: score += 0
    except:
        pass
    
    #6 Month Price Momentum 

    try:
        closes = history["Close"]

        momentum_6m = (closes.iloc[-1] - closes.iloc[-126]) / closes.iloc[-126]

        if momentum_6m >= 0.2: score += 5
        elif momentum_6m > 0: score += 2.5
        else: score += 0
    except:
        pass

    #Short Interest Ratio
    