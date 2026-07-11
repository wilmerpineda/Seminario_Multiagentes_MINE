from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from agents.business_intelligence.contracts import BIQueryRequest, QueryFilters
from agents.business_intelligence.database import BIDatabase
from agents.business_intelligence.security import UnsafeQuery, validate_read_only_sql
from agents.business_intelligence.workflow import BusinessIntelligenceWorkflow
from apps.sesion8_bi_api import app


def database(tmp_path: Path) -> BIDatabase:
    db = BIDatabase(f"sqlite:///{tmp_path / 'bi.db'}")
    statements = [
        "CREATE TABLE sales (id INTEGER, period TEXT, region TEXT, seller TEXT, customer TEXT, revenue REAL, cost REAL)",
        "CREATE TABLE opportunities (id INTEGER, period TEXT, region TEXT, seller TEXT, customer TEXT, status TEXT, cycle_days INTEGER)",
        "CREATE TABLE goals (id INTEGER, period TEXT, region TEXT, actual_revenue REAL, target_revenue REAL)",
        "CREATE TABLE payments (id INTEGER, period TEXT, region TEXT, customer TEXT, balance REAL, payment_status TEXT, due_date TEXT)",
        "INSERT INTO sales VALUES (1,'2026-01-01','Andina','Ana','Acme',100,60),(2,'2026-02-01','Andina','Ana','Acme',120,65)",
        "INSERT INTO opportunities VALUES (1,'2026-01-01','Andina','Ana','Acme','won',20),(2,'2026-01-01','Andina','Ana','Acme','lost',30)",
        "INSERT INTO goals VALUES (1,'2026-01-01','Andina',90,100)",
        "INSERT INTO payments VALUES (1,'2026-01-01','Andina','Acme',40,'overdue','2026-02-01')",
    ]
    with db.engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    return db


def test_revenue_workflow_is_auditable(tmp_path: Path) -> None:
    workflow = BusinessIntelligenceWorkflow(database(tmp_path))
    result = workflow.run(BIQueryRequest(question="¿Cómo evolucionaron los ingresos?", filters=QueryFilters(region="Andina")))
    assert result.kpis[0].value == 220
    assert result.review_approved
    assert "LIMIT 200" in result.sql
    assert {trace.agent for trace in result.traces} >= {"supervisor", "sql_agent", "sql_security_reviewer", "insight_agent", "quality_reviewer"}
    assert workflow.get_run(result.run_id).run_id == result.run_id


def test_other_intents_and_unsupported_filter(tmp_path: Path) -> None:
    workflow = BusinessIntelligenceWorkflow(database(tmp_path))
    conversion = workflow.run(BIQueryRequest(question="¿Cuál es la conversión?"))
    margin = workflow.run(BIQueryRequest(question="Analiza el margen"))
    goals = workflow.run(BIQueryRequest(question="Cumplimiento de meta", filters=QueryFilters(customer="ignored")))
    overdue = workflow.run(BIQueryRequest(question="Cartera vencida"))
    assert conversion.kpis[0].value == 50
    assert round(margin.kpis[0].value, 2) == 42.91
    assert goals.kpis[0].value == 90
    assert overdue.kpis[0].value == 40


def test_sql_guard_rejects_mutations() -> None:
    for sql in ("DELETE FROM sales", "SELECT * FROM secrets", "SELECT * FROM sales; DROP TABLE sales", "SELECT * FROM sales -- bypass", "SELECT * FROM sales LIMIT 9999"):
        try:
            validate_read_only_sql(sql)
        except UnsafeQuery:
            pass
        else:
            raise AssertionError(sql)
    assert validate_read_only_sql("WITH totals AS (SELECT * FROM sales) SELECT * FROM totals").endswith("LIMIT 500")


def test_api_key() -> None:
    client = TestClient(app)
    assert client.get("/openapi.json").json()["openapi"] == "3.0.3"
    assert client.get("/docs").status_code == 200
    assert client.get("/v1/metadata/kpis").status_code == 401
    assert client.get("/v1/metadata/kpis", headers={"X-API-Key": "session8-local-key"}).status_code == 200
