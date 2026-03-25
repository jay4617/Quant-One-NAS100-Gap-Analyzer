"""
dashboard.py — Streamlit interactive dashboard for NAS100 Overnight Gap Analyzer.

Run with:  streamlit run dashboard.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import numpy as np

from data_fetcher import fetch_nas100_data, fetch_realtime_quote
from gap_calculator import calculate_gaps, filter_meaningful_gaps
from gap_analyzer import (
    overall_fill_rate,
    fill_rate_by_size,
    fill_rate_by_day,
    fill_rate_by_market_condition,
    statistical_tests,
    backtest_gap_fill_strategy,
    backtest_summary,
    jarvis_analysis,
)
from visualizer import (
    set_bw_theme,
    plot_gap_distribution,
    plot_fill_rate_by_size,
    plot_fill_rate_by_day,
    plot_gap_vs_return,
    plot_monthly_heatmap,
    plot_cumulative_return,
)

set_bw_theme()

# ═══════════════════════════════════════════════════════════════════════════════
# Page config
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NAS100 Gap Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional CSS — clean, no frills
st.markdown("""
<style>
    /* Clean metric cards */
    .metric-card {
        background: #111111;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 22px 20px 18px;
        text-align: center;
        margin-bottom: 8px;
    }
    .metric-card .label {
        color: #777;
        font-family: monospace;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    .metric-card .value {
        color: #fff;
        font-family: monospace;
        font-size: 28px;
        font-weight: bold;
        line-height: 1.1;
    }
    .metric-card .sub {
        color: #555;
        font-family: monospace;
        font-size: 10px;
        margin-top: 4px;
    }

    /* Clean tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        border-bottom: 1px solid #2a2a2a;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: monospace;
        font-size: 13px;
        letter-spacing: 0.5px;
        padding: 10px 28px;
    }

    /* Dividers */
    hr { border-color: #1a1a1a !important; }

    /* Section headers */
    .section-header {
        color: #999;
        font-family: monospace;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin: 30px 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 1px solid #1a1a1a;
    }

    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Data loading (cached)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="Loading NAS100 data ...")
def load_data():
    raw = fetch_nas100_data()
    gaps = calculate_gaps(raw)
    return gaps


gaps_all = load_data()

# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar filters
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown("## FILTERS")

# Date range
min_date = gaps_all.index.min().date()
max_date = gaps_all.index.max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Gap direction
gap_type = st.sidebar.radio("Gap Direction", ["All", "Gap Up Only", "Gap Down Only"], index=0)

# Min gap size
min_gap = st.sidebar.slider(
    "Min Gap Size (%)",
    min_value=0.00,
    max_value=1.00,
    value=0.05,
    step=0.01,
    format="%.2f%%",
    help="Filter out gaps smaller than this threshold. Default 0.05% removes market noise.",
)

# Gap categories
st.sidebar.markdown("**Size Categories**")
cat_micro  = st.sidebar.checkbox("Micro  (< 0.1%)",   value=True)
cat_small  = st.sidebar.checkbox("Small  (0.1 - 0.3%)", value=True)
cat_medium = st.sidebar.checkbox("Medium (0.3 - 0.7%)", value=True)
cat_large  = st.sidebar.checkbox("Large  (> 0.7%)",   value=True)

selected_cats = []
if cat_micro:  selected_cats.append("Micro")
if cat_small:  selected_cats.append("Small")
if cat_medium: selected_cats.append("Medium")
if cat_large:  selected_cats.append("Large")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = gaps_all.copy()

# Date range filter
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    df = df[(df.index >= start) & (df.index <= end)]

# Min gap size
df = filter_meaningful_gaps(df, min_pct=min_gap)

# Direction
if gap_type == "Gap Up Only":
    df = df[df["gap_direction"] == "UP"]
elif gap_type == "Gap Down Only":
    df = df[df["gap_direction"] == "DOWN"]

# Categories
if selected_cats:
    df = df[df["gap_category"].isin(selected_cats)]

# ═══════════════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("# NAS100  OVERNIGHT  GAP  ANALYZER")
if len(df):
    st.markdown(
        f'<p style="color:#666; font-family:monospace; font-size:13px; margin-top:-10px;">'
        f'Analyzing {len(df):,} gaps &nbsp;|&nbsp; '
        f'{df.index.min().date()} to {df.index.max().date()}</p>',
        unsafe_allow_html=True,
    )
else:
    st.warning("No gaps match the current filter criteria. Adjust the sidebar filters.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# Tabs
# ═══════════════════════════════════════════════════════════════════════════════

tab_jarvis, tab1, tab2, tab3, tab4 = st.tabs([
    "JARVIS",
    "OVERVIEW",
    "DAY OF WEEK",
    "STRATEGY BACKTEST",
    "RAW DATA",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB — JARVIS  (Real-time gap intelligence)
# ─────────────────────────────────────────────────────────────────────────────
with tab_jarvis:
    st.markdown('<div class="section-header">JARVIS  |  REAL-TIME GAP INTELLIGENCE</div>', unsafe_allow_html=True)

    # Fetch live quote
    with st.spinner("Fetching latest NAS100 data..."):
        quote = fetch_realtime_quote()

    if quote is None:
        st.error("Unable to fetch real-time data. Markets may be closed or Yahoo Finance is unavailable.")
    else:
        # JARVIS always uses the full unfiltered dataset for maximum context
        j = jarvis_analysis(quote, gaps_all)

        # ── Status banner ─────────────────────────────────────────────────────
        dir_label = "GAP UP" if j["direction"] == "UP" else "GAP DOWN"
        fill_status = "FILLED" if j["filled"] else "OPEN"
        prob_pct = j["composite_fill_prob"] * 100

        st.markdown(f"""
        <div style="background:#111; border:1px solid #2a2a2a; border-radius:6px; padding:24px 28px; margin-bottom:20px;">
            <div style="color:#777; font-family:monospace; font-size:10px; letter-spacing:2px; text-transform:uppercase;">Today's Session  |  {j['day_name']}  {j['today_date'].strftime('%Y-%m-%d')}</div>
            <div style="color:#fff; font-family:monospace; font-size:26px; font-weight:bold; margin:10px 0 6px 0;">
                {dir_label} &nbsp; {j['abs_gap_pct']:.2f}% &nbsp; ({abs(j['gap_size']):.2f} pts)
            </div>
            <div style="color:#999; font-family:monospace; font-size:13px;">
                Category: {j['category']}  &nbsp;|&nbsp;  Status: {fill_status}  &nbsp;|&nbsp;  Fill: {j['fill_pct']:.0f}%  &nbsp;|&nbsp;  Confidence: {j['confidence']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Price cards row ───────────────────────────────────────────────────
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Yesterday Close</div>
                <div class="value">{j['prev_close']:.2f}</div>
            </div>""", unsafe_allow_html=True)
        with p2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Today Open</div>
                <div class="value">{j['today_open']:.2f}</div>
            </div>""", unsafe_allow_html=True)
        with p3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Current Price</div>
                <div class="value">{j['current_price']:.2f}</div>
                <div class="sub">{j['price_vs_open_pct']:+.2f}% from open</div>
            </div>""", unsafe_allow_html=True)
        with p4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Gap Fill Probability</div>
                <div class="value">{prob_pct:.0f}%</div>
                <div class="sub">{j['confidence']} confidence</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # ── JARVIS Insights ───────────────────────────────────────────────────
        st.markdown('<div class="section-header">Analysis</div>', unsafe_allow_html=True)
        for i, insight in enumerate(j["insights"]):
            # Highlight STATUS lines
            if insight.startswith("STATUS:"):
                st.markdown(f"""
                <div style="background:#111; border-left:3px solid #fff; padding:12px 16px; margin:10px 0; font-family:monospace; font-size:13px; color:#ccc;">
                    {insight}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="padding:6px 0; font-family:monospace; font-size:13px; color:#bbb; line-height:1.6;">
                    {insight}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")

        # ── Action Hint ───────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#111; border:1px solid #2a2a2a; border-radius:6px; padding:18px 24px; margin:10px 0;">
            <div style="color:#777; font-family:monospace; font-size:10px; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;">Trade Outlook</div>
            <div style="color:#fff; font-family:monospace; font-size:15px; font-weight:bold;">{j['action_hint']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        # ── Expected Fill Levels ──────────────────────────────────────────────
        fl = j.get("fill_levels", {})
        if fl:
            st.markdown('<div class="section-header">Expected Fill Levels  |  Price Targets</div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="color:#666; font-family:monospace; font-size:11px; margin-bottom:12px;">'
                f'Based on {fl["sample_size"]} historical {j["category"].lower()} {j["direction"].lower()} gaps — '
                f'how far does the gap typically retrace?</p>',
                unsafe_allow_html=True,
            )

            f1, f2, f3, f4 = st.columns(4)
            with f1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">25th Percentile</div>
                    <div class="value">{fl['p25_price']:.2f}</div>
                    <div class="sub">{fl['p25_fill']:.0f}% of gap filled</div>
                </div>""", unsafe_allow_html=True)
            with f2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">Median (50th)</div>
                    <div class="value">{fl['p50_price']:.2f}</div>
                    <div class="sub">{fl['p50_fill']:.0f}% of gap filled</div>
                </div>""", unsafe_allow_html=True)
            with f3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">75th Percentile</div>
                    <div class="value">{fl['p75_price']:.2f}</div>
                    <div class="sub">{fl['p75_fill']:.0f}% of gap filled</div>
                </div>""", unsafe_allow_html=True)
            with f4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="label">Full Fill</div>
                    <div class="value">{fl['full_fill_price']:.2f}</div>
                    <div class="sub">100% = prev close</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")

        # ── Win Rate & Strategy Stats ─────────────────────────────────────────
        st.markdown('<div class="section-header">Win Rate  |  Strategy Stats</div>', unsafe_allow_html=True)
        w1, w2, w3, w4 = st.columns(4)
        with w1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Win Rate ({j['category']} {j['direction']})</div>
                <div class="value">{j['dc_win_rate']:.0%}</div>
                <div class="sub">{j['dc_wins']}W / {j['dc_losses']}L</div>
            </div>""", unsafe_allow_html=True)
        with w2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Avg Fill Extent</div>
                <div class="value">{j['dc_avg_fill_pct']:.0f}%</div>
                <div class="sub">of gap retraced</div>
            </div>""", unsafe_allow_html=True)
        with w3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Continuation Risk</div>
                <div class="value">{j['dc_continuation_rate']:.0%}</div>
                <div class="sub">gaps that kept going</div>
            </div>""", unsafe_allow_html=True)
        with w4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Best Day for {j['direction']}</div>
                <div class="value">{j['best_day'][:3]}</div>
                <div class="sub">{j['best_day_rate']:.0%} fill rate</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # ── Historical breakdown table ────────────────────────────────────────
        st.markdown('<div class="section-header">Historical Breakdown</div>', unsafe_allow_html=True)

        breakdown_data = {
            "Signal": [
                f"{j['category']} + {j['direction']}",
                f"Similar size ({j['abs_gap_pct']:.2f}% +/- 0.1)",
                f"{j['day_name']} + {j['direction']}",
                f"{j['market_condition']} + {j['direction']}",
                f"Recent 20 {j['direction'].lower()} gaps",
                f"All {j['direction'].lower()} gaps",
            ],
            "Fill Rate": [
                f"{j['dir_cat_fill_rate']:.0%}",
                f"{j['similar_fill_rate']:.0%}",
                f"{j['day_dir_fill_rate']:.0%}",
                f"{j['mkt_fill_rate']:.0%}",
                f"{j['recent_fill_rate']:.0%}",
                f"{j['dir_fill_rate']:.0%}",
            ],
            "Sample Size": [
                j['dir_cat_count'],
                j['similar_count'],
                j['day_dir_count'],
                j['mkt_count'],
                20,
                j['dir_count'],
            ],
        }

        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        # ── Yesterday's session ────────────────────────────────────────────────
        st.markdown('<div class="section-header">Yesterday\'s Session</div>', unsafe_allow_html=True)
        y1, y2, y3, y4 = st.columns(4)
        with y1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Open</div>
                <div class="value">{j['prev_open']:.2f}</div>
            </div>""", unsafe_allow_html=True)
        with y2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">High</div>
                <div class="value">{j['prev_high']:.2f}</div>
            </div>""", unsafe_allow_html=True)
        with y3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Low</div>
                <div class="value">{j['prev_low']:.2f}</div>
            </div>""", unsafe_allow_html=True)
        with y4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Close</div>
                <div class="value">{j['prev_close']:.2f}</div>
            </div>""", unsafe_allow_html=True)

        # ── Disclaimer ─────────────────────────────────────────────────────────
        st.markdown("")
        st.markdown(
            '<p style="color:#444; font-family:monospace; font-size:10px; text-align:center; margin-top:30px;">'
            'JARVIS insights are based on historical probabilities and do not constitute financial advice. '
            'Past performance does not guarantee future results.</p>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Overview Dashboard
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    ov = overall_fill_rate(df)

    # Metric cards row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Total Gaps Analyzed</div>
            <div class="value">{ov['total_gaps']:,}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Overall Fill Rate</div>
            <div class="value">{ov['overall_fill_rate']:.1%}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Avg Gap Size</div>
            <div class="value">{ov['avg_gap_percent']:.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Avg Fill Extent</div>
            <div class="value">{ov['avg_fill_percent']:.0f}%</div>
            <div class="sub">of gap retraced on average</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Direction comparison
    c_up, c_dn = st.columns(2)
    with c_up:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Gap Up Fill Rate</div>
            <div class="value">{ov['gap_up_fill_rate']:.1%}</div>
            <div class="sub">{ov['gap_up_count']} gap-up days</div>
        </div>""", unsafe_allow_html=True)
    with c_dn:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Gap Down Fill Rate</div>
            <div class="value">{ov['gap_down_fill_rate']:.1%}</div>
            <div class="sub">{ov['gap_down_count']} gap-down days</div>
        </div>""", unsafe_allow_html=True)

    # Charts
    st.markdown('<div class="section-header">Gap Distribution</div>', unsafe_allow_html=True)
    fig_dist = plot_gap_distribution(df)
    st.pyplot(fig_dist)

    st.markdown('<div class="section-header">Fill Rate by Size Category</div>', unsafe_allow_html=True)
    size_df = fill_rate_by_size(df)
    fig_size = plot_fill_rate_by_size(size_df)
    st.pyplot(fig_size)

    st.markdown('<div class="section-header">Gap Size vs Intraday Return</div>', unsafe_allow_html=True)
    fig_scatter = plot_gap_vs_return(df)
    st.pyplot(fig_scatter)

    st.markdown('<div class="section-header">Monthly Heatmap</div>', unsafe_allow_html=True)
    fig_heat = plot_monthly_heatmap(df)
    st.pyplot(fig_heat)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Day of Week Analysis
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    day_df = fill_rate_by_day(df)

    st.markdown('<div class="section-header">Fill Rate by Day</div>', unsafe_allow_html=True)
    fig_day = plot_fill_rate_by_day(day_df)
    st.pyplot(fig_day)

    st.markdown('<div class="section-header">Day-of-Week Statistics</div>', unsafe_allow_html=True)
    day_display = day_df.copy()
    day_display.columns = ["Count", "Fill Rate", "Avg Fill %", "Avg Gap %"]
    st.dataframe(
        day_display.style.format({
            "Fill Rate": "{:.1%}",
            "Avg Fill %": "{:.1f}",
            "Avg Gap %": "{:.3f}",
        }),
        use_container_width=True,
    )

    st.markdown('<div class="section-header">Bullish vs Bearish Market</div>', unsafe_allow_html=True)
    mkt_df = fill_rate_by_market_condition(df)
    mkt_display = mkt_df.copy()
    mkt_display.columns = ["Count", "Fill Rate", "Avg Fill %", "Avg Gap %", "Avg Day Return %"]
    st.dataframe(
        mkt_display.style.format({
            "Fill Rate": "{:.1%}",
            "Avg Fill %": "{:.1f}",
            "Avg Gap %": "{:.3f}",
            "Avg Day Return %": "{:.3f}",
        }),
        use_container_width=True,
    )

    st.markdown('<div class="section-header">Statistical Significance</div>', unsafe_allow_html=True)
    tests = statistical_tests(df)
    for name, result in tests.items():
        sig_label = "SIGNIFICANT" if result.get("significant") else "NOT SIGNIFICANT"
        with st.expander(f"[{sig_label}]  {result['description']}", expanded=True):
            cols = st.columns(3)
            if "z_statistic" in result:
                cols[0].metric("Z-statistic", f"{result['z_statistic']:.3f}")
            if "chi2_statistic" in result:
                cols[0].metric("Chi-squared", f"{result['chi2_statistic']:.3f}")
            cols[1].metric("p-value", f"{result['p_value']:.4f}")
            cols[2].metric("Significant at 5%", "Yes" if result["significant"] else "No")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Strategy Backtest
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    bt = backtest_gap_fill_strategy(df)
    bt_stats = backtest_summary(bt)

    # Top-level performance metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Total Trades</div>
            <div class="value">{bt_stats['total_trades']:,}</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Win Rate</div>
            <div class="value">{bt_stats['win_rate']:.1%}</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Sharpe Ratio</div>
            <div class="value">{bt_stats['sharpe_ratio']:.2f}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    m4, m5, m6, m7 = st.columns(4)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Avg Win</div>
            <div class="value">+{bt_stats['avg_win_pct']:.3f}%</div>
        </div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Avg Loss</div>
            <div class="value">{bt_stats['avg_loss_pct']:.3f}%</div>
        </div>""", unsafe_allow_html=True)
    with m6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Total Return</div>
            <div class="value">{bt_stats['total_return_pct']:.2f}%</div>
        </div>""", unsafe_allow_html=True)
    with m7:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Max Drawdown</div>
            <div class="value">{bt_stats['max_drawdown_pct']:.2f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Equity Curve</div>', unsafe_allow_html=True)
    fig_cum = plot_cumulative_return(bt)
    st.pyplot(fig_cum)

    st.markdown('<div class="section-header">Strategy Rules</div>', unsafe_allow_html=True)
    st.markdown("""
    | Condition | Action | Target | Stop Loss |
    |-----------|--------|--------|-----------|
    | Gap Up | SHORT at open | Previous close | Open + gap size |
    | Gap Down | LONG at open | Previous close | Open - gap size |

    A trade **wins** if the gap fills (price reaches the previous close during the session).
    A trade **loses** if the gap does not fill by close.
    """)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Raw Data
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">All Gaps</div>', unsafe_allow_html=True)

    display_cols = [
        "Open", "High", "Low", "Close", "prev_close",
        "gap_size", "gap_percent", "gap_direction", "gap_category",
        "gap_filled", "fill_percent", "day_return", "day_return_pct",
        "continuation", "market_condition", "day_name",
    ]
    display_df = df[display_cols].copy()
    display_df.index = display_df.index.strftime("%Y-%m-%d")
    display_df.index.name = "Date"

    # Rename columns for readability
    display_df.columns = [
        "Open", "High", "Low", "Close", "Prev Close",
        "Gap (pts)", "Gap (%)", "Direction", "Category",
        "Filled?", "Fill %", "Day Return", "Day Ret %",
        "Continuation", "Market", "Day",
    ]

    st.dataframe(
        display_df.style.format({
            "Open": "{:.2f}",
            "High": "{:.2f}",
            "Low": "{:.2f}",
            "Close": "{:.2f}",
            "Prev Close": "{:.2f}",
            "Gap (pts)": "{:.2f}",
            "Gap (%)": "{:.3f}",
            "Fill %": "{:.1f}",
            "Day Return": "{:.2f}",
            "Day Ret %": "{:.3f}",
        }),
        use_container_width=True,
        height=600,
    )

    # CSV download
    csv = display_df.to_csv()
    st.download_button(
        label="Export to CSV",
        data=csv,
        file_name="nas100_gaps_export.csv",
        mime="text/csv",
    )
