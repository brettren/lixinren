import akshare as ak
import pandas as pd
import datetime as _dt

_today = pd.Timestamp(_dt.date.today())
_df = ak.tool_trade_date_hist_sina()
_dates = pd.to_datetime(_df['trade_date'])
today = _dates[_dates <= _today].max().strftime('%Y-%m-%d')
token = "YOUR_TOKEN_HERE"
positionMaps = {
    "H30533": "中国互联网50",
    "399296": "创成长",
    "931139": "CS消费50",
    "931484": "CS医药创新",
    "399295": "创业蓝筹",
    "931140": "医药50",
    "930641": "中证中药",
    "399324": "深证红利",
    "399814": "大农业",
    "000941": "新能源汽车",
    "399965": "800地产",
    "H30035": "300非银",
    "931468": "红利质量",
    "000859": "国企一带一路",
    "399997": "中证白酒",
    "931068": "消费龙头",
    "HSCGSI": "恒生消费指数"
}
observationPositionMaps = {
}