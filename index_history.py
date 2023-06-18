#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
import requests
import json
import datetime
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import unicodecsv as csv
from pylab import mpl


reload(sys)
sys.setdefaultencoding('utf8')


myfont = matplotlib.font_manager.FontProperties(fname="Light.ttc")
mpl.rcParams['axes.unicode_minus'] = False

metrics = [
        "pe_ttm.mcw",
        "pe_ttm.ew",
        "pb.mcw",
        "pb.ew",
        "ps_ttm.mcw",
        "ps_ttm.ew",
        "dyr.mcw",
        "dyr.ew",
        "cp"  # for index
]


equalAvgIndex = ["000922", "000978", "000827", "399812", "000300", "000919", "H30269", "H30094", "930782", "000905"]


stockMap = {
    "000922": "中证红利等权",
    "000925": "基本面50",
    "000905": "中证500等权",
    "000991": "全指医药",
    "399975": "证券公司",
    "399394": "国证医药",
    "399324": "深证红利",
    "399986": "中证银行",
    "000016": "上证50",
    "000300": "沪深300等权",
    "000993": "全指信息",
    "000990": "全指消费",
    "000989": "全指可选",
    "000919": "300价值等权",
    "399812": "养老产业",
    "000978": "医药100",
    "000827": "中证环保",
    "399971": "中证传媒",
    "399997": "中证白酒",
    "000992": "全指金融",
    "930782": "500SNLV等权",
    "HSI": "恒生指数",
    "HSCEI": "国企指数",
    "950090": "上证50优选",
    "000994": "全指电信",
    "H30533": "中国互联网50",
    "H30094": "消费红利",
    "H30269": "红利低波"
}
stockCodes = stockMap.keys()
token = "567edf4c-b751-4b44-9b6c-afdb1380830b"
headers = {'Content-Type': 'application/json'}
# today = datetime.date.today().strftime("%Y-%m-%d")
today = "2021-12-03"
fileHeaders = ['Date', 'cp', 'pb', 'pe', 'B', 'B Growth', 'E', 'E Growth', 'ROE', 'ps', 'div', 'S', 'total div']
if len(sys.argv) > 1:
    today = sys.argv[1]


date_col = 0
cp_col = date_col + 1
pb_col = cp_col + 1
pe_col = pb_col + 1
book_col = pe_col + 1
book_grow_col = book_col + 1
earning_col = book_grow_col + 1
earning_grow_col = earning_col + 1
roe_col = earning_grow_col + 1
ps_col = roe_col + 1
div_col = ps_col + 1
sale_col = div_col + 1
total_div_col = sale_col + 1

# ----------------- Methods -----------------
def get_response(url, data):
    return requests.post(url=url, headers=headers, data=json.dumps(data)).json()


def process(d, data, pos, mode):
    rowData = []
    rowData.append(today.replace('-', '/'))
    rowData.append(d['cp'])
    rowData.append(round(d['pb'][mode], 2))
    rowData.append(round(d['pe_ttm'][mode], 2))
    b = d['cp']/d['pb'][mode]
    rowData.append(round(b, 2))
    bGrowth = "{:.2%}".format(round(b, 2)/data.iloc[pos-51, book_col]-1)
    rowData.append(bGrowth)
    e = d['cp']/d['pe_ttm'][mode]
    rowData.append(round(e, 2))
    eGrowth = "{:.2%}".format(round(e, 2)/data.iloc[pos-51, earning_col]-1)
    rowData.append(eGrowth)
    # roe = "{:.2%}".format(round(d['pb'][mode], 2)/round(d['pe_ttm'][mode], 2))
    roe = "{:.4}".format(round(d['pb'][mode], 2) / round(d['pe_ttm'][mode], 2))
    rowData.append(roe)
    rowData.append(round(d['ps_ttm'][mode], 2))
    rowData.append(round(d['dyr'][mode], 2))
    s = d['cp'] / d['ps_ttm'][mode]
    rowData.append(round(s, 2))
    div = d['cp'] * d['dyr'][mode]
    rowData.append(round(div, 2))
    return rowData


