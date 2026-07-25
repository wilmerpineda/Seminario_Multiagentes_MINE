from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


RiskCategory = Literal[
    "data",
    "bias",
    "model",
    "rag",
    "multiagent",
    "security",
    "privacy",
    "human",
    "operations",
    "cost",
]


class CohortDefinition(BaseModel):
    name: str
    dimensions: dict[str, str] = Field(default_factory=dict)


class EvaluationCase(BaseModel):
    case_id: str
    title: str
    question: str
    category: RiskCategory
    expected_intent: str | None = None
    expected_min_rows: int = 0
    expected_refusal: bool = False
    prohibited_terms: list[str] = Field(default_factory=list)
    cohort: CohortDefinition | None = None
    tags: set[str] = Field(default_factory=set)
    filters: dict[str, str] = Field(default_factory=dict)


class ObservedResponse(BaseModel):
    case_id: str
    status: Literal["completed", "refused", "failed"]
    intent: str | None = None
    summary: str = ""
    rows: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    traces: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0
    error: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class MetricResult(BaseModel):
    metric: str
    passed: bool
    score: float = Field(ge=0, le=1)
    detail: str
    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"


class CaseResult(BaseModel):
    case: EvaluationCase
    response: ObservedResponse
    metrics: list[MetricResult]

    @property
    def passed(self) -> bool:
        return all(metric.passed for metric in self.metrics)


class CostEstimate(BaseModel):
    currency: str = "USD"
    input_tokens: int = 0
    output_tokens: int = 0
    model_calls: int = 0
    estimated_cost: float = 0
    budget: float = 0
    budget_exceeded: bool = False
    pricing_source: str = "Valores configurables para el laboratorio; no representan una tarifa vigente."


class EvaluationRun(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    system_name: str
    results: list[CaseResult]
    aggregate_scores: dict[str, float]
    cohort_scores: dict[str, float]
    worst_cohort: str | None = None
    disparity_gap: float = 0
    cost: CostEstimate


class ControlRecord(BaseModel):
    control_id: str
    name: str
    kind: Literal["preventive", "detective", "corrective"]
    lifecycle_stage: Literal[
        "data",
        "design",
        "build",
        "predeployment",
        "runtime",
        "incident_response",
    ]
    owner: str
    evidence: str


class RiskRecord(BaseModel):
    risk_id: str
    category: RiskCategory
    scenario: str
    affected_groups: str
    signal: str
    controls: list[str]
    residual_risk: Literal["low", "medium", "high", "critical"]
    decision_owner: str
    review_frequency: str

