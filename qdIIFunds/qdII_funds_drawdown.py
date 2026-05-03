# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import datetime

import config
from qdII_funds_info import token, headers, get_response, load_qdII_funds

endDate = config.today
startDate = (datetime.datetime.today() - datetime.timedelta(weeks=52 * 10)).strftime('%Y-%m-%d')
summary = list()
summary.append([endDate, "", "", "", "Current drawdown", "Largest drawdown", "To lowest drawdown 📉🔽",
                "To Highest required 📈🔼"])


def getEachFundDrawdown(fund):
    response = get_response(url=f"https://open.lixinger.com/api/cn/fund/drawdown",
                            data={
                                "stockCode": fund['stockCode'],
                                "startDate": startDate,
                                "endDate": endDate,
                                "token": token,
                                "granularity": "fs",
                            })
    if response.get('message') == 'success':
        data = response['data']
        if len(data) == 0:
            print(fund['stockCode'] + " has No Drawback data")
            return
        current_drawdown = data[0]['value']
        currentDrawdownText = "{:.2%}".format(current_drawdown)
        # sort the data by date
        sorted_data = sorted(data, key=lambda day: day['value'])
        # get the lowest and highest index
        largest_drawdown = sorted_data[0]['value']
        drawdown = "{:.2%}".format(largest_drawdown)
        number = 1 - (1 + largest_drawdown) / (1 + current_drawdown)
        toLowest = "{:.2%}".format(number)
        toHighest = "{:.2%}".format(1 / (1 + current_drawdown) - 1)
        summary.append(
            [fund['fundSecondLevel'], fund['stockCode'], fund['inceptionDate'][0:10], fund['shortName'],
             currentDrawdownText, drawdown, toLowest, toHighest])
        print(fund['stockCode'] + ' ' + fund['inceptionDate'][0:10] + ' ' + fund['shortName'] + ' ' +
             currentDrawdownText + ' ' + drawdown + ' ' + toLowest + ' ' + toHighest)
    else:
        print(f"Failed to fetch data {fund['stockCode']} {fund['shortName']}: {response}")


if __name__ == '__main__':
    qdIIFunds = load_qdII_funds()
    print(endDate, "inceptionDate", "name", "", "Current drawdown", "Largest drawdown", "To lowest drawdown 📉🔽",
                    "To Highest required 📈🔼")
    for fund in qdIIFunds:
        getEachFundDrawdown(fund)
    summary[1:] = sorted(summary[1:], key=lambda index: float(index[6].replace("%", "")))
    with open(f'qdII_funds_drawdown.csv', 'w', encoding='utf_8_sig') as summaryf:
        writer = csv.writer(summaryf)
        writer.writerows(summary)
