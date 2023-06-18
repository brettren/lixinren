# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import json
import requests
import config

token = config.token
headers = {'Content-Type': 'application/json'}
summary = list()


class Stock:
    def __int__(self, code, shortName):
        self.code = code
        self.shortName = shortName


def get_index_codes(country):
    stock_codes_url = f'https://open.lixinger.com/api/{country}/index'
    stock_codes_data = {
        "token": token,
    }
    response = requests.post(url=stock_codes_url, headers=headers, data=json.dumps(stock_codes_data)).json()
    data = response["data"]
    cnName_map = {}
    for d in data:
        cnName_map[d["stockCode"]] = d["name"]
    return cnName_map


def get_response(url, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data)).json()
    return response


def get_tracking_fund(stockCode, country):
    response = get_response(url=f'https://open.lixinger.com/api/{country}/index/tracking-fund',
                            data={
                                "stockCode": stockCode,
                                "token": token
                            })
    index_funds = []
    for d in response["data"]:
        stock = Stock()
        stock.code = d["stockCode"]
        stock.shortName = d["shortName"]
        index_funds.append(stock.shortName + "(" + stock.code + ")")
    summary.append([stockCode, ", ".join(index_funds)])


def get_all_index_tracking_fund(stockCodes, country):
    for code, value in stockCodes.items():
        get_tracking_fund(code, country)


stockMapsCN = get_index_codes("cn")
get_all_index_tracking_fund(stockMapsCN, "cn")
stockMapsHK = get_index_codes("hk")
get_all_index_tracking_fund(stockMapsHK, "hk")
with open('all_index_tracking_fund.csv', 'w', encoding='utf_8_sig') as summaryf:
    writer = csv.writer(summaryf)
    writer.writerows(summary)

