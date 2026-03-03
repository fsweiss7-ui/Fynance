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
        elif fcf_yield < 0.02: score += 2
        elif fcf_yield < 0.04: score += 4
        elif fcf_yield < 0.06: score += 6
        elif fcf_yield < 0.08: score += 8
        elif fcf_yield < 0.10: score += 10
        else: score += 8
    
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

        delta_ROA = roa_current - ROA_last_year

        if delta_ROA > 0: P3 = 1
        else: P3 = 0
    except: 
        P3 = 0

    if OCF > net_income.iloc[0]:
        P4 = 1
    else: P4=0

        #Leverage, liquidity & fund source (3pts max)

    try:
        longTermDebt = balance_sheet.loc["Long Term Debt"]
        total_assets = balance_sheet.loc["Total Assets"]

        lev_current = longTermDebt.iloc[0] / total_assets.iloc[0]
        lev_previous_year = longTermDebt.iloc[1] / total_asset.iloc[1]

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

    if P_scores = 9: score += 10
    elif P_scores = 8: score += 8.89
    elif P_scores = 7: score += 7.78
    elif P_scores = 6: score += 6.67
    elif P_scores = 5: score += 5.56
    elif P_scores = 4: score += 4.44
    elif P_scores = 3: score += 3.33
    elif P_scores = 2: score += 2.22
    elif P_scores = 1: score += 1.11
    else: score += 0

    

