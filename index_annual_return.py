#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
import requests
import json
import datetime
metrics = [
        "pe_ttm.y_10.weightedAvg",
        "pe_ttm.y_10.equalAvg",
        "pb.y_10.weightedAvg",
        "pb.y_10.equalAvg",
        "dyr.weightedAvg",
        "dyr.equalAvg",
        "cp"  # for index
]

stockCodes = [
    "000016"
]
token = "afb329e1-73ea-41d6-9672-dcf5ba22a4bc"
headers = {'Content-Type': 'application/json'}
today = datetime.date.today().strftime("%Y-%m-%d")
# today = "2020-01-03"
oneYearAgo = (datetime.datetime.now() - datetime.timedelta(days=1*52*7)).strftime("%Y-%m-%d")
twoYearAgo = (datetime.datetime.now() - datetime.timedelta(days=2*52*7)).strftime("%Y-%m-%d")
threeYearAgo = (datetime.datetime.now() - datetime.timedelta(days=3*52*7)).strftime("%Y-%m-%d")
fourYearAgo = (datetime.datetime.now() - datetime.timedelta(days=4*52*7)).strftime("%Y-%m-%d")
fiveYearAgo = (datetime.datetime.now() - datetime.timedelta(days=5*52*7)).strftime("%Y-%m-%d")

def get_response(url, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data)).json()
    return response


def process(data):
    if len(data) == 0:
        return
    close_point = datetime["cp"]

    d = data[0]["date"]


response = get_response(url='https://open.lixinger.com/api/a/indice/fundamental',
                        data={
                            "stockCodes": stockCodes,
                            "metrics": metrics,
                            "token": token,
                            "date": today
                        })
# print 'response a:'
# print response
data = response["data"]
process(data)


#
