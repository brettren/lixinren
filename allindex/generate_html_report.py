# !/usr/bin/python
# -*- coding: UTF-8 -*-
import csv
import sys
import os
import html
import re
import glob
from datetime import datetime, timezone, timedelta

def find_latest_csv():
    pattern = os.path.join(os.path.dirname(__file__), "all_index_drawdown_current_and_history.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files)

def find_second_latest_csv():
    pattern = os.path.join(os.path.dirname(__file__), "all_index_drawdown_current_and_history.csv")
    files = sorted(glob.glob(pattern))
    if len(files) < 2:
        return None
    return files[-2]

def find_latest_qdii_csv():
    pattern = os.path.join(os.path.dirname(__file__), "..", "qdIIFunds", "qdII_funds_drawdown.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files)


def find_sw_industry_csv():
    path = os.path.join(os.path.dirname(__file__), "sw_industry_valuation.csv")
    if os.path.exists(path):
        return path
    return None


def load_sw_industry_data(csv_path):
    rows = []
    date_str = ''
    with open(csv_path, 'r', encoding='utf_8_sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        date_str = header[0] if header else ''
        for row in reader:
            if len(row) < 11:
                continue
            rows.append({
                'code': row[0],
                'name': row[1],
                'count': int(row[2]),
                'pe_static': float(row[3]),
                'pe_ttm': float(row[4]),
                'pb': float(row[5]),
                'div_yield': float(row[6]),
                'pe_pct': float(row[7]),
                'pb_pct': float(row[8]),
                'div_pct': float(row[9]),
                'score': float(row[10]),
            })
    return rows, date_str

def load_qdii_data(csv_path):
    rows = []
    date_str = ''
    with open(csv_path, 'r', encoding='utf_8_sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        date_str = header[0] if header else ''
        for row in reader:
            if len(row) < 8:
                continue
            parsed = {
                'current_drawdown': parse_percent(row[4]),
                'largest_drawdown': parse_percent(row[5]),
                'to_lowest': parse_percent(row[6]),
                'to_highest': parse_percent(row[7]),
            }
            rows.append({
                'sector': row[0],
                'code': row[1],
                'publishDate': row[2],
                'name': row[3],
                'current_drawdown': row[4],
                'largest_drawdown': row[5],
                'to_lowest': row[6],
                'to_highest': row[7],
                '_parsed': parsed,
                'score': score_qdii(parsed),
            })
    return rows, date_str

def parse_percent(s):
    if not s or s.strip() == '':
        return None
    s = s.strip().replace('%', '')
    try:
        v = float(s)
        import math
        return None if math.isnan(v) else v
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

def score_qdii(parsed):
    score = 0
    to_lowest = parsed.get('to_lowest')
    if to_lowest is not None:
        if to_lowest <= 2:
            score += 40
        elif to_lowest <= 5:
            score += 35
        elif to_lowest <= 10:
            score += 28
        elif to_lowest <= 15:
            score += 20
        elif to_lowest <= 25:
            score += 12
        elif to_lowest <= 40:
            score += 5
    curr_dd = parsed.get('current_drawdown')
    if curr_dd is not None:
        if curr_dd < -40:
            score += 30
        elif curr_dd < -25:
            score += 25
        elif curr_dd < -15:
            score += 20
        elif curr_dd < -5:
            score += 12
        elif curr_dd < 0:
            score += 5
    largest_dd = parsed.get('largest_drawdown')
    if largest_dd is not None:
        if largest_dd > -15:
            score += 15
        elif largest_dd > -25:
            score += 12
        elif largest_dd > -40:
            score += 8
        elif largest_dd > -60:
            score += 4
    to_highest = parsed.get('to_highest')
    if to_highest is not None:
        if to_highest <= 3:
            score += 15
        elif to_highest <= 10:
            score += 12
        elif to_highest <= 20:
            score += 8
        elif to_highest <= 35:
            score += 4
    return score

def load_previous_data(csv_path):
    prev = {}
    if not csv_path or not os.path.exists(csv_path):
        return prev, ''
    with open(csv_path, 'r', encoding='utf_8_sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        prev_date = header[0] if header else ''
        for row in reader:
            if len(row) < 16:
                continue
            code = row[1]
            parsed = {
                'fall_to_lowest_drawdown': parse_percent(row[8]),
                'pe10pos': parse_percent(row[10]),
                'pb10pos': parse_percent(row[12]),
                'roe': parse_percent(row[13]),
                'div': parse_percent(row[14]),
            }
            prev[code] = {
                'pe10pos': parsed['pe10pos'],
                'pb10pos': parsed['pb10pos'],
                'score': score_index({'_parsed': parsed}),
            }
    return prev, prev_date

def compute_position_concentration(rows):
    held = [r for r in rows if r['hasPosition'] == '*']
    theme_counts = {}
    for r in held:
        theme = classify_theme(r['stockName']) or '其他'
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    total = len(held)
    theme_pcts = {t: round(c / total * 100) for t, c in theme_counts.items()} if total > 0 else {}
    return theme_pcts, total

def generate_scatter_svg(rows):
    points = []
    for r in rows:
        p = r['_parsed']
        if p.get('roe') is None or p.get('pe10pos') is None:
            continue
        theme = classify_theme(r['stockName']) or '其他'
        points.append({
            'x': min(p['roe'], 30),
            'y': p['pe10pos'],
            'pb10pos': p.get('pb10pos'),
            'name': r['stockName'],
            'code': r['stockCode'],
            'theme': theme,
            'held': r['hasPosition'] == '*',
            'score': r['score'],
        })

    theme_colors_map = {
        '消费': '#e74c3c', '医药': '#27ae60', '互联网': '#8e44ad',
        '金融': '#f39c12', '红利': '#c0392b', '家电': '#2980b9',
        '基建': '#7f8c8d', '养老': '#16a085', '港股': '#3498db',
        '科技': '#9b59b6', '新能源': '#2ecc71', '军工': '#34495e',
        '资源': '#d35400', '汽车': '#1abc9c', '地产': '#e67e22',
        '制造': '#607d8b', '宽基': '#3f51b5', '传媒': '#ff6f61',
        '运输': '#6b5b95', '环保': '#88b04b', '其他': '#95a5a6',
    }

    pe_svg = _build_scatter(points, theme_colors_map, x_key='x', y_key='y',
                            x_label='ROE', y_label='PE百分位',
                            x_max=30, y_max=100,
                            value_zone=(10, 30, 0, 30),
                            tip_fmt=lambda pt: f'{pt["name"]}&#10;ROE:{pt["x"]:.1f}% PE位:{pt["y"]:.1f}%&#10;评分:{pt["score"]} {pt["theme"]}')

    pb_svg = _build_scatter(points, theme_colors_map, x_key='x', y_key='pb10pos',
                            x_label='ROE', y_label='PB百分位',
                            x_max=30, y_max=100,
                            value_zone=(10, 30, 0, 30),
                            tip_fmt=lambda pt: f'{pt["name"]}&#10;ROE:{pt["x"]:.1f}% PB位:{pt["pb10pos"]:.1f}%&#10;评分:{pt["score"]} {pt["theme"]}',
                            legend=False)

    return pe_svg, pb_svg


def _build_scatter(points, theme_colors_map, x_key, y_key, x_label, y_label,
                   x_max, y_max, value_zone, tip_fmt, legend=True):
    w, h = 640, 400
    pad_l, pad_r, pad_t, pad_b = 50, 20, 20, 40
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b

    def scale_x(v):
        return pad_l + (v / x_max) * chart_w

    def scale_y(v):
        return pad_t + (v / y_max) * chart_h

    svg_parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:700px;height:auto;font-family:sans-serif;">']

    vx0, vx1, vy0, vy1 = value_zone
    svg_parts.append(f'<rect x="{scale_x(vx0)}" y="{scale_y(vy0)}" width="{scale_x(vx1)-scale_x(vx0)}" height="{scale_y(vy1)-scale_y(vy0)}" fill="#27ae60" fill-opacity="0.06" />')
    svg_parts.append(f'<text x="{scale_x((vx0+vx1)/2)}" y="{scale_y((vy0+vy1)/2)}" text-anchor="middle" font-size="10" fill="#27ae60" opacity="0.5">价值区</text>')

    for v in [0, 20, 50, 80, 100]:
        y = scale_y(v)
        svg_parts.append(f'<line x1="{pad_l}" y1="{y}" x2="{w-pad_r}" y2="{y}" stroke="#eee" stroke-width="0.5"/>')
        svg_parts.append(f'<text x="{pad_l-5}" y="{y+3}" text-anchor="end" font-size="9" fill="#888">{v}%</text>')
    for v in range(0, x_max + 1, 5):
        x = scale_x(v)
        svg_parts.append(f'<line x1="{x}" y1="{pad_t}" x2="{x}" y2="{h-pad_b}" stroke="#eee" stroke-width="0.5"/>')
        svg_parts.append(f'<text x="{x}" y="{h-pad_b+14}" text-anchor="middle" font-size="9" fill="#888">{v}%</text>')

    svg_parts.append(f'<text x="{w/2}" y="{h-5}" text-anchor="middle" font-size="10" fill="#555">{x_label}</text>')
    svg_parts.append(f'<text x="12" y="{h/2}" text-anchor="middle" font-size="10" fill="#555" transform="rotate(-90,12,{h/2})">{y_label}</text>')

    for pt in points:
        yval = pt.get(y_key)
        if yval is None:
            continue
        cx = scale_x(pt[x_key])
        cy = scale_y(yval)
        color = theme_colors_map.get(pt['theme'], '#95a5a6')
        r = 5 if pt['held'] else 3
        stroke = ' stroke="#333" stroke-width="1.5"' if pt['held'] else ''
        opacity = '0.8' if pt['held'] else '0.55'
        tip = tip_fmt(pt)
        svg_parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{color}" opacity="{opacity}"{stroke} data-tip="{tip}" onmousemove="showTip(evt)" onmouseout="hideTip()" style="cursor:pointer;"/>')

    if legend:
        legend_x = pad_l + 5
        legend_y = pad_t + 5
        svg_parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="80" height="{len(theme_colors_map)*13+4}" fill="white" fill-opacity="0.85" rx="3"/>')
        for i, (t, c) in enumerate(theme_colors_map.items()):
            svg_parts.append(f'<circle cx="{legend_x+8}" cy="{legend_y+10+i*13}" r="3" fill="{c}"/>')
            svg_parts.append(f'<text x="{legend_x+15}" y="{legend_y+13+i*13}" font-size="8" fill="#555">{t}</text>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

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

def generate_html(csv_path, output_path, qdii_csv_path=None, sw_csv_path=None):
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
                'pe5pos': row[16] if len(row) > 16 else '',
                'pb5pos': row[17] if len(row) > 17 else '',
                'pe_pb_divergence': row[18] if len(row) > 18 else '',
                'val_adj_div': row[19] if len(row) > 19 else '',
            }
            d['_parsed'] = {
                'current_drawdown': parse_percent(d['current_drawdown']),
                'largest_drawdown': parse_percent(d['largest_drawdown']),
                'fall_to_lowest_drawdown': parse_percent(d['fall_to_lowest_drawdown']),
                'pe10pos': parse_percent(d['pe10pos']),
                'pb10pos': parse_percent(d['pb10pos']),
                'roe': parse_percent(d['roe']),
                'div': parse_percent(d['div']),
                'pe5pos': parse_percent(d['pe5pos']),
                'pb5pos': parse_percent(d['pb5pos']),
                'pe_pb_divergence': parse_percent(d['pe_pb_divergence']),
                'val_adj_div': parse_percent(d['val_adj_div']),
            }
            d['score'] = score_index(d)
            rows.append(d)

    date_str = header[0] if header else ''

    prev_csv = find_second_latest_csv()
    prev_data, prev_date = load_previous_data(prev_csv)
    for r in rows:
        code = r['stockCode']
        if code in prev_data:
            old = prev_data[code]
            r['_delta'] = {
                'score': r['score'] - old['score'] if old['score'] is not None else None,
                'pe10pos': (r['_parsed']['pe10pos'] - old['pe10pos']) if (r['_parsed']['pe10pos'] is not None and old['pe10pos'] is not None) else None,
                'pb10pos': (r['_parsed']['pb10pos'] - old['pb10pos']) if (r['_parsed']['pb10pos'] is not None and old['pb10pos'] is not None) else None,
            }
        else:
            r['_delta'] = {'score': None, 'pe10pos': None, 'pb10pos': None}

    tz_cst = timezone(timedelta(hours=8))
    gen_time = datetime.now(tz_cst).strftime('%Y-%m-%d %H:%M CST')

    rows_json_parts = []
    for r in rows:
        p = r['_parsed']
        delta = r['_delta']
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
            f'{fund_count},"{esc(first_fund)}","{esc(r["funds"])}",'
            f'{json_num(delta["score"])},'
            f'{json_num(delta["pe10pos"])},'
            f'{json_num(delta["pb10pos"])},'
            f'{json_num(p["pe5pos"])},'
            f'{json_num(p["pb5pos"])},'
            f'{json_num(p["pe_pb_divergence"])},'
            f'{json_num(p["val_adj_div"])}]'
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

    qdii_rows = []
    qdii_date_str = ''
    qdii_json = '[]'
    if qdii_csv_path and os.path.exists(qdii_csv_path):
        qdii_rows, qdii_date_str = load_qdii_data(qdii_csv_path)
        qdii_json_parts = []
        for r in qdii_rows:
            p = r['_parsed']
            qdii_json_parts.append(
                f'["{esc(r["code"])}","{esc(r["publishDate"])}","{esc(r["name"])}",'
                f'"{esc(r["current_drawdown"])}","{esc(r["largest_drawdown"])}",'
                f'"{esc(r["to_lowest"])}","{esc(r["to_highest"])}",'
                f'{json_num(p["current_drawdown"])},{json_num(p["largest_drawdown"])},'
                f'{json_num(p["to_lowest"])},{json_num(p["to_highest"])},{r["score"]}]'
            )
        qdii_json = ',\n'.join(qdii_json_parts)

    sw_rows = []
    sw_date_str = ''
    sw_json = '[]'
    if sw_csv_path and os.path.exists(sw_csv_path):
        sw_rows, sw_date_str = load_sw_industry_data(sw_csv_path)
        sw_json_parts = []
        for r in sw_rows:
            sw_json_parts.append(
                f'["{esc(r["code"])}","{esc(r["name"])}",{r["count"]},'
                f'{r["pe_static"]},{r["pe_ttm"]},{r["pb"]},{r["div_yield"]},'
                f'{r["pe_pct"]},{r["pb_pct"]},{r["div_pct"]},{r["score"]}]'
            )
        sw_json = ',\n'.join(sw_json_parts)

    position_pcts, position_total = compute_position_concentration(rows)
    scatter_pe_svg, scatter_pb_svg = generate_scatter_svg(rows)

    all_theme_colors = {
        '消费': '#e74c3c', '医药': '#27ae60', '互联网': '#8e44ad',
        '金融': '#f39c12', '红利': '#c0392b', '家电': '#2980b9',
        '基建': '#7f8c8d', '养老': '#16a085', '港股': '#3498db', '其他': '#95a5a6',
    }

    position_bar_html = ''
    if position_pcts:
        bar_parts = []
        legend_parts = []
        for theme, pct in sorted(position_pcts.items(), key=lambda x: -x[1]):
            color = all_theme_colors.get(theme, '#95a5a6')
            bar_parts.append(f'<div style="width:{pct}%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:600;min-width:20px;">{theme}{pct}%</div>')
            legend_parts.append(f'{theme} {pct}%')
        position_bar_html = '<div style="display:flex;height:28px;border-radius:4px;overflow:hidden;box-shadow:inset 0 1px 2px rgba(0,0,0,.08);">' + ''.join(bar_parts) + '</div>'
        position_bar_html += f'<div style="font-size:11px;color:#666;margin-top:4px;">共{position_total}只持仓 | {" | ".join(legend_parts)}</div>'

    rebalance_html = ''
    if position_pcts and 'M' in portfolios:
        target_themes = {}
        for item in portfolios['M']['items']:
            target_themes[item['theme']] = target_themes.get(item['theme'], 0) + item['w']
        all_rb_themes = sorted(set(list(position_pcts.keys()) + list(target_themes.keys())))
        rb_rows = []
        for t in all_rb_themes:
            curr = position_pcts.get(t, 0)
            tgt = target_themes.get(t, 0)
            diff = curr - tgt
            color = all_theme_colors.get(t, '#95a5a6')
            arrow = ''
            if diff > 5:
                arrow = f'<span style="color:#c0392b;font-weight:700;">超配+{diff}%</span>'
            elif diff < -5:
                arrow = f'<span style="color:#27ae60;font-weight:700;">欠配{diff}%</span>'
            else:
                arrow = '<span style="color:#888;">均衡</span>'
            rb_rows.append(f'<tr><td><span style="display:inline-block;width:10px;height:10px;background:{color};border-radius:2px;margin-right:4px;"></span>{t}</td><td style="text-align:center;">{curr}%</td><td style="text-align:center;">{tgt}%</td><td style="text-align:center;">{arrow}</td></tr>')
        rebalance_html = '<table class="rec-table" style="margin-top:10px;"><thead><tr><th>主题</th><th>当前持仓</th><th>推荐配比</th><th>调整建议</th></tr></thead><tbody>' + ''.join(rb_rows) + '</tbody></table>'

    prev_date_display = prev_date if prev_date else ''

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
.buy-badge {{ background: #27ae60; color: white; font-size: 9px; padding: 1px 4px; border-radius: 3px; margin-left: 2px; vertical-align: middle; }}
.delta {{ font-size: 9px; margin-left: 2px; }}
.delta-up {{ color: #27ae60; }}
.delta-down {{ color: #c0392b; }}
.divergence-flag {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-left: 3px; vertical-align: middle; }}
.divergence-high {{ background: #e74c3c; }}
.divergence-low {{ background: #f39c12; }}
.analysis-section {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.12); margin-bottom: 12px; padding: 16px; }}
.analysis-section h3 {{ font-size: 14px; font-weight: 600; color: #2c3e50; margin-bottom: 10px; }}
.scatter-wrap {{ text-align: center; margin: 8px 0; position: relative; }}
#scatterTip {{ position: fixed; pointer-events: none; background: rgba(44,62,80,.92); color: #fff; padding: 6px 10px; border-radius: 5px; font-size: 12px; line-height: 1.5; white-space: pre-line; display: none; z-index: 999; box-shadow: 0 2px 8px rgba(0,0,0,.25); }}
.opp-badge {{ font-size: 10px; color: #888; }}
.opp-reached {{ color: #27ae60; font-weight: 600; font-size: 10px; }}
.extra-col {{ font-size: 11px; }}
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
.main-tabs {{ display: flex; gap: 0; margin-bottom: 16px; border-radius: 8px; overflow: hidden; border: 2px solid #2c3e50; }}
.main-tabs button {{ flex: 1; padding: 10px 16px; font-size: 14px; border: none; background: #f8f9fa; color: #2c3e50; cursor: pointer; font-weight: 600; transition: all .15s; }}
.main-tabs button:not(:last-child) {{ border-right: 2px solid #2c3e50; }}
.main-tabs button.active {{ background: #2c3e50; color: white; }}
.main-tabs button:hover:not(.active) {{ background: #e8f0fe; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
#swTable {{ min-width: 900px; }}
#qdiiTable {{ min-width: 900px; }}
@media (max-width: 768px) {{
  .main-tabs button {{ font-size: 12px; padding: 8px 10px; }}
}}
</style>
</head>
<body>
<div class="container">
<h1>指数回撤与估值分析</h1>
<p class="subtitle">数据日期: {date_str} | 生成时间: {gen_time} | 共 {len(rows)} 只指数{f' | 对比: {prev_date_display}' if prev_date_display else ''}</p>

<div class="main-tabs">
<button class="active" onclick="switchTab('tab1')">指数回撤与估值 ({len(rows)})</button>
<button onclick="switchTab('tab2')">QDII基金回撤 ({len(qdii_rows)})</button>
<button onclick="switchTab('tab3')">申万行业估值 ({len(sw_rows)})</button>
</div>

<div id="tab1" class="tab-content active">
<div class="legend">
<span style="font-weight:600;">颜色说明:</span>
<div class="legend-item"><div class="legend-color bg-green-strong"></div> 极好</div>
<div class="legend-item"><div class="legend-color bg-green"></div> 良好</div>
<div class="legend-item"><div class="legend-color bg-green-light"></div> 一般</div>
<div class="legend-item"><div class="legend-color bg-yellow"></div> 注意</div>
<div class="legend-item"><div class="legend-color bg-red"></div> 警告</div>
<span style="margin-left:12px;font-weight:600;">评分:</span>
<span>距最低回撤(30) + PE百分位(25) + PB百分位(15) + ROE(20) + 股息率(15) = 满分105</span>
<span style="margin-left:12px;font-weight:600;"><span class="buy-badge">值</span></span>
<span>PE位&lt;30% 且 PB位&lt;30% 且 距最低&gt;-20%，三重低估信号</span>
<span style="margin-left:12px;font-weight:600;">背离:</span>
<span>PE位与PB位之差，<span class="divergence-flag divergence-high"></span>&gt;30%严重背离 <span class="divergence-flag divergence-low"></span>&gt;15%轻度背离，提示盈利与资产估值不一致</span>
</div>

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

<div class="analysis-section">
<h3>持仓主题集中度分析</h3>
{position_bar_html if position_bar_html else '<div style="color:#999;font-size:12px;">暂无持仓数据</div>'}
{rebalance_html}
</div>

<div class="analysis-section">
<h3>ROE-估值象限图 <span style="font-size:11px;color:#888;font-weight:400;">(右下方=高ROE+低估值=价值区 | 实心大圆=持仓 | 鼠标悬停查看详情)</span></h3>
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start;">
<div class="scatter-wrap" style="flex:1;min-width:320px;">
<div style="font-size:12px;font-weight:600;color:#555;margin-bottom:4px;">PE百分位 vs ROE</div>
{scatter_pe_svg}
</div>
<div class="scatter-wrap" style="flex:1;min-width:320px;">
<div style="font-size:12px;font-weight:600;color:#555;margin-bottom:4px;">PB百分位 vs ROE</div>
{scatter_pb_svg}
</div>
</div>
<div id="scatterTip"></div>
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
<button onclick="exportTop()" style="background:#2c3e50;border-color:#2c3e50;">导出Top20</button>
<button onclick="toggleExtraCols()" id="extraColsBtn" style="background:#4a90d9;border-color:#4a90d9;">5年/背离</button>
</div>

<div class="stats" id="stats"></div>

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
<th onclick="sortBy(33)" title="距PE20%分位还需下跌多少" class="extra-col">距机会 <span class="sort-arrow" id="arrow33"></span></th>
<th onclick="sortBy(29)" title="PE 5年百分位" class="extra-col">PE5位 <span class="sort-arrow" id="arrow29"></span></th>
<th onclick="sortBy(30)" title="PB 5年百分位" class="extra-col">PB5位 <span class="sort-arrow" id="arrow30"></span></th>
<th onclick="sortBy(31)" title="PE位-PB位 背离度" class="extra-col">背离 <span class="sort-arrow" id="arrow31"></span></th>
</tr>
</thead>
<tbody id="tbody"></tbody>
</table>
<div id="nodata">没有匹配的数据</div>
</div>

</div><!-- end tab1 -->

<div id="tab2" class="tab-content">
<div class="legend" style="margin-bottom:8px;">
<span style="font-weight:600;">评分:</span>
<span>距最低(40) + 当前回撤深度(30) + 最大回撤控制(15) + 距最高(15) = 满分100</span>
</div>
<div class="controls">
<div class="filter-group">
<label>搜索:</label>
<input type="text" id="qdiiSearch" placeholder="名称/代码..." oninput="qdiiApplyFilter()">
</div>
<div class="filter-group">
<label>距最低≤:</label>
<select id="qdiiToLowestFilter" onchange="qdiiApplyFilter()">
<option value="999">全部</option>
<option value="5">≤5%</option>
<option value="10">≤10%</option>
<option value="15">≤15%</option>
<option value="20">≤20%</option>
<option value="30">≤30%</option>
</select>
</div>
<div class="filter-group">
<label>评分≥:</label>
<select id="qdiiScoreFilter" onchange="qdiiApplyFilter()">
<option value="0">全部</option>
<option value="40">40+</option>
<option value="50">50+</option>
<option value="60">60+</option>
<option value="70">70+</option>
<option value="80">80+</option>
</select>
</div>
<button onclick="qdiiReset()">重置</button>
</div>
<div class="stats" id="qdiiStats"></div>
<div class="table-wrap" style="max-height:calc(100vh - 220px);">
<table id="qdiiTable">
<thead><tr>
<th onclick="qdiiSortBy(0)">代码 <span class="sort-arrow" id="qArrow0"></span></th>
<th onclick="qdiiSortBy(1)">成立日期 <span class="sort-arrow" id="qArrow1"></span></th>
<th onclick="qdiiSortBy(2)">基金名称 <span class="sort-arrow" id="qArrow2"></span></th>
<th onclick="qdiiSortBy(7)" title="回撤评分(满分100)">评分 <span class="sort-arrow" id="qArrow7"></span></th>
<th onclick="qdiiSortBy(3)" title="当前回撤">当前回撤 <span class="sort-arrow" id="qArrow3"></span></th>
<th onclick="qdiiSortBy(4)" title="历史最大回撤">最大回撤 <span class="sort-arrow" id="qArrow4"></span></th>
<th onclick="qdiiSortBy(5)" title="距历史最低还有多远(越小越安全)">距最低↓ <span class="sort-arrow" id="qArrow5"></span></th>
<th onclick="qdiiSortBy(6)" title="回到历史最高需要涨多少">距最高↑ <span class="sort-arrow" id="qArrow6"></span></th>
</tr></thead>
<tbody id="qdiiTbody"></tbody>
</table>
<div id="qdiiNodata" style="display:none;padding:40px;text-align:center;color:#999;">没有匹配的数据</div>
</div>
</div><!-- end tab2 -->

<div id="tab3" class="tab-content">
<div class="legend" style="margin-bottom:8px;">
<span style="font-weight:600;">评分说明:</span>
<span>PE百分位排名(35) + PB百分位排名(25) + 股息率排名(25) + PE/PB一致性(15) = 满分100</span>
<span style="margin-left:12px;">百分位=在31个行业中的相对排名，越低越便宜</span>
</div>
<div class="controls">
<div class="filter-group">
<label>搜索:</label>
<input type="text" id="swSearch" placeholder="行业名称..." oninput="swApplyFilter()">
</div>
<div class="filter-group">
<label>评分≥:</label>
<select id="swScoreFilter" onchange="swApplyFilter()">
<option value="0">全部</option>
<option value="40">40+</option>
<option value="50">50+</option>
<option value="60">60+</option>
<option value="70">70+</option>
<option value="80">80+</option>
</select>
</div>
<button onclick="swReset()">重置</button>
</div>
<div class="stats" id="swStats"></div>
<div class="table-wrap" style="max-height:calc(100vh - 220px);">
<table id="swTable">
<thead><tr>
<th onclick="swSortBy(0)">行业代码 <span class="sort-arrow" id="sArrow0"></span></th>
<th onclick="swSortBy(1)">行业名称 <span class="sort-arrow" id="sArrow1"></span></th>
<th onclick="swSortBy(2)">成份个数 <span class="sort-arrow" id="sArrow2"></span></th>
<th onclick="swSortBy(10)" title="估值评分(满分100)">评分 <span class="sort-arrow" id="sArrow10"></span></th>
<th onclick="swSortBy(3)" title="静态市盈率">静态PE <span class="sort-arrow" id="sArrow3"></span></th>
<th onclick="swSortBy(4)" title="TTM滚动市盈率">TTM PE <span class="sort-arrow" id="sArrow4"></span></th>
<th onclick="swSortBy(5)" title="市净率">PB <span class="sort-arrow" id="sArrow5"></span></th>
<th onclick="swSortBy(6)" title="静态股息率">股息率 <span class="sort-arrow" id="sArrow6"></span></th>
<th onclick="swSortBy(7)" title="PE在31行业中的百分位排名(越低越便宜)">PE百分位 <span class="sort-arrow" id="sArrow7"></span></th>
<th onclick="swSortBy(8)" title="PB在31行业中的百分位排名(越低越便宜)">PB百分位 <span class="sort-arrow" id="sArrow8"></span></th>
<th onclick="swSortBy(9)" title="股息率在31行业中的百分位排名(越低越好)">股息率百分位 <span class="sort-arrow" id="sArrow9"></span></th>
</tr></thead>
<tbody id="swTbody"></tbody>
</table>
<div id="swNodata" style="display:none;padding:40px;text-align:center;color:#999;">没有匹配的数据</div>
</div>
</div><!-- end tab3 -->

</div>

<script>
function showTip(evt) {{
  var tip = document.getElementById('scatterTip');
  tip.textContent = evt.target.getAttribute('data-tip');
  tip.style.display = 'block';
  tip.style.left = (evt.clientX + 12) + 'px';
  tip.style.top = (evt.clientY - 10) + 'px';
}}
function hideTip() {{
  document.getElementById('scatterTip').style.display = 'none';
}}
const DATA=[
{rows_json}
];
// Column indices: 0=sector,1=code,2=pubDate,3=name,4=style,5=position,
// 6=currDD,7=largestDD,8=ftld,9=pe,10=pePos,11=pb,12=pbPos,13=roe,14=div,
// 15=score,16=ftld_n,17=currDD_n,18=largestDD_n,19=pePos_n,20=pbPos_n,
// 21=roe_n,22=div_n,23=fundCount,24=firstFund,25=allFunds,
// 26=scoreDelta,27=pePosChg,28=pbPosChg,29=pe5pos_n,30=pb5pos_n,31=divergence_n,32=valAdjDiv_n

let sortCol = 15;
let sortAsc = false;
let filtered = [...Array(DATA.length).keys()];
let showExtraCols = true;

function esc(s) {{ return s; }}

function hasBuySignal(r) {{
  return r[19]!==null && r[19]<30 && r[20]!==null && r[20]<30 && r[16]!==null && r[16]>-20;
}}

function deltaHtml(v, suffix) {{
  if(v===null || v===0) return '';
  if(v>0) return '<span class="delta delta-up">+'+v.toFixed(suffix?1:0)+(suffix||'')+'</span>';
  return '<span class="delta delta-down">'+v.toFixed(suffix?1:0)+(suffix||'')+'</span>';
}}

function distToOpp(r) {{
  if(r[5]==='*') return '-';
  var pePos = r[19];
  if(pePos===null) return '-';
  if(pePos<=20) return '<span class="opp-reached">已达</span>';
  return '<span class="opp-badge">'+(pePos-20).toFixed(0)+'%↓</span>';
}}

function divergenceFlag(v) {{
  if(v===null) return '';
  var abs = Math.abs(v);
  if(abs>30) return '<span class="divergence-flag divergence-high" title="PE-PB背离'+v.toFixed(1)+'%"></span>';
  if(abs>15) return '<span class="divergence-flag divergence-low" title="PE-PB背离'+v.toFixed(1)+'%"></span>';
  return '';
}}

function toggleExtraCols() {{
  showExtraCols = !showExtraCols;
  var cols = document.querySelectorAll('.extra-col');
  cols.forEach(function(el) {{ el.style.display = showExtraCols ? '' : 'none'; }});
  document.getElementById('extraColsBtn').style.background = showExtraCols ? '#4a90d9' : '#7f8c8d';
  document.getElementById('extraColsBtn').style.borderColor = showExtraCols ? '#4a90d9' : '#7f8c8d';
}}

function exportTop() {{
  var n = Math.min(20, filtered.length);
  var sorted = [...filtered].sort(function(a,b){{ return DATA[b][15]-DATA[a][15]; }});
  var text = '排名\\t代码\\t名称\\t评分\\tPE位\\tPB位\\tROE\\t股息率\\t距最低\\t推荐基金\\n';
  for(var i=0; i<n; i++) {{
    var r = DATA[sorted[i]];
    text += (i+1)+'\\t'+r[1]+'\\t'+r[3]+'\\t'+r[15]+'\\t'+r[10]+'\\t'+r[12]+'\\t'+r[13]+'\\t'+r[14]+'\\t'+r[8]+'\\t'+r[24]+'\\n';
  }}
  navigator.clipboard.writeText(text).then(function(){{ alert('已复制Top'+n+'到剪贴板'); }});
}}

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
  if(col===26) return r[26];
  if(col===29) return r[29];
  if(col===30) return r[30];
  if(col===31) return r[31]!==null ? Math.abs(r[31]) : -1;
  if(col===33) return r[19]!==null ? (r[19]<=20 ? -1 : r[19]-20) : 99999;
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

  for(let i=0; i<=33; i++) {{
    const el = document.getElementById('arrow'+i);
    if(el) el.textContent = sortCol===i ? (sortAsc ? '▲' : '▼') : '';
  }}

  const tbody = document.getElementById('tbody');
  const nodata = document.getElementById('nodata');
  const ecDisp = showExtraCols ? '' : 'display:none;';
  if(filtered.length===0) {{
    tbody.innerHTML='';
    nodata.style.display='block';
  }} else {{
    nodata.style.display='none';
    const parts = [];
    for(const idx of filtered) {{
      const r = DATA[idx];
      const hp = r[5]==='*';
      const buyBadge = hasBuySignal(r) ? ' <span class="buy-badge">值</span>' : '';
      const scoreDelta = deltaHtml(r[26], '');
      const peDelta = deltaHtml(r[27], '%');
      const pbDelta = deltaHtml(r[28], '%');
      const divFlag = divergenceFlag(r[31]);
      parts.push(
        '<tr'+(hp?' class="has-position"':'')+'>' +
        '<td>'+sectorTag(r[0])+'</td>' +
        '<td>'+r[1]+'</td>' +
        '<td>'+r[3]+'</td>' +
        '<td>'+styleTag(r[4])+'</td>' +
        '<td>'+(hp?'<span class="position-star">★</span>':'')+'</td>' +
        '<td class="score-cell '+colorScore(r[15])+'">'+r[15]+buyBadge+scoreDelta+'</td>' +
        '<td class="'+valClass(r[6])+'">'+r[6]+'</td>' +
        '<td class="neg-val">'+r[7]+'</td>' +
        '<td class="'+colorFtld(r[16])+'">'+r[8]+'</td>' +
        '<td>'+fmtNum(r[9])+'</td>' +
        '<td class="'+colorPct(r[19])+'">'+r[10]+peDelta+'</td>' +
        '<td>'+fmtNum(r[11])+'</td>' +
        '<td class="'+colorPct(r[20])+'">'+r[12]+pbDelta+'</td>' +
        '<td class="'+colorRoe(r[21])+'">'+r[13]+'</td>' +
        '<td class="'+colorDiv(r[22])+'">'+r[14]+'</td>' +
        '<td class="fund-cell" title="'+r[25]+'"><span class="fund-count">'+r[23]+'只</span> '+r[24]+'</td>' +
        '<td class="extra-col" style="'+ecDisp+'">'+distToOpp(r)+'</td>' +
        '<td class="extra-col '+colorPct(r[29])+'" style="'+ecDisp+'">'+(r[29]!==null?r[29].toFixed(1)+'%':'-')+'</td>' +
        '<td class="extra-col '+colorPct(r[30])+'" style="'+ecDisp+'">'+(r[30]!==null?r[30].toFixed(1)+'%':'-')+'</td>' +
        '<td class="extra-col" style="'+ecDisp+'">'+(r[31]!==null?r[31].toFixed(1)+'%':'-')+divFlag+'</td>' +
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

const QDII_DATA=[
{qdii_json}
];
// QDII columns: 0=code,1=pubDate,2=name,3=currDD,4=largestDD,5=toLowest,6=toHighest,
// 7=currDD_n,8=largestDD_n,9=toLowest_n,10=toHighest_n,11=score

let qdiiSortCol = 11;
let qdiiSortAsc = false;
let qdiiFiltered = [...Array(QDII_DATA.length).keys()];

function qdiiSortBy(col) {{
  if(qdiiSortCol === col) qdiiSortAsc = !qdiiSortAsc;
  else {{ qdiiSortCol = col; qdiiSortAsc = (col<=2); }}
  qdiiRenderTable();
}}

function qdiiGetVal(idx, col) {{
  const r = QDII_DATA[idx];
  if(col<=2) return r[col];
  if(col===3) return r[7];
  if(col===4) return r[8];
  if(col===5) return r[9];
  if(col===6) return r[10];
  if(col===7) return r[11];
  return r[col];
}}

function qdiiApplyFilter() {{
  const search = document.getElementById('qdiiSearch').value.toLowerCase();
  const maxToLowest = parseFloat(document.getElementById('qdiiToLowestFilter').value);
  const minScore = parseInt(document.getElementById('qdiiScoreFilter').value);
  qdiiFiltered = [];
  for(let i=0; i<QDII_DATA.length; i++) {{
    const r = QDII_DATA[i];
    if(maxToLowest < 999 && r[9] !== null && r[9] > maxToLowest) continue;
    if(r[11] < minScore) continue;
    if(search) {{
      const hay = (r[0]+r[2]).toLowerCase();
      if(!hay.includes(search)) continue;
    }}
    qdiiFiltered.push(i);
  }}
  qdiiRenderTable();
}}

function qdiiReset() {{
  document.getElementById('qdiiSearch').value = '';
  document.getElementById('qdiiToLowestFilter').value = '999';
  document.getElementById('qdiiScoreFilter').value = '0';
  qdiiFiltered = [...Array(QDII_DATA.length).keys()];
  qdiiRenderTable();
}}

function qdiiColorDD(v) {{
  if(v===null) return '';
  if(v>-5) return 'bg-green-strong';
  if(v>-15) return 'bg-green';
  if(v>-25) return 'bg-green-light';
  if(v>-40) return 'bg-yellow';
  return 'bg-red';
}}

function qdiiColorToLowest(v) {{
  if(v===null) return '';
  if(v<=2) return 'bg-green-strong';
  if(v<=5) return 'bg-green';
  if(v<=10) return 'bg-green-light';
  if(v<=20) return 'bg-yellow';
  return 'bg-red';
}}

function qdiiColorScore(v) {{
  if(v>=80) return 'bg-green-strong';
  if(v>=60) return 'bg-green';
  if(v>=40) return 'bg-green-light';
  if(v>=20) return 'bg-yellow';
  return 'bg-red';
}}

function qdiiRenderTable() {{
  qdiiFiltered.sort((a,b) => {{
    let va = qdiiGetVal(a, qdiiSortCol);
    let vb = qdiiGetVal(b, qdiiSortCol);
    if(va===null) va = qdiiSortAsc ? 99999 : -99999;
    if(vb===null) vb = qdiiSortAsc ? 99999 : -99999;
    if(typeof va==='string') return qdiiSortAsc ? va.localeCompare(vb,'zh') : vb.localeCompare(va,'zh');
    return qdiiSortAsc ? va-vb : vb-va;
  }});

  for(let i=0; i<=7; i++) {{
    const el = document.getElementById('qArrow'+i);
    if(el) el.textContent = qdiiSortCol===i ? (qdiiSortAsc ? '▲' : '▼') : '';
  }}

  const tbody = document.getElementById('qdiiTbody');
  const nodata = document.getElementById('qdiiNodata');
  if(qdiiFiltered.length===0) {{
    tbody.innerHTML='';
    nodata.style.display='block';
  }} else {{
    nodata.style.display='none';
    const parts = [];
    for(const idx of qdiiFiltered) {{
      const r = QDII_DATA[idx];
      parts.push(
        '<tr>' +
        '<td>'+r[0]+'</td>' +
        '<td style="color:#888;font-size:11px">'+r[1]+'</td>' +
        '<td style="font-weight:500">'+r[2]+'</td>' +
        '<td class="score-cell '+qdiiColorScore(r[11])+'">'+r[11]+'</td>' +
        '<td class="'+qdiiColorDD(r[7])+'">'+r[3]+'</td>' +
        '<td class="neg-val">'+r[4]+'</td>' +
        '<td class="'+qdiiColorToLowest(r[9])+'">'+r[5]+'</td>' +
        '<td>'+r[6]+'</td>' +
        '</tr>'
      );
    }}
    tbody.innerHTML = parts.join('');
  }}
  document.getElementById('qdiiStats').textContent =
    '显示 '+qdiiFiltered.length+' / '+QDII_DATA.length+' 只QDII基金' +
    (qdiiFiltered.length>0 ? ' | 平均评分: '+(qdiiFiltered.reduce((s,i)=>s+QDII_DATA[i][11],0)/qdiiFiltered.length).toFixed(1) : '');
}}

function switchTab(tabId) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.main-tabs button').forEach(el => el.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  var idx = {{'tab1':0,'tab2':1,'tab3':2}}[tabId];
  document.querySelectorAll('.main-tabs button')[idx].classList.add('active');
  if(tabId==='tab2' && !document.getElementById('tab2').dataset.init) {{
    document.getElementById('tab2').dataset.init='1';
    qdiiRenderTable();
  }}
  if(tabId==='tab3' && !document.getElementById('tab3').dataset.init) {{
    document.getElementById('tab3').dataset.init='1';
    swRenderTable();
  }}
}}

const SW_DATA=[
{sw_json}
];
// SW columns: 0=code,1=name,2=count,3=pe_static,4=pe_ttm,5=pb,6=div_yield,
// 7=pe_pct,8=pb_pct,9=div_pct,10=score

let swSortCol = 10;
let swSortAsc = false;
let swFiltered = [...Array(SW_DATA.length).keys()];

function swSortBy(col) {{
  if(swSortCol === col) swSortAsc = !swSortAsc;
  else {{ swSortCol = col; swSortAsc = (col<=2); }}
  swRenderTable();
}}

function swGetVal(idx, col) {{
  return SW_DATA[idx][col];
}}

function swApplyFilter() {{
  const search = document.getElementById('swSearch').value.toLowerCase();
  const minScore = parseInt(document.getElementById('swScoreFilter').value);
  swFiltered = [];
  for(let i=0; i<SW_DATA.length; i++) {{
    const r = SW_DATA[i];
    if(r[10] < minScore) continue;
    if(search && !r[1].toLowerCase().includes(search)) continue;
    swFiltered.push(i);
  }}
  swRenderTable();
}}

function swReset() {{
  document.getElementById('swSearch').value = '';
  document.getElementById('swScoreFilter').value = '0';
  swFiltered = [...Array(SW_DATA.length).keys()];
  swRenderTable();
}}

function swColorPE(v) {{
  if(v<15) return 'bg-green-strong';
  if(v<20) return 'bg-green';
  if(v<30) return 'bg-green-light';
  if(v<50) return 'bg-yellow';
  return 'bg-red';
}}

function swColorPB(v) {{
  if(v<1.0) return 'bg-green-strong';
  if(v<1.5) return 'bg-green';
  if(v<2.5) return 'bg-green-light';
  if(v<4.0) return 'bg-yellow';
  return 'bg-red';
}}

function swColorDiv(v) {{
  if(v>4) return 'bg-green-strong';
  if(v>3) return 'bg-green';
  if(v>2) return 'bg-green-light';
  if(v>1) return 'bg-yellow';
  return '';
}}

function swColorPct(v) {{
  if(v<20) return 'bg-green-strong';
  if(v<35) return 'bg-green';
  if(v<50) return 'bg-green-light';
  if(v<70) return 'bg-yellow';
  return 'bg-red';
}}

function swRenderTable() {{
  swFiltered.sort((a,b) => {{
    let va = swGetVal(a, swSortCol);
    let vb = swGetVal(b, swSortCol);
    if(va===null) va = swSortAsc ? 99999 : -99999;
    if(vb===null) vb = swSortAsc ? 99999 : -99999;
    if(typeof va==='string') return swSortAsc ? va.localeCompare(vb,'zh') : vb.localeCompare(va,'zh');
    return swSortAsc ? va-vb : vb-va;
  }});

  for(let i=0; i<=10; i++) {{
    const el = document.getElementById('sArrow'+i);
    if(el) el.textContent = swSortCol===i ? (swSortAsc ? '▲' : '▼') : '';
  }}

  const tbody = document.getElementById('swTbody');
  const nodata = document.getElementById('swNodata');
  if(swFiltered.length===0) {{
    tbody.innerHTML='';
    nodata.style.display='block';
  }} else {{
    nodata.style.display='none';
    const parts = [];
    for(const idx of swFiltered) {{
      const r = SW_DATA[idx];
      parts.push(
        '<tr>' +
        '<td style="color:#888;font-size:11px">'+r[0]+'</td>' +
        '<td style="font-weight:600">'+r[1]+'</td>' +
        '<td style="text-align:center">'+r[2]+'</td>' +
        '<td class="score-cell '+colorScore(r[10])+'">'+r[10].toFixed(1)+'</td>' +
        '<td>'+r[3].toFixed(2)+'</td>' +
        '<td class="'+swColorPE(r[4])+'">'+r[4].toFixed(2)+'</td>' +
        '<td class="'+swColorPB(r[5])+'">'+r[5].toFixed(2)+'</td>' +
        '<td class="'+swColorDiv(r[6])+'">'+r[6].toFixed(2)+'%</td>' +
        '<td class="'+swColorPct(r[7])+'">'+r[7].toFixed(1)+'%</td>' +
        '<td class="'+swColorPct(r[8])+'">'+r[8].toFixed(1)+'%</td>' +
        '<td class="'+swColorPct(r[9])+'">'+r[9].toFixed(1)+'%</td>' +
        '</tr>'
      );
    }}
    tbody.innerHTML = parts.join('');
  }}
  document.getElementById('swStats').textContent =
    '显示 '+swFiltered.length+' / '+SW_DATA.length+' 个行业' +
    (swFiltered.length>0 ? ' | 平均评分: '+(swFiltered.reduce((s,i)=>s+SW_DATA[i][10],0)/swFiltered.length).toFixed(1) : '');
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
    consumer_keys = ['消费', '白酒', '食品', '酒', '饮', '农业', '粮食', '畜牧', '生猪', '可选']
    medical_keys = ['医', '药', '生科', '疫苗', '健康']
    internet_keys = ['互联网', '线上']
    finance_keys = ['证券', '非银', '金融', '证保', '银行', '保险']
    dividend_keys = ['红利', '高股息', '股息', '现金流']
    appliance_keys = ['家用电器', '家电', '龙头家电']
    infra_keys = ['一带一路', '基建', '建筑材料', '高铁']
    eldercare_keys = ['养老']
    hk_keys = ['恒生', '恒指', '港股', 'HK', 'HKC', '港中小', '香港']
    tech_keys = ['科技', '科创', '人工智', 'AI', '计算机', '软件', '信息', '信创', '云计算',
                 '数字', '电子', '半导体', '芯片', '5G', '通信', '物联网', 'TMT',
                 '区块链', '智能', '机器人', 'VR', '算力']
    newenergy_keys = ['新能源', '新能车', '光伏', '电池', '储能', '风电', '碳中和',
                      '绿色电力', '绿色能源', '电力', '低碳']
    military_keys = ['军工', '国防', '空天']
    resource_keys = ['有色', '稀土', '资源', '煤炭', '钢铁', '石化', '油气',
                     '大宗商品', '材料', '化工', '黄金', '稀金属']
    auto_keys = ['汽车', '电车', '智能汽车', '智能电车']
    realestate_keys = ['地产', '房地产']
    manufacturing_keys = ['制造', '机械', '工业', '装备', '机床', '高端造', '工程',
                          '高装']
    media_keys = ['传媒', '影视', '娱乐', '游戏', '动漫']
    transport_keys = ['运输', '物流']
    env_keys = ['环保', '环境']
    broad_keys = ['沪深300', '中证500', '中证1000', '中证800', '中证200', '中证700',
                  '中证2000', '上证50', '上证180', '上证380', '创业板指', '创业板',
                  '深证100', '深证300', '科创50', '北证50', 'A500', 'A50', 'A100',
                  '巨潮', '全指', '500等权', '800等权', '中小板', '大盘', '中盘', '小盘',
                  '沪深B', '深圳A', '深圳B', '上海A', '深证成指', '上证指数',
                  '中创', '深证50', '中证龙头', '沪港深', '价值', '成长',
                  '国企', '央企', '质量', 'SNLV', '基本面']
    for k in hk_keys:
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
    for k in newenergy_keys:
        if k in name:
            return '新能源'
    for k in auto_keys:
        if k in name:
            return '汽车'
    for k in military_keys:
        if k in name:
            return '军工'
    for k in tech_keys:
        if k in name:
            return '科技'
    for k in resource_keys:
        if k in name:
            return '资源'
    for k in realestate_keys:
        if k in name:
            return '地产'
    for k in manufacturing_keys:
        if k in name:
            return '制造'
    for k in media_keys:
        if k in name:
            return '传媒'
    for k in transport_keys:
        if k in name:
            return '运输'
    for k in env_keys:
        if k in name:
            return '环保'
    for k in consumer_keys:
        if k in name:
            return '消费'
    for k in broad_keys:
        if k in name:
            return '宽基'
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
    import math
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 'null'
    return str(v)


if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else find_latest_csv()
    if not csv_path or not os.path.exists(csv_path):
        print("CSV file not found. Usage: python generate_html_report.py [csv_file]")
        sys.exit(1)
    output_path = os.path.join(os.path.dirname(csv_path), 'all_index_drawdown_current_and_history.html')
    qdii_csv_path = find_latest_qdii_csv()
    sw_csv_path = find_sw_industry_csv()
    generate_html(csv_path, output_path, qdii_csv_path, sw_csv_path)
