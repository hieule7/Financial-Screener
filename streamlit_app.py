# =============================================================================
# Hayes Le — Financial Screener
# streamlit_app.py  |  v3.2  (Cyber / Deep Navy · Bloomberg Terminal aesthetic)
#
# RUN:  py -m streamlit run streamlit_app.py
# SETUP: Edit the two file paths in config.py before running for the first time.
# New in v3.2: Health Score, Anomaly Flags, Percentile Ranking
# =============================================================================

import glob, os, warnings
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import config as cfg

warnings.filterwarnings("ignore")

# ── Brand colors — Cyber / Deep Navy ─────────────────────────────────────────
C = dict(
    bg       = "#0A0F1E",
    surface  = "#0F1629",
    surface2 = "#141D35",
    border   = "#1E2D4F",
    accent   = "#00D4FF",
    accent2  = "#7C3AED",
    accent3  = "#06B6D4",
    positive = "#10B981",
    negative = "#F43F5E",
    text     = "#E2E8F0",
    muted    = "#64748B",
    dim      = "#334155",
    gold     = "#F59E0B",
)

PLOTLY_BASE = dict(
    font         = dict(family="'JetBrains Mono', 'Fira Code', monospace", color=C["text"], size=11),
    paper_bgcolor = C["bg"],
    plot_bgcolor  = C["surface"],
    margin       = dict(l=48, r=24, t=52, b=44),
    colorway     = [C["accent"], C["accent2"], C["accent3"], C["gold"], "#A78BFA"],
    xaxis        = dict(
        gridcolor = C["border"], linecolor = C["border"],
        tickfont  = dict(size=10, color=C["muted"]),
        showgrid  = True, zeroline = False,
    ),
    yaxis        = dict(
        gridcolor = C["border"], linecolor = C["border"],
        tickfont  = dict(size=10, color=C["muted"]),
        showgrid  = True, zeroline = False,
    ),
    legend       = dict(
        bgcolor     = "rgba(0,0,0,0)",
        font        = dict(size=10, color=C["muted"]),
        bordercolor = "rgba(0,0,0,0)",
    ),
    title        = dict(
        font    = dict(size=12, color=C["text"]),
        x       = 0,
        xanchor = "left",
    ),
)

