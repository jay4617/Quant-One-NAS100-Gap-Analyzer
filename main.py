"""
main.py — CLI entry point for NAS100 Overnight Gap Analyzer.

Runs the full pipeline:
  1. Fetch / load data
  2. Calculate gaps
  3. Run analyses
  4. Print summary to console
  5. Save charts to data/
"""

import sys
import os

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_fetcher import fetch_nas100_data
from gap_calculator import calculate_gaps, filter_meaningful_gaps
from gap_analyzer import run_all_analyses
from visualizer import save_all_charts


def print_header(title: str):
    w = 60
    print(f"\n{'═' * w}")
    print(f"  {title}")
    print(f"{'═' * w}")


def main():
    print_header("NAS100 OVERNIGHT GAP ANALYZER")

    # ── Step 1: Data ──────────────────────────────────────────────────────────
    print("\n▸ Fetching data …")
    raw = fetch_nas100_data()
    print(f"  Loaded {len(raw)} trading days  ({raw.index[0].date()} → {raw.index[-1].date()})")

    # ── Step 2: Gaps ──────────────────────────────────────────────────────────
    print("\n▸ Calculating gaps …")
    gaps = calculate_gaps(raw)
    meaningful = filter_meaningful_gaps(gaps)
    print(f"  Total gaps           : {len(gaps)}")
    print(f"  Meaningful (≥0.05%)  : {len(meaningful)}")

    # ── Step 3: Analysis ──────────────────────────────────────────────────────
    print("\n▸ Running analyses …")
    results = run_all_analyses(meaningful)

    # ── Step 4: Console summary ───────────────────────────────────────────────
    ov = results["overall"]
    print_header("OVERALL FILL RATES")
    print(f"  Gap-up   fill rate : {ov['gap_up_fill_rate']:.1%}  (n={ov['gap_up_count']})")
    print(f"  Gap-down fill rate : {ov['gap_down_fill_rate']:.1%}  (n={ov['gap_down_count']})")
    print(f"  Combined           : {ov['overall_fill_rate']:.1%}")
    print(f"  Avg gap size       : {ov['avg_gap_percent']:.3f}%")
    print(f"  Avg fill percent   : {ov['avg_fill_percent']:.1f}%")

    print_header("FILL RATE BY SIZE")
    print(results["by_size"].to_string())

    print_header("FILL RATE BY DAY OF WEEK")
    print(results["by_day"].to_string())

    print_header("FILL RATE BY MARKET CONDITION")
    print(results["by_market"].to_string())

    print_header("STATISTICAL TESTS")
    for test_name, test in results["stats_tests"].items():
        sig = "✓ SIGNIFICANT" if test.get("significant") else "✗ not significant"
        print(f"\n  [{test_name}] {test['description']}")
        print(f"    p-value = {test.get('p_value', 'N/A'):.4f}   →   {sig}")

    bt_sum = results["backtest_summary"]
    print_header("BACKTEST SUMMARY")
    print(f"  Total trades     : {bt_sum['total_trades']}")
    print(f"  Win rate         : {bt_sum['win_rate']:.1%}")
    print(f"  Avg win          : +{bt_sum['avg_win_pct']:.3f}%")
    print(f"  Avg loss         : {bt_sum['avg_loss_pct']:.3f}%")
    print(f"  Total return     : {bt_sum['total_return_pct']:.2f}%")
    print(f"  Max drawdown     : {bt_sum['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe ratio     : {bt_sum['sharpe_ratio']:.2f}")

    # ── Step 5: Charts ────────────────────────────────────────────────────────
    print("\n▸ Generating charts …")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    save_all_charts(
        df=meaningful,
        size_df=results["by_size"],
        day_df=results["by_day"],
        bt=results["backtest"],
        out_dir=data_dir,
    )

    print_header("DONE")
    print("  Charts saved to data/")
    print("  Run the dashboard:  streamlit run dashboard.py\n")


if __name__ == "__main__":
    main()
