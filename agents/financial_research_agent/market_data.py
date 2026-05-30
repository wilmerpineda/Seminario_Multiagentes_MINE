"""Market data utilities for the Financial Research Agent."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"


def fetch_market_data(
    symbols: str | Iterable[str],
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
) -> pd.DataFrame:
    """Fetch OHLCV market data from Yahoo Finance.

    Args:
        symbols: Ticker symbol or iterable of ticker symbols.
        period: Yahoo Finance period, for example ``1mo``, ``6mo``, ``1y``.
        interval: Yahoo Finance interval, for example ``1d``, ``1wk``.

    Returns:
        A tidy DataFrame with one row per symbol and date.

    Raises:
        ImportError: If yfinance is not installed.
        ValueError: If no market data is returned.
    """

    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "yfinance is required to fetch market data. Install it with Poetry "
            "or pip before running this tool."
        ) from exc

    symbol_list = normalize_symbols(symbols)
    raw_data = yf.download(
        tickers=" ".join(symbol_list),
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
    )

    if raw_data.empty:
        raise ValueError(f"No market data returned for symbols: {', '.join(symbol_list)}")

    return normalize_yfinance_data(raw_data, symbol_list)


def normalize_symbols(symbols: str | Iterable[str]) -> list[str]:
    """Normalize ticker input into a clean uppercase list."""

    if isinstance(symbols, str):
        raw_symbols = symbols.replace(",", " ").split()
    else:
        raw_symbols = list(symbols)

    symbol_list = [str(symbol).strip().upper() for symbol in raw_symbols if str(symbol).strip()]

    if not symbol_list:
        raise ValueError("At least one symbol is required.")

    return list(dict.fromkeys(symbol_list))


def normalize_yfinance_data(raw_data: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """Convert yfinance output into a predictable tidy DataFrame."""

    frames: list[pd.DataFrame] = []

    if isinstance(raw_data.columns, pd.MultiIndex):
        for symbol in symbols:
            if symbol not in raw_data.columns.get_level_values(0):
                continue

            symbol_frame = raw_data[symbol].copy()
            symbol_frame["symbol"] = symbol
            frames.append(symbol_frame)
    else:
        symbol_frame = raw_data.copy()
        symbol_frame["symbol"] = symbols[0]
        frames.append(symbol_frame)

    if not frames:
        raise ValueError(f"No usable market data returned for symbols: {', '.join(symbols)}")

    data = pd.concat(frames)
    data = data.reset_index()
    data.columns = [str(column).strip().lower().replace(" ", "_") for column in data.columns]

    if "date" not in data.columns and "datetime" in data.columns:
        data = data.rename(columns={"datetime": "date"})

    required_columns = {"date", "symbol", "close"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Market data is missing required columns: {missing}")

    data = data.dropna(subset=["close"]).sort_values(["symbol", "date"]).reset_index(drop=True)

    if data.empty:
        raise ValueError("Market data only contains missing close prices.")

    return data