# ── Ratio definitions ─────────────────────────────────────────────────────────
# key: (display_label, format, higher_is_better, group)
RATIOS = {
    # M1
    "ROIC":              ("ROIC (%)",                       "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "ROE":               ("ROE (%)",                        "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "ROA":               ("ROA (%)",                        "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Gross_Margin":      ("Gross Margin (%)",                "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "EBIT_Margin":       ("EBIT Margin (%)",                 "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Net_Margin":        ("Net Profit Margin (%)",           "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "EBITDA_Margin":     ("EBITDA Margin (%)",               "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "CCQ":               ("CCQ — CFO/EBITDA (×)",           "mul",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Asset_Turnover":    ("Asset Turnover (×)",              "mul",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Rev_Growth_YoY":    ("Tăng trưởng DT YoY (%)",         "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "NP_Growth_YoY":     ("Tăng trưởng LNST YoY (%)",       "pct",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Net_Debt_EBITDA":   ("Net Debt / EBITDA (×)",          "mul",  False, "M1 — Hiệu quả & Tăng trưởng"),
    "Fixed_Cost_Cover":  ("Fixed Cost Coverage (×)",        "mul",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Reinvestment_Rate": ("Reinvestment Rate (%)",           "pct",  False, "M1 — Hiệu quả & Tăng trưởng"),
    "EBITDA_abs":        ("EBITDA (tỷ VND)",                "abs",  True,  "M1 — Hiệu quả & Tăng trưởng"),
    "Net_Debt_abs":      ("Net Debt (tỷ VND)",              "abs",  False, "M1 — Hiệu quả & Tăng trưởng"),
    # M2
    "DSCR":              ("DSCR (×)",                       "mul",  True,  "M2 — Khả năng trả nợ"),
    "Current_Ratio":     ("Current Ratio (×)",              "mul",  True,  "M2 — Khả năng trả nợ"),
    "Quick_Ratio":       ("Quick Ratio / TTNQ (×)",         "mul",  True,  "M2 — Khả năng trả nợ"),
    "D_E":               ("Nợ/VCSH (×)",                    "mul",  False, "M2 — Khả năng trả nợ"),
    "Collateral_Cover":  ("Collateral Coverage (×)",        "mul",  True,  "M2 — Khả năng trả nợ"),
    # M3
    "FCF_Margin":        ("FCF Margin (%)",                  "pct",  True,  "M3 — Năng suất & Tăng trưởng"),
    "CFO_Margin":        ("CFO Margin (%)",                  "pct",  True,  "M3 — Năng suất & Tăng trưởng"),
    "CFO_abs":           ("CFO (tỷ VND)",                   "abs",  True,  "M3 — Năng suất & Tăng trưởng"),
    "CAPEX_abs":         ("CAPEX (tỷ VND)",                 "abs",  False, "M3 — Năng suất & Tăng trưởng"),
    "FCF_abs":           ("FCF (tỷ VND)",                   "abs",  True,  "M3 — Năng suất & Tăng trưởng"),
    # M4
    "DSO":               ("DSO (ngày)",                     "day",  False, "M4 — Working Capital"),
    "DIO":               ("DIO (ngày)",                     "day",  False, "M4 — Working Capital"),
    "DPO":               ("DPO (ngày)",                     "day",  True,  "M4 — Working Capital"),
    "CCC":               ("CCC — Chu kỳ tiền mặt (ngày)",  "day",  False, "M4 — Working Capital"),
    "Inv_Turnover":      ("Vòng quay HTK (×)",              "mul",  True,  "M4 — Working Capital"),
}

# YoY metrics — used to detect and label unavailable groups
_YOY_KEYS = {"Rev_Growth_YoY", "NP_Growth_YoY"}

# ── Health Score weights ──────────────────────────────────────────────────────
# (metric_key: (group, weight_within_total_100))
HEALTH_WEIGHTS = {
    "ROIC":          ("M1", 15),
    "Gross_Margin":  ("M1",  8),
    "Net_Margin":    ("M1", 10),
    "EBITDA_Margin": ("M1",  7),
    "DSCR":          ("M2", 12),
    "Current_Ratio": ("M2",  8),
    "D_E":           ("M2",  5),
    "FCF_Margin":    ("M3", 15),
    "CFO_Margin":    ("M3", 10),
    "CCC":           ("M4",  5),
    "Inv_Turnover":  ("M4",  5),
}
# Group contribution to overall score (must sum to 100)
GROUP_WEIGHTS = {"M1": 40, "M2": 25, "M3": 25, "M4": 10}

# ── Alert thresholds ──────────────────────────────────────────────────────────
# (ratio_key, display_label, operator, threshold, level, description)
ALERT_THRESHOLDS = [
    ("D_E",             "Nợ/VCSH",          "gt", 3.0,  "ALERT", "High leverage (D/E > 3×)"),
    ("Current_Ratio",   "Current Ratio",    "lt", 1.0,  "ALERT", "Liquidity risk (CR < 1×)"),
    ("DSCR",            "DSCR",             "lt", 1.5,  "WARN",  "Debt service stress (< 1.5×)"),
    ("Net_Margin",      "Net Margin",       "lt", 0.0,  "ALERT", "Loss-making quarter"),
    ("FCF_abs",         "FCF",              "lt", 0.0,  "WARN",  "Negative free cash flow"),
    ("Net_Debt_EBITDA", "Net Debt/EBITDA",  "gt", 4.0,  "WARN",  "High net leverage (> 4×)"),
]
SPIKE_METRICS = ["ROIC", "ROE", "Net_Margin", "D_E", "Current_Ratio", "FCF_Margin", "DSCR"]


def fmt(v, style):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "—"
    try:
        if style == "pct": return f"{v:.1f}%"
        if style == "mul": return f"{v:.2f}×"
        if style == "day": return f"{v:.0f}"
        if style == "abs": return f"{v:,.0f}"
    except Exception:
        pass
    return "—"


# =============================================================================
# ANALYTICS HELPERS — Percentile / Health Score / Flags
# =============================================================================
def compute_percentile(val, peer_series, higher_is_better):
    """Return 0–100 percentile adjusted for metric direction."""
    if not np.isfinite(val):
        return np.nan
    s = pd.to_numeric(peer_series, errors="coerce").dropna()
    s = s[np.isfinite(s)]
    if len(s) < 2:
        return np.nan
    return float((s < val).sum() / len(s) * 100) if higher_is_better \
           else float((s > val).sum() / len(s) * 100)


def compute_health_score(co_row, peers_df):
    """
    Compute composite 0–100 Health Score using percentile-weighted method.
    Returns dict: {score, M1, M2, M3, M4, n}
    """
    def _wavg(items):
        if not items: return np.nan
        tw = sum(w for _, w in items)
        return sum(p * w for p, w in items) / tw if tw else np.nan

    group_scores = {g: [] for g in GROUP_WEIGHTS}

    for rk, (grp, w) in HEALTH_WEIGHTS.items():
        if rk not in RATIOS or rk not in peers_df.columns:
            continue
        _, _, higher, _ = RATIOS[rk]
        try:
            val = float(co_row.get(rk, np.nan))
        except Exception:
            val = np.nan
        if not np.isfinite(val):
            continue
        pct = compute_percentile(val, peers_df[rk], higher)
        if np.isfinite(pct):
            group_scores[grp].append((pct, w))

    g = {k: _wavg(v) for k, v in group_scores.items()}
    overall_parts = [(g[k], GROUP_WEIGHTS[k]) for k in GROUP_WEIGHTS if np.isfinite(g[k])]
    return dict(score=_wavg(overall_parts), M1=g["M1"], M2=g["M2"], M3=g["M3"], M4=g["M4"],
                n=peers_df[cfg.COL_TICKER].nunique() if cfg.COL_TICKER in peers_df.columns else 0)


def compute_flags(df_co):
    """Return list of flag dicts: {level, metric, value, msg}"""
    flags = []
    if df_co.empty:
        return flags
    df_sorted = df_co.sort_values("period")
    latest = df_sorted.iloc[-1]
    prev   = df_sorted.iloc[-2] if len(df_sorted) >= 2 else None

    for rk, lbl, op, threshold, level, msg in ALERT_THRESHOLDS:
        try: val = float(latest.get(rk, np.nan))
        except: continue
        if not np.isfinite(val): continue
        if (op == "gt" and val > threshold) or (op == "lt" and val < threshold):
            flags.append({"level": level, "metric": lbl, "value": val, "msg": msg})

    if prev is not None:
        for rk in SPIKE_METRICS:
            if rk not in RATIOS: continue
            try:
                cv = float(latest.get(rk, np.nan))
                pv = float(prev.get(rk, np.nan))
            except: continue
            if not (np.isfinite(cv) and np.isfinite(pv)): continue
            if abs(pv) < 1e-9: continue
            rel = abs(cv - pv) / abs(pv)
            abs_d = abs(cv - pv)
            if rel > 0.40 and abs_d > 3.0:
                direction = "▲" if cv > pv else "▼"
                flags.append({"level": "SPIKE", "metric": RATIOS[rk][0], "value": cv,
                               "msg": f"{direction} {abs_d:.1f}pt QoQ ({rel*100:.0f}%)"})
    return flags


def render_health_card(hs, compact=False):
    """Return HTML string for the health score card."""
    score = hs["score"]
    if not np.isfinite(score):
        return (f'<div class="health-na">Health Score: insufficient peer data '
                f'({hs["n"]} peers)</div>')

    color = C["positive"] if score >= 70 else (C["gold"] if score >= 40 else C["negative"])

    if compact:
        return (f'<div class="health-compact">'
                f'<span class="hc-label">HEALTH</span>'
                f'<span class="hc-score" style="color:{color}">{score:.0f}</span>'
                f'<span class="hc-sub">/ 100 · {hs["n"]} peers</span>'
                f'</div>')

    groups = [("M1", "Profitability", hs["M1"]),
              ("M2", "Leverage",      hs["M2"]),
              ("M3", "Cash Flow",     hs["M3"]),
              ("M4", "Working Cap",   hs["M4"])]
    bars = ""
    for gk, glabel, gs in groups:
        if not np.isfinite(gs): continue
        gc = C["positive"] if gs >= 70 else (C["gold"] if gs >= 40 else C["negative"])
        bars += (f'<div class="hs-group-row">'
                 f'<span class="hs-glabel">{gk} · {glabel}</span>'
                 f'<div class="hs-bar-track">'
                 f'<div class="hs-bar-fill" style="width:{gs:.0f}%;background:{gc}"></div>'
                 f'</div>'
                 f'<span class="hs-gscore" style="color:{gc}">{gs:.0f}</span>'
                 f'</div>')

    return (f'<div class="health-card">'
            f'<div class="health-main">'
            f'<div class="hs-score-val" style="color:{color}">{score:.0f}</div>'
            f'<div class="hs-score-lbl">HEALTH SCORE</div>'
            f'<div class="hs-score-sub">vs {hs["n"]} peers · percentile-weighted</div>'
            f'</div>'
            f'<div class="health-groups">{bars}</div>'
            f'</div>')


def render_flags(flags):
    """Return HTML string for the flag panel."""
    if not flags:
        return (f'<div class="flags-clean">'
                f'<span style="color:{C["positive"]}">✓</span>'
                f' No alerts or anomalies detected</div>')

    cfg_map = {
        "ALERT": (C["negative"], "🔴", "ALERT"),
        "WARN":  (C["gold"],     "🟡", "WARN"),
        "SPIKE": (C["accent"],   "⚡", "SPIKE"),
    }
    html = '<div class="flags-container">'
    for f in flags:
        clr, icon, lbl = cfg_map.get(f["level"], (C["muted"], "ℹ", "INFO"))
        html += (f'<div class="flag-row" style="border-left-color:{clr}">'
                 f'<span class="flag-icon">{icon}</span>'
                 f'<span class="flag-lbl" style="color:{clr}">{lbl}</span>'
                 f'<span class="flag-metric">{f["metric"]}</span>'
                 f'<span class="flag-msg">{f["msg"]}</span>'
                 f'</div>')
    return html + '</div>'


def pct_cell(pct):
    """Return a <td> HTML element showing percentile rank with colour coding."""
    if not np.isfinite(pct):
        return f'<td class="pct-na">—</td>'
    clr = (C["accent"] if pct >= 75 else
           C["muted"]  if pct >= 50 else
           C["gold"]   if pct >= 25 else C["negative"])
    return f'<td class="pct-cell" style="color:{clr}">P{pct:.0f}</td>'


# =============================================================================
# DATA LOADING
# =============================================================================
@st.cache_data(show_spinner="Loading financial data...")
def load_raw_data():
    pattern = os.path.join(cfg.RAW_EXCEL_DIR, "ALL_BCTC_*.xlsx")
    files   = sorted(glob.glob(pattern))
    if not files:
        return pd.DataFrame(), None, "NOT_FOUND"
    path = files[-1]
    try:
        df = pd.read_excel(path, sheet_name=cfg.RAW_SHEET, dtype={cfg.COL_TICKER: str})
    except Exception as e:
        return pd.DataFrame(), path, str(e)
    df[cfg.COL_YEAR]    = pd.to_numeric(df[cfg.COL_YEAR],    errors="coerce").astype("Int64")
    df[cfg.COL_QUARTER] = pd.to_numeric(df[cfg.COL_QUARTER], errors="coerce").astype("Int64")
    df.dropna(subset=[cfg.COL_YEAR, cfg.COL_QUARTER, cfg.COL_TICKER], inplace=True)
    df["period"] = df[cfg.COL_YEAR].astype(str) + "-Q" + df[cfg.COL_QUARTER].astype(str)
    return df, path, "OK"


# =============================================================================
# RATIO COMPUTATION
# =============================================================================
def _c(df, col):
    if col and col in df.columns:
        return pd.to_numeric(df[col], errors="coerce")
    return pd.Series(np.nan, index=df.index)


def _div(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(b.abs() > 1e-9, a / b, np.nan)
    return pd.Series(r, index=a.index)


def compute_ratios(df):
    d = df.sort_values([cfg.COL_TICKER, cfg.COL_YEAR, cfg.COL_QUARTER]).copy()
    d = d.reset_index(drop=True)

    # YoY self-join: prior year = same quarter, year-1
    d['_ps']  = d[cfg.COL_YEAR].astype(int) * 10 + d[cfg.COL_QUARTER].astype(int)
    d['_pps'] = (d[cfg.COL_YEAR].astype(int) - 1) * 10 + d[cfg.COL_QUARTER].astype(int)
    _yoy_src = {cfg.COL_REVENUE: '_rev_py', cfg.COL_NET_PROFIT: '_np_py'}
    _yoy_src = {k: v for k, v in _yoy_src.items() if k and k in d.columns}
    if _yoy_src:
        _prior = d[[cfg.COL_TICKER, '_ps'] + list(_yoy_src.keys())].rename(
            columns={**{'_ps': '_pps'}, **_yoy_src}
        )
        d = d.merge(_prior, on=[cfg.COL_TICKER, '_pps'], how='left')

    rev   = _c(d, cfg.COL_REVENUE);    cogs  = _c(d, cfg.COL_COGS)
    gp    = _c(d, cfg.COL_GROSS).fillna(rev - cogs)
    ebit  = _c(d, cfg.COL_EBIT);       np_   = _c(d, cfg.COL_NET_PROFIT)
    ie    = _c(d, cfg.COL_INT_EXP).abs()
    da    = _c(d, cfg.COL_DA);         ebt   = _c(d, cfg.COL_EBT)
    tax   = _c(d, cfg.COL_TAX).abs()
    ta    = _c(d, cfg.COL_TOTAL_ASSETS); ca  = _c(d, cfg.COL_CUR_ASSETS)
    cash  = _c(d, cfg.COL_CASH);       rec   = _c(d, cfg.COL_RECEIVABLES)
    inv   = _c(d, cfg.COL_INVENTORY);  cl    = _c(d, cfg.COL_CUR_LIAB)
    std   = _c(d, cfg.COL_ST_DEBT);    ltd   = _c(d, cfg.COL_LT_DEBT)
    eq    = _c(d, cfg.COL_EQUITY);     fa    = _c(d, cfg.COL_FIXED_ASSETS)
    cfo   = _c(d, cfg.COL_CFO);        cap   = _c(d, cfg.COL_CAPEX).abs()

    total_debt = std + ltd
    net_debt   = total_debt - cash
    ebitda     = ebit + da          # ≈ EBIT if D&A missing
    fcf        = cfo - cap

    tax_rate = _div(tax, ebt.abs()).clip(0, 0.45).fillna(0.20)
    nopat    = ebit * 4 * (1 - tax_rate)
    inv_cap  = (eq + total_debt).replace(0, np.nan)

    R, G, E, N = rev*4, gp*4, ebit*4, np_*4
    EB, CF, F  = ebitda*4, cfo*4, fcf*4

    # M1
    d["ROIC"]              = _div(nopat, inv_cap) * 100
    d["ROE"]               = _div(N,  eq)   * 100
    d["ROA"]               = _div(N,  ta)   * 100
    d["Gross_Margin"]      = _div(G,  R)    * 100
    d["EBIT_Margin"]       = _div(E,  R)    * 100
    d["Net_Margin"]        = _div(N,  R)    * 100
    d["EBITDA_Margin"]     = _div(EB, R)    * 100
    d["CCQ"]               = _div(CF, EB)
    d["Asset_Turnover"]    = _div(R,  ta)
    d["Net_Debt_EBITDA"]   = _div(net_debt, EB)
    # FIX #5: Fixed Cost Coverage = EBITDA / Interest (pure, no CAPEX)
    d["Fixed_Cost_Cover"]  = _div(EB, ie * 4)
    d["Reinvestment_Rate"] = _div((cap - da) * 4, nopat.abs()) * 100
    d["EBITDA_abs"]        = ebitda
    d["Net_Debt_abs"]      = net_debt

    # YoY — will be NaN when prior year data not in dataset
    rev_py = _c(d, '_rev_py') if '_rev_py' in d.columns else pd.Series(np.nan, index=d.index)
    np_py  = _c(d, '_np_py')  if '_np_py'  in d.columns else pd.Series(np.nan, index=d.index)
    d["Rev_Growth_YoY"]    = _div(rev - rev_py, rev_py.abs()) * 100
    d["NP_Growth_YoY"]     = _div(np_ - np_py,  np_py.abs())  * 100

    # M2
    d["DSCR"]              = _div(EB, ie * 4)
    d["Current_Ratio"]     = _div(ca,  cl)
    d["Quick_Ratio"]       = _div(ca - inv, cl)
    d["D_E"]               = _div(total_debt, eq)
    d["Collateral_Cover"]  = _div(fa + cash, total_debt)

    # M3
    d["FCF_Margin"]        = _div(F,  R)  * 100
    d["CFO_Margin"]        = _div(CF, R)  * 100
    d["CFO_abs"]           = cfo
    d["CAPEX_abs"]         = cap
    d["FCF_abs"]           = fcf

    # M4
    d["DSO"]               = _div(rec, rev)  * 90
    d["DIO"]               = _div(inv, cogs) * 90
    d["DPO"]               = _div(cl - std, cogs) * 90
    d["CCC"]               = d["DSO"] + d["DIO"] - d["DPO"]
    d["Inv_Turnover"]      = _div(cogs * 4, inv)

    d.drop(columns=[c for c in ['_ps', '_pps', '_rev_py', '_np_py'] if c in d.columns],
           inplace=True)
    return d


# =============================================================================
# BENCHMARK ENGINE
# =============================================================================
# FIX #3: td_peer defined outside loop with explicit sty parameter
def td_peer(v, ticker, sty):
    t = (f'<span class="sub">{ticker}</span>'
         if ticker not in ("--", "-") else "")
    return f"<td>{fmt(v, sty)}{t}</td>"


def benchmarks_for(df, industry, period, co_ticker=None):
    mask  = (df[cfg.COL_INDUSTRY] == industry) & (df["period"] == period)
    peers = df[mask]
    out   = {}
    for rk, (_, style, higher, _grp) in RATIOS.items():
        if rk not in peers.columns:
            continue
        s = peers[[cfg.COL_TICKER, rk]].copy()
        s[rk] = pd.to_numeric(s[rk], errors="coerce")
        s = s.dropna(subset=[rk])
        s = s[np.isfinite(s[rk])]
        if s.empty:
            out[rk] = dict(avg=np.nan, vals=[np.nan]*3, tickers=["--"]*3,
                           avg_top3=np.nan, pct=np.nan)
            continue
        ranked = s.sort_values(rk, ascending=not higher).head(3)
        vals   = ranked[rk].tolist()
        ticks  = ranked[cfg.COL_TICKER].tolist()
        while len(vals) < 3:
            vals.append(np.nan); ticks.append("--")

        # Percentile rank for co_ticker
        pct = np.nan
        if co_ticker:
            co_s = peers[peers[cfg.COL_TICKER] == co_ticker]
            if not co_s.empty and rk in co_s.columns:
                try:
                    co_val = float(co_s[rk].values[0])
                    pct = compute_percentile(co_val, s[rk], higher)
                except Exception:
                    pass

        out[rk] = dict(avg=s[rk].mean(), vals=vals, tickers=ticks,
                       avg_top3=np.nanmean(vals), pct=pct)
    # FIX #2: use nunique() for accurate company count
    return out, peers[cfg.COL_TICKER].nunique()


# =============================================================================
# PAGE CONFIG & GLOBAL CSS — v3.1 Cyber / Deep Navy (dark-only)
# =============================================================================
st.set_page_config(
    page_title="Hayes Le — Financial Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset ───────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, sans-serif;
    background: {C["bg"]} !important;
    color: {C["text"]};
    -webkit-font-smoothing: antialiased;
}}
.stApp {{ background: {C["bg"]} !important; }}
.block-container {{ padding-top: 2rem !important; padding-bottom: 3rem !important; }}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: {C["surface"]} !important;
    border-right: 1px solid {C["border"]};
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0 !important; }}

.sb-header {{
    background: linear-gradient(135deg, {C["surface2"]} 0%, {C["bg"]} 100%);
    border-bottom: 1px solid {C["border"]};
    padding: 24px 20px 20px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}}
.sb-header::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, {C["accent"]}, {C["accent2"]}, {C["accent3"]});
}}
.sb-brand {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: {C["accent"]};
    margin-bottom: 6px;
}}
.sb-title {{
    font-size: 17px;
    font-weight: 700;
    color: {C["text"]};
    line-height: 1.25;
    letter-spacing: -0.01em;
}}
.sb-subtitle {{
    font-size: 10px;
    color: {C["muted"]};
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
}}

[data-testid="stSidebar"] .stRadio label {{
    color: {C["muted"]} !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 6px 0 !important;
    transition: color 0.15s;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    color: {C["text"]} !important;
}}

/* ── Section labels & page header ────────────────────────────────────────── */
.hl-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: {C["accent"]};
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.hl-label::before {{
    content: '';
    display: inline-block;
    width: 16px; height: 1px;
    background: {C["accent"]};
    opacity: 0.6;
}}
.hl-title {{
    font-size: 28px;
    font-weight: 700;
    color: {C["text"]};
    letter-spacing: -0.02em;
    margin: 0 0 4px;
    line-height: 1.15;
}}
.hl-sub {{
    font-size: 13px;
    color: {C["muted"]};
    font-weight: 400;
}}
.hl-divider {{
    height: 1px;
    background: linear-gradient(90deg, {C["accent"]}55, transparent);
    border: none;
    margin: 16px 0 28px;
}}

/* ── KPI metric cards ─────────────────────────────────────────────────────── */
div[data-testid="metric-container"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-top: 2px solid {C["accent"]} !important;
    border-radius: 4px !important;
    padding: 18px 20px 16px !important;
}}
div[data-testid="metric-container"] > label,
div[data-testid="metric-container"] > div:first-child {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 8.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0.20em !important;
    text-transform: uppercase !important;
    color: {C["muted"]} !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 26px !important;
    font-weight: 600 !important;
    color: {C["accent"]} !important;
    letter-spacing: -0.02em !important;
}}
/* FIX #8: delta color preserved — no SVG hide, Streamlit handles green/red */
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    font-size: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

