"""Validated contracts shared by the session 7 workflow interfaces."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RandomForestConfig(BaseModel):
    """Student-configurable model and evaluation settings."""

    n_estimators: int = Field(default=200, ge=50, le=500)
    max_depth: int | None = Field(default=10, ge=3, le=30)
    min_samples_leaf: int = Field(default=2, ge=1, le=10)
    min_samples_split: int = Field(default=4, ge=2, le=20)
    max_features: Literal["sqrt", "log2", 0.5, 1.0] = "sqrt"
    bootstrap: bool = True
    random_state: int = Field(default=42, ge=0, le=9999)
    test_size: float = Field(default=0.2, ge=0.1, le=0.4)


class WorkflowRequest(BaseModel):
    """Input accepted by CLI, Streamlit and the Codex plugin."""

    question: str = Field(min_length=12, max_length=800)
    city: str = Field(default="Pereira", min_length=2)
    segment: str = Field(default="Alto valor", min_length=2)
    discount_options: list[int] = Field(default_factory=lambda: [0, 5, 10, 15, 20])
    model_name: str = "qwen2.5:3b"
    forest: RandomForestConfig = Field(default_factory=RandomForestConfig)

    @field_validator("discount_options")
    @classmethod
    def validate_discounts(cls, values: list[int]) -> list[int]:
        cleaned = sorted(set(values))
        if not cleaned or any(value < 0 or value > 40 for value in cleaned):
            raise ValueError("discount_options must contain values between 0 and 40")
        return cleaned


class ModelMetrics(BaseModel):
    """Metrics exposed to students and downstream agents."""

    train_mae: float
    test_mae: float
    train_r2: float
    test_r2: float
    training_seconds: float
    overfit_gap: float
    feature_importance: dict[str, float]


class ScenarioPrediction(BaseModel):
    """One business scenario derived from the predictive model."""

    discount_pct: int
    predicted_uplift_pct: float
    expected_orders: float
    expected_revenue: float
    expected_margin: float
    margin_pct: float


class AgentFinding(BaseModel):
    """Structured result produced by one specialist agent."""

    agent_name: str
    role: str
    status: Literal["completed", "degraded", "failed"] = "completed"
    summary: str
    evidence_sources: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0


class ReviewDecision(BaseModel):
    """Quality gate result."""

    approved: bool
    issues: list[str] = Field(default_factory=list)
    revision_instructions: str = ""


class TraceEvent(BaseModel):
    """Observable workflow event."""

    stage: str
    status: str
    detail: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    elapsed_seconds: float = 0.0


class WorkflowResult(BaseModel):
    """Complete result persisted and consumed by all interfaces."""

    run_id: str
    request: WorkflowRequest
    supervisor_plan: list[str]
    metrics: ModelMetrics
    scenarios: list[ScenarioPrediction]
    findings: list[AgentFinding]
    review: ReviewDecision
    recommendation: str
    report_markdown: str
    sources: list[str]
    trace: list[TraceEvent]


class FollowUpAnswer(BaseModel):
    """Grounded response about a completed workflow run."""

    answer: str
    citations: list[str] = Field(default_factory=list)
