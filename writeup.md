# Submission Writeup — Financial Screener

---

## Problem Framing

Analyzing the financial health of Vietnamese listed companies is slow and manual. A financial analyst working across ~1,155 tickers has to switch between Excel tabs, recompute the same ratios for each company, and rebuild comparisons from scratch every quarter. The specific pain point: there is no fast way to answer "how does this company's ROE compare to its industry peers, and who are the top performers in that industry right now?"

The goal of this tool is to eliminate that friction — load the raw vnstock data once, compute all ratios automatically, and surface three views that cover the most common analytical questions: (1) how is this company trending over time, (2) how does it rank within its industry, and (3) what does the full industry landscape look like right now.

---

## Architecture Choices

**Data pipeline:** The companion Jupyter notebook (`vnstock_pull_bctc.ipynb`) pulls Income Statement, Balance Sheet, and Cash Flow data from the KBS source via the vnstock v3 Python library, for all HOSE, HNX, and UPCOM listed companies, across 4 rolling quarters. It outputs a single flat Excel file (`ALL_BCTC_*.xlsx`) in long format: one row per company per quarter. The Streamlit app reads this one file directly — no database, no server, no API.

**Industry classification:** The `industry` column is sourced manually from SSI's industry classification export — not from KBS, which does not provide sufficiently complete or standardised sector mapping. This means re-running the notebook does not automatically refresh industry assignments; a new SSI export is required when the classification changes.

**Why flat Excel, not a database?** For a single analyst on a local machine, the Excel file is the simplest and most auditable format. The analyst can open it, verify the data, and the notebook already produces it. Adding a database layer would mean managing migrations, connection strings, and an additional tool — none of which are justified at this scale.

**Why Streamlit?** Fast to build, runs locally, requires no deployment infrastructure. The analyst runs `py -m streamlit run streamlit_app.py` and gets an interactive dashboard in under 30 seconds.

**Ratio computation:** All 17 ratios are computed on-the-fly in pandas when the app loads. Quarterly IS/CF items are annualised ×4. Division-by-zero and NaN/Inf are handled explicitly — ratios that cannot be computed display as `-` rather than crashing or showing misleading zeros.

**Industry benchmarks:** The app groups companies by the `industry` column (embedded in the Excel by the notebook, sourced from the KBS listing API), then computes Avg, Top 1/2/3, and Avg Top 3 for each ratio in each quarter. Rankings respect a `higher_is_better` flag per metric (e.g. ROE higher = better, D/E lower = better). This runs as a pure pandas groupby — no pre-aggregation, always reflects the current dataset.

**Configuration:** All file paths and column names live in `config.py`, separate from application logic. The app includes a first-time setup screen when files are missing, and a Column Check panel in the sidebar to diagnose missing column mappings without reading source code.

---

## Tools Used

| Tool | Role |
|------|------|
| Python 3.13 | Runtime |
| vnstock v3 (KBS source) | Financial data API for Vietnamese listed companies |
| pandas, numpy | Data loading, ratio computation, benchmarking |
| Streamlit 1.35+ | Dashboard framework |
| Plotly | Interactive charts |
| openpyxl | Excel read/write |
| Claude Sonnet 4.6 | Architecture decisions, code generation, debugging, this writeup |

**Total AI cost:** All code was generated via Claude.ai (claude.ai/chat) — no direct API calls billed separately. Claude was used for: architecture design, full code generation of `streamlit_app.py` and `config.py`, debugging column-mapping issues, and drafting documentation. Estimated session cost: ~$0 (covered under Claude Pro subscription).

---

## What Works

- **End-to-end data flow**: notebook exports Excel → app reads it, no manual steps in between
- **17 financial ratios** computed correctly across all tickers and quarters
- **Industry benchmarking** with 5 comparison columns (Avg / Top 1 / Top 2 / Top 3 / Avg Top 3), color-coded green/red vs industry average
- **First-time UX**: setup screen with clear instructions if files are missing, Column Check panel for debugging
- **NaN/Inf handling**: division by zero, missing columns, and tickers without industry classification all degrade gracefully
- **Streamlit caching**: raw data and ratio computation are cached — subsequent interactions are fast even on a 50MB file

---

## Edge Cases Handled

