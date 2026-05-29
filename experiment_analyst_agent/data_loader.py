"""Data loading utilities for the Experiment Analyst Agent.

This module centralizes the logic used to read the activation experiment
dataset and validate its expected structure.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS: set[str] = {
    "Id",
    "Activo",
    "Segmento",
    "Flujo",
    "SO",
    "Experimento"
}


def load_activations_data(file_path: str | Path) -> pd.DataFrame:
    """Load and validate the activation experiment dataset.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A pandas DataFrame with the activation experiment data.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    data = pd.read_csv(path)

    validate_activations_schema(data)

    return data


def validate_activations_schema(data: pd.DataFrame) -> None:
    """Validate that the activation dataset contains required columns.

    Args:
        data: DataFrame to validate.
,
    Raises:
        ValueError: If one or more required columns are missing.
    """

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")


def get_dataset_summary(data: pd.DataFrame) -> dict[str, int]:
    """Return a simple structural summary of the dataset.

    Args:
        data: Activation experiment DataFrame.

    Returns:
        Dictionary with number of rows, columns and unique users.
    """

    return {
        "rows": data.shape[0],
        "columns": data.shape[1],
        "unique_users": data["Id"].nunique(),
    }