/* ── Dividers ─────────────────────────────────────────────────────────────── */
hr {{
    border: none;
    border-top: 1px solid {C["border"]};
    margin: 24px 0;
}}

/* ── Alert / info / warning boxes ────────────────────────────────────────── */
.stAlert, div[data-testid="stInfo"], div.stWarning, div.stError,
[data-testid="stNotification"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-left: 3px solid {C["accent"]} !important;
    border-radius: 3px !important;
    color: {C["text"]} !important;
}}

/* ── Setup card ───────────────────────────────────────────────────────────── */
.setup-card {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-left: 3px solid {C["accent"]};
    border-radius: 4px;
    padding: 28px 32px;
    margin: 24px 0;
}}
.setup-card h3 {{
    color: {C["text"]};
    margin-top: 0;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.01em;
}}
.setup-card pre {{
    background: {C["bg"]};
    border: 1px solid {C["border"]};
    padding: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    border-radius: 3px;
    color: {C["accent3"]};
}}

/* ── Benchmark table (btable) ─────────────────────────────────────────────── */
.btable {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
}}
.btable thead tr {{ background: {C["surface2"]}; }}
.btable th {{
    background: {C["surface2"]};
    color: {C["muted"]};
    padding: 10px 14px;
    text-align: right;
    font-size: 8.5px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    white-space: nowrap;
    border-bottom: 1px solid {C["border"]};
}}
.btable th:first-child {{
    text-align: left;
    min-width: 190px;
    border-right: 1px solid {C["border"]};
    color: {C["text"]};
}}
.btable td {{
    padding: 8px 14px;
    border-bottom: 1px solid {C["border"]}55;
    text-align: right;
    color: {C["muted"]};
    white-space: nowrap;
    font-size: 12px;
}}
.btable td:first-child {{
    text-align: left;
    font-weight: 500;
    color: {C["text"]};
    border-right: 1px solid {C["border"]}55;
    font-size: 11.5px;
}}
.btable tbody tr:nth-child(even) td {{ background: {C["surface"]}88; }}
.btable tbody tr:hover td {{ background: {C["border"]}55; }}
.btable tr.grp td {{
    background: {C["surface2"]};
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: {C["accent"]};
    padding: 7px 14px;
    border-top: 1px solid {C["accent"]}33;
    border-bottom: 1px solid {C["border"]};
    text-align: left !important;
}}
.v-co {{ color: {C["accent"]}; font-weight: 600; }}
.v-hi {{ color: {C["positive"]}; font-weight: 600; }}
.v-lo {{ color: {C["negative"]}; font-weight: 600; }}
.sub  {{
    font-size: 8.5px;
    color: {C["dim"]};
    display: block;
    margin-top: 2px;
    font-weight: 400;
    font-family: 'Inter', sans-serif;
}}
.btable-legend {{
    display: flex;
    gap: 20px;
    align-items: center;
    margin-top: 12px;
    font-size: 10.5px;
    color: {C["muted"]};
    font-family: 'JetBrains Mono', monospace;
}}
.btable-legend .dot {{
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
}}

