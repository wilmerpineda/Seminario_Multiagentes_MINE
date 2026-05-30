"""Plotting utilities for the Financial Research Agent."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def create_research_plots(
    market_data: pd.DataFrame,
    output_dir: str | Path = Path(__file__).resolve().parent / "outputs",
) -> dict[str, str]:
    """Create standard financial research charts and return their paths."""

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required to generate visualizations. Install it with "
            "Poetry or pip before running this tool."
        ) from exc

    validate_market_data(market_data)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    paths = {
        "normalized_prices": str(output_path / "normalized_prices.png"),
        "drawdowns": str(output_path / "drawdowns.png"),
        "daily_returns": str(output_path / "daily_returns.png"),
    }

    plt.figure(figsize=(10, 5))
    for symbol, symbol_data in market_data.groupby("symbol"):
        prices = symbol_data.sort_values("date")["close"].astype(float)
        normalized_prices = prices / prices.iloc[0] * 100
        plt.plot(symbol_data.sort_values("date")["date"], normalized_prices, label=symbol)
    plt.title("Normalized price performance")
    plt.xlabel("Date")
    plt.ylabel("Index value (start = 100)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths["normalized_prices"], dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    for symbol, symbol_data in market_data.groupby("symbol"):
        sorted_data = symbol_data.sort_values("date")
        drawdown = compute_drawdown(sorted_data["close"].astype(float))
        plt.plot(sorted_data["date"], drawdown * 100, label=symbol)
    plt.title("Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths["drawdowns"], dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    for symbol, symbol_data in market_data.groupby("symbol"):
        returns = symbol_data.sort_values("date")["close"].astype(float).pct_change().dropna()
        plt.hist(returns * 100, bins=30, alpha=0.45, label=symbol)
    plt.title("Daily return distribution")
    plt.xlabel("Daily return (%)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths["daily_returns"], dpi=150)
    plt.close()

    return paths


def compute_drawdown(prices: pd.Series) -> pd.Series:
    """Compute drawdown from a price series."""

    running_max = prices.cummax()
    return prices / running_max - 1


def validate_market_data(market_data: pd.DataFrame) -> None:
    """Validate the minimum schema required by plotting tools."""

    required_columns = {"date", "symbol", "close"}
    missing_columns = required_columns.difference(market_data.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Market data is missing required columns: {missing}")

    if market_data.empty:
        raise ValueError("Market data cannot be empty.")