- **Missing industry column**: the `industry` column is sourced from SSI's classification export and added manually. If absent in an older file, the app surfaces a warning via the Column Check panel rather than silently failing
- **File not found**: shows a setup screen with exact instructions rather than a Python traceback
- **File open in Excel**: handled with a readable error message
- **Column name changes across vnstock versions**: configurable in `config.py`, with a sidebar panel showing which columns are found vs missing
- **CAPEX sign**: stored as negative in some sources — taken as `abs()` before FCF computation
- **D&A missing**: EBITDA falls back to EBIT; flagged as an approximation in documentation
- **Zero denominators**: `_div()` returns NaN (not Inf) when denominator < 1e-9

## Known Limitations

**Data source constraints**

- **vnstock free tier cap**: KBS returns a maximum of 4 quarters per request on the free account. Accessing deeper history requires a paid vnstock Insiders plan. This is a hard API-level limit, not a code choice.
- **No true incremental update**: re-running the notebook to capture a new quarter does not fetch only that quarter — it re-pulls all 4 quarters for every ticker from scratch. With ~1,500 tickers at ~1.5s delay, each full run takes approximately 2 hours. There is no lightweight "add one quarter" mode under the current architecture.
- **KBS data availability lag**: KBS typically reflects newly filed quarterly reports 30–45 days after quarter-end. Running the notebook immediately after a quarter closes will produce incomplete coverage for the most recent period.
- **Dependency on vnstock and KBS**: if the vnstock library updates its API schema, column names or response format may change and break the column mapping in `config.py`. The Column Check panel in the sidebar surfaces this, but manual fixing is required.

**Industry classification**

- **Manual SSI export required**: KBS does not provide complete or standardised industry classification. The `industry` column is sourced from SSI's sector mapping, exported by hand. This means industry assignments do not auto-refresh when companies reclassify — a new SSI export and notebook re-run is needed.
- **Newly listed companies**: tickers listed after the last SSI export will have no industry assignment and will be excluded from all industry benchmark views.

**Financial ratio computation**

- **Quarterly annualisation ×4**: IS and CF ratios multiply the single-quarter value by 4 rather than using a rolling TTM sum. This overstates or understates for seasonal businesses.
- **EBITDA approximation**: computed as EBIT + D&A. If the `depreciation_amortization` column is missing from the KBS output, EBITDA falls back to EBIT, understating the true figure.
- **Column name fragility**: actual column names in the Excel depend on the vnstock/KBS version at the time of the pull. If they differ from the defaults in `config.py`, all ratios using that column show `-` until manually remapped.

**Operational**

- **File size**: the merged Excel is ~50MB. First load in Streamlit takes 10–20 seconds; Streamlit cache handles subsequent interactions.
- **No live data**: the dashboard reflects the last notebook run. There is no auto-refresh or scheduled pull.

1. **TTM (trailing twelve months) ratios** — rolling sum of last 4 quarters for IS/CF items, instead of single-quarter ×4. More accurate for seasonal businesses.

2. **YoY growth flags** — for each ratio, show the direction and magnitude of change vs the same quarter one year prior. Currently the time-series charts show the trend visually but don't surface the number explicitly.

3. **Export to PDF** — a one-click export of the Company vs Industry view as a formatted PDF, using the Fortune Advisory brand system. Currently the analyst has to screenshot.

4. **Watchlist** — let the analyst save a list of tickers and see them all side-by-side in a single dashboard, rather than selecting one at a time.

5. **Automatic column detection** — fuzzy-match common vnstock column name variants (e.g. `net_profit` vs `profit_after_tax` vs `net_income`) so the app works out of the box across KBS versions without manual config.

---

## Brief Architecture Diagram

```
[vnstock KBS API]
      |
      | Finance() + listing.symbols_by_industries()
      v
[vnstock_pull_bctc.ipynb]  ──exports──>  ALL_BCTC_KBS_quarter_4Q_[ts].xlsx
                                               |  TONG_HOP sheet
                                               |  ticker / exchange / year / quarter
                                               |  industry (from KBS listing, built-in)
                                               |  ~750 financial columns (IS + BS + CF)
                                               |
                                               v
                                      [streamlit_app.py]
                                               |
                                         load + cache
                                         compute 17 ratios
                                               |
                               +---------------+---------------+
                               |               |               |
                        Company            Company         Industry
                        Dashboard       vs Industry        Screener
                               |               |               |
                         Plotly line      HTML table      Plotly bar +
                         charts x5        7 columns       trend lines
```