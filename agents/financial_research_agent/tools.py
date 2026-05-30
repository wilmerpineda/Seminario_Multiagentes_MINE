"""Financial tools for the Financial Research Agent.

This module defines executable tools that the agent can use to retrieve market
data, compute metrics, generate charts, and compare financial assets.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


TRADING_DAYS_PER_YEAR = 252
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


@dataclass(frozen=True)
class Tool:
    """Representation of an executable tool."""

    name: str
    description: str
    function: Callable[..., Any]


class ToolRegistry:
    """Registry of tools available to the financial research agent."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {
            "get_stock_data": Tool(
                name="get_stock_data",
                description="Download recent historical OHLCV data from Yahoo Finance.",
                function=get_stock_data,
            ),
            "compute_stock_metrics": Tool(
                name="compute_stock_metrics",
                description="Compute return, volatility and drawdown metrics for one stock or ETF.",
                function=compute_stock_metrics,
            ),
            "plot_price_history": Tool(
                name="plot_price_history",
                description="Generate a price history chart for one stock or ETF.",
                function=plot_price_history,
            ),
            "compare_stocks": Tool(
                name="compare_stocks",
                description="Compare multiple stocks or ETFs over the same period.",
                function=compare_stocks,
            ),
        }

    def run(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a registered tool."""

        if tool_name not in self._tools:
            available_tools = ", ".join(sorted(self._tools))
            raise ValueError(
                f"Unknown tool: {tool_name}. Available tools: {available_tools}"
            )

        tool = self._tools[tool_name]
        normalized_arguments = normalize_tool_arguments(tool_name, arguments)
        return tool.function(**normalized_arguments)

    def list_tools(self) -> list[str]:
        """Return names of available tools."""

        return list(self._tools.keys())

    def describe_tools(self) -> list[dict[str, str]]:
        """Return tool metadata for the planning prompt."""

        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]


def get_stock_data(ticker: str, period: str = "1y") -> dict[str, Any]:
    """Download historical stock data from Yahoo Finance."""

    clean_ticker = clean_symbol(ticker)
    data = download_price_data(clean_ticker, period)
    close = get_close_series(data)
    data = data.reset_index()

    return {
        "ticker": clean_ticker,
        "period": period,
        "rows": int(len(data)),
        "start_date": str(close.index.min().date()),
        "end_date": str(close.index.max().date()),
        "last_close": round(float(close.iloc[-1]), 2),
        "last_rows": data.tail(5).to_dict(orient="records"),
    }


def compute_stock_metrics(ticker: str, period: str = "1y") -> dict[str, Any]:
    """Compute key financial metrics for a stock or ETF."""

    clean_ticker = clean_symbol(ticker)
    data = download_price_data(clean_ticker, period)
    close = get_close_series(data)
    daily_returns = close.pct_change().dropna()

    cumulative_return = (close.iloc[-1] / close.iloc[0]) - 1
    annualized_volatility = daily_returns.std() * (TRADING_DAYS_PER_YEAR**0.5)
    running_max = close.cummax()
    drawdown = (close / running_max) - 1
    max_drawdown = drawdown.min()

    return {
        "ticker": clean_ticker,
        "period": period,
        "start_date": str(close.index.min().date()),
        "end_date": str(close.index.max().date()),
        "last_close": round(float(close.iloc[-1]), 2),
        "cumulative_return_pct": round(float(cumulative_return * 100), 2),
        "annualized_volatility_pct": round(float(annualized_volatility * 100), 2),
        "max_drawdown_pct": round(float(max_drawdown * 100), 2),
        "observations": int(close.shape[0]),
    }


def plot_price_history(
    ticker: str,
    period: str = "1y",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Generate a price history chart for a stock or ETF."""

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("matplotlib is required to generate charts.") from exc

    clean_ticker = clean_symbol(ticker)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data = download_price_data(clean_ticker, period)
    close = get_close_series(data)

    chart_path = output_path / f"{clean_ticker.lower()}_{period}_price_history.png"

    plt.figure(figsize=(10, 5))
    plt.plot(close.index, close.values)
    plt.title(f"{clean_ticker} price history ({period})")
    plt.xlabel("Date")
    plt.ylabel("Adjusted close price")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150)
    plt.close()

    return {
        "ticker": clean_ticker,
        "period": period,
        "chart_path": str(chart_path),
        "start_date": str(close.index.min().date()),
        "end_date": str(close.index.max().date()),
    }


