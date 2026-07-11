from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text


DEFAULT_URL = f"sqlite:///{Path(__file__).resolve().parents[2] / 'artifacts' / 'session8.db'}"


class BIDatabase:
    def __init__(self, url: str | None = None):
        use_local_demo = url is None and not os.getenv("DATABASE_URL")
        self.url = url or os.getenv("DATABASE_URL", DEFAULT_URL)
        if self.url.startswith("sqlite:///"):
            Path(self.url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(self.url, pool_pre_ping=True)
        if use_local_demo and self.url.startswith("sqlite"):
            self._ensure_local_demo()

    def _ensure_local_demo(self) -> None:
        """Create an idempotent demo dataset when Docker/PostgreSQL is absent."""
        schema = [
            "CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, period TEXT, region TEXT, seller TEXT, customer TEXT, revenue REAL, cost REAL)",
            "CREATE TABLE IF NOT EXISTS opportunities (id INTEGER PRIMARY KEY, period TEXT, region TEXT, seller TEXT, customer TEXT, status TEXT, cycle_days INTEGER)",
            "CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, period TEXT, region TEXT, actual_revenue REAL, target_revenue REAL)",
            "CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, period TEXT, region TEXT, customer TEXT, balance REAL, payment_status TEXT, due_date TEXT)",
        ]
        regions = [("Andina", "Ana", "Acme SAS"), ("Caribe", "Bruno", "Norte Ltda"), ("Pacífica", "Carla", "Pacífico SA"), ("Centro", "Diego", "Central SAS")]
        with self.engine.begin() as connection:
            for statement in schema:
                connection.execute(text(statement))
            if connection.execute(text("SELECT COUNT(*) FROM sales")).scalar_one():
                return
            identifier = 1
            for month in range(1, 13):
                period = f"2026-{month:02d}-01"
                for offset, (region, seller, customer) in enumerate(regions):
                    revenue = 8_000_000 + month * 320_000 + offset * 450_000
                    params = {"id": identifier, "period": period, "region": region, "seller": seller, "customer": customer}
                    connection.execute(text("INSERT INTO sales VALUES (:id,:period,:region,:seller,:customer,:revenue,:cost)"), {**params, "revenue": revenue, "cost": revenue * (0.58 + offset * 0.02)})
                    connection.execute(text("INSERT INTO opportunities VALUES (:id,:period,:region,:seller,:customer,:status,:days)"), {**params, "status": "won" if (month + offset) % 3 else "lost", "days": 20 + month + offset})
                    connection.execute(text("INSERT INTO goals VALUES (:id,:period,:region,:actual,:target)"), {"id": identifier, "period": period, "region": region, "actual": revenue, "target": 11_000_000})
                    connection.execute(text("INSERT INTO payments VALUES (:id,:period,:region,:customer,:balance,:status,:due)"), {"id": identifier, "period": period, "region": region, "customer": customer, "balance": 900_000 + offset * 250_000, "status": "overdue" if (month + offset) % 4 == 0 else "paid", "due": period})
                    identifier += 1

    def health(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    def query(self, sql: str, parameters: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
        with self.engine.connect() as connection:
            result = connection.execute(text(sql), parameters)
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result]
        return columns, rows
