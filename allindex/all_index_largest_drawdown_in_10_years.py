# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import datetime
import json
import pandas as pd
import requests
import config
import openpyxl
import xlsxwriter
from openpyxl.styles import PatternFill, colors
from openpyxl.utils import column_index_from_string
from openpyxl.styles import numbers

token = config.token
metricsList = [
    "cp"
]
stockMapsCN = {

}
stockMapsHK = {

}
all_index_highest_index_in_history_csv_file = "all_index_largest_drawdown_in_10_years.csv"
index = {}


class Stock:
    def __int__(self, code, pe, pePos, peToLowest, pb, pbPos, pbToLowest, roe, roe_vs_pe, div, cp, max_drawdown):
        self.code = code
        self.pe = pe
        self.pePos = pePos
        self.peToLowest = peToLowest
        self.pb = pb
        self.pbPos = pbPos
        self.pbToLowest = pbToLowest
        self.roe = roe
        self.roe_vs_pe = roe_vs_pe
        self.div = div
        self.cp = cp
        self.max_drawdown = max_drawdown


# endDate = datetime.datetime.today().strftime('%Y-%m-%d')
endDate = config.today
startDate = (datetime.datetime.today() - datetime.timedelta(weeks=52 * 10)).strftime('%Y-%m-%d')
headers = {'Content-Type': 'application/json'}
summary = list()


def get_index_codes(country):
    stock_codes_url = f'https://open.lixinger.com/api/{country}/index'
    stock_codes_data = {
        "token": token,
    }
    response = requests.post(url=stock_codes_url, headers=headers, data=json.dumps(stock_codes_data)).json()
    data = response["data"]
    cnName_map = {}
    publishDate_map = {}
    for d in data:
        cnName_map[d["stockCode"]] = d["name"]
        publishDate_map[d["stockCode"]] = d["launchDate"][0:10]
    return cnName_map, publishDate_map


def get_response(url, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data)).json()
    return response


def get_max_drawdown(data):
    peak = data[0]["cp"]
    drawdown_max = 0
    for price in data:
        if price["cp"] > peak:
            peak = price["cp"]
        drawdown = price["cp"] / peak - 1
        if drawdown < drawdown_max:
            drawdown_max = drawdown
    return drawdown_max


def getFundamental(stockCodes, country):
    valueMap = {}
    i = 0
    while i < len(stockCodes):
        if index.get(stockCodes[i]) is not None:
            i += 1
            continue
        getEachIndexFundamental(valueMap, stockCodes[i], country)
        i += 1
    return valueMap


def getEachIndexFundamental(valueMap, stockCodes, country):
    response = get_response(url=f'https://open.lixinger.com/api/{country}/index/fundamental',
                            data={
                                "stockCodes": [stockCodes],
                                "metricsList": metricsList,
                                "token": token,
                                "startDate": startDate,
                                "endDate": endDate
                            })
    try:
        data = response["data"]
        index = Stock()
        index.code = data[0]["stockCode"]
        # cp = data[0]["cp"]
        # index.cp = cp
        # index.highest_cp = max(item["cp"] if "cp" in item else float('-inf') for item in data)
        data = [d for d in data if 'cp' in d and d['cp'] is not None]
        index.max_drawdown = "{:.2%}".format(get_max_drawdown(data[::-1]))
        print(f"{index.code}, get max_drawdown, {index.max_drawdown}")
        valueMap[data[0]["stockCode"]] = index
    except:
        print(f"{index.code} cannot get max_drawdown")
    return valueMap


def log_each_index_max_drawdown(code, valueInfo, value):
    try:
        summary.append(
            [code, value, valueInfo.max_drawdown])
    except Exception as e:
        print(str(e))


def fetch_all_index_max_drawdown():
    with open("all_index_largest_drawdown_in_10_years_first.csv", 'r', encoding='utf_8_sig') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            index[row[0]] = row[1]
    # Load the CSV file into a pandas DataFrame
    stockMapsCN, publishDate_map = get_index_codes("cn")
    valueMap = getFundamental(list(stockMapsCN.keys()), "cn")
    for key, value in stockMapsCN.items():
        if valueMap.get(key) is None:
            print(f"{key} cannot get Fundamental info")
            continue
        log_each_index_max_drawdown(key, valueMap[key], value)
    stockMapsHK, publishDate_map = get_index_codes("hk")
    valueMap = getFundamental(list(stockMapsHK.keys()), "hk")
    for key, value in stockMapsHK.items():
        log_each_index_max_drawdown(key, valueMap[key], value)
    with open(all_index_highest_index_in_history_csv_file, 'w', encoding='utf_8_sig') as summaryf:
        writer = csv.writer(summaryf)
        writer.writerows(summary)
    # for line in summary:
    #     print(line)


fetch_all_index_max_drawdown()
