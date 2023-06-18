# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import datetime
import json

import requests

import config

token = config.token
headers = {'Content-Type': 'application/json'}
summary = list()
endDate = config.today
startDate = (datetime.datetime.today() - datetime.timedelta(weeks=52 * 10)).strftime('%Y-%m-%d')
summary.append([endDate, "", "", "", "Current drawdown", "Largest drawdown", "To lowest drawdown 📉🔽",
                "To Highest required 📈🔼"])

class Stock:
    def __int__(self, code, shortName):
        self.code = code
        self.shortName = shortName


def get_qdII_funds_info():
    stock_codes_url = f'https://open.lixinger.com/api/cn/fund'
    stock_codes_data = {
        "token": token,
    }
    response = requests.post(url=stock_codes_url, headers=headers, data=json.dumps(stock_codes_data)).json()
    data = list(filter(lambda x: x.get('fundSecondLevel') == 'QDII', response["data"]))
    response["data"] = data
    return response


def get_sub_active_qdII_funds(funds, sub_fund_codes):
    stock_codes_url = f'https://open.lixinger.com/api/cn/fund/profile'
    stock_codes_data = {
        "token": token,
        "stockCodes": sub_fund_codes
    }
    response = requests.post(url=stock_codes_url, headers=headers, data=json.dumps(stock_codes_data)).json()
    for fund in response["data"]:
        funds.append(fund)


def get_active_qdII_funds(fund_codes):
    funds = []
    i = 0
    while i < len(fund_codes):
        get_sub_active_qdII_funds(funds, fund_codes[i: i + 100])
        i += 100
    return funds


def writeJsonFile(data, file):
    with open(file, "w", encoding='utf-8-sig') as output_file:
        json.dump(data, output_file, ensure_ascii=False)


qdIIFunds = get_qdII_funds_info()
# filter the dollar funds
qdIIFunds = list(filter(lambda x: '现汇' not in x.get('shortName'), qdIIFunds))
qdIIFunds = list(filter(lambda x: '现钞' not in x.get('shortName'), qdIIFunds))
qdIIFunds = list(filter(lambda x: 'C' not in x.get('shortName'), qdIIFunds))
inactiveFundCodes = ['006778', '150175', '150169', '007628', '007629', '008357', '005440', '150176']
qdIIFunds = list(filter(lambda x: x.get('stockCode') not in inactiveFundCodes, qdIIFunds))
fund_codes = [fund['stockCode'] for fund in qdIIFunds['data']]
activeQdIIFunds = get_active_qdII_funds(fund_codes)
active_fund_codes = [fund['stockCode'] for fund in activeQdIIFunds]
# filter the inactive funds
qdIIFunds = list(filter(lambda x: x.get('stockCode') in active_fund_codes, qdIIFunds['data']))
writeJsonFile(qdIIFunds, "all_qdII_funds_info.json")


def get_response(url, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data)).json()
    return response


def getEachFundDrawdown(fund):
    response = get_response(url=f"https://open.lixinger.com/api/cn/fund/drawdown",
                            data={
                                "stockCode": fund['stockCode'],
                                "startDate": startDate,
                                "endDate": endDate,
                                "token": token,
                                "granularity": "y",
                            })
    if response['message'] == 'success':
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
    else:
        print("Failed to fetch data")


for fund in qdIIFunds:
    getEachFundDrawdown(fund)
summary[1:] = sorted(summary[1:], key=lambda index: float(index[6].replace("%", "")))
with open('qdII_funds_drawdown.csv', 'w', encoding='utf_8_sig') as summaryf:
    writer = csv.writer(summaryf)
    writer.writerows(summary)
