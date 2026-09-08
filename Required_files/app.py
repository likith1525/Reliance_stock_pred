"""
Reliance Industries — 30-Day Forecast Dashboard
Run with:  streamlit run app.py

Expects (optional — the app degrades gracefully if missing):
  - Company_stock_prices.xlsx        (sheet 'in')   -> historical prices
  - Reliance_30_Day_Forecast.csv                     -> forecast output (Step 20)
  - reliance_forecast_model.pkl                       -> the ONE deployed model (Step 21)
  - model_metadata.json                               -> which models were trained/compared,
                                                          which one won, which one is deployed
                                                          (Step 22 of the training script)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from pathlib import Path

# ----------------------------------------------------------------------------
# PAGE CONFIG — must be the first Streamlit call
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="RELIANCE · 30D Forecast",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# DESIGN TOKENS
# ----------------------------------------------------------------------------
INK       = "#0A0E1A"   # page background
SURFACE   = "#121826"   # card background
SURFACE_2 = "#1A2236"   # elevated card / hover
BORDER    = "#232B3D"   # hairline borders
TEXT      = "#E8ECF4"   # primary text
MUTED     = "#7C889E"   # secondary text
GAIN      = "#1FD9A8"   # teal — price up
LOSS      = "#FF6B6B"   # coral — price down
AMBER     = "#F2B84B"   # signature accent — forecast / highlight

# ----------------------------------------------------------------------------
# GLOBAL CSS
# ----------------------------------------------------------------------------
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
    html, body, [class*="css"]  {{
        font-family: 'Inter', sans-serif;
    }}
    #MainMenu, footer, header {{visibility: hidden;}}

    .stApp {{
        background: {INK};
        background-image:
            radial-gradient(circle at 15% 0%, rgba(31,217,168,0.06) 0%, transparent 35%),
            radial-gradient(circle at 85% 15%, rgba(242,184,75,0.05) 0%, transparent 40%);
        color: {TEXT};
    }}

    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }}

    /* ---------- Ticker tape (signature element) ---------- */
    .ticker-wrap {{
        width: 100%;
        overflow: hidden;
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px 0;
        margin-bottom: 28px;
    }}
    .ticker-move {{
        display: inline-block;
        white-space: nowrap;
        animation: scroll-left 32s linear infinite;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        letter-spacing: 0.02em;
    }}
    .ticker-wrap:hover .ticker-move {{ animation-play-state: paused; }}
    @keyframes scroll-left {{
        0%   {{ transform: translateX(0); }}
        100% {{ transform: translateX(-50%); }}
    }}
    .tick-up   {{ color: {GAIN}; margin: 0 22px; }}
    .tick-down {{ color: {LOSS}; margin: 0 22px; }}

    /* ---------- Header ---------- */
    .eyebrow {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        letter-spacing: 0.14em;
        color: {AMBER};
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .headline {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 40px;
        line-height: 1.1;
        color: {TEXT};
        margin: 0 0 6px 0;
    }}
    .subhead {{
        color: {MUTED};
        font-size: 15px;
        margin-bottom: 30px;
    }}

    /* ---------- Stat cards ---------- */
    .stat-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 18px 20px;
        height: 100%;
    }}
    .stat-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {MUTED};
        margin-bottom: 8px;
    }}
    .stat-value {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 28px;
        color: {TEXT};
    }}
    .stat-delta-up   {{ color: {GAIN}; font-family: 'IBM Plex Mono', monospace; font-size: 13px; margin-top: 6px; }}
    .stat-delta-down {{ color: {LOSS}; font-family: 'IBM Plex Mono', monospace; font-size: 13px; margin-top: 6px; }}

    /* ---------- Section labels ---------- */
    .section-label {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 18px;
        color: {TEXT};
        margin: 36px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .section-label::before {{
        content: "";
        width: 3px;
        height: 18px;
        background: {AMBER};
        border-radius: 2px;
        display: inline-block;
    }}

    /* ---------- Dataframe ---------- */
    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    /* ---------- Footer ---------- */
    .footer-box {{
        margin-top: 40px;
        padding: 16px 20px;
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        color: {MUTED};
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .footer-box span b {{ color: {TEXT}; }}

    .disclaimer {{
        color: {MUTED};
        font-size: 12px;
        margin-top: 10px;
        line-height: 1.5;
    }}

    /* ---------- Model badges ---------- */
    .model-pill {{
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        padding: 5px 12px;
        margin: 3px 4px 3px 0;
        border-radius: 999px;
        border: 1px solid {BORDER};
        background: {SURFACE};
        color: {MUTED};
    }}
    .model-pill-winner {{
        border-color: {GAIN};
        color: {GAIN};
        background: rgba(31,217,168,0.08);
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# DATA LOADING (graceful — app still renders with sample data if files absent)
# ----------------------------------------------------------------------------
def load_historical():
    path = Path("Company_stock_prices.xlsx")
    if path.exists():
        df = pd.read_excel(path, sheet_name="in")
        df = df.sort_values("Date").reset_index(drop=True)
        return df
    return None

def load_forecast():
    path = Path("Reliance_30_Day_Forecast.csv")
    if path.exists():
        fdf = pd.read_csv(path, parse_dates=["Date"])
        return fdf
    return None

def load_metadata():
    """Loads which models were trained/compared, which one won on RMSE,
    and which one was actually saved for deployment — written by the
    training script (Step 22) so the dashboard never has to guess this
    from the pickle's Python type."""
    path = Path("model_metadata.json")
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None

