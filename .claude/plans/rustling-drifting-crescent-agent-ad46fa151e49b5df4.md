# News Aggregation Module - Implementation Plan

## Overview

Design a news aggregation module for the lixinren project that collects industry news from three free Chinese financial platforms (巨潮资讯, 东方财富, 雪球), maps news to the 31 Shenwan first-level industries, stores data in SQLite, and generates a weekly summary report integrated into the existing HTML report and GitHub Actions workflow.

---

## 1. File/Directory Structure

```
news/
├── __init__.py                    # Module init (empty or with version)
├── collectors/
│   ├── __init__.py
│   ├── base.py                    # BaseCollector ABC with shared logic
│   ├── cninfo.py                  # 巨潮资讯 collector
│   ├── eastmoney.py               # 东方财富 collector
│   └── xueqiu.py                  # 雪球 collector
├── industry_mapping.py            # Shenwan industry -> platform search params
├── storage.py                     # SQLite DB init, insert, query functions
├── aggregator.py                  # Orchestrator: runs all collectors for all industries
├── report.py                      # Weekly report generation (HTML section)
├── run_weekly.py                  # Entry point script (called by CI or manually)
└── news.db                        # SQLite database (gitignored)
```

**Rationale:** Follows the existing pattern where each top-level directory (`allindex/`, `qdIIFunds/`) is a self-contained module with its own scripts and data outputs. The `collectors/` subdirectory keeps the three platform-specific implementations cleanly separated.

---

## 2. Core Classes/Functions

### 2.1 `collectors/base.py` - Base Collector

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import time
import requests
from fake_useragent import UserAgent

@dataclass
class NewsItem:
    title: str
    publish_time: str          # ISO format: "2026-05-09 14:30:00"
    source: str                # "巨潮资讯" | "东方财富" | "雪球"
    url: str
    industry_code: str         # SW code like "801150.SI"
    industry_name: str         # "医药生物"
    content: Optional[str] = None  # Brief summary/snippet (first 200 chars)
    author: Optional[str] = None

class BaseCollector(ABC):
    def __init__(self, request_interval: float = 3.0):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UserAgent().random})
        self.request_interval = request_interval

    @abstractmethod
    def collect_industry(self, industry_code: str, industry_name: str,
                         start_date: str, end_date: str) -> List[NewsItem]:
        """Collect news for a single industry within date range."""
        pass

    def _sleep(self):
        time.sleep(self.request_interval)
```

### 2.2 `collectors/cninfo.py` - 巨潮资讯

Key function: `collect_industry()` posts to `https://www.cninfo.com.cn/new/hisAnnouncement/query` with the `plate` parameter mapped from Shenwan industry name. Returns formal company announcements (earnings, policies, disclosures).

### 2.3 `collectors/eastmoney.py` - 东方财富

Key function: `collect_industry()` calls the EastMoney news API (board-level news aggregation endpoint). Uses the EastMoney industry board code mapped from the Shenwan industry.

**Practical note:** EastMoney's sector news API is at:
```
https://search.eastmoney.com/bussiness/Web/GetCMSSearchList
```
with params `KeyWord=<industry_name>&type=8001` for financial news search. This is more reliable than the quote-based API for news content.

### 2.4 `collectors/xueqiu.py` - 雪球

Key function: `collect_industry()` searches via `https://xueqiu.com/statuses/search.json?q=<keyword>&count=20`. Requires an initial page visit to get `xq_a_token` cookie. Captures investor discussions and sentiment.

**Practical note:** Xueqiu rate-limits aggressively. For weekly batch (not daily), 31 industries at 3-5 sec intervals = ~2-3 minutes total, well within tolerance.

### 2.5 `industry_mapping.py` - Platform Search Parameter Mapping