/* ── Column Check badges ──────────────────────────────────────────────────── */
.col-check-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
    border-bottom: 1px solid {C["border"]}44;
    font-size: 11px;
}}
.col-check-row:last-child {{ border-bottom: none; }}
.badge-ok   {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {C["positive"]}; flex-shrink: 0;
    box-shadow: 0 0 6px {C["positive"]}66;
}}
.badge-miss {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {C["negative"]}; flex-shrink: 0;
    box-shadow: 0 0 6px {C["negative"]}66;
}}
.col-check-label {{ color: {C["text"]}; font-weight: 500; flex: 1; }}
.col-check-code  {{
    color: {C["muted"]}; font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
}}

/* ── Screener table (View C) ──────────────────────────────────────────────── */
.sc-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
}}
.sc-table thead tr {{ background: {C["surface2"]}; }}
.sc-table th {{
    background: {C["surface2"]};
    color: {C["muted"]};
    padding: 10px 14px;
    text-align: right;
    font-size: 8.5px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    white-space: nowrap;
    border-bottom: 1px solid {C["border"]};
}}
.sc-table th:first-child, .sc-table th:nth-child(2) {{ text-align: left; }}
.sc-table th:first-child {{ color: {C["accent"]}; }}
.sc-table td {{
    padding: 7px 14px;
    border-bottom: 1px solid {C["border"]}44;
    text-align: right;
    color: {C["muted"]};
    white-space: nowrap;
}}
.sc-table td:first-child {{
    text-align: left;
    font-weight: 600;
    color: {C["accent"]};
}}
.sc-table td:nth-child(2) {{
    text-align: left;
    color: {C["dim"]};
    font-size: 10px;
}}
.sc-table tbody tr:nth-child(even) td {{ background: {C["surface"]}66; }}
.sc-table tbody tr:hover td {{ background: {C["border"]}55; }}

