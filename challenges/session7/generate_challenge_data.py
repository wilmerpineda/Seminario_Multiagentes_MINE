"""Generate reproducible synthetic datasets for the two team challenges."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def fraud_data(rows: int = 700, seed: int = 71) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    amount = rng.lognormal(11.2, 0.9, rows).clip(15_000, 8_000_000)
    hour = rng.integers(0, 24, rows)
    device_age = rng.integers(0, 1200, rows)
    attempts = rng.integers(1, 8, rows)
    country_match = rng.choice([0, 1], rows, p=[0.12, 0.88])
    channel = rng.choice(["web", "app", "call_center"], rows, p=[0.5, 0.4, 0.1])
    score = (
        0.00000045 * amount
        + 0.8 * (hour < 5)
        + 0.7 * (device_age < 14)
        + 0.25 * attempts
        + 1.2 * (1 - country_match)
        + rng.normal(0, 0.3, rows)
    )
    fraud = (score > 2.35).astype(int)
    return pd.DataFrame(
        {
            "transaction_id": [f"TX-{index + 1:05d}" for index in range(rows)],
            "amount": amount.round(0),
            "hour": hour,
            "device_age_days": device_age,
            "attempts_24h": attempts,
            "country_match": country_match,
            "channel": channel,
            "is_fraud": fraud,
        }
    )


def churn_data(rows: int = 700, seed: int = 72) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    tenure = rng.integers(1, 73, rows)
    monthly_spend = rng.normal(185_000, 70_000, rows).clip(30_000, 600_000)
    late_deliveries = rng.integers(0, 8, rows)
    support_tickets = rng.integers(0, 10, rows)
    purchases = rng.integers(0, 18, rows)
    segment = rng.choice(["alto_valor", "frecuente", "ocasional"], rows, p=[0.2, 0.45, 0.35])
    score = (
        -0.035 * tenure
        + 0.32 * late_deliveries
        + 0.2 * support_tickets
        - 0.13 * purchases
        + 0.7 * (segment == "ocasional")
        + rng.normal(0, 0.7, rows)
    )
    churn = (score > 0.45).astype(int)
    return pd.DataFrame(
        {
            "customer_id": [f"CL-{index + 1:05d}" for index in range(rows)],
            "tenure_months": tenure,
            "monthly_spend": monthly_spend.round(0),
            "late_deliveries_90d": late_deliveries,
            "support_tickets_90d": support_tickets,
            "purchases_90d": purchases,
            "segment": segment,
            "churned": churn,
        }
    )


def main() -> None:
    fraud_path = ROOT / "fraud" / "transactions.csv"
    churn_path = ROOT / "churn" / "customers.csv"
    fraud_path.parent.mkdir(parents=True, exist_ok=True)
    churn_path.parent.mkdir(parents=True, exist_ok=True)
    fraud_data().to_csv(fraud_path, index=False)
    churn_data().to_csv(churn_path, index=False)
    print(f"Created {fraud_path}")
    print(f"Created {churn_path}")


if __name__ == "__main__":
    main()
