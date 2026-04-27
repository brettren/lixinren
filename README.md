# lixinren

A collection of Python scripts for fetching and analyzing Chinese stock index valuation data using the [Lixinger (理杏仁)](https://www.lixinger.com/) open API.

## Features

- **Index Valuation Snapshot** (`lixinren.py`) — Fetches PE, PB, ROE, dividend yield, and percentile positions for A-share, Hong Kong, and industry indices. Outputs color-coded results to `stock_stat.xlsx`.
- **Index Drawdown Analysis** (`index_drawdown.py`) — Calculates current and largest 3-year drawdowns for tracked indices, with distance-to-lowest and recovery-to-highest metrics.
- **All-Index Drawdown & History** (`allindex/all_index_drawdown_current_and_history.py`) — Comprehensive drawdown analysis across all indices with fund tracking, style classification, and valuation data.
- **Historical Index Data** (`index_history.py`) — Records weekly index fundamentals (PE, PB, PS, ROE, dividend, book value, earnings) to CSV and generates trend charts.
- **Annual Return Summary** — Computes annual book value growth, earnings growth, and ROE for each tracked index.
- **QDII Fund Analysis** (`qdIIFunds/qdII_funds_info.py`) — Fetches all active QDII funds, calculates drawdown metrics, and exports to CSV/Excel.
- **Highest Index Tracking** (`get_highest_index.py`) — Finds historical highest net values for funds via the dividend reinvestment API.

## Project Structure

```
lixinren.py              # Main index valuation script (A-share, HK, industry sectors)
index_drawdown.py        # Index drawdown analysis (3-year)
index_history.py         # Weekly historical data collection & charting
index_annual_return.py   # Annual return calculation (prototype)
get_highest_index.py     # Fund highest net value lookup
config.py                # Shared config (date, API token, position maps)
utils.py                 # Utility functions
main.py                  # Entry point — runs lixinren.py and index_history.py
allindex/                # All-index analysis scripts
  all_index_drawdown_current_and_history.py
  all_index_largest_drawdown_in_10_years.py
  all_index_highest_index_in_history.py
  all_index_tracking_fund.py
  all_index_drawdown.py
qdIIFunds/               # QDII fund analysis
  qdII_funds_info.py
index/                   # Historical CSV data per index
```

## Prerequisites

- Python 3
- A valid [Lixinger Open API](https://www.lixinger.com/) token

## Dependencies

```
requests
openpyxl
pandas
matplotlib
xlsxwriter
```

## Configuration

Edit `config.py` to set:

- `today` — the target date for data fetching
- `token` — your Lixinger API token
- `positionMaps` — indices you currently hold positions in (highlighted in output)

## Usage

Run the main entry point:

```bash
python main.py
```

Or run individual scripts:

```bash
python lixinren.py [date]          # e.g. python lixinren.py 2026-04-24
python index_drawdown.py
python get_highest_index.py
cd allindex && python all_index_drawdown_current_and_history.py
cd qdIIFunds && python qdII_funds_info.py
```
