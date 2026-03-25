# NAS100 Overnight Gap Analyzer

Quantitative analysis of NAS100 overnight gaps — detects whether gaps tend to **fill** (price reverts to previous close) or **continue** (price extends in gap direction).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the CLI pipeline (downloads data, calculates gaps, prints results, saves charts)
python main.py

# 3. Launch the interactive dashboard
streamlit run dashboard.py
```

## Project Structure

```
nas100-gap-analyzer/
├── data/                  ← cached data & generated charts
├── src/
│   ├── data_fetcher.py    ← downloads ^NDX data via yfinance
│   ├── gap_calculator.py  ← core gap logic & classification
│   ├── gap_analyzer.py    ← statistical analyses & backtest
│   └── visualizer.py      ← B&W chart suite (matplotlib)
├── .streamlit/config.toml ← dark theme config
├── dashboard.py           ← Streamlit interactive dashboard
├── main.py                ← CLI entry point
├── requirements.txt
└── README.md
```

## Features

- **5 years** of NAS100 daily data (auto-downloaded & cached)
- **Gap classification**: Micro / Small / Medium / Large
- **Fill rate analysis**: overall, by size, by day of week, by market condition
- **Statistical significance tests** (z-test, chi-square)
- **Gap-fill strategy backtest** with Sharpe ratio, max drawdown, win rate
- **6 publication-quality B&W charts**
- **Interactive Streamlit dashboard** with sidebar filters & 4 tabs

## Tech Stack

Python · pandas · numpy · yfinance · scipy · matplotlib · seaborn · Streamlit
