from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    customer_id: str
    segment: Literal["nuevo", "frecuente", "alto_valor", "en_riesgo"]
    preferred_channel: Literal["email", "app", "whatsapp", "call_center"]
    category_affinity: set[str] = Field(default_factory=set)
    expected_order_value: float = Field(ge=0)
    contact_allowed: bool = True
    vulnerable_customer: bool = False


class CandidateAction(BaseModel):
    action_id: str
    label: str
    channel: Literal["email", "app", "whatsapp", "call_center"]
    category: str
    eligible_segments: set[str]
    incentive_cost: float = Field(ge=0)
    expected_conversion: float = Field(ge=0, le=1)
    operational_risk: float = Field(ge=0, le=1)
    requires_human_approval: bool = False


class RecommendationRequest(BaseModel):
    customer: CustomerProfile
    candidates: list[CandidateAction]
    top_k: int = Field(default=3, ge=1, le=10)
    max_operational_risk: float = Field(default=0.7, ge=0, le=1)


class Recommendation(BaseModel):
    rank: int
    action_id: str
    label: str
    score: float
    expected_value: float
    factors: dict[str, float]
    explanation: str
    requires_human_approval: bool


class RecommendationResult(BaseModel):
    customer_id: str
    recommendations: list[Recommendation]
    excluded: dict[str, str]
    policy_version: str = "session9-v1"

