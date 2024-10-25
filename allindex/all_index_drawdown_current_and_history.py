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
funds = {}
fund_styles = {}
all_index_largest_drawdown = {}
all_index_highest_index_in_history = {}
all_index_drawdown_current_and_history_csv_file = "all_index_drawdown_current_and_history.csv"


class Stock:
    def __int__(self, code, pe, pePos, peToLowest, pb, pbPos, pbToLowest, roe, roe_vs_pe, div, cp, highest_cp,
                highest_cp_date, fall_to_lowest_drawdown):
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
        self.fall_to_lowest_drawdown = fall_to_lowest_drawdown


# endDate = datetime.datetime.today().strftime('%Y-%m-%d')
endDate = config.today
startDate = (datetime.datetime.today() - datetime.timedelta(weeks=52 * 10)).strftime('%Y-%m-%d')
headers = {'Content-Type': 'application/json'}
summary = list()
summary.append([endDate, "stockCode", "publishDate", "stockName", "style", "Current drawdown", "Largest drawdown",
                "fall_to_lowest_drawdown", "funds"])


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
    while i < len(stockCodes):
        getFundamentalSubPart(valueMap, stockCodes[i: i + 100], country)
        i += 100
    return valueMap


def getFundamentalSubPart(valueMap, stockCodes, country):
    response = get_response(url=f'https://open.lixinger.com/api/{country}/index/fundamental',
                            data={
                                "stockCodes": stockCodes,
                                "metricsList": metricsList,
                                "token": token,
                                "date": endDate
                            })
    for stock in response["data"]:
        index = Stock()
        index.code = stock["stockCode"]
        try:
            cp = stock["cp"]
            index.cp = cp
        except:
            print(f"{index.code} cannot get cp")
        valueMap[stock["stockCode"]] = index
    return valueMap


def mark_as_percent(df, column):
    # Convert the percentage strings to percentage numbers.
    df[column] = df[column].str.replace("%", "")
    df[column] = df[column].astype(float)
    df[column] = df[column].div(100)


def read_other_files():
    # Load the CSV file into a pandas DataFrame
    with open("all_index_tracking_fund.csv", 'r', encoding='utf_8_sig') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            funds[row[0]] = row[1]
    with open("all_index_style.csv", 'r', encoding='utf_8_sig') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if not funds.get(row[0]):
                print(f"{row[0]} has no tracking fund, no need to add style")
                continue
            fund_styles[row[0]] = row[2]
    # all_index_largest_drawdown_in_10_years.py
    with open("all_index_largest_drawdown_in_10_years.csv", 'r', encoding='utf_8_sig') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            all_index_largest_drawdown[row[0]] = row[1]
    with open("all_index_highest_index_in_history.csv", 'r', encoding='utf_8_sig') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            all_index_highest_index_in_history[row[1]] = row[4]


def log_each_index_info(sector, code, publishDate, valueInfo, value):
    try:
        if funds.get(code) is None:
            return
        current_drawdown = "{:.2%}".format(valueInfo.cp / float(all_index_highest_index_in_history.get(code)) - 1)
        # endDate, "stockCode", "publishDate", "stockName", "style", "Current drawdown", "Largest drawdown","funds"
        largest_drawdown = all_index_largest_drawdown.get(code)
        a_value = float(current_drawdown.strip('%')) / 100
        b_value = float(largest_drawdown.strip('%')) / 100
        result = (1 + b_value) / (1 + a_value) - 1
        summary.append([sector, code, publishDate, value, fund_styles.get(code), current_drawdown,
                        largest_drawdown, "{:.2%}".format(result), funds.get(code)])
    except Exception as e:
        print(str(e))


def fetch_all_index_current_cp():
    # Load the CSV file into a pandas DataFrame
    stockMapsCN, publishDate_map = get_index_codes("cn")
    valueMap = getFundamental(list(stockMapsCN.keys()), "cn")
    read_other_files()
    for key, value in stockMapsCN.items():
        if valueMap.get(key) is None:
            print(f"{key} cannot get Fundamental info")
            continue
        if (funds.get(key) is None) or (funds.get(key) == ''):
            print(f"{key} cannot get tracking fund")
            continue
        log_each_index_info("A股", key, publishDate_map[key], valueMap[key], value)
    stockMapsHK, publishDate_map = get_index_codes("hk")
    valueMap = getFundamental(list(stockMapsHK.keys()), "hk")
    for key, value in stockMapsHK.items():
        if valueMap.get(key) is None:
            print(f"{key} cannot get Fundamental info")
            continue
        if (funds.get(key) is None) or (funds.get(key) == ''):
            print(f"{key} cannot get tracking fund")
            continue
        log_each_index_info("港股", key, publishDate_map[key], valueMap[key], value)
    with open(all_index_drawdown_current_and_history_csv_file, 'w', encoding='utf_8_sig') as summaryf:
        writer = csv.writer(summaryf)
        writer.writerows(summary)
    # for line in summary:
    #     print(line)


fetch_all_index_current_cp()
