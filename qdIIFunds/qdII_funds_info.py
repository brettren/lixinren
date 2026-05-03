# !/usr/bin/python
# -*- coding: UTF-8 -*-
import json

import requests

import config

token = config.token
headers = {'Content-Type': 'application/json'}


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


def get_response(url, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data)).json()
    return response


def load_qdII_funds():
    qdIIFunds = get_qdII_funds_info()
    # filter the dollar funds
    qdIIFunds['data'] = list(filter(lambda x: '现汇' not in x.get('shortName'), qdIIFunds['data']))
    qdIIFunds['data'] = list(filter(lambda x: '现钞' not in x.get('shortName'), qdIIFunds['data']))
    qdIIFunds['data'] = list(filter(lambda x: 'C' not in x.get('shortName'), qdIIFunds['data']))
    fund_codes = [fund['stockCode'] for fund in qdIIFunds['data']]
    activeQdIIFunds = get_active_qdII_funds(fund_codes)
    active_fund_codes = [fund['stockCode'] for fund in activeQdIIFunds]
    # filter the inactive funds
    qdIIFunds = list(filter(lambda x: x.get('stockCode') in active_fund_codes, qdIIFunds['data']))
    writeJsonFile(qdIIFunds, f"all_qdII_funds_info.json")
    return qdIIFunds


if __name__ == '__main__':
    load_qdII_funds()