def compare_stocks(
    tickers: list[str],
    period: str = "1y",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Compare multiple stocks or ETFs over the same period."""

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("matplotlib is required to generate charts.") from exc

    if len(tickers) < 2:
        raise ValueError("At least two tickers are required for comparison.")

    clean_tickers = [clean_symbol(ticker) for ticker in tickers]
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    prices: dict[str, pd.Series] = {}
    metrics: list[dict[str, Any]] = []

    for ticker in clean_tickers:
        data = download_price_data(ticker, period)
        close = get_close_series(data)
        prices[ticker] = close

        daily_returns = close.pct_change().dropna()
        cumulative_return = (close.iloc[-1] / close.iloc[0]) - 1
        annualized_volatility = daily_returns.std() * (TRADING_DAYS_PER_YEAR**0.5)
        running_max = close.cummax()
        drawdown = (close / running_max) - 1
        max_drawdown = drawdown.min()

        metrics.append(
            {
                "ticker": ticker,
                "last_close": round(float(close.iloc[-1]), 2),
                "cumulative_return_pct": round(float(cumulative_return * 100), 2),
                "annualized_volatility_pct": round(float(annualized_volatility * 100), 2),
                "max_drawdown_pct": round(float(max_drawdown * 100), 2),
            }
        )

    normalized_prices = pd.DataFrame(
        {ticker: series / series.iloc[0] * 100 for ticker, series in prices.items()}
    )
    chart_path = output_path / f"{'_'.join(clean_tickers).lower()}_{period}_comparison.png"

    plt.figure(figsize=(10, 5))
    for ticker in clean_tickers:
        plt.plot(normalized_prices.index, normalized_prices[ticker], label=ticker)
    plt.title(f"Normalized stock performance comparison ({period})")
    plt.xlabel("Date")
    plt.ylabel("Normalized price index")
    plt.legend()
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150)
    plt.close()

    return {
        "tickers": clean_tickers,
        "period": period,
        "metrics": metrics,
        "chart_path": str(chart_path),
        "start_date": str(normalized_prices.index.min().date()),
        "end_date": str(normalized_prices.index.max().date()),
    }


def download_price_data(ticker: str, period: str) -> pd.DataFrame:
    """Download adjusted price data for a ticker."""

    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("yfinance is required to download market data.") from exc

    data = yf.download(
        ticker,
        period=normalize_period(period),
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise ValueError(f"No market data found for ticker: {ticker}")

    return data


def get_close_series(data: pd.DataFrame) -> pd.Series:
    """Return a clean close-price series from yfinance output."""

    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()
    if close.empty:
        raise ValueError("No close prices found in market data.")

    return close


def clean_symbol(symbol: str) -> str:
    """Normalize one stock or ETF symbol."""

    clean_value = symbol.upper().strip()
    if not clean_value:
        raise ValueError("Ticker symbol cannot be empty.")

    return clean_value


def normalize_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Normalize common LLM argument aliases before tool execution."""

    normalized = dict(arguments)

    if tool_name == "compare_stocks":
        if "tickers" not in normalized and "symbols" in normalized:
            normalized["tickers"] = normalized.pop("symbols")
        if "tickers" not in normalized and "ticker" in normalized:
            normalized["tickers"] = [normalized.pop("ticker")]

    if tool_name in {"get_stock_data", "compute_stock_metrics", "plot_price_history"}:
        if "ticker" not in normalized and "symbol" in normalized:
            normalized["ticker"] = normalized.pop("symbol")

    if "period" in normalized and isinstance(normalized["period"], str):
        normalized["period"] = normalize_period(normalized["period"])

    return normalized


def normalize_period(period: str) -> str:
    """Normalize yfinance period values emitted by the LLM."""

    return period.strip().lower()
