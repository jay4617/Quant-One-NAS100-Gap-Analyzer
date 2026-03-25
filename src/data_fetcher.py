"""
data_fetcher.py — Download and cache NAS100 (NASDAQ-100 Index) historical data.

Uses yfinance to pull daily OHLCV data for ^NDX.
Caches result to data/nas100_raw.csv so subsequent runs skip the download.
"""

import os
import pandas as pd
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_FILE = os.path.join(DATA_DIR, "nas100_raw.csv")


def fetch_nas100_data(period: str = "5y", interval: str = "1d", force: bool = False) -> pd.DataFrame:
    """
    Download NAS100 daily data from Yahoo Finance.

    Parameters
    ----------
    period : str
        yfinance period string (e.g. "5y", "10y", "max").
    interval : str
        Bar interval (default "1d").
    force : bool
        If True, re-download even if a cached CSV exists.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by Date with columns: Open, High, Low, Close, Volume.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not force and os.path.exists(CACHE_FILE):
        print(f"[data_fetcher] Loading cached data from {CACHE_FILE}")
        return load_cached_data()

    print(f"[data_fetcher] Downloading ^NDX data  period={period}  interval={interval} ...")
    ticker = yf.Ticker("^NDX")
    data = ticker.history(period=period, interval=interval)

    # Clean up — drop Dividends / Stock Splits columns if present
    drop_cols = [c for c in ("Dividends", "Stock Splits", "Capital Gains") if c in data.columns]
    data.drop(columns=drop_cols, inplace=True)

    # Ensure timezone-naive datetime index for easier handling
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    data.index.name = "Date"
    data.to_csv(CACHE_FILE)
    print(f"[data_fetcher] Saved {len(data)} rows → {CACHE_FILE}")
    return data


def load_cached_data() -> pd.DataFrame:
    """Load previously cached CSV data."""
    df = pd.read_csv(CACHE_FILE, index_col="Date", parse_dates=True)
    return df


def fetch_realtime_quote() -> dict:
    """
    Fetch the latest NAS100 quote for JARVIS real-time analysis.

    Returns a dict with:
        today_open, today_high, today_low, today_close (current price),
        prev_close, today_date, prev_date, is_market_open
    """
    ticker = yf.Ticker("^NDX")

    # Get the last 5 trading days at daily granularity
    recent = ticker.history(period="5d", interval="1d")

    # Clean timezone
    if recent.index.tz is not None:
        recent.index = recent.index.tz_localize(None)

    if len(recent) < 2:
        return None

    today = recent.iloc[-1]
    yesterday = recent.iloc[-2]

    return {
        "today_date": recent.index[-1],
        "prev_date": recent.index[-2],
        "today_open": today["Open"],
        "today_high": today["High"],
        "today_low": today["Low"],
        "today_close": today["Close"],
        "prev_close": yesterday["Close"],
        "prev_open": yesterday["Open"],
        "prev_high": yesterday["High"],
        "prev_low": yesterday["Low"],
        "volume": today.get("Volume", 0),
    }


if __name__ == "__main__":
    df = fetch_nas100_data()
    print(df.tail())
    print(f"\nTotal trading days: {len(df)}")