```python
import akshare as ak

def get_sw_industries() -> list:
    """Fetch current 31 Shenwan first-level industries dynamically.
    Returns list of dicts: [{"code": "801150.SI", "name": "医药生物"}, ...]
    """
    df = ak.sw_index_first_info()
    return [{"code": row["行业代码"], "name": row["行业名称"]}
            for _, row in df.iterrows()]

# Static mapping: SW industry name -> platform-specific search terms
# Some industries need adjusted keywords for better search results
INDUSTRY_SEARCH_KEYWORDS = {
    "农林牧渔": ["农业", "养殖", "种植", "饲料"],
    "基础化工": ["化工", "化学"],
    "钢铁": ["钢铁", "钢材"],
    "有色金属": ["有色金属", "铜铝", "稀土"],
    "电子": ["电子", "半导体", "芯片"],
    "汽车": ["汽车", "新能源车"],
    "家用电器": ["家电", "白色家电"],
    "食品饮料": ["食品饮料", "白酒"],
    "纺织服饰": ["纺织服装"],
    "轻工制造": ["轻工制造", "造纸"],
    "医药生物": ["医药", "生物医药", "创新药"],
    "公用事业": ["公用事业", "电力", "水务"],
    "交通运输": ["交通运输", "航运", "物流"],
    "房地产": ["房地产", "地产"],
    "商贸零售": ["商贸零售", "零售"],
    "社会服务": ["社会服务", "旅游", "教育"],
    "银行": ["银行"],
    "非银金融": ["非银金融", "证券", "保险"],
    "综合": ["综合"],
    "建筑材料": ["建筑材料", "水泥"],
    "建筑装饰": ["建筑装饰", "基建"],
    "电力设备": ["电力设备", "光伏", "储能"],
    "机械设备": ["机械设备", "工程机械"],
    "国防军工": ["军工", "国防"],
    "计算机": ["计算机", "软件", "信创"],
    "传媒": ["传媒", "游戏", "影视"],
    "通信": ["通信", "5G", "算力"],
    "煤炭": ["煤炭"],
    "石油石化": ["石油", "石化"],
    "环保": ["环保", "固废"],
    "美容护理": ["美容护理", "化妆品"],
}

# EastMoney board codes (static lookup, sourced from their API)
EASTMONEY_BOARD_CODES = {
    "农林牧渔": "BK0475",
    "基础化工": "BK0537",
    "钢铁": "BK0478",
    # ... (to be populated by running a one-time discovery script)
}

# cninfo plate names (matches their API "plate" parameter)
CNINFO_PLATE_NAMES = {
    "农林牧渔": "农林牧渔",
    "医药生物": "医药生物",
    # ... (directly uses SW industry names - cninfo uses same taxonomy)
}
```

**Key design decision:** Use the SW industry name directly as the primary search keyword (it works on all three platforms as general text search). The `INDUSTRY_SEARCH_KEYWORDS` dict provides supplementary keywords for broader coverage. For the initial implementation, searching by industry name alone is sufficient and avoids maintaining a complex mapping.

### 2.6 `storage.py` - SQLite Storage

```python
import sqlite3
import hashlib
from typing import List
from .collectors.base import NewsItem

DB_PATH = os.path.join(os.path.dirname(__file__), "news.db")

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_id TEXT UNIQUE,
        title TEXT NOT NULL,
        publish_time TEXT,
        source TEXT,
        url TEXT,
        industry_code TEXT,
        industry_name TEXT,
        content TEXT,
        author TEXT,
        collected_at TEXT DEFAULT (datetime('now', 'localtime')),
        week_label TEXT  -- e.g. "2026-W19"
    )''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_industry
                    ON news(industry_code, publish_time)''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_week
                    ON news(week_label)''')
    conn.commit()
    conn.close()

def compute_unique_id(title: str, url: str) -> str:
    return hashlib.md5(f"{title}|{url}".encode()).hexdigest()

def insert_news(items: List[NewsItem], week_label: str, db_path=DB_PATH) -> int:
    """Insert news items, skip duplicates. Returns count of new items."""
    conn = sqlite3.connect(db_path)
    inserted = 0
    for item in items:
        uid = compute_unique_id(item.title, item.url)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO news (unique_id, title, publish_time, source, url, "
                "industry_code, industry_name, content, author, week_label) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (uid, item.title, item.publish_time, item.source, item.url,
                 item.industry_code, item.industry_name, item.content, item.author, week_label)
            )
            inserted += conn.total_changes
        except Exception:
            pass
    conn.commit()
    conn.close()
    return inserted

def query_week_news(week_label: str, db_path=DB_PATH) -> list:
    """Get all news for a given week, grouped by industry."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM news WHERE week_label = ? ORDER BY industry_name, publish_time DESC",
        (week_label,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
```

### 2.7 `aggregator.py` - Orchestrator

```python
from datetime import datetime, timedelta
from .industry_mapping import get_sw_industries, INDUSTRY_SEARCH_KEYWORDS
from .collectors.cninfo import CninfoCollector
from .collectors.eastmoney import EastMoneyCollector
from .collectors.xueqiu import XueqiuCollector
from .storage import init_db, insert_news

def run_collection(days_back: int = 7):
    """Run all collectors for all 31 industries for the past N days."""
    init_db()
    industries = get_sw_industries()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    week_label = datetime.now().strftime("%G-W%V")  # ISO week

    collectors = [
        CninfoCollector(request_interval=3.0),
        EastMoneyCollector(request_interval=2.0),
        XueqiuCollector(request_interval=5.0),
    ]

    total_items = 0
    for industry in industries:
        code = industry["code"]
        name = industry["name"]
        print(f"Collecting news for {name} ({code})...")
        for collector in collectors:
            try:
                items = collector.collect_industry(code, name, start_date, end_date)
                if items:
                    count = insert_news(items, week_label)
                    total_items += count
                    print(f"  {collector.__class__.__name__}: {count} new items")
            except Exception as e:
                print(f"  {collector.__class__.__name__} failed: {e}")

    print(f"\nTotal new items collected: {total_items}")
    return total_items
```