hist_df = load_historical()
fcst_df = load_forecast()
meta = load_metadata()

DEMO_MODE = hist_df is None or fcst_df is None

if DEMO_MODE:
    # Synthetic placeholder so the dashboard is still viewable before the pipeline has run
    rng = pd.date_range(end=pd.Timestamp.today(), periods=180, freq="B")
    price = 400 + np.cumsum(np.random.randn(180) * 3)
    hist_df = pd.DataFrame({"Date": rng, "Close": price})
    fdates = pd.date_range(start=rng[-1] + pd.Timedelta(days=1), periods=30, freq="B")
    fprice = price[-1] + np.cumsum(np.random.randn(30) * 3)
    fcst_df = pd.DataFrame({"Date": fdates, "Forecast_Close": fprice})
    if "Lower_Bound" not in fcst_df:
        fcst_df["Lower_Bound"] = fcst_df["Forecast_Close"] - 12
        fcst_df["Upper_Bound"] = fcst_df["Forecast_Close"] + 12

if "Lower_Bound" not in fcst_df.columns:
    spread = (hist_df["Close"].pct_change().std() or 0.01) * fcst_df["Forecast_Close"] * 1.96
    fcst_df["Lower_Bound"] = fcst_df["Forecast_Close"] - spread
    fcst_df["Upper_Bound"] = fcst_df["Forecast_Close"] + spread

# ----------------------------------------------------------------------------
# TICKER TAPE — last ~25 trading days, % change, colored
# ----------------------------------------------------------------------------
tape = hist_df.tail(26).copy()
tape["pct"] = tape["Close"].pct_change() * 100
tape = tape.dropna()

tick_items = ""
for _, row in tape.iterrows():
    cls = "tick-up" if row["pct"] >= 0 else "tick-down"
    arrow = "▲" if row["pct"] >= 0 else "▼"
    tick_items += f'<span class="{cls}">{row["Date"].strftime("%d %b")}&nbsp; {arrow} {row["pct"]:+.2f}%</span>'

st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker-move">{tick_items}{tick_items}</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown('<div class="eyebrow">RIL · NSE · Forecast Terminal</div>', unsafe_allow_html=True)
st.markdown('<div class="headline">Reliance Industries — 30 Day Outlook</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subhead">Model-generated price projection with a 95% confidence band, '
    'built on historical OHLCV data.</div>',
    unsafe_allow_html=True,
)

