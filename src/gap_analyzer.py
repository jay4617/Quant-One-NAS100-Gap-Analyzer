"""
gap_analyzer.py — Statistical analysis engine for NAS100 gaps.

Five analyses:
  1. Overall gap fill rate (up vs down)
  2. Fill rate by gap size category
  3. Fill rate by day of week
  4. Fill rate by market condition (bullish / bearish)
  5. Statistical significance tests
"""

import numpy as np
import pandas as pd
from scipy import stats


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis 1 — Overall fill rates
# ═══════════════════════════════════════════════════════════════════════════════

def overall_fill_rate(df: pd.DataFrame) -> dict:
    """
    Returns
    -------
    dict with keys: total_gaps, gap_up_count, gap_down_count,
                    gap_up_fill_rate, gap_down_fill_rate, overall_fill_rate,
                    avg_fill_percent, avg_gap_percent
    """
    up = df[df["gap_direction"] == "UP"]
    dn = df[df["gap_direction"] == "DOWN"]
    return {
        "total_gaps": len(df),
        "gap_up_count": len(up),
        "gap_down_count": len(dn),
        "gap_up_fill_rate": up["gap_filled"].mean() if len(up) else 0.0,
        "gap_down_fill_rate": dn["gap_filled"].mean() if len(dn) else 0.0,
        "overall_fill_rate": df["gap_filled"].mean(),
        "avg_fill_percent": df["fill_percent"].mean(),
        "avg_gap_percent": df["abs_gap_percent"].mean(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis 2 — Fill rate by gap size category
# ═══════════════════════════════════════════════════════════════════════════════

def fill_rate_by_size(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame indexed by gap_category with columns:
        count, fill_rate, avg_fill_pct, avg_gap_pct, avg_day_return_pct, continuation_rate
    """
    cat_order = ["Micro", "Small", "Medium", "Large"]
    grouped = df.groupby("gap_category").agg(
        count=("gap_filled", "size"),
        fill_rate=("gap_filled", "mean"),
        avg_fill_pct=("fill_percent", "mean"),
        avg_gap_pct=("abs_gap_percent", "mean"),
        avg_day_return_pct=("day_return_pct", "mean"),
        continuation_rate=("continuation", "mean"),
    )
    # Reindex to ensure fixed category order, fill missing with 0
    grouped = grouped.reindex(cat_order).fillna(0)
    grouped["count"] = grouped["count"].astype(int)
    return grouped


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis 3 — Fill rate by day of week
# ═══════════════════════════════════════════════════════════════════════════════

def fill_rate_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame indexed by day_name with columns:
        count, fill_rate, avg_fill_pct, avg_gap_pct
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    grouped = df.groupby("day_name").agg(
        count=("gap_filled", "size"),
        fill_rate=("gap_filled", "mean"),
        avg_fill_pct=("fill_percent", "mean"),
        avg_gap_pct=("abs_gap_percent", "mean"),
    )
    grouped = grouped.reindex(day_order).fillna(0)
    grouped["count"] = grouped["count"].astype(int)
    return grouped


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis 4 — Fill rate by market condition
# ═══════════════════════════════════════════════════════════════════════════════

def fill_rate_by_market_condition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split by market_condition (Bullish / Bearish) × gap_direction (UP / DOWN).

    Returns a DataFrame with multi-level index (market_condition, gap_direction).
    """
    valid = df.dropna(subset=["ma_20"])
    grouped = valid.groupby(["market_condition", "gap_direction"]).agg(
        count=("gap_filled", "size"),
        fill_rate=("gap_filled", "mean"),
        avg_fill_pct=("fill_percent", "mean"),
        avg_gap_pct=("abs_gap_percent", "mean"),
        avg_day_return_pct=("day_return_pct", "mean"),
    )
    grouped["count"] = grouped["count"].astype(int)
    return grouped


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis 5 — Statistical significance tests
# ═══════════════════════════════════════════════════════════════════════════════

def statistical_tests(df: pd.DataFrame) -> dict:
    """
    Run three tests and return a dict of results.

    1. Z-test: Is the overall fill rate significantly different from 50 %?
    2. Z-test: Is the gap-up fill rate significantly different from the gap-down fill rate?
    3. Chi-square: Is fill rate independent of gap size category?
    """
    results = {}

    # ── Test 1: One-sample proportion z-test (fill rate vs 50 %) ──────────────
    fills = df["gap_filled"].values.astype(float)
    n = len(fills)
    p_hat = fills.mean()
    p0 = 0.5
    z = (p_hat - p0) / np.sqrt(p0 * (1 - p0) / n)
    p_val = 2 * (1 - stats.norm.cdf(abs(z)))
    results["overall_vs_50"] = {
        "description": "Is overall fill rate ≠ 50%?",
        "fill_rate": p_hat,
        "z_statistic": z,
        "p_value": p_val,
        "significant": p_val < 0.05,
        "n": n,
    }

    # ── Test 2: Two-proportion z-test (gap-up fill vs gap-down fill) ──────────
    up = df[df["gap_direction"] == "UP"]["gap_filled"].values.astype(float)
    dn = df[df["gap_direction"] == "DOWN"]["gap_filled"].values.astype(float)
    n1, n2 = len(up), len(dn)
    if n1 > 0 and n2 > 0:
        p1, p2 = up.mean(), dn.mean()
        p_pool = (up.sum() + dn.sum()) / (n1 + n2)
        se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        z2 = (p1 - p2) / se if se > 0 else 0
        p_val2 = 2 * (1 - stats.norm.cdf(abs(z2)))
        results["up_vs_down"] = {
            "description": "Is gap-up fill rate ≠ gap-down fill rate?",
            "gap_up_fill_rate": p1,
            "gap_down_fill_rate": p2,
            "z_statistic": z2,
            "p_value": p_val2,
            "significant": p_val2 < 0.05,
            "n_up": n1,
            "n_down": n2,
        }

    # ── Test 3: Chi-square — fill rate independence across categories ────────
    cat_order = ["Micro", "Small", "Medium", "Large"]
    present = [c for c in cat_order if c in df["gap_category"].unique()]
    if len(present) >= 2:
        contingency = pd.crosstab(df["gap_category"], df["gap_filled"])
        contingency = contingency.reindex(present).dropna()
        if contingency.shape[0] >= 2 and contingency.shape[1] == 2:
            chi2, p_val3, dof, _ = stats.chi2_contingency(contingency)
            results["category_independence"] = {
                "description": "Is fill rate independent of gap category?",
                "chi2_statistic": chi2,
                "p_value": p_val3,
                "degrees_of_freedom": dof,
                "significant": p_val3 < 0.05,
            }

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Backtest — simple gap-fill strategy
# ═══════════════════════════════════════════════════════════════════════════════

def backtest_gap_fill_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate a gap-fill strategy:
      - Gap up  → short at open, target = prev_close, stop = open + gap_size
      - Gap down → long at open, target = prev_close, stop = open − |gap_size|

    Returns a copy of df with extra columns:
        strategy_return, strategy_return_pct, cumulative_return, win
    """
    out = df.copy()
    out["strategy_return"] = 0.0
    out["win"] = False

    up = out["gap_direction"] == "UP"
    dn = out["gap_direction"] == "DOWN"

    # Gap up (short): profit if filled, loss if gap doubles
    out.loc[up & out["gap_filled"], "strategy_return"] = out.loc[up & out["gap_filled"], "gap_size"]
    out.loc[up & ~out["gap_filled"], "strategy_return"] = -out.loc[up & ~out["gap_filled"], "gap_size"]

    # Gap down (long): profit if filled, loss if gap doubles
    out.loc[dn & out["gap_filled"], "strategy_return"] = out.loc[dn & out["gap_filled"], "gap_size"].abs()
    out.loc[dn & ~out["gap_filled"], "strategy_return"] = -out.loc[dn & ~out["gap_filled"], "gap_size"].abs()

    out["win"] = out["strategy_return"] > 0
    out["strategy_return_pct"] = (out["strategy_return"] / out["Open"]) * 100
    out["cumulative_return"] = out["strategy_return"].cumsum()
    out["cumulative_return_pct"] = out["strategy_return_pct"].cumsum()

    return out


def backtest_summary(bt: pd.DataFrame) -> dict:
    """Compute key performance metrics from backtest results."""
    total = len(bt)
    wins = bt["win"].sum()
    losses = total - wins
    win_rate = wins / total if total else 0

    avg_win = bt.loc[bt["win"], "strategy_return_pct"].mean() if wins else 0
    avg_loss = bt.loc[~bt["win"], "strategy_return_pct"].mean() if losses else 0

    cum = bt["strategy_return_pct"]
    running_max = cum.cummax()
    drawdown = cum - running_max
    max_drawdown = drawdown.min()

    # Sharpe ratio (annualized, assuming 252 trading days)
    daily_returns = bt["strategy_return_pct"]
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else 0

    return {
        "total_trades": total,
        "wins": int(wins),
        "losses": int(losses),
        "win_rate": win_rate,
        "avg_win_pct": avg_win,
        "avg_loss_pct": avg_loss,
        "total_return_pct": cum.iloc[-1] if len(cum) else 0,
        "max_drawdown_pct": max_drawdown,
        "sharpe_ratio": sharpe,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience: run all analyses
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_analyses(df: pd.DataFrame) -> dict:
    """Return a dict of all analysis results."""
    bt = backtest_gap_fill_strategy(df)
    return {
        "overall": overall_fill_rate(df),
        "by_size": fill_rate_by_size(df),
        "by_day": fill_rate_by_day(df),
        "by_market": fill_rate_by_market_condition(df),
        "stats_tests": statistical_tests(df),
        "backtest": bt,
        "backtest_summary": backtest_summary(bt),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# JARVIS — Real-time gap intelligence
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_gap(abs_pct: float) -> str:
    """Classify gap by absolute percentage."""
    if abs_pct < 0.1:
        return "Micro"
    elif abs_pct < 0.3:
        return "Small"
    elif abs_pct < 0.7:
        return "Medium"
    else:
        return "Large"


def jarvis_analysis(quote: dict, historical_df: pd.DataFrame) -> dict:
    """
    Generate JARVIS real-time trading insights for today's gap.

    Parameters
    ----------
    quote : dict
        Output of data_fetcher.fetch_realtime_quote().
    historical_df : dict
        Processed historical gap data (output of gap_calculator.calculate_gaps + filter).

    Returns
    -------
    dict with comprehensive insights about today's gap.
    """
    today_open = quote["today_open"]
    prev_close = quote["prev_close"]
    today_high = quote["today_high"]
    today_low = quote["today_low"]
    today_close = quote["today_close"]

    # ── Today's gap metrics ───────────────────────────────────────────────────
    gap_size = today_open - prev_close
    gap_pct = (gap_size / prev_close) * 100
    abs_gap_pct = abs(gap_pct)
    direction = "UP" if gap_size >= 0 else "DOWN"
    category = _classify_gap(abs_gap_pct)

    # ── Fill status check ─────────────────────────────────────────────────────
    if direction == "UP":
        filled = today_low <= prev_close
        fill_pct = (today_open - today_low) / gap_size * 100 if gap_size != 0 else 0
    else:
        filled = today_high >= prev_close
        fill_pct = (today_high - today_open) / abs(gap_size) * 100 if gap_size != 0 else 0
    fill_pct = max(0, fill_pct)

    # Current price position relative to gap
    current_price = today_close
    if direction == "UP":
        price_vs_open = ((current_price - today_open) / today_open) * 100
    else:
        price_vs_open = ((current_price - today_open) / today_open) * 100

    # ── Historical lookups ────────────────────────────────────────────────────
    today_date = quote["today_date"]
    day_name = today_date.strftime("%A")
    day_of_week = today_date.weekday()

    # Same direction
    same_dir = historical_df[historical_df["gap_direction"] == direction]
    dir_fill_rate = same_dir["gap_filled"].mean() if len(same_dir) else 0
    dir_count = len(same_dir)

    # Same category
    same_cat = historical_df[historical_df["gap_category"] == category]
    cat_fill_rate = same_cat["gap_filled"].mean() if len(same_cat) else 0
    cat_count = len(same_cat)

    # Same direction + same category
    same_dir_cat = same_dir[same_dir["gap_category"] == category]
    dir_cat_fill_rate = same_dir_cat["gap_filled"].mean() if len(same_dir_cat) else 0
    dir_cat_count = len(same_dir_cat)

    # Same day of week
    same_day = historical_df[historical_df["day_name"] == day_name]
    day_fill_rate = same_day["gap_filled"].mean() if len(same_day) else 0
    day_count = len(same_day)

    # Same day + same direction
    same_day_dir = same_day[same_day["gap_direction"] == direction]
    day_dir_fill_rate = same_day_dir["gap_filled"].mean() if len(same_day_dir) else 0
    day_dir_count = len(same_day_dir)

    # Market condition (use last available MA)
    valid_ma = historical_df.dropna(subset=["ma_20"])
    if len(valid_ma) > 0:
        last_ma = valid_ma["ma_20"].iloc[-1]
        market_condition = "Bullish" if prev_close > last_ma else "Bearish"
        same_mkt = historical_df[historical_df["market_condition"] == market_condition]
        same_mkt_dir = same_mkt[same_mkt["gap_direction"] == direction]
        mkt_fill_rate = same_mkt_dir["gap_filled"].mean() if len(same_mkt_dir) else 0
        mkt_count = len(same_mkt_dir)
    else:
        last_ma = None
        market_condition = "Unknown"
        mkt_fill_rate = 0
        mkt_count = 0

    # Similar-sized gaps (within ±0.1% of today's gap)
    similar = historical_df[
        (historical_df["abs_gap_percent"] >= abs_gap_pct - 0.1) &
        (historical_df["abs_gap_percent"] <= abs_gap_pct + 0.1) &
        (historical_df["gap_direction"] == direction)
    ]
    similar_fill_rate = similar["gap_filled"].mean() if len(similar) else 0
    similar_count = len(similar)
    similar_avg_return = similar["day_return_pct"].mean() if len(similar) else 0

    # Recent trend (last 20 matching gaps)
    recent_same = same_dir.tail(20)
    recent_fill_rate = recent_same["gap_filled"].mean() if len(recent_same) else 0

    # ── Win rate & strategy stats for this gap type ───────────────────────────
    # If you traded every gap like today's (same direction + category), what's the track record?
    if len(same_dir_cat) > 0:
        dc_wins = same_dir_cat["gap_filled"].sum()
        dc_losses = len(same_dir_cat) - dc_wins
        dc_win_rate = dc_wins / len(same_dir_cat)
        dc_avg_return = same_dir_cat["day_return_pct"].mean()
        dc_avg_fill_pct = same_dir_cat["fill_percent"].mean()
        dc_continuation_rate = same_dir_cat["continuation"].mean() if "continuation" in same_dir_cat.columns else 0
    else:
        dc_wins, dc_losses, dc_win_rate = 0, 0, 0
        dc_avg_return, dc_avg_fill_pct, dc_continuation_rate = 0, 0, 0

    # Strategy P&L for similar gaps
    if len(similar) > 0:
        sim_wins = similar["gap_filled"].sum()
        sim_win_rate = sim_wins / len(similar)
        sim_avg_fill_pct = similar["fill_percent"].mean()
    else:
        sim_wins, sim_win_rate, sim_avg_fill_pct = 0, 0, 0

    # Best and worst day of week for this direction
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_rates = {}
    for d in day_order:
        d_subset = same_dir[same_dir["day_name"] == d]
        if len(d_subset) >= 5:
            day_rates[d] = d_subset["gap_filled"].mean()
    best_day = max(day_rates, key=day_rates.get) if day_rates else day_name
    worst_day = min(day_rates, key=day_rates.get) if day_rates else day_name
    best_day_rate = day_rates.get(best_day, 0)
    worst_day_rate = day_rates.get(worst_day, 0)

    # ── Expected fill extent & price levels ───────────────────────────────────
    # Use historical fill_percent distribution to predict how far today's gap
    # is likely to retrace, and convert to actual price targets.
    fill_levels = {}
    if len(same_dir_cat) >= 5:
        fill_pcts_hist = same_dir_cat["fill_percent"].dropna()
    elif len(same_dir) >= 5:
        fill_pcts_hist = same_dir["fill_percent"].dropna()
    else:
        fill_pcts_hist = historical_df["fill_percent"].dropna()

    if len(fill_pcts_hist) > 0:
        p25 = np.percentile(fill_pcts_hist, 25)
        p50 = np.percentile(fill_pcts_hist, 50)   # median
        p75 = np.percentile(fill_pcts_hist, 75)
        p90 = np.percentile(fill_pcts_hist, 90)
        avg = fill_pcts_hist.mean()

        # Calculate price levels: how far does each fill % translate to?
        # For gap UP: fill moves price DOWN from open toward prev_close
        # For gap DOWN: fill moves price UP from open toward prev_close
        def _fill_pct_to_price(fpct):
            retracement = abs(gap_size) * fpct / 100
            if direction == "UP":
                return today_open - retracement
            else:
                return today_open + retracement

        fill_levels = {
            "p25_fill": p25,
            "p25_price": _fill_pct_to_price(p25),
            "p50_fill": p50,
            "p50_price": _fill_pct_to_price(p50),
            "p75_fill": p75,
            "p75_price": _fill_pct_to_price(p75),
            "p90_fill": p90,
            "p90_price": _fill_pct_to_price(p90),
            "avg_fill": avg,
            "avg_price": _fill_pct_to_price(avg),
            "full_fill_price": prev_close,
            "sample_size": len(fill_pcts_hist),
        }

    # ── Composite probability ─────────────────────────────────────────────────
    # Weighted average of all historical signals
    weights_and_rates = [
        (3.0, dir_cat_fill_rate, dir_cat_count),   # direction + category (most specific)
        (2.0, similar_fill_rate, similar_count),    # similar size
        (1.5, day_dir_fill_rate, day_dir_count),    # day + direction
        (1.5, mkt_fill_rate, mkt_count),            # market condition
        (1.0, recent_fill_rate, len(recent_same)),  # recent trend
    ]

    total_weight = 0
    weighted_sum = 0
    for w, rate, cnt in weights_and_rates:
        if cnt >= 5:  # only include signals with enough data
            total_weight += w
            weighted_sum += w * rate

    composite_fill_prob = weighted_sum / total_weight if total_weight > 0 else dir_fill_rate

    # ── Confidence level ──────────────────────────────────────────────────────
    total_supporting = sum(cnt for _, _, cnt in weights_and_rates)
    if total_supporting >= 200 and abs(composite_fill_prob - 0.5) > 0.1:
        confidence = "HIGH"
    elif total_supporting >= 50:
        confidence = "MODERATE"
    else:
        confidence = "LOW"

    # ── Generate insights ─────────────────────────────────────────────────────
    insights = []

    # 1. Main gap summary
    dir_word = "gapped UP" if direction == "UP" else "gapped DOWN"
    insights.append(
        f"NAS100 {dir_word} by {abs_gap_pct:.2f}% ({abs(gap_size):.2f} pts) at today's open. "
        f"This is classified as a {category.upper()} gap."
    )

    # 2. Fill probability
    if composite_fill_prob >= 0.65:
        fill_outlook = "Historically, this type of gap fills more often than not."
        action_hint = "Gap-fill trade has favorable odds" if not filled else "Gap has already filled"
    elif composite_fill_prob <= 0.35:
        fill_outlook = "Historically, this type of gap tends to continue rather than fill."
        action_hint = "Fading this gap has poor historical odds"
    else:
        fill_outlook = "Historical data shows roughly even odds of filling vs continuing."
        action_hint = "No strong directional edge from historical data"
    insights.append(fill_outlook)

    # 3. Historical win rate for this exact gap type
    insights.append(
        f"TRACK RECORD: {category} {direction.lower()} gaps have a {dc_win_rate:.0%} win rate "
        f"({int(dc_wins)}W / {int(dc_losses)}L out of {dir_cat_count} occurrences). "
        f"Average fill extent: {dc_avg_fill_pct:.0f}%."
    )

    # 4. Day-of-week context with comparison
    insights.append(
        f"DAY CONTEXT: On {day_name}s, {direction.lower()} gaps fill {day_dir_fill_rate:.0%} "
        f"of the time (n={day_dir_count}). "
        f"Best day for {direction.lower()} gap fills: {best_day} ({best_day_rate:.0%}). "
        f"Worst: {worst_day} ({worst_day_rate:.0%})."
    )

    # 5. Similar-sized gaps performance
    if similar_count > 0:
        insights.append(
            f"SIMILAR GAPS: In the past, {direction.lower()} gaps between "
            f"{abs_gap_pct - 0.1:.2f}% and {abs_gap_pct + 0.1:.2f}% filled {sim_win_rate:.0%} "
            f"of the time (n={similar_count}). Average rest-of-day return: {similar_avg_return:+.3f}%."
        )

    # 6. Market condition
    if market_condition != "Unknown":
        insights.append(
            f"MARKET REGIME: {market_condition.upper()} (price {'above' if market_condition == 'Bullish' else 'below'} "
            f"20-day MA at {last_ma:.2f}). In {market_condition.lower()} markets, "
            f"{direction.lower()} gaps fill {mkt_fill_rate:.0%} (n={mkt_count})."
        )

    # 7. Continuation risk
    if dc_continuation_rate > 0:
        insights.append(
            f"CONTINUATION RISK: {dc_continuation_rate:.0%} of past {category.lower()} {direction.lower()} gaps "
            f"continued in the gap direction instead of reverting."
        )

    # 8. Current session status
    if filled:
        insights.append("STATUS: The gap has ALREADY FILLED during today's session.")
    else:
        remaining = abs(current_price - prev_close)
        insights.append(
            f"STATUS: Gap is {fill_pct:.0f}% filled so far. "
            f"Price needs to move {remaining:.2f} pts to reach previous close ({prev_close:.2f})."
        )

    # 9. Expected fill extent
    if fill_levels:
        insights.append(
            f"EXPECTED FILL: Based on {fill_levels['sample_size']} past {category.lower()} {direction.lower()} gaps, "
            f"the median fill is {fill_levels['p50_fill']:.0f}% (price ~{fill_levels['p50_price']:.2f}). "
            f"75th percentile: {fill_levels['p75_fill']:.0f}% (~{fill_levels['p75_price']:.2f}). "
            f"Full gap fill at {fill_levels['full_fill_price']:.2f}."
        )

    # 9. Recent trend
    if abs(recent_fill_rate - dir_fill_rate) > 0.1:
        trend_word = "higher" if recent_fill_rate > dir_fill_rate else "lower"
        insights.append(
            f"RECENT TREND: The last 20 {direction.lower()} gaps show a {trend_word} fill rate "
            f"({recent_fill_rate:.0%}) vs the 5-year average ({dir_fill_rate:.0%}). "
            f"Market behaviour may be shifting."
        )

    return {
        # Today's gap data
        "today_date": today_date,
        "day_name": day_name,
        "today_open": today_open,
        "prev_close": prev_close,
        "current_price": current_price,
        "gap_size": gap_size,
        "gap_pct": gap_pct,
        "abs_gap_pct": abs_gap_pct,
        "direction": direction,
        "category": category,
        "filled": filled,
        "fill_pct": fill_pct,
        "price_vs_open_pct": price_vs_open,

        # Historical rates
        "dir_fill_rate": dir_fill_rate,
        "dir_count": dir_count,
        "cat_fill_rate": cat_fill_rate,
        "cat_count": cat_count,
        "dir_cat_fill_rate": dir_cat_fill_rate,
        "dir_cat_count": dir_cat_count,
        "day_fill_rate": day_fill_rate,
        "day_count": day_count,
        "day_dir_fill_rate": day_dir_fill_rate,
        "day_dir_count": day_dir_count,
        "mkt_fill_rate": mkt_fill_rate,
        "mkt_count": mkt_count,
        "market_condition": market_condition,
        "ma_20": last_ma,
        "similar_fill_rate": similar_fill_rate,
        "similar_count": similar_count,
        "similar_avg_return": similar_avg_return,
        "recent_fill_rate": recent_fill_rate,

        # Win rate / strategy stats
        "dc_win_rate": dc_win_rate,
        "dc_wins": int(dc_wins),
        "dc_losses": int(dc_losses),
        "dc_avg_return": dc_avg_return,
        "dc_avg_fill_pct": dc_avg_fill_pct,
        "dc_continuation_rate": dc_continuation_rate,
        "sim_win_rate": sim_win_rate,
        "best_day": best_day,
        "best_day_rate": best_day_rate,
        "worst_day": worst_day,
        "worst_day_rate": worst_day_rate,

        # Composite
        "composite_fill_prob": composite_fill_prob,
        "confidence": confidence,
        "action_hint": action_hint,

        # Fill extent distribution
        "fill_levels": fill_levels,

        # Text insights
        "insights": insights,

        # Yesterday
        "prev_date": quote["prev_date"],
        "prev_open": quote["prev_open"],
        "prev_high": quote["prev_high"],
        "prev_low": quote["prev_low"],
    }


