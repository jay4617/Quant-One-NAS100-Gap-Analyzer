"""
visualizer.py — Black & white chart suite for NAS100 Gap Analyzer.

All functions return a matplotlib Figure object so they can be embedded
in Streamlit via st.pyplot(fig) or saved to disk.
"""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


# ═══════════════════════════════════════════════════════════════════════════════
# Global B&W theme
# ═══════════════════════════════════════════════════════════════════════════════

BG       = "#0a0a0a"
FG       = "#ffffff"
GRID_CLR = "#2a2a2a"
ACCENT   = "#666666"
BAR_FILL = "#cccccc"

def set_bw_theme():
    """Apply the black-background / white-elements / monospace theme globally."""
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "axes.edgecolor": "#444444",
        "axes.labelcolor": FG,
        "axes.labelsize": 12,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlepad": 18,
        "text.color": FG,
        "xtick.color": "#cccccc",
        "ytick.color": "#cccccc",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "grid.color": GRID_CLR,
        "grid.linestyle": "-",
        "grid.alpha": 0.4,
        "grid.linewidth": 0.5,
        "font.family": "monospace",
        "font.size": 11,
        "axes.grid": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.facecolor": "#111111",
        "legend.edgecolor": "#444444",
        "legend.labelcolor": FG,
        "legend.fontsize": 10,
        "figure.dpi": 100,
    })

set_bw_theme()


def _add_subtitle(ax, text: str):
    """Add a muted subtitle below the main title."""
    ax.text(0.5, 1.02, text, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=9, color=ACCENT, fontstyle="italic")


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 1 — Gap Distribution Histogram
# ═══════════════════════════════════════════════════════════════════════════════

def plot_gap_distribution(df: pd.DataFrame, bins: int = 60) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 6))

    # Split into up and down for visual clarity
    gap_up = df[df["gap_percent"] >= 0]["gap_percent"]
    gap_dn = df[df["gap_percent"] < 0]["gap_percent"]

    ax.hist(gap_dn, bins=bins // 2, color="#888888", edgecolor="#aaaaaa",
            linewidth=0.5, alpha=0.85, label=f"Gap Down (n={len(gap_dn)})")
    ax.hist(gap_up, bins=bins // 2, color=BAR_FILL, edgecolor=FG,
            linewidth=0.5, alpha=0.85, label=f"Gap Up (n={len(gap_up)})")

    ax.axvline(0, color=FG, linestyle="-", linewidth=0.8, alpha=0.4)

    # Annotate median
    median = df["gap_percent"].median()
    ax.axvline(median, color=FG, linestyle=":", linewidth=1, alpha=0.6)
    ax.text(median, ax.get_ylim()[1] * 0.92, f" Median: {median:.2f}%",
            fontsize=9, color="#bbbbbb", va="top")

    ax.set_xlabel("Gap Size (%)")
    ax.set_ylabel("Number of Occurrences")
    ax.set_title("Overnight Gap Distribution")
    _add_subtitle(ax, "How NAS100 overnight gaps are distributed by size and direction")
    ax.legend(loc="upper right", framealpha=0.8)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 2 — Fill Rate by Gap Size
# ═══════════════════════════════════════════════════════════════════════════════