if DEMO_MODE:
    cwd = Path.cwd()
    files_here = [f.name for f in cwd.iterdir() if f.is_file()]
    st.info(
        "Running in **demo mode** with synthetic data — place `Company_stock_prices.xlsx` "
        "and `Reliance_30_Day_Forecast.csv` in this folder to show your real pipeline output.",
        icon="ℹ️",
    )
    with st.expander("🔍 Debug: why demo mode is on (click to see what the app can actually find)"):
        st.write("**App is looking in this folder:**")
        st.code(str(cwd))
        st.write("**Files it can see in that folder:**")
        st.code("\n".join(files_here) if files_here else "(none found)")
        st.write("**Specific checks:**")
        st.write(f"- `Company_stock_prices.xlsx` found: `{(cwd / 'Company_stock_prices.xlsx').exists()}`")
        st.write(f"- `Reliance_30_Day_Forecast.csv` found: `{(cwd / 'Reliance_30_Day_Forecast.csv').exists()}`")
        st.write(f"- `model_metadata.json` found: `{(cwd / 'model_metadata.json').exists()}`")

# ----------------------------------------------------------------------------
# HERO STAT CARDS
# ----------------------------------------------------------------------------
last_price = hist_df["Close"].iloc[-1]
last_date = hist_df["Date"].iloc[-1]
day30_price = fcst_df["Forecast_Close"].iloc[-1]
day1_price = fcst_df["Forecast_Close"].iloc[0]
total_change = day30_price - last_price
total_change_pct = (total_change / last_price) * 100
day1_change_pct = (day1_price - last_price) / last_price * 100

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Last Close ({last_date.strftime('%d %b %Y')})</div>
        <div class="stat-value">₹{last_price:,.2f}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    cls = "stat-delta-up" if day1_change_pct >= 0 else "stat-delta-down"
    arrow = "▲" if day1_change_pct >= 0 else "▼"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Next Trading Day</div>
        <div class="stat-value">₹{day1_price:,.2f}</div>
        <div class="{cls}">{arrow} {day1_change_pct:+.2f}%</div>
    </div>""", unsafe_allow_html=True)
with c3:
    cls = "stat-delta-up" if total_change_pct >= 0 else "stat-delta-down"
    arrow = "▲" if total_change_pct >= 0 else "▼"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Day 30 Forecast</div>
        <div class="stat-value">₹{day30_price:,.2f}</div>
        <div class="{cls}">{arrow} {total_change_pct:+.2f}% over 30d</div>
    </div>""", unsafe_allow_html=True)
with c4:
    band_width = fcst_df["Upper_Bound"].iloc[-1] - fcst_df["Lower_Bound"].iloc[-1]
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">95% Band Width (Day 30)</div>
        <div class="stat-value">±₹{band_width/2:,.2f}</div>
    </div>""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# MAIN CHART — historical + forecast + confidence band, dark themed
# ----------------------------------------------------------------------------
st.markdown('<div class="section-label">Price History &amp; Forecast</div>', unsafe_allow_html=True)

recent_hist = hist_df.tail(90)

fig = go.Figure()

# Confidence band
fig.add_trace(go.Scatter(
    x=pd.concat([fcst_df["Date"], fcst_df["Date"][::-1]]),
    y=pd.concat([fcst_df["Upper_Bound"], fcst_df["Lower_Bound"][::-1]]),
    fill="toself",
    fillcolor="rgba(242,184,75,0.12)",
    line=dict(color="rgba(0,0,0,0)"),
    hoverinfo="skip",
    showlegend=True,
    name="95% Confidence Band",
))

# Historical line
fig.add_trace(go.Scatter(
    x=recent_hist["Date"], y=recent_hist["Close"],
    mode="lines", name="Historical",
    line=dict(color="#8FA2C7", width=2),
))

# Forecast line
fig.add_trace(go.Scatter(
    x=fcst_df["Date"], y=fcst_df["Forecast_Close"],
    mode="lines+markers", name="Forecast",
    line=dict(color=AMBER, width=2.5, dash="dash"),
    marker=dict(size=5, color=AMBER),
))

# Connector between last actual and first forecast point
fig.add_trace(go.Scatter(
    x=[last_date, fcst_df["Date"].iloc[0]],
    y=[last_price, fcst_df["Forecast_Close"].iloc[0]],
    mode="lines", line=dict(color=AMBER, width=2.5, dash="dash"),
    showlegend=False, hoverinfo="skip",
))

