# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import sys
import os
import html
import re
import glob

def find_latest_csv():
    pattern = os.path.join(os.path.dirname(__file__), "all_index_drawdown_current_and_history_2*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files)

def parse_percent(s):
    if not s or s.strip() == '':
        return None
    s = s.strip().replace('%', '')
    try:
        return float(s)
    except ValueError:
        return None

def parse_float(s):
    if not s or s.strip() == '':
        return None
    try:
        return float(s)
    except ValueError:
        return None

def score_index(row):
    score = 0
    w = row.get('_parsed', {})
    ftld = w.get('fall_to_lowest_drawdown')
    if ftld is not None:
        if ftld > -15:
            score += 30
        elif ftld > -25:
            score += 25
        elif ftld > -35:
            score += 20
        elif ftld > -50:
            score += 10
    pe_pos = w.get('pe10pos')
    if pe_pos is not None:
        if pe_pos < 20:
            score += 25
        elif pe_pos < 30:
            score += 20
        elif pe_pos < 50:
            score += 10
    pb_pos = w.get('pb10pos')
    if pb_pos is not None:
        if pb_pos < 20:
            score += 15
        elif pb_pos < 30:
            score += 12
        elif pb_pos < 50:
            score += 6
    roe = w.get('roe')
    if roe is not None:
        if roe > 15:
            score += 20
        elif roe > 10:
            score += 15
        elif roe > 5:
            score += 5
    div = w.get('div')
    if div is not None:
        if div > 4:
            score += 15
        elif div > 3:
            score += 12
        elif div > 2:
            score += 8
        elif div > 1:
            score += 3
    return score

def color_class_ftld(val):
    if val is None:
        return ''
    if val > -15:
        return 'bg-green-strong'
    if val > -25:
        return 'bg-green'
    if val > -35:
        return 'bg-green-light'
    if val > -50:
        return 'bg-yellow'
    return 'bg-red'

def color_class_percentile(val, invert=False):
    if val is None:
        return ''
    if not invert:
        if val < 20:
            return 'bg-green-strong'
        if val < 30:
            return 'bg-green'
        if val < 50:
            return 'bg-green-light'
        if val < 70:
            return 'bg-yellow'
        return 'bg-red'
    else:
        if val > 80:
            return 'bg-green-strong'
        if val > 70:
            return 'bg-green'
        if val > 50:
            return 'bg-green-light'
        if val > 30:
            return 'bg-yellow'
        return 'bg-red'

def color_class_roe(val):
    if val is None:
        return ''
    if val > 15:
        return 'bg-green-strong'
    if val > 10:
        return 'bg-green'
    if val > 5:
        return 'bg-green-light'
    return 'bg-red'

def color_class_div(val):
    if val is None:
        return ''
    if val > 4:
        return 'bg-green-strong'
    if val > 3:
        return 'bg-green'
    if val > 2:
        return 'bg-green-light'
    if val > 1:
        return 'bg-yellow'
    return ''

def color_class_score(val):
    if val >= 80:
        return 'bg-green-strong'
    if val >= 60:
        return 'bg-green'
    if val >= 40:
        return 'bg-green-light'
    if val >= 20:
        return 'bg-yellow'
    return 'bg-red'

def generate_html(csv_path, output_path):
    rows = []
    with open(csv_path, 'r', encoding='utf_8_sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 16:
                continue
            d = {
                'sector': row[0],
                'stockCode': row[1],
                'publishDate': row[2],
                'stockName': row[3],
                'style': row[4],
                'hasPosition': row[5].strip(),
                'current_drawdown': row[6],
                'largest_drawdown': row[7],
                'fall_to_lowest_drawdown': row[8],
                'pe': row[9],
                'pe10pos': row[10],
                'pb': row[11],
                'pb10pos': row[12],
                'roe': row[13],
                'div': row[14],
                'funds': row[15] if len(row) > 15 else '',
            }
            d['_parsed'] = {
                'current_drawdown': parse_percent(d['current_drawdown']),
                'largest_drawdown': parse_percent(d['largest_drawdown']),
                'fall_to_lowest_drawdown': parse_percent(d['fall_to_lowest_drawdown']),
                'pe10pos': parse_percent(d['pe10pos']),
                'pb10pos': parse_percent(d['pb10pos']),
                'roe': parse_percent(d['roe']),
                'div': parse_percent(d['div']),
            }
            d['score'] = score_index(d)
            rows.append(d)

    date_str = header[0] if header else ''
    rows_json_parts = []
    for r in rows:
        p = r['_parsed']
        fund_count = len([f.strip() for f in r['funds'].split(',') if f.strip()]) if r['funds'].strip() else 0
        first_fund = ''
        if r['funds'].strip():
            first_fund = r['funds'].split(',')[0].strip()
        rows_json_parts.append(
            f'["{esc(r["sector"])}","{esc(r["stockCode"])}","{esc(r["publishDate"])}",'
            f'"{esc(r["stockName"])}","{esc(r["style"])}","{esc(r["hasPosition"])}",'
            f'"{esc(r["current_drawdown"])}","{esc(r["largest_drawdown"])}","{esc(r["fall_to_lowest_drawdown"])}",'
            f'"{esc(r["pe"])}","{esc(r["pe10pos"])}","{esc(r["pb"])}","{esc(r["pb10pos"])}",'
            f'"{esc(r["roe"])}","{esc(r["div"])}",{r["score"]},'
            f'{json_num(p["fall_to_lowest_drawdown"])},'
            f'{json_num(p["current_drawdown"])},'
            f'{json_num(p["largest_drawdown"])},'
            f'{json_num(p["pe10pos"])},'
            f'{json_num(p["pb10pos"])},'
            f'{json_num(p["roe"])},'
            f'{json_num(p["div"])},'
            f'{fund_count},"{esc(first_fund)}","{esc(r["funds"])}"]'
        )

    rows_json = ',\n'.join(rows_json_parts)

    portfolios = generate_portfolios(rows)
    portfolios_js = portfolios_to_js(portfolios)
    s_count = len(portfolios.get('S', {}).get('items', []))
    m_count = len(portfolios.get('M', {}).get('items', []))
    l_count = len(portfolios.get('L', {}).get('items', []))

    all_themes = []
    for p in portfolios.values():
        for item in p.get('items', []):
            if item['theme'] not in all_themes:
                all_themes.append(item['theme'])
    theme_colors = get_theme_colors(all_themes)
    theme_css = '\n'.join(f".theme-{t} {{ background: {c}; }}" for t, c in theme_colors.items())
    theme_colors_js = ',\n  '.join(f"'{t}':'{c}'" for t, c in theme_colors.items())
    overlap_caps = portfolios.get('_overlap_caps', {'消费': 25, '医药': 20, '互联网': 15})
    overlap_caps_js = '{' + ','.join(f"'{k}':{v}" for k, v in overlap_caps.items()) + '}'
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>指数回撤与估值分析 - {date_str}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f5f5; color: #333; font-size: 13px; }}
.container {{ max-width: 100%; padding: 12px; }}
h1 {{ font-size: 18px; margin-bottom: 4px; color: #1a1a1a; }}
.subtitle {{ color: #666; font-size: 12px; margin-bottom: 12px; }}
.controls {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; align-items: center; }}
.controls label {{ font-size: 12px; color: #555; }}
.controls select, .controls input {{ font-size: 12px; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; background: #fff; }}
.controls input[type="text"] {{ width: 200px; }}
.controls button {{ font-size: 12px; padding: 4px 12px; border: 1px solid #4a90d9; border-radius: 4px; background: #4a90d9; color: white; cursor: pointer; }}
.controls button:hover {{ background: #357abd; }}
.controls button.active {{ background: #2c5f8f; }}
.controls .filter-group {{ display: flex; align-items: center; gap: 4px; }}
.stats {{ font-size: 12px; color: #666; margin-bottom: 8px; }}
.table-wrap {{ overflow: auto; max-height: calc(100vh - 180px); background: white; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
table {{ border-collapse: collapse; width: 100%; min-width: 1400px; }}
th {{ background: #2c3e50; color: white; padding: 8px 6px; text-align: left; font-size: 11px; font-weight: 600; position: sticky; top: 0; z-index: 10; cursor: pointer; user-select: none; white-space: nowrap; }}
th:hover {{ background: #34495e; }}
th .sort-arrow {{ font-size: 10px; margin-left: 2px; }}
td {{ padding: 6px; border-bottom: 1px solid #eee; white-space: nowrap; font-size: 12px; }}
tr:hover {{ background: #f0f7ff !important; }}
tr.has-position {{ font-weight: 600; }}
.bg-green-strong {{ background: #c6efce; }}
.bg-green {{ background: #dff0d8; }}
.bg-green-light {{ background: #e8f5e9; }}
.bg-yellow {{ background: #fff3cd; }}
.bg-red {{ background: #f8d7da; }}
.score-cell {{ font-weight: 700; font-size: 13px; text-align: center; }}
.position-star {{ color: #e67e22; font-weight: bold; }}
.fund-cell {{ max-width: 200px; overflow: hidden; text-overflow: ellipsis; cursor: pointer; position: relative; }}
.fund-cell:hover {{ overflow: visible; white-space: normal; background: #fff; position: relative; z-index: 5; box-shadow: 0 2px 8px rgba(0,0,0,.15); border-radius: 4px; padding: 6px; max-width: 600px; }}
.fund-count {{ color: #888; font-size: 11px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; font-size: 11px; align-items: center; }}
.legend-item {{ display: flex; align-items: center; gap: 4px; }}
.legend-color {{ width: 14px; height: 14px; border-radius: 2px; border: 1px solid #ddd; }}
.neg-val {{ color: #c0392b; }}
.pos-val {{ color: #27ae60; }}
.sector-tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
.sector-a {{ background: #e74c3c; color: white; }}
.sector-hk {{ background: #3498db; color: white; }}
.style-tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; }}
.style-价值 {{ background: #27ae60; color: white; }}
.style-成长 {{ background: #8e44ad; color: white; }}
.style-周期 {{ background: #e67e22; color: white; }}
.style-宽基 {{ background: #2c3e50; color: white; }}
.style-default {{ background: #95a5a6; color: white; }}
#nodata {{ display: none; padding: 40px; text-align: center; color: #999; }}
.rec-section {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.12); margin-bottom: 12px; overflow: hidden; }}
.rec-header {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: linear-gradient(135deg, #1a5276, #2c3e50); color: white; cursor: pointer; user-select: none; }}
.rec-header h2 {{ font-size: 15px; font-weight: 600; margin: 0; }}
.rec-header .rec-arrow {{ font-size: 12px; transition: transform .2s; }}
.rec-header .rec-arrow.open {{ transform: rotate(180deg); }}
.rec-body {{ display: none; padding: 12px 16px; }}
.rec-body.open {{ display: block; }}
.rec-tabs {{ display: flex; gap: 0; margin-bottom: 12px; border-radius: 6px; overflow: hidden; border: 1px solid #4a90d9; }}
.rec-tabs button {{ flex: 1; padding: 8px 12px; font-size: 12px; border: none; background: #f8f9fa; color: #4a90d9; cursor: pointer; font-weight: 600; transition: all .15s; }}
.rec-tabs button:not(:last-child) {{ border-right: 1px solid #4a90d9; }}
.rec-tabs button.active {{ background: #4a90d9; color: white; }}
.rec-tabs button:hover:not(.active) {{ background: #e8f0fe; }}
.rec-bar {{ display: flex; height: 28px; border-radius: 4px; overflow: hidden; margin-bottom: 12px; box-shadow: inset 0 1px 2px rgba(0,0,0,.08); }}
.rec-bar div {{ display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 600; color: white; white-space: nowrap; overflow: hidden; min-width: 20px; }}
.rec-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px; }}
.rec-table th {{ background: #34495e; color: white; padding: 7px 8px; text-align: left; font-size: 11px; font-weight: 600; white-space: nowrap; }}
.rec-table td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
.rec-table tr:hover {{ background: #f0f7ff; }}
.rec-table .w-col {{ text-align: center; font-weight: 700; font-size: 13px; }}
.rec-table .s-col {{ text-align: center; }}
.theme-tag {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; color: white; }}
{theme_css}
.rec-notes {{ font-size: 11px; color: #777; line-height: 1.6; padding: 8px 12px; background: #f8f9fa; border-radius: 4px; margin-top: 8px; }}
.rec-notes strong {{ color: #555; }}
.rec-summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 10px; font-size: 12px; }}
.rec-summary .rec-stat {{ background: #f0f4f8; padding: 6px 12px; border-radius: 4px; }}
.rec-summary .rec-stat span {{ font-weight: 700; color: #2c3e50; }}
.rec-asset-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding: 8px 12px; background: #f0f4f8; border-radius: 6px; }}
.rec-asset-row label {{ font-size: 13px; font-weight: 600; color: #2c3e50; white-space: nowrap; }}
.rec-asset-row input {{ width: 160px; font-size: 14px; padding: 6px 10px; border: 1px solid #4a90d9; border-radius: 4px; text-align: right; }}
.rec-asset-row input:focus {{ outline: none; border-color: #2c5f8f; box-shadow: 0 0 0 2px rgba(74,144,217,.2); }}
.rec-asset-unit {{ font-size: 13px; color: #555; }}
.amt-col {{ text-align: right; font-weight: 600; color: #c0392b; font-size: 12px; white-space: nowrap; }}
@media (max-width: 768px) {{
  .container {{ padding: 8px; }}
  h1 {{ font-size: 15px; }}
  .legend {{ display: none; }}
  .controls {{ gap: 6px; }}
  .controls input[type="text"] {{ width: 120px; }}
  .controls select, .controls input {{ font-size: 11px; padding: 3px 6px; }}
  .controls label {{ font-size: 11px; }}
  .table-wrap {{ max-height: calc(100vh - 140px); border-radius: 4px; }}
  table {{ min-width: 900px; }}
  th {{ padding: 6px 4px; font-size: 10px; }}
  td {{ padding: 4px 3px; font-size: 11px; }}
  .score-cell {{ font-size: 12px; }}
  .fund-cell {{ max-width: 120px; }}
  .sector-tag, .style-tag {{ font-size: 9px; padding: 1px 4px; }}
  .rec-header h2 {{ font-size: 13px; }}
  .rec-body {{ padding: 8px 10px; }}
  .rec-tabs button {{ font-size: 11px; padding: 6px 8px; }}
  .rec-table {{ font-size: 11px; }}
  .rec-table th {{ font-size: 10px; padding: 5px 4px; }}
  .rec-table td {{ padding: 4px; font-size: 10px; }}
  .rec-summary {{ font-size: 11px; gap: 8px; }}
  .rec-bar {{ height: 22px; }}
  .rec-bar div {{ font-size: 9px; }}
  .rec-notes {{ font-size: 10px; }}
  .theme-tag {{ font-size: 9px; padding: 1px 5px; }}
  .rec-asset-row {{ padding: 6px 8px; gap: 6px; }}
  .rec-asset-row label {{ font-size: 11px; }}
  .rec-asset-row input {{ width: 120px; font-size: 12px; padding: 4px 8px; }}
  .amt-col {{ font-size: 10px; }}
}}
</style>
</head>
<body>
<div class="container">
<h1>指数回撤与估值分析</h1>
<p class="subtitle">数据日期: {date_str} | 共 {len(rows)} 只指数</p>

<div class="legend">
<span style="font-weight:600;">颜色说明:</span>
<div class="legend-item"><div class="legend-color bg-green-strong"></div> 极好</div>
<div class="legend-item"><div class="legend-color bg-green"></div> 良好</div>
<div class="legend-item"><div class="legend-color bg-green-light"></div> 一般</div>
<div class="legend-item"><div class="legend-color bg-yellow"></div> 注意</div>
<div class="legend-item"><div class="legend-color bg-red"></div> 警告</div>
<span style="margin-left:12px;font-weight:600;">评分:</span>
<span>距最低回撤(30) + PE百分位(25) + PB百分位(15) + ROE(20) + 股息率(15) = 满分105</span>
</div>

<div class="controls">
<div class="filter-group">
<label>搜索:</label>
<input type="text" id="searchInput" placeholder="名称/代码/基金..." oninput="applyFilters()">
</div>
<div class="filter-group">
<label>市场:</label>
<select id="sectorFilter" onchange="applyFilters()">
<option value="">全部</option>
<option value="A股">A股</option>
<option value="港股">港股</option>
</select>
</div>
<div class="filter-group">
<label>风格:</label>
<select id="styleFilter" onchange="applyFilters()">
<option value="">全部</option>
<option value="价值">价值</option>
<option value="成长">成长</option>
<option value="周期">周期</option>
<option value="宽基">宽基</option>
</select>
</div>
<div class="filter-group">
<label>持仓:</label>
<select id="posFilter" onchange="applyFilters()">
<option value="">全部</option>
<option value="yes">有持仓</option>
<option value="no">无持仓</option>
</select>
</div>
<div class="filter-group">
<label>评分≥:</label>
<select id="scoreFilter" onchange="applyFilters()">
<option value="0">全部</option>
<option value="40">40+</option>
<option value="50">50+</option>
<option value="60">60+</option>
<option value="70">70+</option>
<option value="80">80+</option>
</select>
</div>
<button onclick="resetFilters()">重置</button>
</div>

<div class="stats" id="stats"></div>

<div class="rec-section">
<div class="rec-header" onclick="toggleRec()">
<h2>📊 均衡配置推荐组合</h2>
<span class="rec-arrow" id="recArrow">▼</span>
</div>
<div class="rec-body" id="recBody">
<div class="rec-tabs">
<button id="tabS" onclick="showPortfolio('S')" class="active">精简组合 ({s_count}只)</button>
<button id="tabM" onclick="showPortfolio('M')">均衡组合 ({m_count}只)</button>
<button id="tabL" onclick="showPortfolio('L')">全面组合 ({l_count}只)</button>
</div>
<div class="rec-asset-row">
<label>投入总金额:</label>
<input type="text" id="assetInput" placeholder="例: 100000" oninput="onAssetInput()">
<span class="rec-asset-unit">元</span>
</div>
<div class="rec-summary" id="recSummary"></div>
<div class="rec-bar" id="recBar"></div>
<table class="rec-table">
<thead><tr>
<th>主题</th><th>指数名称</th><th>代码</th><th>配比</th><th>金额</th><th>评分</th>
<th>PE位</th><th>PB位</th><th>ROE</th><th>股息率</th><th>距最低</th><th>推荐基金</th>
</tr></thead>
<tbody id="recTbody"></tbody>
</table>
<div class="rec-notes" id="recNotes"></div>
</div>
</div>

<div class="table-wrap">
<table id="mainTable">
<thead>
<tr>
<th onclick="sortBy(0)">市场 <span class="sort-arrow" id="arrow0"></span></th>
<th onclick="sortBy(1)">代码 <span class="sort-arrow" id="arrow1"></span></th>
<th onclick="sortBy(3)">名称 <span class="sort-arrow" id="arrow3"></span></th>
<th onclick="sortBy(4)">风格 <span class="sort-arrow" id="arrow4"></span></th>
<th onclick="sortBy(5)">持仓 <span class="sort-arrow" id="arrow5"></span></th>
<th onclick="sortBy(15)" title="综合评分">评分 <span class="sort-arrow" id="arrow15"></span></th>
<th onclick="sortBy(6)" title="当前回撤">当前回撤 <span class="sort-arrow" id="arrow6"></span></th>
<th onclick="sortBy(7)" title="历史最大回撤(10年)">最大回撤 <span class="sort-arrow" id="arrow7"></span></th>
<th onclick="sortBy(8)" title="距最大回撤还有多远(越小越安全)">距最低↓ <span class="sort-arrow" id="arrow8"></span></th>
<th onclick="sortBy(9)" title="市盈率">PE <span class="sort-arrow" id="arrow9"></span></th>
<th onclick="sortBy(10)" title="PE 10年百分位(越低越便宜)">PE位 <span class="sort-arrow" id="arrow10"></span></th>
<th onclick="sortBy(11)" title="市净率">PB <span class="sort-arrow" id="arrow11"></span></th>
<th onclick="sortBy(12)" title="PB 10年百分位(越低越便宜)">PB位 <span class="sort-arrow" id="arrow12"></span></th>
<th onclick="sortBy(13)" title="净资产收益率(越高越好)">ROE <span class="sort-arrow" id="arrow13"></span></th>
<th onclick="sortBy(14)" title="股息率(越高越好)">股息率 <span class="sort-arrow" id="arrow14"></span></th>
<th onclick="sortBy(23)" title="可跟踪基金数量">基金 <span class="sort-arrow" id="arrow23"></span></th>
</tr>
</thead>
<tbody id="tbody"></tbody>
</table>
<div id="nodata">没有匹配的数据</div>
</div>
</div>

<script>
const DATA=[
{rows_json}
];
// Column indices: 0=sector,1=code,2=pubDate,3=name,4=style,5=position,
// 6=currDD,7=largestDD,8=ftld,9=pe,10=pePos,11=pb,12=pbPos,13=roe,14=div,
// 15=score,16=ftld_n,17=currDD_n,18=largestDD_n,19=pePos_n,20=pbPos_n,
// 21=roe_n,22=div_n,23=fundCount,24=firstFund,25=allFunds

let sortCol = 15;
let sortAsc = false;
let filtered = [...Array(DATA.length).keys()];

function esc(s) {{ return s; }}

function colorFtld(v) {{
  if(v===null) return '';
  if(v>-15) return 'bg-green-strong';
  if(v>-25) return 'bg-green';
  if(v>-35) return 'bg-green-light';
  if(v>-50) return 'bg-yellow';
  return 'bg-red';
}}
function colorPct(v) {{
  if(v===null) return '';
  if(v<20) return 'bg-green-strong';
  if(v<30) return 'bg-green';
  if(v<50) return 'bg-green-light';
  if(v<70) return 'bg-yellow';
  return 'bg-red';
}}
function colorRoe(v) {{
  if(v===null) return '';
  if(v>15) return 'bg-green-strong';
  if(v>10) return 'bg-green';
  if(v>5) return 'bg-green-light';
  return 'bg-red';
}}
function colorDiv(v) {{
  if(v===null) return '';
  if(v>4) return 'bg-green-strong';
  if(v>3) return 'bg-green';
  if(v>2) return 'bg-green-light';
  if(v>1) return 'bg-yellow';
  return '';
}}
function colorScore(v) {{
  if(v>=80) return 'bg-green-strong';
  if(v>=60) return 'bg-green';
  if(v>=40) return 'bg-green-light';
  if(v>=20) return 'bg-yellow';
  return 'bg-red';
}}
function fmtNum(s) {{
  if(!s || s.trim()==='') return s;
  var n = parseFloat(s);
  if(isNaN(n)) return s;
  return n%1===0 ? n.toFixed(0) : n.toFixed(2).replace(/0+$/,'').replace(/\\.$/,'');
}}
function valClass(s) {{
  if(!s) return '';
  return s.includes('-') ? 'neg-val' : (parseFloat(s)>0 ? 'pos-val' : '');
}}
function sectorTag(s) {{
  if(s==='A股') return '<span class="sector-tag sector-a">A股</span>';
  if(s==='港股') return '<span class="sector-tag sector-hk">港股</span>';
  return s;
}}
function styleTag(s) {{
  if(!s) return '';
  const cls = ['价值','成长','周期','宽基'].includes(s) ? 'style-'+s : 'style-default';
  return '<span class="style-tag '+cls+'">'+s+'</span>';
}}

function sortBy(col) {{
  if(sortCol === col) sortAsc = !sortAsc;
  else {{ sortCol = col; sortAsc = (col<=5 || col===23); }}
  renderTable();
}}

function getVal(idx, col) {{
  const r = DATA[idx];
  if(col===15) return r[15];
  if(col===16||col===8) return r[16];
  if(col===17||col===6) return r[17];
  if(col===18||col===7) return r[18];
  if(col===19||col===10) return r[19];
  if(col===20||col===12) return r[20];
  if(col===21||col===13) return r[21];
  if(col===22||col===14) return r[22];
  if(col===23) return r[23];
  if(col===9) return parseFloat(r[9])||99999;
  if(col===11) return parseFloat(r[11])||99999;
  return r[col];
}}

function applyFilters() {{
  const search = document.getElementById('searchInput').value.toLowerCase();
  const sector = document.getElementById('sectorFilter').value;
  const style = document.getElementById('styleFilter').value;
  const pos = document.getElementById('posFilter').value;
  const minScore = parseInt(document.getElementById('scoreFilter').value);

  filtered = [];
  for(let i=0; i<DATA.length; i++) {{
    const r = DATA[i];
    if(sector && r[0]!==sector) continue;
    if(style && r[4]!==style) continue;
    if(pos==='yes' && r[5]!=='*') continue;
    if(pos==='no' && r[5]==='*') continue;
    if(r[15]<minScore) continue;
    if(search) {{
      const hay = (r[1]+r[3]+r[4]+r[24]+r[25]).toLowerCase();
      if(!hay.includes(search)) continue;
    }}
    filtered.push(i);
  }}
  renderTable();
}}

function resetFilters() {{
  document.getElementById('searchInput').value='';
  document.getElementById('sectorFilter').value='';
  document.getElementById('styleFilter').value='';
  document.getElementById('posFilter').value='';
  document.getElementById('scoreFilter').value='0';
  applyFilters();
}}

function renderTable() {{
  filtered.sort((a,b) => {{
    let va = getVal(a, sortCol);
    let vb = getVal(b, sortCol);
    if(va===null) va = sortAsc ? 99999 : -99999;
    if(vb===null) vb = sortAsc ? 99999 : -99999;
    if(typeof va==='string') return sortAsc ? va.localeCompare(vb,'zh') : vb.localeCompare(va,'zh');
    return sortAsc ? va-vb : vb-va;
  }});

  for(let i=0; i<=25; i++) {{
    const el = document.getElementById('arrow'+i);
    if(el) el.textContent = sortCol===i ? (sortAsc ? '▲' : '▼') : '';
  }}

  const tbody = document.getElementById('tbody');
  const nodata = document.getElementById('nodata');
  if(filtered.length===0) {{
    tbody.innerHTML='';
    nodata.style.display='block';
  }} else {{
    nodata.style.display='none';
    const parts = [];
    for(const idx of filtered) {{
      const r = DATA[idx];
      const hp = r[5]==='*';
      parts.push(
        '<tr'+(hp?' class="has-position"':'')+'>' +
        '<td>'+sectorTag(r[0])+'</td>' +
        '<td>'+r[1]+'</td>' +
        '<td>'+r[3]+'</td>' +
        '<td>'+styleTag(r[4])+'</td>' +
        '<td>'+(hp?'<span class="position-star">★</span>':'')+'</td>' +
        '<td class="score-cell '+colorScore(r[15])+'">'+r[15]+'</td>' +
        '<td class="'+valClass(r[6])+'">'+r[6]+'</td>' +
        '<td class="neg-val">'+r[7]+'</td>' +
        '<td class="'+colorFtld(r[16])+'">'+r[8]+'</td>' +
        '<td>'+fmtNum(r[9])+'</td>' +
        '<td class="'+colorPct(r[19])+'">'+r[10]+'</td>' +
        '<td>'+fmtNum(r[11])+'</td>' +
        '<td class="'+colorPct(r[20])+'">'+r[12]+'</td>' +
        '<td class="'+colorRoe(r[21])+'">'+r[13]+'</td>' +
        '<td class="'+colorDiv(r[22])+'">'+r[14]+'</td>' +
        '<td class="fund-cell" title="'+r[25]+'"><span class="fund-count">'+r[23]+'只</span> '+r[24]+'</td>' +
        '</tr>'
      );
    }}
    tbody.innerHTML = parts.join('');
  }}
  document.getElementById('stats').textContent =
    '显示 '+filtered.length+' / '+DATA.length+' 只指数' +
    (filtered.length>0 ? ' | 平均评分: '+(filtered.reduce((s,i)=>s+DATA[i][15],0)/filtered.length).toFixed(1) : '');
}}

sortCol = 15;
sortAsc = false;
applyFilters();

const PORTFOLIOS = {portfolios_js};

const THEME_COLORS = {{
  {theme_colors_js}
}};

const OVERLAP_CAPS = {overlap_caps_js};

let curPortfolio = 'S';

function toggleRec() {{
  const body = document.getElementById('recBody');
  const arrow = document.getElementById('recArrow');
  const isOpen = body.classList.toggle('open');
  arrow.classList.toggle('open', isOpen);
  if(isOpen && !body.dataset.init) {{
    body.dataset.init = '1';
    showPortfolio('S');
  }}
}}

function showPortfolio(size) {{
  curPortfolio = size;
  ['S','M','L'].forEach(s => {{
    document.getElementById('tab'+s).classList.toggle('active', s===size);
  }});
  renderPortfolio(PORTFOLIOS[size]);
}}

function getAssetAmount() {{
  const raw = document.getElementById('assetInput').value.replace(/[,，\s]/g, '');
  const v = parseFloat(raw);
  return isNaN(v) || v <= 0 ? 0 : v;
}}

function fmtAmt(v) {{
  if(v >= 10000) return (v/10000).toFixed(2).replace(/0+$/,'').replace(/\\.$/,'') + '万';
  return v.toFixed(0);
}}

function onAssetInput() {{
  renderPortfolio(PORTFOLIOS[curPortfolio]);
}}

function renderPortfolio(p) {{
  const tbody = document.getElementById('recTbody');
  const bar = document.getElementById('recBar');
  const summary = document.getElementById('recSummary');
  const notes = document.getElementById('recNotes');
  const items = p.items;
  const totalW = items.reduce((s,x) => s+x.w, 0);
  const avgScore = (items.reduce((s,x) => s+x.score, 0)/items.length).toFixed(1);
  const avgDiv = (items.reduce((s,x) => s+parseFloat(x.div), 0)/items.length).toFixed(2);
  const asset = getAssetAmount();
  const themes = {{}};
  items.forEach(x => {{ themes[x.theme] = (themes[x.theme]||0) + x.w; }});
  let summaryHtml =
    '<div class="rec-stat">组合: <span>'+p.label+'</span></div>' +
    '<div class="rec-stat">指数数量: <span>'+items.length+'只</span></div>' +
    '<div class="rec-stat">平均评分: <span>'+avgScore+'</span></div>' +
    '<div class="rec-stat">平均股息率: <span>'+avgDiv+'%</span></div>';
  if(asset > 0) summaryHtml += '<div class="rec-stat">投入总额: <span>'+fmtAmt(asset)+'元</span></div>';
  summaryHtml += '<div class="rec-stat" style="color:#999;font-size:11px;">'+p.desc+'</div>';
  summary.innerHTML = summaryHtml;
  let barHtml = '';
  for(const [theme, w] of Object.entries(themes)) {{
    const pct = (w/totalW*100).toFixed(0);
    barHtml += '<div style="width:'+pct+'%;background:'+THEME_COLORS[theme]+'" title="'+theme+' '+pct+'%">'+theme+' '+pct+'%</div>';
  }}
  bar.innerHTML = barHtml;
  let rows = '';
  let prevTheme = '';
  for(const x of items) {{
    const themeCell = x.theme !== prevTheme
      ? '<span class="theme-tag theme-'+x.theme+'">'+x.theme+'</span>' : '';
    prevTheme = x.theme;
    const amtStr = asset > 0 ? fmtAmt(asset * x.w / 100) : '-';
    rows +=
      '<tr><td>'+themeCell+'</td>' +
      '<td style="font-weight:600">'+x.name+'</td>' +
      '<td style="color:#888;font-size:11px">'+x.code+'</td>' +
      '<td class="w-col" style="color:'+THEME_COLORS[x.theme]+'">'+x.w+'%</td>' +
      '<td class="amt-col">'+amtStr+'</td>' +
      '<td class="s-col '+colorScore(x.score)+'">'+x.score+'</td>' +
      '<td class="'+colorPctStr(x.pe)+'">'+x.pe+'</td>' +
      '<td class="'+colorPctStr(x.pb)+'">'+x.pb+'</td>' +
      '<td class="'+colorRoeStr(x.roe)+'">'+x.roe+'</td>' +
      '<td class="'+colorDivStr(x.div)+'">'+x.div+'</td>' +
      '<td class="'+colorFtldStr(x.ftld)+'">'+x.ftld+'</td>' +
      '<td style="font-size:11px;color:#555;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+x.fund+'">'+x.fund+'</td></tr>';
  }}
  tbody.innerHTML = rows;
  const overlapCaps = OVERLAP_CAPS;
  let overlapParts = [];
  for(const [theme, cap] of Object.entries(overlapCaps)) {{
    const tw = items.filter(x=>x.theme===theme).reduce((s,x)=>s+x.w,0);
    if(tw > 0) overlapParts.push(theme+'类合计 '+tw+'% (上限'+cap+'%)');
  }}
  notes.innerHTML =
    '<strong>重叠控制:</strong> '+(overlapParts.length ? overlapParts.join(' | ') : '无')+'<br>' +
    '<strong>配置逻辑:</strong> 优先选择各主题中PE/PB百分位最低(估值最便宜)、ROE和股息率较高的代表性指数。同类指数仅保留1-2只避免重复暴露。<br>' +
    '<strong>风险提示:</strong> 本推荐基于历史估值数据和量化评分，不构成投资建议。指数过去表现不代表未来收益。请根据自身风险承受能力决定配置比例。';
}}

function colorPctStr(s) {{
  var v = parseFloat(s); if(isNaN(v)) return '';
  if(v<20) return 'bg-green-strong'; if(v<30) return 'bg-green';
  if(v<50) return 'bg-green-light'; if(v<70) return 'bg-yellow'; return 'bg-red';
}}
function colorRoeStr(s) {{
  var v = parseFloat(s); if(isNaN(v)) return '';
  if(v>15) return 'bg-green-strong'; if(v>10) return 'bg-green';
  if(v>5) return 'bg-green-light'; return 'bg-red';
}}
function colorDivStr(s) {{
  var v = parseFloat(s); if(isNaN(v)) return '';
  if(v>4) return 'bg-green-strong'; if(v>3) return 'bg-green';
  if(v>2) return 'bg-green-light'; if(v>1) return 'bg-yellow'; return '';
}}
function colorFtldStr(s) {{
  var v = parseFloat(s); if(isNaN(v)) return '';
  if(v>-15) return 'bg-green-strong'; if(v>-25) return 'bg-green';
  if(v>-35) return 'bg-green-light'; if(v>-50) return 'bg-yellow'; return 'bg-red';
}}
</script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Generated: {output_path}")
    print(f"Total indices: {len(rows)}")
    top = sorted(rows, key=lambda r: r['score'], reverse=True)[:10]
    print("\nTop 10 by composite score:")
    for r in top:
        print(f"  {r['score']:3d}  {r['stockName']}  PE位:{r['pe10pos']}  PB位:{r['pb10pos']}  ROE:{r['roe']}  股息:{r['div']}  距最低:{r['fall_to_lowest_drawdown']}")


def classify_theme(name):
    consumer_keys = ['消费', '白酒', '食品', '酒', '饮']
    medical_keys = ['医', '药', '生科']
    internet_keys = ['互联网']
    finance_keys = ['证券', '非银', '金融', '证保']
    dividend_keys = ['红利']
    appliance_keys = ['家用电器', '家电']
    infra_keys = ['一带一路', '基建']
    eldercare_keys = ['养老']
    hk_consumer_keys = ['恒生消费']
    for k in hk_consumer_keys:
        if k in name:
            return '港股'
    for k in eldercare_keys:
        if k in name:
            return '养老'
    for k in infra_keys:
        if k in name:
            return '基建'
    for k in appliance_keys:
        if k in name:
            return '家电'
    for k in dividend_keys:
        if k in name:
            return '红利'
    for k in finance_keys:
        if k in name:
            return '金融'
    for k in internet_keys:
        if k in name:
            return '互联网'
    for k in medical_keys:
        if k in name:
            return '医药'
    for k in consumer_keys:
        if k in name:
            return '消费'
    return None


def pick_best_per_theme(rows, theme, count=1, min_score=50):
    candidates = []
    for r in rows:
        if classify_theme(r['stockName']) != theme:
            continue
        if r['score'] < min_score:
            continue
        p = r['_parsed']
        pe_pos = p.get('pe10pos')
        pb_pos = p.get('pb10pos')
        if pe_pos is None or pb_pos is None:
            continue
        fund_count = len([f.strip() for f in r['funds'].split(',') if f.strip()]) if r['funds'].strip() else 0
        if fund_count == 0:
            continue
        val_score = r['score'] * 2 - pe_pos - pb_pos
        candidates.append((val_score, r))
    candidates.sort(key=lambda x: -x[0])
    seen_names = set()
    result = []
    for _, r in candidates:
        if len(result) >= count:
            break
        if r['stockName'] not in seen_names:
            seen_names.add(r['stockName'])
            result.append(r)
    return result


def build_portfolio_item(r):
    p = r['_parsed']
    first_fund = r['funds'].split(',')[0].strip() if r['funds'].strip() else ''
    return {
        'theme': classify_theme(r['stockName']),
        'name': r['stockName'],
        'code': r['stockCode'],
        'score': r['score'],
        'pe': f"{p['pe10pos']:.1f}%" if p['pe10pos'] is not None else '',
        'pb': f"{p['pb10pos']:.1f}%" if p['pb10pos'] is not None else '',
        'roe': f"{p['roe']:.2f}%" if p['roe'] is not None else '',
        'div': f"{p['div']:.2f}%" if p['div'] is not None else '',
        'ftld': f"{p['fall_to_lowest_drawdown']:.2f}%" if p['fall_to_lowest_drawdown'] is not None else '',
        'fund': first_fund,
    }


THEME_COLOR_PALETTE = [
    '#e74c3c', '#27ae60', '#8e44ad', '#f39c12', '#c0392b',
    '#2980b9', '#7f8c8d', '#16a085', '#3498db', '#d35400',
    '#1abc9c', '#9b59b6', '#2ecc71', '#e67e22', '#34495e',
]

def get_theme_colors(themes):
    known = {
        '消费': '#e74c3c', '医药': '#27ae60', '互联网': '#8e44ad',
        '金融': '#f39c12', '红利': '#c0392b', '家电': '#2980b9',
        '基建': '#7f8c8d', '养老': '#16a085', '港股': '#3498db',
    }
    result = {}
    palette_idx = 0
    for t in themes:
        if t in known:
            result[t] = known[t]
        else:
            while palette_idx < len(THEME_COLOR_PALETTE) and THEME_COLOR_PALETTE[palette_idx] in result.values():
                palette_idx += 1
            result[t] = THEME_COLOR_PALETTE[palette_idx % len(THEME_COLOR_PALETTE)]
            palette_idx += 1
    return result


def generate_portfolios(rows):
    theme_order = ['消费', '医药', '红利', '互联网', '金融', '家电', '基建', '养老', '港股']
    theme_picks = {}
    for theme in theme_order:
        max_count = 3 if theme == '消费' else 2 if theme == '医药' else 1
        picks = pick_best_per_theme(rows, theme, count=max_count)
        if picks:
            theme_picks[theme] = picks

    small_themes = {
        '消费': 1, '医药': 1, '红利': 1, '互联网': 1, '金融': 1, '家电': 1
    }
    medium_themes = {
        '消费': 2, '医药': 2, '红利': 1, '互联网': 1, '金融': 1, '家电': 1, '基建': 1
    }
    large_themes = {
        '消费': 3, '医药': 2, '红利': 1, '互联网': 1, '金融': 1, '家电': 1, '基建': 1, '养老': 1, '港股': 1
    }

    overlap_caps = {'消费': 25, '医药': 20, '互联网': 15}

    def build_tier(theme_counts, label, desc):
        items = []
        for theme in theme_order:
            count = theme_counts.get(theme, 0)
            if count == 0 or theme not in theme_picks:
                continue
            picks = theme_picks[theme][:count]
            for r in picks:
                items.append(build_portfolio_item(r))

        if not items:
            return None

        n = len(items)
        theme_item_counts = {}
        for item in items:
            theme_item_counts[item['theme']] = theme_item_counts.get(item['theme'], 0) + 1

        base_weight = 100 // n
        weights = [base_weight] * n
        remainder = 100 - sum(weights)
        for i in range(remainder):
            weights[i] += 1

        for theme, cap in overlap_caps.items():
            theme_indices = [i for i, item in enumerate(items) if item['theme'] == theme]
            if not theme_indices:
                continue
            theme_total = sum(weights[i] for i in theme_indices)
            if theme_total <= cap:
                continue
            excess = theme_total - cap
            per_item_reduce = excess // len(theme_indices)
            leftover_reduce = excess % len(theme_indices)
            for idx in theme_indices:
                weights[idx] -= per_item_reduce
            for j in range(leftover_reduce):
                weights[theme_indices[-(j+1)]] -= 1
            other_indices = [i for i in range(n) if i not in theme_indices]
            if other_indices:
                per_other_add = excess // len(other_indices)
                leftover_add = excess % len(other_indices)
                for idx in other_indices:
                    weights[idx] += per_other_add
                for j in range(leftover_add):
                    weights[other_indices[j]] += 1

        total = sum(weights)
        if total != 100:
            weights[0] += (100 - total)

        for i, item in enumerate(items):
            item['w'] = weights[i]

        return {'label': label, 'desc': desc, 'items': items}

    portfolios = {}
    s = build_tier(small_themes, '精简组合', f'集中持有，适合资金量较小或偏好简单管理的投资者')
    if s:
        portfolios['S'] = s
    m = build_tier(medium_themes, '均衡组合', f'风格均衡，覆盖消费/医药/科技/金融/红利，适合中等资金量')
    if m:
        portfolios['M'] = m
    l = build_tier(large_themes, '全面组合', f'全面覆盖，包含港股分散化配置，适合较大资金量长期持有')
    if l:
        portfolios['L'] = l

    portfolios['_overlap_caps'] = overlap_caps

    return portfolios


def portfolios_to_js(portfolios):
    parts = []
    for key in ['S', 'M', 'L']:
        if key not in portfolios:
            continue
        p = portfolios[key]
        items_js = []
        for item in p['items']:
            items_js.append(
                '{' +
                f"theme:'{item['theme']}',name:'{item['name']}',code:'{item['code']}'," +
                f"w:{item['w']},score:{item['score']}," +
                f"pe:'{item['pe']}',pb:'{item['pb']}',roe:'{item['roe']}'," +
                f"div:'{item['div']}',ftld:'{item['ftld']}'," +
                f"fund:'{esc(item['fund'])}'" +
                '}'
            )
        items_str = ',\n      '.join(items_js)
        parts.append(
            f"  {key}: {{\n"
            f"    label: '{p['label']}',\n"
            f"    desc: '{p['desc']}',\n"
            f"    items: [\n      {items_str}\n    ]\n"
            f"  }}"
        )
    return '{\n' + ',\n'.join(parts) + '\n}'


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', ' ').replace('\r', '')

def json_num(v):
    return 'null' if v is None else str(v)


if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else find_latest_csv()
    if not csv_path or not os.path.exists(csv_path):
        print("CSV file not found. Usage: python generate_html_report.py [csv_file]")
        sys.exit(1)
    base = os.path.splitext(csv_path)[0]
    output_path = base + '.html'
    generate_html(csv_path, output_path)
