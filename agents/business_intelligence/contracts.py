from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class QueryFilters(BaseModel):
    region: str | None = None
    seller: str | None = None
    customer: str | None = None


class BIQueryRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    start_date: str | None = None
    end_date: str | None = None
    filters: QueryFilters = Field(default_factory=QueryFilters)
    max_rows: int = Field(default=200, ge=1, le=500)


class ExplainRequest(BaseModel):
    title: str
    metrics: dict[str, float]
    context: str | None = None


class TraceEvent(BaseModel):
    agent: str
    status: Literal["completed", "rejected", "degraded", "failed"]
    detail: str
    elapsed_ms: float = 0


class KPIValue(BaseModel):
    name: str
    label: str
    value: float
    unit: str


class BIQueryResult(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    question: str
    intent: str
    sql: str
    parameters: dict[str, Any]
    columns: list[str]
    rows: list[dict[str, Any]]
    kpis: list[KPIValue]
    chart: dict[str, Any]
    executive_summary: str
    evidence: list[str]
    warnings: list[str] = Field(default_factory=list)
    review_approved: bool
    traces: list[TraceEvent]