/* ── YoY placeholder ──────────────────────────────────────────────────────── */
.yoy-placeholder {{
    background: {C["surface"]};
    border: 1px dashed {C["border"]};
    border-radius: 4px;
    padding: 20px;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: {C["dim"]};
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}}

/* ── Caption ──────────────────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {C["muted"]} !important;
    font-size: 10.5px !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

/* ── Expander ─────────────────────────────────────────────────────────────── */
details[data-testid="stExpander"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-radius: 4px !important;
}}
details[data-testid="stExpander"] summary {{
    font-size: 11.5px;
    font-weight: 600;
    color: {C["muted"]};
    letter-spacing: 0.04em;
    padding: 10px 14px;
}}

/* ── Selectbox / slider / checkbox ───────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] label,
.stSlider label, .stCheckbox label {{
    color: {C["text"]} !important;
    font-size: 12px !important;
}}

/* ── Footer ───────────────────────────────────────────────────────────────── */
.hl-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 52px;
    padding-top: 14px;
    border-top: 1px solid {C["border"]};
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {C["dim"]};
}}
.hl-footer .hl-footer-brand {{
    color: {C["accent"]};
    font-weight: 600;
}}

/* ── Spacers ──────────────────────────────────────────────────────────────── */
.sp-sm {{ margin-top: 12px; }}
.sp-md {{ margin-top: 24px; }}
.sp-lg {{ margin-top: 40px; }}

/* ── Health Score card ────────────────────────────────────────────────────── */
.health-card {{
    display: flex;
    gap: 28px;
    align-items: center;
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 20px;
}}
.health-main {{
    flex-shrink: 0;
    text-align: center;
    min-width: 100px;
}}
.hs-score-val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 56px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.03em;
}}
.hs-score-lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    font-weight: 600;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: {C["muted"]};
    margin-top: 4px;
}}
.hs-score-sub {{
    font-size: 10px;
    color: {C["dim"]};
    margin-top: 3px;
    font-family: 'JetBrains Mono', monospace;
}}
.health-groups {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.hs-group-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 11px;
}}
.hs-glabel {{
    width: 150px;
    flex-shrink: 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5px;
    color: {C["muted"]};
    letter-spacing: 0.05em;
}}
.hs-bar-track {{
    flex: 1;
    height: 5px;
    background: {C["border"]};
    border-radius: 3px;
    overflow: hidden;
}}
.hs-bar-fill {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
}}
.hs-gscore {{
    width: 32px;
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 600;
}}
.health-na {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: {C["dim"]};
    padding: 12px 16px;
    background: {C["surface"]};
    border: 1px dashed {C["border"]};
    border-radius: 4px;
    margin-bottom: 16px;
}}
/* Compact health for View B */
.health-compact {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 4px;
    padding: 6px 14px;
    margin-bottom: 14px;
}}
.hc-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {C["muted"]};
}}
.hc-score {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.02em;
}}
.hc-sub {{
    font-size: 10px;
    color: {C["dim"]};
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Flags ────────────────────────────────────────────────────────────────── */
.flags-container {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 20px;
}}
.flag-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-left: 3px solid;
    border-radius: 3px;
    padding: 8px 14px;
    font-size: 11.5px;
}}
.flag-icon {{ font-size: 13px; flex-shrink: 0; }}
.flag-lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    flex-shrink: 0;
    width: 42px;
}}
.flag-metric {{
    font-weight: 600;
    color: {C["text"]};
    flex-shrink: 0;
    min-width: 120px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}}
.flag-msg {{
    color: {C["muted"]};
    font-size: 11px;
}}
.flags-clean {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: {C["dim"]};
    padding: 10px 0;
    margin-bottom: 12px;
}}

/* ── Percentile cell (btable) ─────────────────────────────────────────────── */
.pct-cell {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    text-align: right;
}}
.pct-na {{ color: {C["dim"]}; text-align: right; }}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# LOAD DATA
# =============================================================================
df_raw, raw_path, load_status = load_raw_data()


