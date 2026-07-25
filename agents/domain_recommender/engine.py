from __future__ import annotations

from .contracts import (
    CandidateAction,
    Recommendation,
    RecommendationRequest,
    RecommendationResult,
)


class RecommendationEngine:
    """Auditable next-best-action ranking with explicit policy gates."""

    def recommend(self, request: RecommendationRequest) -> RecommendationResult:
        customer = request.customer
        excluded: dict[str, str] = {}
        scored: list[tuple[CandidateAction, float, float, dict[str, float]]] = []

        for action in request.candidates:
            reason = self._exclusion_reason(request, action)
            if reason:
                excluded[action.action_id] = reason
                continue

            expected_value = customer.expected_order_value * action.expected_conversion - action.incentive_cost
            affinity = 1.0 if action.category in customer.category_affinity else 0.35
            channel_match = 1.0 if action.channel == customer.preferred_channel else 0.5
            value_score = max(-1.0, min(1.0, expected_value / max(customer.expected_order_value, 1.0)))
            safety = 1.0 - action.operational_risk
            factors = {
                "category_affinity": affinity,
                "channel_match": channel_match,
                "expected_value": value_score,
                "operational_safety": safety,
            }
            score = 0.30 * affinity + 0.20 * channel_match + 0.35 * value_score + 0.15 * safety
            scored.append((action, score, expected_value, factors))

        scored.sort(key=lambda item: (-item[1], item[0].action_id))
        recommendations = [
            Recommendation(
                rank=index,
                action_id=action.action_id,
                label=action.label,
                score=round(score, 4),
                expected_value=round(expected_value, 2),
                factors={name: round(value, 4) for name, value in factors.items()},
                explanation=self._explain(action, factors, expected_value),
                requires_human_approval=action.requires_human_approval or customer.vulnerable_customer,
            )
            for index, (action, score, expected_value, factors) in enumerate(
                scored[: request.top_k], start=1
            )
        ]
        return RecommendationResult(
            customer_id=customer.customer_id,
            recommendations=recommendations,
            excluded=excluded,
        )

    @staticmethod
    def _exclusion_reason(
        request: RecommendationRequest, action: CandidateAction
    ) -> str | None:
        customer = request.customer
        if not customer.contact_allowed:
            return "El cliente no autorizó comunicaciones comerciales."
        if customer.segment not in action.eligible_segments:
            return "El segmento no cumple la regla de elegibilidad."
        if action.operational_risk > request.max_operational_risk:
            return "El riesgo operativo supera el límite permitido."
        return None

    @staticmethod
    def _explain(
        action: CandidateAction, factors: dict[str, float], expected_value: float
    ) -> str:
        affinity = "alta" if factors["category_affinity"] >= 0.8 else "parcial"
        channel = "preferido" if factors["channel_match"] >= 0.8 else "alternativo"
        return (
            f"Afinidad {affinity}, canal {channel}, valor esperado "
            f"{expected_value:,.0f} y riesgo operativo {action.operational_risk:.0%}."
        )
