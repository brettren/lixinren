# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import datetime
import json

import requests

token = "632bbc8f-bf24-4bd0-b7e9-29cdd3b20200"
stockMapsCN = {
    "000922": "中证红利",
    "000925": "基本面50",
    "000905": "中证500",
    "000991": "全指医药",
    "399975": "证券公司",
    "399394": "国证医药",
    "399324": "深证红利",
    "399986": "中证银行",
    "000016": "上证50",
    "000300": "沪深300",
    "000993": "全指信息",
    "000990": "全指消费",
    "000989": "全指可选",
    "000919": "300价值",
    "399812": "养老产业",
    "000978": "医药100",
    "000827": "中证环保",
    "399971": "中证传媒",
    "399997": "中证白酒",
    "000992": "全指金融",
    "930782": "500SNLV",
    "950090": "上证50优选",
    "000994": "全指电信",
    "931160": "通信设备",
    "399441": "生物医药",
    "399965": "800地产",
    "H30533": "中国互联网50",
    "H30094": "消费红利",
    "H30269": "红利低波",
    "931052": "国信价值"
}
stockMapsHK = {
    "HSI": "恒生指数",
    "HSCEI": "国企指数",
    "HSTECH": "恒生科技",
    "HSHDYI": "恒生高股息",
    "HSHCI": "恒生医疗保健",
    "HSHKBIO": "恒生生物科技"
}
stockMapsObserve = {
    "930743": "中证生科",
    "000015": "红利指数"
}
positionMaps = {
    "399975": "证券公司",
    "000016": "上证50",
    "399441": "生物医药",
    "399965": "800地产",
    "H30533": "中国互联网50",
    "HSHDYI": "恒生高股息",
    "HSHKBIO": "恒生生物科技"
}

endDate = datetime.datetime.today().strftime('%Y-%m-%d')
startDate = (datetime.datetime.today() - datetime.timedelta(weeks=52 * 3)).strftime('%Y-%m-%d')
headers = {'Content-Type': 'application/json'}
summary = list()
summary.append([endDate, "", "", "Current drawdown", "Largest drawdown", "To lowest drawdown 📉🔽", "To Highest required 📈🔼"])


def get_index_codes():
    stock_codes_url = 'https://open.lixinger.com/api/cn/index'
    stock_codes_data = {
        "token": token,
        "stockCodes": stockMapsCN
    }
    response = requests.post(url=stock_codes_url, headers=headers, data=json.dumps(stock_codes_data)).json()
    data = response["data"]
    cnName_map = {}
    publishDate_map = {}
    for d in data:
        cnName_map[d["stockCode"]] = d["name"]
        publishDate_map[d["stockCode"]] = d["launchDate"]
    return cnName_map, publishDate_map


def get_response(url, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data)).json()
    return response


def getEachIndexDrawdown(sector, code, value, country):
    response = get_response(url=f"https://open.lixinger.com/api/{country}/index/drawdown",
                            data={
                                "stockCode": code,
                                "startDate": startDate,
                                "endDate": endDate,
                                "token": token,
                                "granularity": "y3",
                            })
    if response['message'] == 'success':
        data = response['data']
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
        if key in positionMaps.keys():
            value = "\033[1;31m{}\033[0m".format(value)
        summary.append([sector, key, value, currentDrawdownText, drawdown, toLowest, toHighest])
    else:
        print("Failed to fetch data")


for key, value in stockMapsCN.items():
    getEachIndexDrawdown("A股", key, value, "cn")
for key, value in stockMapsHK.items():
    getEachIndexDrawdown("港股", key, value, "hk")
for key, value in stockMapsObserve.items():
    getEachIndexDrawdown("观察", key, value, "cn")
summary[1:] = sorted(summary[1:], key=lambda index: float(index[5].replace("%", "")))
with open('index_drawdown.csv', 'w', encoding='utf_8_sig') as summaryf:
    writer = csv.writer(summaryf)
    writer.writerows(summary)

# for line in summary:
#     print(line)