def show_setup_screen(status, path):
    st.markdown('<span class="hl-label">Hayes Le — Financial Screener</span>', unsafe_allow_html=True)
    st.markdown('<div class="hl-title">First-Time Setup</div>', unsafe_allow_html=True)
    st.markdown('<hr class="hl-divider">', unsafe_allow_html=True)

    if status == "NOT_FOUND":
        st.error(f"Could not find `ALL_BCTC_*.xlsx` in:\n\n`{cfg.RAW_EXCEL_DIR}`")
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"""
            <div class="setup-card">
            <h3>Two steps to get started</h3>
            <p><b>Step 1 —</b> Run the companion Jupyter notebook
            (<code>vnstock_pull_bctc.ipynb</code>) to generate the raw data file.
            It will export to the directory shown above.</p>
            <p><b>Step 2 —</b> If the directory path is wrong, open <code>config.py</code>
            and update this line, then restart the app:</p>
            <pre>RAW_EXCEL_DIR = r"C:\\path\\to\\your\\CTCK\\folder"</pre>
            <p style="margin-bottom:0">Restart: <code>py -m streamlit run streamlit_app.py</code></p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            # FIX #4: updated filename pattern from 8Q to 4Q
            st.info(
                "**Expected filename:**\n"
                "```\nALL_BCTC_KBS_quarter_4Q_\nYYYYMMDD_HHMM.xlsx\n```\n\n"
                "**Required sheet:** `TONG_HOP`\n\n"
                "**Note:** the `industry` column must be\n"
                "present — generated from SSI export\n"
                "via `vnstock_pull_bctc.ipynb`."
            )
    else:
        st.error(f"Error reading `{path}`:\n```\n{status}\n```")
        st.warning("Make sure the file is not open in Excel, then restart.")
    st.stop()


if load_status != "OK":
    show_setup_screen(load_status, raw_path)

with st.spinner("Computing financial ratios..."):
    df = compute_ratios(df_raw)

all_periods    = sorted(df["period"].dropna().unique())
all_tickers    = sorted(df[cfg.COL_TICKER].dropna().unique())
all_industries = sorted(df[cfg.COL_INDUSTRY].dropna().unique())


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown(
        '<div class="sb-header">'
        '<div class="sb-brand">Hayes Le</div>'
        '<div class="sb-title">Financial<br>Screener</div>'
        '<div class="sb-subtitle">v3.1 · Vietnam Equities</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    view = st.radio(
        "View",
        ["Company Dashboard", "Company vs Industry", "Industry Screener"],
        label_visibility="collapsed",
    )

    st.markdown(f'<hr style="border-color:{C["border"]};margin:12px 0">', unsafe_allow_html=True)

    with st.expander("Column Check", expanded=False):
        st.caption("Verify key columns exist in your Excel file.")
        checks = [
            ("Ticker",          cfg.COL_TICKER),
            ("Industry",        cfg.COL_INDUSTRY),
            ("Doanh thu thuần", cfg.COL_REVENUE),
            ("Giá vốn HB",      cfg.COL_COGS),
            ("EBIT proxy",      cfg.COL_EBIT),
            ("Chi phí lãi vay", cfg.COL_INT_EXP),
            ("LNST",            cfg.COL_NET_PROFIT),
            ("Thuế TNDN",       cfg.COL_TAX),
            ("Khấu hao",        cfg.COL_DA),
            ("Tổng TS",         cfg.COL_TOTAL_ASSETS),
            ("TSNH",            cfg.COL_CUR_ASSETS),
            ("Nợ NH",           cfg.COL_CUR_LIAB),
            ("VCSH",            cfg.COL_EQUITY),
            ("TSCĐ",            cfg.COL_FIXED_ASSETS),
            ("CFO",             cfg.COL_CFO),
            ("CAPEX",           cfg.COL_CAPEX),
        ]
        any_missing = False
        check_html  = ""
        for lbl, col in checks:
            ok = bool(col and col in df.columns)
            if not ok:
                any_missing = True
            badge = '<div class="badge-ok"></div>' if ok else '<div class="badge-miss"></div>'
            check_html += (
                f'<div class="col-check-row">'
                f'{badge}'
                f'<span class="col-check-label">{lbl}</span>'
                f'<span class="col-check-code">{col}</span>'
                f'</div>'
            )
        st.markdown(check_html, unsafe_allow_html=True)
        if any_missing:
            st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
            st.warning(
                "Some columns are missing. Ratios will show `—` for those metrics.\n\n"
                "```python\nimport pandas as pd, glob\n"
                "f = sorted(glob.glob('ALL_BCTC_*.xlsx'))[-1]\n"
                "print(pd.read_excel(f, sheet_name='TONG_HOP', nrows=0).columns.tolist())\n```"
            )

    st.markdown(f'<hr style="border-color:{C["border"]};margin:12px 0">', unsafe_allow_html=True)

    fname = os.path.basename(raw_path) if raw_path else "—"
    st.markdown(
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:9.5px;'
        f'color:{C["dim"]};line-height:2;padding:0 2px">'
        f'<span style="color:{C["muted"]}">FILE</span> {fname}<br>'
        f'<span style="color:{C["muted"]}">TICK</span> {len(all_tickers):,} &nbsp; '
        f'<span style="color:{C["muted"]}">QTRS</span> {len(all_periods)} &nbsp; '
        f'<span style="color:{C["muted"]}">SECT</span> {len(all_industries)}'
        f'</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# VIEW A — COMPANY DASHBOARD
# =============================================================================
if view == "Company Dashboard":

    default_idx = all_tickers.index("CLX") if "CLX" in all_tickers else 0
    sel      = st.sidebar.selectbox("Ticker", all_tickers, index=default_idx)
    df_co    = df[df[cfg.COL_TICKER] == sel].sort_values("period")
    ind      = df_co[cfg.COL_INDUSTRY].dropna().mode()
    ind      = ind.iloc[0] if not ind.empty else "N/A"
    df_peers = (df[(df[cfg.COL_INDUSTRY] == ind) & (df[cfg.COL_TICKER] != sel)]
                if ind != "N/A" else pd.DataFrame())

    st.markdown(f'<span class="hl-label">Company Dashboard — {ind}</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="hl-title">{sel}</div>', unsafe_allow_html=True)
    # FIX #4: "8-quarter" → "4-quarter"
    st.markdown('<div class="hl-sub">4-quarter trend · industry benchmark overlay</div>', unsafe_allow_html=True)
    st.markdown('<hr class="hl-divider">', unsafe_allow_html=True)

    if not df_co.empty:
        latest   = df_co.iloc[-1]
        last_per = df_co["period"].max()
        peer_now = (df_peers[df_peers["period"] == last_per]
                    if not df_peers.empty else pd.DataFrame())

        kpis = ["ROIC", "ROE", "Net_Margin", "DSCR", "Current_Ratio", "FCF_Margin"]
        cols = st.columns(len(kpis))
        for i, rk in enumerate(kpis):
            lbl, sty, higher, _ = RATIOS[rk]
            val = float(latest.get(rk, np.nan))
            avg = (float(peer_now[rk].mean())
                   if not peer_now.empty and rk in peer_now.columns else np.nan)
            delta       = None
            delta_color = "normal"
            if np.isfinite(val) and np.isfinite(avg):
                diff  = val - avg
                delta = f"{'▲' if diff > 0 else '▼'} {abs(diff):.1f} vs avg"
                # FIX #8: invert delta color for "lower is better" metrics
                delta_color = "normal" if higher else "inverse"
            cols[i].metric(lbl,
                           fmt(val, sty) if np.isfinite(val) else "—",
                           delta=delta,
                           delta_color=delta_color)

    st.markdown('<div class="sp-md"></div>', unsafe_allow_html=True)

    # ── Health Score + Flags ──────────────────────────────────────────────────
    hs_cols = st.columns([2, 3])
    with hs_cols[0]:
        st.markdown('<span class="hl-label">Health Score</span>', unsafe_allow_html=True)
        if not df_peers.empty:
            peers_now = df_peers[df_peers["period"] == last_per] if not df_peers.empty else pd.DataFrame()
            if not peers_now.empty:
                hs = compute_health_score(latest, peers_now)
                st.markdown(render_health_card(hs), unsafe_allow_html=True)
            else:
                st.markdown('<div class="health-na">No peer data for this period</div>',
                            unsafe_allow_html=True)
        else:
            st.markdown('<div class="health-na">No industry peers found</div>',
                        unsafe_allow_html=True)
    with hs_cols[1]:
        st.markdown('<span class="hl-label">Alerts & Anomalies</span>', unsafe_allow_html=True)
        flags = compute_flags(df_co)
        st.markdown(render_flags(flags), unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Solid = selected company   ·   Dashed = industry average")

    chart_groups = [
        ["ROIC", "ROE", "ROA"],
        ["Gross_Margin", "EBIT_Margin", "Net_Margin", "EBITDA_Margin"],
        # FIX #1 & #6: YoY group kept but placeholder shown if all NaN
        ["Rev_Growth_YoY", "NP_Growth_YoY"],
        ["CCQ", "Fixed_Cost_Cover", "Reinvestment_Rate"],
        ["D_E", "DSCR", "Current_Ratio", "Quick_Ratio"],
        ["FCF_Margin", "CFO_Margin", "Net_Debt_EBITDA"],
        ["DSO", "DIO", "DPO", "CCC"],
    ]

    for grp_orig in chart_groups:
        # Check if this is a YoY group before filtering
        is_yoy_group = any(r in _YOY_KEYS for r in grp_orig)

        grp = [r for r in grp_orig if r in df_co.columns and df_co[r].notna().any()]

        if not grp:
            if is_yoy_group:
                st.markdown(
                    '<div class="yoy-placeholder">'
                    '📊 &nbsp; YOY GROWTH — Prior year data unavailable'
                    ' (requires &gt;4 quarters of history)'
                    '</div>',
                    unsafe_allow_html=True,
                )
            continue

        cols_row = st.columns(len(grp))
        for ci, rk in enumerate(grp):
            lbl, sty, _, _ = RATIOS[rk]
            ts  = df_co.sort_values("period")
            fig = go.Figure()
            fig.add_scatter(
                x=ts["period"], y=ts[rk],
                mode="lines+markers", name=sel,
                line=dict(color=C["accent"], width=2),
                marker=dict(size=5, color=C["accent"],
                            line=dict(width=1.5, color=C["bg"])),
            )
            if not df_peers.empty and rk in df_peers.columns:
                avg_ts = (df_peers.groupby("period")[rk].mean()
                          .reset_index().sort_values("period"))
                fig.add_scatter(
                    x=avg_ts["period"], y=avg_ts[rk], mode="lines",
                    name="Avg",
                    line=dict(color=C["accent2"], width=1.2, dash="dot"),
                )
            fig.update_layout(**PLOTLY_BASE, title_text=lbl, height=230, xaxis_tickangle=-40)
            fig.update_layout(legend=dict(orientation="h", y=1.22, font=dict(size=9)))
            cols_row[ci].plotly_chart(fig, use_container_width=True,
                                       config={"displayModeBar": False})

    st.markdown('<div class="sp-md"></div>', unsafe_allow_html=True)
    with st.expander("Raw ratio table — all quarters"):
        show_cols = ["period"] + [r for r in RATIOS if r in df_co.columns]
        tbl       = df_co[show_cols].set_index("period").T.copy()
        tbl.index = [RATIOS[r][0] if r in RATIOS else r for r in tbl.index]
        st.dataframe(tbl, use_container_width=True)


# =============================================================================
# VIEW B — COMPANY vs INDUSTRY
# =============================================================================
elif view == "Company vs Industry":

    default_idx = all_tickers.index("CLX") if "CLX" in all_tickers else 0
    sel   = st.sidebar.selectbox("Ticker", all_tickers, index=default_idx, key="b_t")
    df_co = df[df[cfg.COL_TICKER] == sel]
    ind   = df_co[cfg.COL_INDUSTRY].dropna().mode()
    ind   = ind.iloc[0] if not ind.empty else None
    avail = sorted(df_co["period"].dropna().unique(), reverse=True)
    per   = st.sidebar.selectbox("Period", avail, key="b_p")

    st.markdown(f'<span class="hl-label">Peer Benchmarking — {ind or "N/A"}</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="hl-title">{sel}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hl-sub">{per}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="hl-divider">', unsafe_allow_html=True)

    if ind is None:
        st.warning("Industry not found for this ticker.")
        st.stop()

    bench, n_peers = benchmarks_for(df, ind, per, co_ticker=sel)
    co_row = df[(df[cfg.COL_TICKER] == sel) & (df["period"] == per)]

    st.caption(f"Industry: {ind}   ·   {n_peers} companies in period")
    st.markdown('<div class="sp-sm"></div>', unsafe_allow_html=True)

    # ── Compact Health Score ──────────────────────────────────────────────────
    peers_per = df[(df[cfg.COL_INDUSTRY] == ind) & (df["period"] == per) &
                   (df[cfg.COL_TICKER] != sel)]
    if not peers_per.empty and not co_row.empty:
        hs_b = compute_health_score(co_row.iloc[0], peers_per)
        st.markdown(render_health_card(hs_b, compact=True), unsafe_allow_html=True)

    st.markdown('<div class="sp-sm"></div>', unsafe_allow_html=True)

    rows    = ""
    cur_grp = None
    for rk, (lbl, sty, higher, grp) in RATIOS.items():
        if grp != cur_grp:
            cur_grp = grp
            rows += f'<tr class="grp"><td colspan="7">{grp}</td></tr>'
        if rk not in bench:
            continue
        b   = bench[rk]
        raw = np.nan
        if not co_row.empty and rk in co_row.columns:
            try:
                raw = float(co_row[rk].values[0])
            except Exception:
                pass

        # FIX #1: YoY metrics — show placeholder row if no prior year data
        if rk in _YOY_KEYS and np.isnan(raw) and np.isnan(b["avg"]):
            rows += (
                f"<tr>"
                f"<td>{lbl}</td>"
                f'<td colspan="7" style="text-align:center;color:{C["dim"]};'
                f'font-size:10px;font-style:italic">Prior year data unavailable</td>'
                f"</tr>"
            )
            continue

        cls = "v-co"
        if np.isfinite(raw) and np.isfinite(b["avg"]):
            cls = "v-hi" if (raw > b["avg"]) == higher else "v-lo"

        rows += (
            f"<tr>"
            f"<td>{lbl}</td>"
            f'<td class="{cls}">{fmt(raw, sty)}</td>'
            f"{pct_cell(b.get('pct', np.nan))}"
            f"<td>{fmt(b['avg'], sty)}</td>"
            # FIX #3: td_peer called with explicit sty
            f"{td_peer(b['vals'][0], b['tickers'][0], sty)}"
            f"{td_peer(b['vals'][1], b['tickers'][1], sty)}"
            f"{td_peer(b['vals'][2], b['tickers'][2], sty)}"
            f"<td>{fmt(b['avg_top3'], sty)}</td>"
            f"</tr>"
        )

    st.markdown(
        f'<div style="overflow-x:auto">'
        f'<table class="btable">'
        f'<thead><tr>'
        f'<th style="text-align:left">Metric</th>'
        f'<th>{sel}</th>'
        f'<th>P-Rank</th>'
        f'<th>Avg Industry</th>'
        f'<th>Top 1</th><th>Top 2</th><th>Top 3</th>'
        f'<th>Avg Top 3</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="btable-legend">'
        f'<span><span class="dot" style="background:{C["accent"]}"></span>Company value</span>'
        f'<span><span class="dot" style="background:{C["positive"]}"></span>Better than avg</span>'
        f'<span><span class="dot" style="background:{C["negative"]}"></span>Worse than avg</span>'
        f'<span style="margin-left:12px;color:{C["dim"]}">P-Rank: '
        f'<span style="color:{C["accent"]}">P75+</span> · '
        f'<span style="color:{C["muted"]}">P50</span> · '
        f'<span style="color:{C["gold"]}">P25</span> · '
        f'<span style="color:{C["negative"]}">P0</span>'
        f' (direction-adjusted)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sp-lg"></div>', unsafe_allow_html=True)

    bar_keys = [k for k in ["ROIC", "ROE", "Net_Margin", "EBITDA_Margin",
                             "Current_Ratio", "FCF_Margin"]
                if k in bench and not co_row.empty and k in co_row.columns]
    if bar_keys:
        def safe_f(v):
            try:
                f = float(v); return f if np.isfinite(f) else 0
            except Exception:
                return 0
        labels    = [RATIOS[k][0] for k in bar_keys]
        co_vals   = [safe_f(co_row[k].values[0]) for k in bar_keys]
        avg_vals  = [safe_f(bench[k]["avg"]) for k in bar_keys]
        top3_vals = [safe_f(bench[k]["avg_top3"]) for k in bar_keys]

        fig = go.Figure()
        fig.add_bar(name=sel,          x=labels, y=co_vals,
                    marker_color=C["accent"],
                    marker_line_color="rgba(0,0,0,0)")
        fig.add_bar(name="Avg Ind.",   x=labels, y=avg_vals,
                    marker_color=C["surface2"],
                    marker_line_color=C["border"], marker_line_width=1)
        fig.add_bar(name="Avg Top 3",  x=labels, y=top3_vals,
                    marker_color=C["accent2"])
        fig.update_layout(
            **PLOTLY_BASE, barmode="group",
            title_text=f"Key Metrics — {sel} vs Industry ({per})",
            height=340,
        )
        fig.update_layout(legend=dict(orientation="h", y=1.12, font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# =============================================================================
# VIEW C — INDUSTRY SCREENER
# =============================================================================
elif view == "Industry Screener":

    sel_ind  = st.sidebar.selectbox("Industry", all_industries)
    sel_per  = st.sidebar.selectbox("Period", sorted(all_periods, reverse=True), key="c_p")
    sort_k   = st.sidebar.selectbox("Sort by", list(RATIOS.keys()),
                                    format_func=lambda k: RATIOS[k][0])
    sort_asc = st.sidebar.checkbox("Ascending", value=False)

    st.markdown('<span class="hl-label">Industry Screener</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="hl-title">{sel_ind}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hl-sub">{sel_per} · All companies</div>', unsafe_allow_html=True)
    st.markdown('<hr class="hl-divider">', unsafe_allow_html=True)

    mask   = (df[cfg.COL_INDUSTRY] == sel_ind) & (df["period"] == sel_per)
    df_sec = df[mask].copy()

    if df_sec.empty:
        st.warning("No data for this industry / period.")
        st.stop()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Companies", str(df_sec[cfg.COL_TICKER].nunique()))
    for col, rk in zip([c2, c3, c4, c5], ["ROIC", "Net_Margin", "DSCR", "Current_Ratio"]):
        lbl, sty, _, _ = RATIOS[rk]
        avg = df_sec[rk].mean() if rk in df_sec.columns else np.nan
        col.metric(f"Avg {lbl}", fmt(avg, sty) if np.isfinite(avg) else "—")

    st.markdown("---")

    ratio_cols = [r for r in RATIOS if r in df_sec.columns]
    if sort_k in df_sec.columns:
        df_sec = df_sec.sort_values(sort_k, ascending=sort_asc)

    th_ticker   = '<th style="text-align:left">Ticker</th>'
    th_exchange = '<th style="text-align:left">Exchange</th>'
    th_ratios   = "".join(f'<th>{RATIOS[rk][0]}</th>' for rk in ratio_cols)
    sc_head     = f"<thead><tr>{th_ticker}{th_exchange}{th_ratios}</tr></thead>"

    sc_rows = ""
    for _, row in df_sec.iterrows():
        ticker_val   = row.get(cfg.COL_TICKER, "—")
        exchange_val = (row.get(cfg.COL_EXCHANGE, "—")
                        if cfg.COL_EXCHANGE in df_sec.columns else "—")
        tds = f'<td>{ticker_val}</td><td>{exchange_val}</td>'
        for rk in ratio_cols:
            _, sty, _, _ = RATIOS[rk]
            tds += f'<td>{fmt(row.get(rk, np.nan), sty)}</td>'
        sc_rows += f"<tr>{tds}</tr>"

    st.markdown(
        f'<div style="overflow-x:auto;max-height:380px;overflow-y:auto">'
        f'<table class="sc-table">'
        f'{sc_head}<tbody>{sc_rows}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    chart_r = st.selectbox("Bar chart metric", ratio_cols,
                            format_func=lambda k: RATIOS[k][0])
    _, chart_sty, _, _ = RATIOS[chart_r]
    df_bar = df_sec[[cfg.COL_TICKER, chart_r]].dropna().sort_values(chart_r, ascending=False)
    if not df_bar.empty:
        avg_v  = float(df_bar[chart_r].mean())
        colors = [C["gold"] if i < 3 else C["accent"] for i in range(len(df_bar))]
        fig    = go.Figure(go.Bar(
            x=df_bar[cfg.COL_TICKER], y=df_bar[chart_r],
            marker_color=colors,
            marker_line_color="rgba(0,0,0,0)",
            text=df_bar[chart_r].apply(lambda v: fmt(v, chart_sty)),
            textposition="outside",
            textfont=dict(size=9, family="JetBrains Mono", color=C["muted"]),
        ))
        fig.add_hline(
            y=avg_v, line_dash="dot", line_color=C["accent3"], line_width=1.5,
            annotation_text=f"avg {fmt(avg_v, chart_sty)}",
            annotation_font_color=C["accent3"],
            annotation_font_size=10,
            annotation_font_family="JetBrains Mono",
        )
        fig.update_layout(
            **PLOTLY_BASE,
            title_text=f"{RATIOS[chart_r][0]} — {sel_ind} ({sel_per})",
            height=380, xaxis_tickangle=-45,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Gold = Top 3   ·   Cyan = rest   ·   Dashed = industry average")

    st.markdown("---")

    trend_r   = st.selectbox("Trend metric — all quarters", ratio_cols, key="c_trend",
                              format_func=lambda k: RATIOS[k][0])
    n_top     = st.slider("Number of companies", 3, 10, 5)
    top_ticks = (df_sec.sort_values(trend_r, ascending=False).head(n_top)[cfg.COL_TICKER].tolist()
                 if trend_r in df_sec.columns else df_sec.head(n_top)[cfg.COL_TICKER].tolist())

    df_trend = df[(df[cfg.COL_INDUSTRY] == sel_ind) & df[cfg.COL_TICKER].isin(top_ticks)]
    if not df_trend.empty and trend_r in df_trend.columns:
        palette = [C["accent"], C["accent2"], C["gold"], C["accent3"], "#A78BFA",
                   "#22d3ee", "#f59e0b", "#34d399", "#f87171", "#a3e635"]
        fig2    = go.Figure()
        for i, tk in enumerate(top_ticks):
            d_tk = df_trend[df_trend[cfg.COL_TICKER] == tk].sort_values("period")
            fig2.add_scatter(
                x=d_tk["period"], y=d_tk[trend_r],
                mode="lines+markers", name=tk,
                line=dict(color=palette[i % len(palette)], width=2),
                marker=dict(size=5),
            )
        avg_t = (df[df[cfg.COL_INDUSTRY] == sel_ind]
                 .groupby("period")[trend_r].mean().reset_index())
        fig2.add_scatter(
            x=avg_t["period"], y=avg_t[trend_r], mode="lines",
            name="Avg Industry",
            line=dict(color=C["dim"], width=1.2, dash="longdash"),
        )
        fig2.update_layout(
            **PLOTLY_BASE,
            title_text=f"{RATIOS[trend_r][0]} — Top {n_top} vs Avg Industry",
            height=320, xaxis_tickangle=-40,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# =============================================================================
# FOOTER
# =============================================================================
st.markdown(
    f'<div class="hl-footer">'
    f'<span class="hl-footer-brand">Hayes Le</span>'
    f'<span>Confidential — Internal Use Only</span>'
    f'<span>Financial Screener · v3.2</span>'
    f'</div>',
    unsafe_allow_html=True,
)