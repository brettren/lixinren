#!/usr/bin/python
# -*- coding:utf8 -*-

import akshare as ak, pandas as pd, datetime

today = pd.Timestamp(datetime.date.today())
df = ak.tool_trade_date_hist_sina()
dates = pd.to_datetime(df['trade_date'])
print(dates[dates <= today].max().strftime('%Y-%m-%d'))