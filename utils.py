import requests
import json


def get_index_codes(token, stockCodes, headers):
    stock_codes_url = 'https://open.lixinger.com/api/a/indice'
    stock_codes_data = {
        "token": token,
        "stockCodes": stockCodes
    }
    response = requests.post(url=stock_codes_url, headers=headers, data=json.dumps(stock_codes_data)).json()
    data = response["data"]
    cnName_map = {}
    publishDate_map = {}
    for d in data:
        cnName_map[d["stockCode"]] = d["cnName"]
        publishDate_map[d["stockCode"]] = d["publishDate"]
    return cnName_map, publishDate_map