### 2.8 `run_weekly.py` - Entry Point

```python
#!/usr/bin/env python
"""Weekly news collection and report generation.
Usage: python -m news.run_weekly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news.aggregator import run_collection
from news.report import generate_weekly_report

def main():
    print("=== News Collection ===")
    run_collection(days_back=7)

    print("\n=== Report Generation ===")
    generate_weekly_report()

if __name__ == "__main__":
    main()
```

---

## 3. Shenwan Industry Mapping Strategy

**Approach: Progressive simplicity**

1. **Primary method:** Use `ak.sw_index_first_info()` (same as `sw_industry_valuation.py`) to get the live list of 31 industries. The industry name (e.g., "医药生物") is used directly as the search keyword on all platforms.

2. **Supplementary keywords:** The `INDUSTRY_SEARCH_KEYWORDS` dict provides 2-3 alternative search terms per industry to broaden coverage (e.g., "医药生物" also searches "创新药").

3. **Platform-specific codes:** Only needed for cninfo's `plate` parameter (which fortunately uses the same industry taxonomy as Shenwan). EastMoney and Xueqiu work with free-text search.

4. **No manual maintenance:** If Shenwan adds/removes an industry, the dynamic fetch via `ak.sw_index_first_info()` handles it automatically. The keyword dict can gracefully fall back to using the industry name if a new industry appears without a mapping entry.

---

## 4. Database Schema

```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_id TEXT UNIQUE,           -- MD5(title|url) for deduplication
    title TEXT NOT NULL,
    publish_time TEXT,               -- "2026-05-09 14:30:00"
    source TEXT,                     -- "巨潮资讯" | "东方财富" | "雪球"
    url TEXT,
    industry_code TEXT,              -- "801150.SI"
    industry_name TEXT,              -- "医药生物"
    content TEXT,                    -- First 200 chars of body/snippet
    author TEXT,                     -- Relevant for Xueqiu posts
    collected_at TEXT DEFAULT (datetime('now', 'localtime')),
    week_label TEXT                  -- "2026-W19" for easy weekly grouping
);

CREATE INDEX idx_industry ON news(industry_code, publish_time);
CREATE INDEX idx_week ON news(week_label);
CREATE INDEX idx_source ON news(source);
```

**Design notes:**
- `unique_id` as MD5 hash prevents duplicate inserts across runs
- `week_label` (ISO week format) enables fast weekly report queries without date range calculations
- `industry_code` + `industry_name` stored together for query convenience (denormalized, acceptable for personal tool)
- No separate tables for industries or sources (unnecessary complexity for 31 industries x 3 sources)

---

## 5. Weekly Report Format

**Format: HTML section integrated into the existing report.**

The news report will be generated as a standalone HTML file at `news/weekly_news_report.html`, and also injected as a new tab in the existing `allindex/all_index_drawdown_current_and_history.html` report.

### Report Structure:

```
news/weekly_news_report.html       # Standalone readable report
news/weekly_news_summary.csv       # CSV export for archival / git tracking
```

### HTML Report Content:

1. **Summary header**: Week label, total news count, top 5 industries by news volume
2. **Industry-by-industry sections** (sorted by news count descending):
   - Industry name + valuation score (pulled from sw_industry_valuation.csv)
   - News items listed with title, source, date, link
   - Max 10 items per industry (most recent)
3. **Source breakdown**: Pie/bar showing news distribution across platforms
4. **Hot industries highlight**: Industries with >N news items flagged as "hot"

### Integration with existing HTML report:

Add a 4th tab to `generate_html_report.py`:
```
<button onclick="switchTab('tab4')">行业新闻 (XX)</button>
```

The `generate_html_report.py` will read the news CSV/DB and embed the news summary data similar to how it embeds SW industry valuation data today.

### CSV output format (for git tracking):

```csv
2026-W19,industry_code,industry_name,news_count,top_titles
801150.SI,医药生物,12,"集采政策新规; 创新药获批..."
801780.SI,银行,8,"利率调整; 不良率公布..."
```

---

## 6. GitHub Actions Integration

Add a new step to `.github/workflows/weekly_report.yml`:

```yaml
      - name: Install news dependencies
        run: pip install beautifulsoup4 fake_useragent

      - name: Collect weekly news
        working-directory: news
        run: python run_weekly.py
        env:
          PYTHONPATH: ${{ github.workspace }}

      - name: Commit and push results
        run: |
          # ... existing git add commands ...
          git add news/weekly_news_summary.csv
          # news.db is gitignored (too large, binary)
```

