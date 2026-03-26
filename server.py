"""
server.py — Flask API backend for NAS100 Gap Analyzer.

Reuses existing src/ modules for data fetching, gap calculation, and analysis.
Serves the frontend from templates/ and static/.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
from datetime import datetime

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

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

app = Flask(__name__)

# ─── Custom JSON encoder for numpy/pandas types ──────────────────────────────

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = NumpyEncoder

# ─── Load & process data at startup ──────────────────────────────────────────

print("[server] Loading NAS100 data...")
raw = fetch_nas100_data()
gaps_all = calculate_gaps(raw)
print(f"[server] Processed {len(gaps_all)} gaps")


def serialize_df(df, max_rows=None):
    """Convert DataFrame to list-of-dicts with JSON-safe types."""
    if max_rows:
        df = df.head(max_rows)
    records = []
    for idx, row in df.iterrows():
        rec = {}
        rec["date"] = idx.isoformat() if isinstance(idx, pd.Timestamp) else str(idx)
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                rec[col] = None
            elif isinstance(val, (np.integer,)):
                rec[col] = int(val)
            elif isinstance(val, (np.floating,)):
                rec[col] = round(float(val), 4)
            elif isinstance(val, (np.bool_, bool)):
                rec[col] = bool(val)
            else:
                rec[col] = val
        records.append(rec)
    return records


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/overview")
def api_overview():
    """Overall fill rates and gap statistics."""
    stats = overall_fill_rate(gaps_all)
    
    # Use median to avoid massive distortion from uncapped outliers (e.g., tiny gaps)
    # This prevents the UI from showing "1089%" as the average fill extent
    stats["avg_fill_percent"] = gaps_all["fill_percent"].median()
    
    stats["total_trading_days"] = len(raw)
    stats["date_range"] = {
        "start": gaps_all.index.min().isoformat(),
        "end": gaps_all.index.max().isoformat(),
    }
    return jsonify(stats)


@app.route("/api/by-size")
def api_by_size():
    """Fill rate breakdown by gap size category."""
    df = fill_rate_by_size(gaps_all)
    result = []
    for cat in df.index:
        row = df.loc[cat]
        result.append({
            "category": cat,
            "count": int(row["count"]),
            "fill_rate": round(float(row["fill_rate"]), 4),
            "avg_fill_pct": round(float(row["avg_fill_pct"]), 2),
            "avg_gap_pct": round(float(row["avg_gap_pct"]), 4),
            "continuation_rate": round(float(row["continuation_rate"]), 4),
        })
    return jsonify(result)


@app.route("/api/by-day")
def api_by_day():
    """Fill rate breakdown by day of week."""
    df = fill_rate_by_day(gaps_all)
    result = []
    for day in df.index:
        row = df.loc[day]
        result.append({
            "day": day,
            "count": int(row["count"]),
            "fill_rate": round(float(row["fill_rate"]), 4),
            "avg_fill_pct": round(float(row["avg_fill_pct"]), 2),
            "avg_gap_pct": round(float(row["avg_gap_pct"]), 4),
        })
    return jsonify(result)


@app.route("/api/by-market")
def api_by_market():
    """Fill rate by market condition × gap direction."""
    df = fill_rate_by_market_condition(gaps_all)
    result = []
    for (condition, direction) in df.index:
        row = df.loc[(condition, direction)]
        result.append({
            "market_condition": condition,
            "gap_direction": direction,
            "count": int(row["count"]),
            "fill_rate": round(float(row["fill_rate"]), 4),
            "avg_fill_pct": round(float(row["avg_fill_pct"]), 2),
        })
    return jsonify(result)


@app.route("/api/stats-tests")
def api_stats_tests():
    """Statistical significance tests."""
    results = statistical_tests(gaps_all)
    # Deep-convert numpy types to native Python for JSON serialization
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return round(float(obj), 6)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    return jsonify(convert(results))


@app.route("/api/backtest")
def api_backtest():
    """Backtest results with cumulative return series."""
    bt = backtest_gap_fill_strategy(gaps_all)
    summary = backtest_summary(bt)

    # Cumulative return series (sample every N points for performance)
    cum = bt[["cumulative_return_pct"]].copy()
    cum["date"] = cum.index.map(lambda x: x.isoformat())

    # Thin to ~200 points for the chart
    step = max(1, len(cum) // 200)
    sampled = cum.iloc[::step]
    series = [
        {"date": r["date"], "value": round(float(r["cumulative_return_pct"]), 2)}
        for _, r in sampled.iterrows()
    ]

    return jsonify({
        "summary": summary,
        "cumulative_series": series,
    })


@app.route("/api/jarvis")
def api_jarvis():
    """JARVIS real-time gap intelligence."""
    try:
        quote = fetch_realtime_quote()
        if quote is None:
            return jsonify({"error": "Unable to fetch real-time data"}), 503

        j = jarvis_analysis(quote, gaps_all)

        # Convert non-serializable types
        result = {}
        for k, v in j.items():
            if isinstance(v, pd.Timestamp):
                result[k] = v.isoformat()
            elif isinstance(v, (np.integer,)):
                result[k] = int(v)
            elif isinstance(v, (np.floating,)):
                result[k] = round(float(v), 4)
            elif isinstance(v, (np.bool_,)):
                result[k] = bool(v)
            elif isinstance(v, dict):
                result[k] = {
                    kk: (round(float(vv), 4) if isinstance(vv, (float, np.floating)) else vv)
                    for kk, vv in v.items()
                }
            else:
                result[k] = v

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gaps")
def api_gaps():
    """Raw gap data (most recent first, paginated)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 200)

    sorted_df = gaps_all.sort_index(ascending=False)
    total = len(sorted_df)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = sorted_df.iloc[start:end]

    cols = ["Open", "Close", "gap_size", "gap_percent", "abs_gap_percent",
            "gap_direction", "gap_category", "gap_filled", "fill_percent",
            "day_return_pct", "day_name", "market_condition"]
    available_cols = [c for c in cols if c in page_df.columns]

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "data": serialize_df(page_df[available_cols]),
    })


@app.route("/api/distribution")
def api_distribution():
    """Gap size distribution data for histogram."""
    up = gaps_all[gaps_all["gap_direction"] == "UP"]["gap_percent"].tolist()
    down = gaps_all[gaps_all["gap_direction"] == "DOWN"]["gap_percent"].tolist()

    # Bin the data
    all_vals = gaps_all["gap_percent"].dropna()
    bins = np.linspace(all_vals.min(), all_vals.max(), 40)
    up_hist, _ = np.histogram(up, bins=bins)
    dn_hist, _ = np.histogram(down, bins=bins)
    labels = [f"{bins[i]:.2f}" for i in range(len(bins) - 1)]

    return jsonify({
        "labels": labels,
        "up_counts": up_hist.tolist(),
        "down_counts": dn_hist.tolist(),
        "bin_edges": bins.tolist(),
    })


if __name__ == "__main__":
    print("[server] Starting on http://localhost:5000")
    app.run(debug=True, port=5000)