def plot_fill_rate_by_size(size_df: pd.DataFrame) -> plt.Figure:
    """size_df: output of gap_analyzer.fill_rate_by_size()"""
    fig, ax = plt.subplots(figsize=(12, 6))
    categories = size_df.index.tolist()
    rates = size_df["fill_rate"].values * 100
    counts = size_df["count"].values

    # Use gradient-like bars: lighter for higher fill rates
    bar_colors = [f"#{int(180 * r / 100 + 40):02x}" * 3 for r in rates]
    bars = ax.bar(categories, rates, color=BAR_FILL, edgecolor=FG, linewidth=1.2, width=0.6)

    ax.axhline(50, color=ACCENT, linestyle="--", linewidth=1, alpha=0.6, label="50% baseline")

    for bar, rate, cnt in zip(bars, rates, counts):
        # Value on top
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{rate:.1f}%",
            ha="center", va="bottom", fontsize=12, fontweight="bold", color=FG,
        )
        # Sample size inside bar
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() / 2,
            f"n={cnt}",
            ha="center", va="center", fontsize=9, color="#333333",
        )

    # Add category descriptions on x-axis
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels([
        "Micro\n(<0.1%)", "Small\n(0.1-0.3%)", "Medium\n(0.3-0.7%)", "Large\n(>0.7%)"
    ][:len(categories)])

    ax.set_ylabel("Fill Rate (%)")
    ax.set_title("Gap Fill Rate by Size Category")
    _add_subtitle(ax, "Smaller gaps fill far more often than larger gaps")
    ax.set_ylim(0, max(rates) + 12 if len(rates) else 100)
    ax.legend(loc="upper right", framealpha=0.8)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 3 — Fill Rate by Day of Week
# ═══════════════════════════════════════════════════════════════════════════════

def plot_fill_rate_by_day(day_df: pd.DataFrame) -> plt.Figure:
    """day_df: output of gap_analyzer.fill_rate_by_day()"""
    fig, ax = plt.subplots(figsize=(12, 6))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    full_days = day_df.index.tolist()
    rates = day_df["fill_rate"].values * 100
    counts = day_df["count"].values

    bars = ax.bar(days[:len(rates)], rates, color=BAR_FILL, edgecolor=FG, linewidth=1.2, width=0.55)
    ax.axhline(50, color=ACCENT, linestyle="--", linewidth=1, alpha=0.6)

    # Highlight best and worst days
    best_idx = np.argmax(rates)
    worst_idx = np.argmin(rates)

    for i, (bar, rate, cnt) in enumerate(zip(bars, rates, counts)):
        weight = "bold" if i in (best_idx, worst_idx) else "normal"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{rate:.1f}%",
            ha="center", va="bottom", fontsize=11, fontweight=weight, color=FG,
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() / 2,
            f"n={cnt}",
            ha="center", va="center", fontsize=9, color="#333333",
        )

    ax.set_ylabel("Fill Rate (%)")
    ax.set_title("Gap Fill Rate by Day of Week")
    _add_subtitle(ax, "Does the day of the week affect whether a gap fills?")
    ax.set_ylim(0, max(rates) + 10 if len(rates) else 100)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 4 — Scatter: Gap Size vs Day Return
# ═══════════════════════════════════════════════════════════════════════════════

def plot_gap_vs_return(df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 7))

    filled = df[df["gap_filled"]]
    unfilled = df[~df["gap_filled"]]

    ax.scatter(unfilled["gap_percent"], unfilled["day_return_pct"],
               color="#555555", alpha=0.3, s=14, label=f"Unfilled (n={len(unfilled)})",
               zorder=2, marker="o")
    ax.scatter(filled["gap_percent"], filled["day_return_pct"],
               color=FG, alpha=0.45, s=14, label=f"Filled (n={len(filled)})",
               zorder=3, marker="o")

    # Regression line
    x = df["gap_percent"].values
    y = df["day_return_pct"].values
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 2:
        m, b = np.polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 200)
        ax.plot(x_line, m * x_line + b, color=BAR_FILL, linestyle="--", linewidth=1.8,
                alpha=0.9, label=f"Trend (slope = {m:.3f})")

    ax.axhline(0, color="#444444", linewidth=0.6)
    ax.axvline(0, color="#444444", linewidth=0.6)
    ax.set_xlabel("Gap Size (%)")
    ax.set_ylabel("Rest-of-Day Return (%)")
    ax.set_title("Gap Size vs Intraday Return")
    _add_subtitle(ax, "Each dot is one trading day — does the gap predict the day's direction?")
    ax.legend(loc="upper left", framealpha=0.8, markerscale=2)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 5 — Monthly Heatmap