**Important considerations for CI:**
- The SQLite DB (`news.db`) should NOT be committed to git (add to `.gitignore`). It is ephemeral in CI - each run collects fresh data for that week.
- Only the CSV summary is committed for historical tracking.
- The news data gets embedded into the HTML report via `generate_html_report.py` reading the CSV.
- Total runtime estimate: 31 industries x 3 platforms x 3-5 sec delay = ~5-8 minutes. Acceptable for a weekly job.

### Updated workflow step order:

```
1. Generate drawdown CSV        (existing)
2. Generate QDII funds drawdown (existing)
3. Generate SW industry valuation (existing)
4. Collect weekly news           (NEW)
5. Generate HTML report          (existing, enhanced to include news tab)
6. Commit and push               (existing, add news CSV)
```

---

## 7. New Dependencies

| Package | Purpose | Already installed? |
|---------|---------|-------------------|
| `requests` | HTTP requests | Yes (in venv) |
| `beautifulsoup4` | HTML parsing (Xueqiu page parsing) | Yes (in venv) |
| `pandas` | Data manipulation | Yes (used everywhere) |
| `fake_useragent` | Random User-Agent rotation | **No - needs install** |
| `sqlite3` | Database | Built-in (Python stdlib) |
| `akshare` | SW industry list fetch | Yes (already used) |
| `hashlib` | Dedup hash generation | Built-in (Python stdlib) |

**Only `fake_useragent` needs to be added.** Add to the `pip install` line in the GitHub Actions workflow:
```yaml
run: pip install requests pandas openpyxl xlsxwriter akshare numpy beautifulsoup4 fake_useragent
```

**Alternative:** If `fake_useragent` proves unreliable (it fetches UA lists from an external source), a simple hardcoded list of 5-10 User-Agent strings in a constant would work fine for a personal tool.

---

## 8. Implementation Sequence

### Phase 1: Core infrastructure (do first)
1. Create `news/` directory structure with `__init__.py` files
2. Implement `storage.py` (SQLite init + insert + query)
3. Implement `industry_mapping.py` (dynamic SW fetch + keyword dict)
4. Implement `collectors/base.py` (dataclass + ABC)

### Phase 2: Collectors (can be done incrementally)
5. Implement `collectors/cninfo.py` (most reliable, start here)
6. Implement `collectors/eastmoney.py`
7. Implement `collectors/xueqiu.py` (most complex, do last)

### Phase 3: Orchestration + Report
8. Implement `aggregator.py`
9. Implement `report.py` (HTML + CSV generation)
10. Implement `run_weekly.py` (entry point)

### Phase 4: Integration
11. Update `allindex/generate_html_report.py` to add news tab
12. Update `.github/workflows/weekly_report.yml`
13. Update `.gitignore` (add `news/news.db`)
14. Update `README.md`

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Platform API changes | Each collector is isolated; one failure doesn't break others. Use try/except per collector. |
| Rate limiting / IP bans | Conservative delays (3-5s between requests). Weekly-only frequency is very light. |
| Xueqiu requires auth | Start without auth (public content only). Add cookie-based auth later if needed. |
| CI timeout (8+ min) | Set `timeout-minutes: 15` on the news step. If too slow, limit to top 10 industries by valuation score. |
| Empty results for some industries | Expected and acceptable. Log but don't fail. |
| `fake_useragent` external dependency | Fallback to hardcoded UA list if the package's remote fetch fails. |

---

## 10. Testing Strategy

Since this is a personal tool, formal tests are optional. But a simple validation approach:

```bash
# Test individual collector
python -c "from news.collectors.cninfo import CninfoCollector; c = CninfoCollector(); print(c.collect_industry('801150.SI', '医药生物', '2026-05-03', '2026-05-10'))"

# Test full pipeline
cd /path/to/lixinren && python -m news.run_weekly

# Verify DB
sqlite3 news/news.db "SELECT industry_name, COUNT(*) FROM news GROUP BY industry_name;"
```

---

## Key Design Decisions Summary

1. **Flat module structure** over complex package - this is a personal tool, keep it simple.
2. **Dynamic industry list** from akshare, not hardcoded - stays in sync with sw_industry_valuation.py.
3. **SQLite single table** over normalized schema - 31 industries x ~20 items x 3 sources = ~1800 rows/week max, trivial volume.
4. **HTML tab integration** over separate report - user already has one dashboard, add to it.
5. **CSV for git, DB for queries** - best of both worlds for tracking history.
6. **Weekly only, no scheduler** - aligns with requirements and GitHub Actions cadence.
7. **Graceful degradation** - if one platform fails, others still produce useful output.
