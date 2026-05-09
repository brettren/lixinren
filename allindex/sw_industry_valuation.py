# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import os
import akshare as ak
import numpy as np
from datetime import datetime, timezone, timedelta


def fetch_sw_first_level():
    df = ak.sw_index_first_info()
    return df


def compute_percentile_rank(values, reverse=False):
    """Compute percentile rank (0-100) for each value in the array.
    reverse=True means higher value gets lower percentile (used for dividend)."""
    n = len(values)
    ranks = np.zeros(n)
    sorted_indices = np.argsort(values)
    if reverse:
        sorted_indices = sorted_indices[::-1]
    for rank, idx in enumerate(sorted_indices):
        ranks[idx] = rank / (n - 1) * 100 if n > 1 else 50
    return ranks


def compute_valuation_score(df):
    pe_ttm = df['TTM(滚动)市盈率'].values.astype(float)
    pb = df['市净率'].values.astype(float)
    div_yield = df['静态股息率'].values.astype(float)

    pe_pct = compute_percentile_rank(pe_ttm, reverse=False)
    pb_pct = compute_percentile_rank(pb, reverse=False)
    div_pct = compute_percentile_rank(div_yield, reverse=True)

    scores = []
    for i in range(len(df)):
        pe_score = (100 - pe_pct[i]) / 100 * 35
        pb_score = (100 - pb_pct[i]) / 100 * 25
        div_score = (100 - div_pct[i]) / 100 * 25

        consistency_bonus = 0
        if pe_pct[i] < 33 and pb_pct[i] < 33:
            consistency_bonus = 15
        elif pe_pct[i] < 50 and pb_pct[i] < 50:
            consistency_bonus = 8

        total = round(pe_score + pb_score + div_score + consistency_bonus, 1)
        scores.append(total)

    df = df.copy()
    df['PE百分位'] = np.round(pe_pct, 1)
    df['PB百分位'] = np.round(pb_pct, 1)
    df['股息率百分位'] = np.round(div_pct, 1)
    df['评分'] = scores
    return df


def save_csv(df, output_path):
    tz = timezone(timedelta(hours=8))
    date_str = datetime.now(tz).strftime('%Y-%m-%d')

    with open(output_path, 'w', encoding='utf_8_sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date_str, '行业代码', '行业名称', '成份个数', '静态市盈率',
                         'TTM市盈率', '市净率', '静态股息率', 'PE百分位', 'PB百分位',
                         '股息率百分位', '评分'])
        for _, row in df.iterrows():
            writer.writerow([
                row['行业代码'],
                row['行业名称'],
                int(row['成份个数']),
                row['静态市盈率'],
                row['TTM(滚动)市盈率'],
                row['市净率'],
                row['静态股息率'],
                row['PE百分位'],
                row['PB百分位'],
                row['股息率百分位'],
                row['评分'],
            ])
    print(f"Saved {len(df)} industries to {output_path}")


def main():
    print("Fetching 申万一级行业 data...")
    df = fetch_sw_first_level()
    print(f"Got {len(df)} industries")

    df = compute_valuation_score(df)

    output_path = os.path.join(os.path.dirname(__file__), "sw_industry_valuation.csv")
    save_csv(df, output_path)

    df_sorted = df.sort_values('评分', ascending=False)
    print("\nTop 10 by valuation score:")
    for _, row in df_sorted.head(10).iterrows():
        print(f"  {row['行业名称']:6s}  PE={row['TTM(滚动)市盈率']:6.2f}  PB={row['市净率']:5.2f}  "
              f"Div={row['静态股息率']:5.2f}%  Score={row['评分']}")


if __name__ == '__main__':
    main()
