"""Metric utilities for the Experiment Analyst Agent.

This module computes descriptive metrics from the activation experiment dataset.
The resulting summaries are later transformed into factual context for the LLM
agent.
"""

from __future__ import annotations

import pandas as pd


def compute_activation_rate(data: pd.DataFrame) -> float:
    """Compute the overall activation rate.

    Args:
        data: Activation experiment DataFrame.

    Returns:
        Activation rate as a proportion between 0 and 1.

    Raises:
        ValueError: If the DataFrame is empty.
    """

    if data.empty:
        raise ValueError("Cannot compute activation rate from an empty DataFrame.")

    return float(data["Activo"].mean())


def compute_activation_rate_by_group(
    data: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    """Compute activation rate by a grouping column.

    Args:
        data: Activation experiment DataFrame.
        group_column: Column used to group observations.

    Returns:
        DataFrame with users, activations and activation rate by group.

    Raises:
        ValueError: If the grouping column does not exist.
    """

    if group_column not in data.columns:
        raise ValueError(f"Column not found in dataset: {group_column}")

    summary = (
        data.groupby(group_column, dropna=False)
        .agg(
            users=("Id", "nunique"),
            activations=("Activo", "sum"),
            activation_rate=("Activo", "mean"),
        )
        .reset_index()
        .sort_values("activation_rate", ascending=False)
    )

    return summary


def compute_activation_rate_by_experiment(data: pd.DataFrame) -> pd.DataFrame:
    """Compute activation rate by experiment.

    Args:
        data: Activation experiment DataFrame.

    Returns:
        DataFrame with activation metrics by experiment.
    """

    return compute_activation_rate_by_group(
        data=data,
        group_column="Experimento",
    )


def compute_segment_analysis(data: pd.DataFrame) -> pd.DataFrame:
    """Compute activation rate by experiment and segment.

    Args:
        data: Activation experiment DataFrame.

    Returns:
        DataFrame with activation metrics by experiment and segment.
    """

    return compute_activation_rate_by_multiple_groups(
        data=data,
        group_columns=["Experimento", "Segmento"],
    )


def compute_activation_rate_by_multiple_groups(
    data: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    """Compute activation rate by multiple grouping columns.

    Args:
        data: Activation experiment DataFrame.
        group_columns: Columns used to group observations.

    Returns:
        DataFrame with users, activations and activation rate by groups.

    Raises:
        ValueError: If any grouping column does not exist.
    """

    missing_columns = [column for column in group_columns if column not in data.columns]

    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Columns not found in dataset: {missing}")

    summary = (
        data.groupby(group_columns, dropna=False)
        .agg(
            users=("Id", "nunique"),
            activations=("Activo", "sum"),
            activation_rate=("Activo", "mean"),
        )
        .reset_index()
        .sort_values("activation_rate", ascending=False)
    )

    return summary


def compute_experiment_gap(data: pd.DataFrame) -> pd.DataFrame:
    """Compute activation rate gap between experiments.

    Args:
        data: Activation experiment DataFrame.

    Returns:
        DataFrame with activation rate by experiment and difference against
        the best performing experiment.
    """

    summary = compute_activation_rate_by_experiment(data)

    best_rate = summary["activation_rate"].max()

    summary["gap_vs_best"] = summary["activation_rate"] - best_rate
    summary["gap_vs_best_pp"] = summary["gap_vs_best"] * 100

    return summary


def format_rate(value: float) -> str:
    """Format a proportion as percentage.

    Args:
        value: Numeric proportion between 0 and 1.

    Returns:
        Percentage string with two decimal places.
    """

    return f"{value * 100:.2f}%"


def format_metric_table(data: pd.DataFrame) -> str:
    """Format a metric DataFrame as a markdown table.

    Args:
        data: DataFrame with computed metrics.

    Returns:
        Markdown-formatted table.
    """

    formatted_data = data.copy()

    for column in formatted_data.columns:
        if "rate" in column or "gap" in column:
            formatted_data[column] = formatted_data[column].apply(
                lambda value: format_rate(float(value)) if pd.notna(value) else value
            )

    return formatted_data.to_markdown(index=False)