fig.update_layout(
    plot_bgcolor=SURFACE,
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=TEXT, size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=10, t=10, b=10),
    height=440,
    xaxis=dict(gridcolor=BORDER, showgrid=True, zeroline=False),
    yaxis=dict(gridcolor=BORDER, showgrid=True, zeroline=False,
                title="Close Price (₹)"),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ----------------------------------------------------------------------------
# FORECAST TABLE
# ----------------------------------------------------------------------------
st.markdown('<div class="section-label">Day-by-Day Forecast</div>', unsafe_allow_html=True)

table = fcst_df.copy()
table["Date"] = table["Date"].dt.strftime("%d %b %Y (%a)")
table["Forecast_Close"] = table["Forecast_Close"].round(2)
table["Lower_Bound"] = table["Lower_Bound"].round(2)
table["Upper_Bound"] = table["Upper_Bound"].round(2)
table = table.rename(columns={
    "Forecast_Close": "Forecast (₹)",
    "Lower_Bound": "Lower 95% (₹)",
    "Upper_Bound": "Upper 95% (₹)",
})

st.dataframe(table, use_container_width=True, hide_index=True, height=360)

csv_bytes = fcst_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇ Download forecast as CSV",
    data=csv_bytes,
    file_name="Reliance_30_Day_Forecast.csv",
    mime="text/csv",
)

# ----------------------------------------------------------------------------
# MODELS TRAINED & DEPLOYED
# ----------------------------------------------------------------------------
st.markdown('<div class="section-label">Models Trained &amp; Deployed</div>', unsafe_allow_html=True)

if meta:
    best_name = meta.get("best_model", "Unknown")
    trained = meta.get("trained_models", [])
    metrics = meta.get("best_model_metrics", {})

    pills = "".join(
        f'<span class="model-pill model-pill-winner">🏆 {m}</span>' if m == best_name
        else f'<span class="model-pill">{m}</span>'
        for m in trained
    )
    st.markdown(pills, unsafe_allow_html=True)

    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Best Model (Lowest RMSE)</div>
            <div class="stat-value" style="font-size:20px;">{best_name}</div>
        </div>""", unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Test RMSE / MAE / MAPE</div>
            <div class="stat-value" style="font-size:18px;">
                ₹{metrics.get('RMSE', '—')} / ₹{metrics.get('MAE', '—')} / {metrics.get('MAPE', '—')}%
            </div>
        </div>""", unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Deployed File</div>
            <div class="stat-value" style="font-size:18px;">{meta.get('saved_model_file', 'reliance_forecast_model.pkl')}</div>
        </div>""", unsafe_allow_html=True)

    with st.expander("📊 Full model leaderboard (all models compared, sorted by RMSE)"):
        leaderboard = meta.get("leaderboard", [])
        if leaderboard:
            lb_df = pd.DataFrame(leaderboard)
            st.dataframe(lb_df, use_container_width=True, hide_index=True)
else:
    st.info(
        "`model_metadata.json` not found — run the training script (it now saves this "
        "automatically in Step 22) to show which models were trained, which won, and "
        "which one is deployed.",
        icon="ℹ️",
    )

# ----------------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------------
model_file = Path("reliance_forecast_model.pkl")
model_status = "Loaded ✓" if model_file.exists() else "Not found (metadata only)"
deployed_name = meta.get("best_model", "Unknown") if meta else "Unknown"

st.markdown(f"""
<div class="footer-box">
    <span>Instrument: <b>RELIANCE (NSE)</b></span>
    <span>Deployed model: <b>{deployed_name}</b></span>
    <span>Model file: <b>{model_status}</b></span>
    <span>Horizon: <b>30 trading days</b></span>
    <span>Generated: <b>{pd.Timestamp.today().strftime('%d %b %Y, %H:%M')}</b></span>
</div>
<div class="disclaimer">
    This forecast is generated for an academic/analytical project and is not investment advice.
    Predictions are based on historical patterns and carry no guarantee of future accuracy —
    always cross-check against live market data before making any decision.
</div>
""", unsafe_allow_html=True)
