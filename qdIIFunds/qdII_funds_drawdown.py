# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import os

import akshare as ak

import config
from qdII_funds_info import load_qdII_funds

endDate = config.today
summary = list()
summary.append([endDate, "", "", "", "Current drawdown", "Largest drawdown", "To lowest drawdown 📉🔽",
                "To Highest required 📈🔼"])

script_dir = os.path.dirname(os.path.abspath(__file__))


def get_fund_nav_history(stock_code):
    """Returns (exists, df). exists=False means fund is defunct."""
    try:
        df = ak.fund_open_fund_info_em(symbol=stock_code, indicator='累计净值走势')
        if df is not None and len(df) > 0:
            return True, df
    except Exception as e:
        print(f"Failed to fetch NAV for {stock_code}: {e}")
    return False, None


def calc_drawdown_from_history(df):
    """Calculate current drawdown and largest drawdown from NAV history."""
    import numpy as np
    navs = df['累计净值'].astype(float).values
    navs = navs[~np.isnan(navs)]
    if len(navs) == 0:
        return None, None
    highest = navs[0]
    largest_drawdown = 0.0
    for nav in navs:
        if nav > highest:
            highest = nav
        drawdown = (nav - highest) / highest
        if drawdown < largest_drawdown:
            largest_drawdown = drawdown

    current_nav = navs[-1]
    current_highest = max(navs)
    if current_nav >= current_highest:
        current_drawdown = 0.0
    else:
        current_drawdown = (current_nav - current_highest) / current_highest

    return current_drawdown, largest_drawdown


def getEachFundDrawdown(fund):
    stock_code = fund['stockCode'].zfill(6)
    exists, df = get_fund_nav_history(stock_code)
    if not exists:
        return 'defunct'

    current_drawdown, largest_drawdown = calc_drawdown_from_history(df)
    if current_drawdown is None:
        print(f"{stock_code} {fund['shortName']}: No valid NAV data (all NaN)")
        return 'defunct'

    currentDrawdownText = "{:.2%}".format(current_drawdown)
    drawdownText = "{:.2%}".format(largest_drawdown)
    number = 1 - (1 + largest_drawdown) / (1 + current_drawdown)
    toLowest = "{:.2%}".format(number)
    toHighest = "{:.2%}".format(1 / (1 + current_drawdown) - 1)

    summary.append(
        [fund['fundSecondLevel'], fund['stockCode'], fund['inceptionDate'][0:10], fund['shortName'],
         currentDrawdownText, drawdownText, toLowest, toHighest])
    print(fund['stockCode'] + ' ' + fund['inceptionDate'][0:10] + ' ' + fund['shortName'] + ' ' +
         currentDrawdownText + ' ' + drawdownText + ' ' + toLowest + ' ' + toHighest)
    return 'ok'


if __name__ == '__main__':
    qdIIFunds = load_qdII_funds()

    print(endDate, "inceptionDate", "name", "", "Current drawdown", "Largest drawdown", "To lowest drawdown 📉🔽",
                    "To Highest required 📈🔼")
    defunct_funds = []
    for fund in qdIIFunds:
        result = getEachFundDrawdown(fund)
        if result == 'defunct':
            defunct_funds.append(fund)
            print(f"❌ {fund['stockCode'].zfill(6)} {fund['shortName']} - no longer exists")

    print(f"\n=== Summary ===")
    print(f"Total funds: {len(qdIIFunds)}, Active: {len(qdIIFunds) - len(defunct_funds)}, Defunct: {len(defunct_funds)}")
    if defunct_funds:
        print("Defunct funds:")
        for fund in defunct_funds:
            print(f"  {fund['stockCode'].zfill(6)} {fund['shortName']}")

    summary[1:] = sorted(summary[1:], key=lambda index: float(index[6].replace("%", "")))
    with open(os.path.join(script_dir, 'qdII_funds_drawdown.csv'), 'w', encoding='utf_8_sig') as summaryf:
        writer = csv.writer(summaryf)
        writer.writerows(summary)