def parse_single_index(d):
    if d["stockCode"] is None:
        return
    code = stockMap[d["stockCode"]]
    file_name = u"index/%s.csv" % code
    todayDate = today.split('-')
    todayWeek = datetime.date(int(todayDate[0]), int(todayDate[1]), int(todayDate[2])).isocalendar()[1]
    data = pd.read_csv(file_name)
    lastDate = data.iloc[-1, 0].split('/')
    lastWeek = datetime.date(int(lastDate[0]), int(lastDate[1]), int(lastDate[2])).isocalendar()[1]

    if lastWeek == todayWeek:
        pos = len(data.index) - 1
    else:
        pos = len(data.index)

    if d["stockCode"] in equalAvgIndex:
        data.loc[pos] = process(d, data, pos, 'ew')
    else:
        data.loc[pos] = process(d, data, pos, 'mcw')

    summary.append([stockMap[d["stockCode"]], 'Annual B Growth', 'Annual E Growth', 'ROE'])
    for nyear in range((pos + 1) / 51, -1, -1):
        bGrowth = (data.iloc[pos - nyear * 51, book_col] / data.iloc[pos - (nyear+1) * 51, book_col]) - 1
        eGrowth = (data.iloc[pos - nyear * 51, earning_col] / data.iloc[pos - (nyear+1) * 51, earning_col]) - 1
        roe = float(data.iloc[pos - nyear * 51, roe_col])
        summary.append([data.iloc[pos - nyear * 51, date_col], "{:.2%}".format(bGrowth), "{:.2%}".format(eGrowth), "{:.2%}".format(roe)])
    # for nyear in range((pos + 1) / 51, 0, -1):
        # bGrowth = (data.iloc[pos, book_col] / data.iloc[pos - nyear * 51, book_col]) ** (1 / float(nyear)) - 1
        # eGrowth = (data.iloc[pos, earning_col] / data.iloc[pos - nyear * 51, earning_col]) ** (1 / float(nyear)) - 1
        # summary.append(['%sY' % nyear, "{:.2%}".format(bGrowth), "{:.2%}".format(eGrowth)])
    for nyear in (5, 3):
        bGrowth = (data.iloc[pos, book_col] / data.iloc[pos - nyear * 51, book_col]) ** (1 / float(nyear)) - 1
        eGrowth = (data.iloc[pos, earning_col] / data.iloc[pos - nyear * 51, earning_col]) ** (1 / float(nyear)) - 1
        summary.append(['%sY annual' % nyear, "{:.2%}".format(bGrowth), "{:.2%}".format(eGrowth)])

    with open(file_name, 'w') as f:
        data.to_csv(f, index=False, encoding='utf_8_sig')


# ----------------- send api request -----------------
summary = list()

response = get_response(url='https://open.lixinger.com/api/a/index/fundamental',
                        data={
                            "stockCodes": stockCodes,
                            "metricsList": metrics,
                            "token": token,
                            "date": today
                        })
# print response
jsonList = response["data"]

for d in jsonList:
    parse_single_index(d)

response = get_response(url='https://open.lixinger.com/api/h/index/fundamental',
                        data={
                            "stockCodes": [
                                "HSI",
                                "HSCEI"
                            ],
                            "metricsList": metrics,
                            "token": token,
                            "date": today
                        })
# print response
jsonList = response["data"]

# for d in jsonList:
#     parse_single_index(d)


# ------------------ summarize annual return ------------------
with open('return_summary.csv', 'wb') as summaryf:
    writer = csv.writer(summaryf)
    writer.writerows(summary)

# ------------------ analyse data ------------------
for stockName in stockMap.values():
    file_name = u"index/%s.csv" % stockName
    df = pd.read_csv(file_name, parse_dates=[0], index_col=0, encoding='utf_8_sig')
    image = df[['cp']].plot()
    # image = df.plot(subplots=True)
    plt.savefig(file_name[:-4])
    image = df[['B']].plot()
    plt.savefig(file_name[:-4] + 'B')
    image = df[['pb']].plot()
    plt.savefig(file_name[:-4] + 'PB')
    image = df[['E']].plot()
    plt.savefig(file_name[:-4] + 'E')
    image = df[['pe']].plot()
    plt.savefig(file_name[:-4] + 'PE')
    image = df[['ROE']].plot()
    plt.savefig(file_name[:-4] + 'ROE')
    image = df[['ps']].plot()
    plt.savefig(file_name[:-4] + 'PS')
    image = df[['S']].plot()
    plt.savefig(file_name[:-4] + 'S')
    image = df[['div']].plot()
    plt.savefig(file_name[:-4] + 'DIV')
    image = df[['total div']].plot()
    plt.savefig(file_name[:-4] + 'TOTAL_DIV')