# ═══════════════════════════════════════════════════════════════════════════════

def plot_monthly_heatmap(df: pd.DataFrame) -> plt.Figure:
    pivot = df.pivot_table(values="gap_filled", index="year", columns="month", aggfunc="mean")
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot.columns = [month_labels[m - 1] for m in pivot.columns]

    fig, ax = plt.subplots(figsize=(14, max(5, len(pivot) * 0.9 + 1.5)))
    sns.heatmap(
        pivot * 100,
        annot=True, fmt=".0f", cmap="gray_r",
        linewidths=1, linecolor="#1a1a1a",
        cbar_kws={"label": "Fill Rate (%)"},
        annot_kws={"size": 11, "weight": "bold"},
        ax=ax,
    )
    ax.set_title("Monthly Fill Rate Heatmap")
    _add_subtitle(ax, "Fill rate (%) for each month — darker = fewer fills, lighter = more fills")
    ax.set_ylabel("Year")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Chart 6 — Cumulative Strategy Return
# ═══════════════════════════════════════════════════════════════════════════════

def plot_cumulative_return(bt: pd.DataFrame) -> plt.Figure:
    """bt: output of gap_analyzer.backtest_gap_fill_strategy()"""
    fig, ax = plt.subplots(figsize=(14, 6))

    cum = bt["cumulative_return_pct"]
    ax.plot(bt.index, cum, color=FG, linewidth=1.0, alpha=0.9)
    ax.axhline(0, color=ACCENT, linestyle="-", linewidth=0.6, alpha=0.5)

    # Shade profit / loss regions
    ax.fill_between(bt.index, cum, 0,
                     where=cum >= 0, color=FG, alpha=0.04)
    ax.fill_between(bt.index, cum, 0,
                     where=cum < 0, color=ACCENT, alpha=0.06)

    # Annotate final value
    final = cum.iloc[-1] if len(cum) else 0
    ax.annotate(
        f"Final: {final:+.2f}%",
        xy=(bt.index[-1], final),
        xytext=(-100, 20), textcoords="offset points",
        fontsize=10, color=FG,
        arrowprops=dict(arrowstyle="->", color=ACCENT, lw=0.8),
    )

    # Annotate max drawdown point
    running_max = cum.cummax()
    drawdown = cum - running_max
    dd_min_idx = drawdown.idxmin()
    dd_min_val = cum.loc[dd_min_idx]
    ax.annotate(
        f"Max DD: {drawdown.min():.2f}%",
        xy=(dd_min_idx, dd_min_val),
        xytext=(60, -25), textcoords="offset points",
        fontsize=9, color="#999999",
        arrowprops=dict(arrowstyle="->", color="#666666", lw=0.8),
    )

    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return (%)")
    ax.set_title("Gap-Fill Strategy  |  Cumulative Return")
    _add_subtitle(ax, "Simulated P&L from shorting gap-ups and buying gap-downs at open")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=8))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Save all charts to disk
# ═══════════════════════════════════════════════════════════════════════════════

def save_all_charts(df: pd.DataFrame, size_df: pd.DataFrame, day_df: pd.DataFrame,
                    bt: pd.DataFrame, out_dir: str = "data"):
    """Generate and save all six charts as PNGs."""
    import os
    os.makedirs(out_dir, exist_ok=True)

    charts = {
        "gap_distribution.png": plot_gap_distribution(df),
        "fill_rate_by_size.png": plot_fill_rate_by_size(size_df),
        "fill_rate_by_day.png": plot_fill_rate_by_day(day_df),
        "gap_vs_return.png": plot_gap_vs_return(df),
        "monthly_heatmap.png": plot_monthly_heatmap(df),
        "cumulative_return.png": plot_cumulative_return(bt),
    }

    for name, fig in charts.items():
        path = os.path.join(out_dir, name)
        fig.savefig(path, dpi=150, facecolor=BG)
        plt.close(fig)
        print(f"[visualizer] Saved: {path}")
