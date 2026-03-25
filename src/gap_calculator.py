"""
gap_calculator.py — Core gap logic for NAS100 Overnight Gap Analyzer.

Computes per-day gap metrics:
  gap_size, gap_percent, gap_direction, gap_filled, fill_percent,
  day_return, gap_category, continuation, market_condition.
"""

import numpy as np
import pandas as pd


# ── Gap size classification thresholds (percentage of previous close) ──────────
GAP_CATEGORIES = {
    "Micro":  (0.0,  0.1),
    "Small":  (0.1,  0.3),
    "Medium": (0.3,  0.7),
    "Large":  (0.7,  float("inf")),
}

MIN_GAP_PERCENT = 0.05  # Ignore gaps smaller than 0.05 %


def classify_gap(abs_pct: float) -> str:
    """Return the category label for a given absolute gap percentage."""
    for label, (lo, hi) in GAP_CATEGORIES.items():
        if lo <= abs_pct < hi:
            return label
    return "Large"


def calculate_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with columns [Open, High, Low, Close] indexed by Date,
    add all gap-related columns and return a **copy** (original untouched).

    Columns added
    -------------
    prev_close      : previous trading day's close
    gap_size        : today_open − prev_close  (points)
    gap_percent     : gap_size / prev_close × 100
    abs_gap_percent : absolute value of gap_percent
    gap_direction   : "UP" or "DOWN"
    gap_category    : Micro / Small / Medium / Large
    gap_filled      : bool — did price retrace fully to prev_close?
    fill_percent    : how much of the gap was retraced (0–100+ %)
    day_return      : today_close − today_open  (rest-of-day move)
    day_return_pct  : day_return / today_open × 100
    continuation    : bool — price kept moving in the gap direction
    ma_20           : 20-day simple moving average of Close
    market_condition: "Bullish" (close > MA20) or "Bearish"
    day_of_week     : 0=Mon … 4=Fri
    day_name        : Monday … Friday
    month           : 1–12
    year            : calendar year
    """
    out = df.copy()

    # ── Previous close (shift handles weekends/holidays automatically) ────────
    out["prev_close"] = out["Close"].shift(1)

    # ── Core gap metrics ──────────────────────────────────────────────────────
    out["gap_size"] = out["Open"] - out["prev_close"]
    out["gap_percent"] = (out["gap_size"] / out["prev_close"]) * 100
    out["abs_gap_percent"] = out["gap_percent"].abs()

    # Direction
    out["gap_direction"] = np.where(out["gap_size"] >= 0, "UP", "DOWN")

    # Category
    out["gap_category"] = out["abs_gap_percent"].apply(classify_gap)

    # ── Fill logic ────────────────────────────────────────────────────────────
    # Gap up  fills if today's Low  ≤ prev_close
    # Gap down fills if today's High ≥ prev_close
    gap_up_mask = out["gap_direction"] == "UP"
    gap_dn_mask = out["gap_direction"] == "DOWN"

    out["gap_filled"] = False
    out.loc[gap_up_mask, "gap_filled"] = out.loc[gap_up_mask, "Low"] <= out.loc[gap_up_mask, "prev_close"]
    out.loc[gap_dn_mask, "gap_filled"] = out.loc[gap_dn_mask, "High"] >= out.loc[gap_dn_mask, "prev_close"]

    # Fill percentage
    out["fill_percent"] = 0.0
    safe_gap = out["gap_size"].replace(0, np.nan)

    out.loc[gap_up_mask, "fill_percent"] = (
        (out.loc[gap_up_mask, "Open"] - out.loc[gap_up_mask, "Low"])
        / safe_gap.loc[gap_up_mask]
        * 100
    )
    out.loc[gap_dn_mask, "fill_percent"] = (
        (out.loc[gap_dn_mask, "High"] - out.loc[gap_dn_mask, "Open"])
        / safe_gap.loc[gap_dn_mask].abs()
        * 100
    )
    out["fill_percent"] = out["fill_percent"].clip(lower=0)

    # ── Rest-of-day return ────────────────────────────────────────────────────
    out["day_return"] = out["Close"] - out["Open"]
    out["day_return_pct"] = (out["day_return"] / out["Open"]) * 100

    # Continuation — price kept moving in gap direction
    out["continuation"] = False
    out.loc[gap_up_mask, "continuation"] = out.loc[gap_up_mask, "day_return"] > 0
    out.loc[gap_dn_mask, "continuation"] = out.loc[gap_dn_mask, "day_return"] < 0

    # ── Market condition (20-day MA) ──────────────────────────────────────────
    out["ma_20"] = out["Close"].rolling(window=20).mean()
    out["market_condition"] = np.where(out["Close"] > out["ma_20"], "Bullish", "Bearish")

    # ── Calendar helpers ──────────────────────────────────────────────────────
    out["day_of_week"] = out.index.dayofweek
    out["day_name"] = out.index.day_name()
    out["month"] = out.index.month
    out["year"] = out.index.year

    # ── Drop first row (no prev_close) and NaN MA rows ────────────────────────
    out.dropna(subset=["prev_close"], inplace=True)

    return out


def filter_meaningful_gaps(df: pd.DataFrame, min_pct: float = MIN_GAP_PERCENT) -> pd.DataFrame:
    """Return only rows where the absolute gap % meets the minimum threshold."""
    return df[df["abs_gap_percent"] >= min_pct].copy()


if __name__ == "__main__":
    from data_fetcher import fetch_nas100_data

    raw = fetch_nas100_data()
    gaps = calculate_gaps(raw)
    meaningful = filter_meaningful_gaps(gaps)
    print(f"Total trading days : {len(gaps)}")
    print(f"Meaningful gaps    : {len(meaningful)}")
    print(f"Gap-up fill rate   : {meaningful[meaningful['gap_direction']=='UP']['gap_filled'].mean():.1%}")
    print(f"Gap-down fill rate : {meaningful[meaningful['gap_direction']=='DOWN']['gap_filled'].mean():.1%}")
