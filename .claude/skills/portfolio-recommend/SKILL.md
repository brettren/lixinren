---
name: portfolio-recommend
description: Analyze index investment data and generate balanced portfolio recommendations for the HTML report. Use this skill whenever the user asks to update portfolio recommendations, rebalance the portfolio, regenerate investment recommendations, or when new index drawdown CSV data is available. Also trigger when the user says "recommend", "portfolio", "rebalance", "update recommendations", or mentions updating the HTML report with new picks. This skill replaces the hardcoded portfolio logic with LLM-driven analysis that adapts to changing market conditions.
---

# Portfolio Recommendation Generator

You are analyzing Chinese index fund data to build balanced, diversified portfolio recommendations. The recommendations are rendered in an interactive HTML report.

## Project Context

- **CSV data**: `allindex/all_index_drawdown_current_and_history_*.csv` (find the latest dated file)
- **Report generator**: `allindex/generate_html_report.py`
- **Output**: The `PORTFOLIOS` JavaScript object inside the HTML template in `generate_html_report.py`

## Step 1: Read and Analyze the Data

Run the analysis script to extract the top candidates:

```bash
python3 -c "
import csv, glob, os

pattern = os.path.join('allindex', 'all_index_drawdown_current_and_history_2*.csv')
csv_path = max(glob.glob(pattern))
print(f'Data file: {csv_path}')

def pct(s):
    if not s or not s.strip(): return None
    try: return float(s.strip().replace('%',''))
    except: return None

def score(r):
    s = 0
    ftld = pct(r[8])
    if ftld is not None:
        if ftld > -15: s += 30
        elif ftld > -25: s += 25
        elif ftld > -35: s += 20
        elif ftld > -50: s += 10
    pe = pct(r[10])
    if pe is not None:
        if pe < 20: s += 25
        elif pe < 30: s += 20
        elif pe < 50: s += 10
    pb = pct(r[12])
    if pb is not None:
        if pb < 20: s += 15
        elif pb < 30: s += 12
        elif pb < 50: s += 6
    roe = pct(r[13])
    if roe is not None:
        if roe > 15: s += 20
        elif roe > 10: s += 15
        elif roe > 5: s += 5
    div = pct(r[14])
    if div is not None:
        if div > 4: s += 15
        elif div > 3: s += 12
        elif div > 2: s += 8
        elif div > 1: s += 3
    return s

rows = []
with open(csv_path, 'r', encoding='utf_8_sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 16: continue
        s = score(row)
        fund_count = len([x.strip() for x in row[15].split(',') if x.strip()]) if row[15].strip() else 0
        first_fund = row[15].split(',')[0].strip() if row[15].strip() else ''
        rows.append({
            'sector': row[0], 'code': row[1], 'name': row[3], 'style': row[4],
            'score': s, 'pe_pos': pct(row[10]), 'pb_pos': pct(row[12]),
            'roe': pct(row[13]), 'div': pct(row[14]), 'ftld': pct(row[8]),
            'curr_dd': pct(row[6]), 'fund_count': fund_count, 'first_fund': first_fund
        })

# Print all indices with score >= 50, sorted by score desc
top = sorted([r for r in rows if r['score'] >= 50 and r['fund_count'] > 0], key=lambda x: -x['score'])
print(f'Total indices: {len(rows)}, Score>=50 with funds: {len(top)}')
print()
for r in top:
    print(f\"Score={r['score']:>3} {r['name']:<20} Style={r['style']:<4} PE%={r['pe_pos']:>5.1f} PB%={r['pb_pos']:>5.1f} ROE={r['roe']:>5.1f} Div={r['div']:>4.2f} FTLD={r['ftld']:>7.2f} Sector={r['sector']} Funds={r['fund_count']} Fund={r['first_fund'][:50]}\")
"
```

## Step 2: Cluster and Select

After reading the data output, perform the following analysis **yourself** (this is the LLM-driven part):

### 2a. Identify Natural Theme Clusters

Look at all indices with score >= 50. Group them into investment theme clusters based on:
- **Name similarity**: indices with overlapping names (e.g., "CS消费50", "消费龙头", "中证白酒" are all consumer-related)
- **Constituent overlap**: indices tracking similar underlying stocks (白酒 is a subset of 消费)
- **Sector coverage**: group by industry (medical, tech, finance, consumer, etc.)

Create 8-12 distinct theme clusters. Common clusters include (but discover dynamically, don't hardcode):
- Consumer/Food/Beverage
- Medical/Pharma (traditional vs modern)
- Technology/Internet
- Finance/Banking/Insurance
- Dividend/Value
- Manufacturing/Industrial
- Energy/Materials/Cycle
- Hong Kong market diversification

### 2b. Pick Best Representatives

For each cluster, select 1-3 best indices using this ranking:
1. **Composite score** (highest first)
2. **PE percentile** (lowest = cheapest)
3. **PB percentile** (lowest = cheapest)
4. **Fund availability** (must have >= 1 trackable fund)
5. **ROE** (higher = more profitable)
6. **Dividend yield** (higher = more income)

### 2c. Build Three Portfolios

- **Small (精简组合)**: 5-7 indices, one per cluster, covering the most important diversified themes
- **Medium (均衡组合)**: 8-10 indices, up to 2 from large clusters
- **Large (全面组合)**: 11-14 indices, up to 3 from large clusters, includes HK if available

### 2d. Assign Weights

Start with equal weights, then apply overlap caps:
- **No single theme cluster > 25%** of the portfolio
- **Prefer value-tilted indices** with slightly higher weight (PE% < 20 or PB% < 20)
- **Weights must sum to exactly 100%**
- **Minimum weight per index: 5%**

## Step 3: Update generate_html_report.py

The portfolios are stored in `generate_html_report.py` in the `generate_portfolios()` function. You need to update two things:

### 3a. Update `classify_theme()` function

Replace the hardcoded keyword lists with new ones based on your discovered clusters. The function maps index names to theme labels.

### 3b. Update theme configurations

Update these dictionaries in `generate_portfolios()`:
- `theme_order` — the list of theme labels in display order
- `small_themes`, `medium_themes`, `large_themes` — how many indices per theme for each tier
- `overlap_caps` — which themes have concentration limits

### 3c. Update THEME_COLORS in the JS template

Add/update the CSS `.theme-XXX` classes and the `THEME_COLORS` JavaScript object to include all your themes with distinct colors.

## Step 4: Regenerate the HTML Report

```bash
python3 allindex/generate_html_report.py
```

Then open it to verify:
```bash
open allindex/all_index_drawdown_current_and_history_*.html
```

## Step 5: Verify

Check:
- All three tabs (精简/均衡/全面) render correctly
- Weights sum to 100% for each portfolio
- No single theme exceeds 25%
- The color bar visualization looks correct
- Each recommended index has a valid fund
- The overlap control notes at the bottom reflect actual allocations

## Important Constraints

- **Every portfolio item MUST have a real trackable fund** (fund_count > 0)
- **Never recommend indices with negative ROE** (loss-making companies)
- **Prefer indices with score >= 60** for small/medium, >= 50 for large
- **The consumer cluster is the most dangerous for over-concentration** — many indices overlap (白酒 ⊂ 食品 ⊂ 消费). Always cap consumer-like themes combined at 25%
- **Include at least one value/dividend-focused index** in every portfolio as a defensive anchor
- **Include geographic diversification** (HK indices) in the large portfolio if good candidates exist
