**It's 100% fixed algorithm + existing data.** No LLM is involved.

Here's how it works:

1. **`generate_portfolios(rows)`** (line 1839) takes the index data rows and uses a deterministic algorithm:
   - Predefined theme order and counts (`消费`, `医药`, `红利`, etc.)
   - `pick_best_per_theme()` selects top indices per theme based on scoring
   - Weights are calculated arithmetically (equal weight with overlap caps like 25% max for 消费)
   - Three tiers (S/M/L) are built with different theme count configurations

2. **`build_portfolio_item(r)`** (line 1797) extracts metrics (PE位, PB位, ROE, 股息率, etc.) directly from the CSV data

3. The result is serialized as a JavaScript constant (`PORTFOLIOS`) embedded in the HTML — the browser just renders it, no further computation needed.

So the entire recommendation is a rule-based selection (pick best-scoring indices per theme, allocate weights with caps) using the same valuation data that populates the rest of the report. The GitHub Actions workflow can regenerate it without any API calls to an LLM.