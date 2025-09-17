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
all_index_highest_index_in_history_csv_file = "all_index_highest_index_in_history.csv"


class Stock:
    def __int__(self, code, pe, pePos, peToLowest, pb, pbPos, pbToLowest, roe, roe_vs_pe, div, cp, highest_cp, highest_cp_date):
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
        self.highest_cp = highest_cp
        self.highest_cp_date = highest_cp_date


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


def getFundamental(stockCodes, country):
    valueMap = {}
    i = 0
    print(f"{country}: Start fetch highest cp in 10 years")
    while i < len(stockCodes):
        getEachIndexFundamental(valueMap, stockCodes[i], country)
        i += 1
    print(f"{country}: fetch Completed")
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
    data = response["data"]
    index = Stock()
    index.code = data[0]["stockCode"]
    # cp = data[0]["cp"]
    # index.cp = cp
    try:
        # index.highest_cp = max(item["cp"] if "cp" in item else float('-inf') for item in data)
        max_cp_item = max(data, key=lambda item: item["cp"] if "cp" in item else float('-inf'))
        index.highest_cp = max_cp_item["cp"]
        index.highest_cp_date = max_cp_item["date"][0:10]
        valueMap[data[0]["stockCode"]] = index
        print(f"{index.code} {index.highest_cp}")
    except:
        print(f"{index.code} cannot get cp")
    return valueMap


def mark_as_percent(df, column):
    # Convert the percentage strings to percentage numbers.
    df[column] = df[column].str.replace("%", "")
    df[column] = df[column].astype(float)
    df[column] = df[column].div(100)


def fetch_each_index_highest_cp(sector, code, publishDate, valueInfo, value):
    try:
        summary.append(
            [sector, code, publishDate, value, valueInfo.highest_cp])
    except Exception as e:
        print(str(e))


def fetch_all_index_highest_cp():
    # Load the CSV file into a pandas DataFrame
    stockMapsCN, publishDate_map = get_index_codes("cn")
    valueMap = getFundamental(list(stockMapsCN.keys()), "cn")
    for key, value in stockMapsCN.items():
        if valueMap.get(key) is None:
            print(f"{key} cannot get Fundamental info")
            continue
        fetch_each_index_highest_cp("A股", key, publishDate_map[key], valueMap[key], value)
    stockMapsHK, publishDate_map = get_index_codes("hk")
    valueMap = getFundamental(list(stockMapsHK.keys()), "hk")
    for key, value in stockMapsHK.items():
        fetch_each_index_highest_cp("港股", key, publishDate_map[key], valueMap[key], value)
    with open(all_index_highest_index_in_history_csv_file, 'w', encoding='utf_8_sig') as summaryf:
        writer = csv.writer(summaryf)
        writer.writerows(summary)
    # for line in summary:
    #     print(line)


fetch_all_index_highest_cp()
