from agents.domain_recommender import (
    CandidateAction,
    CustomerProfile,
    RecommendationEngine,
    RecommendationRequest,
)


def action(action_id: str, **overrides) -> CandidateAction:
    values = {
        "action_id": action_id,
        "label": action_id,
        "channel": "app",
        "category": "hogar",
        "eligible_segments": {"alto_valor"},
        "incentive_cost": 10,
        "expected_conversion": 0.4,
        "operational_risk": 0.2,
    }
    values.update(overrides)
    return CandidateAction(**values)


def customer(**overrides) -> CustomerProfile:
    values = {
        "customer_id": "C001",
        "segment": "alto_valor",
        "preferred_channel": "app",
        "category_affinity": {"hogar"},
        "expected_order_value": 100,
    }
    values.update(overrides)
    return CustomerProfile(**values)


def test_ranking_is_reproducible_and_explainable() -> None:
    request = RecommendationRequest(
        customer=customer(),
        candidates=[
            action("B", expected_conversion=0.2),
            action("A", expected_conversion=0.5),
        ],
        top_k=2,
    )
    first = RecommendationEngine().recommend(request)
    second = RecommendationEngine().recommend(request)
    assert [item.action_id for item in first.recommendations] == ["A", "B"]
    assert first == second
    assert set(first.recommendations[0].factors) == {
        "category_affinity",
        "channel_match",
        "expected_value",
        "operational_safety",
    }


def test_policy_gates_exclude_ineligible_and_risky_actions() -> None:
    result = RecommendationEngine().recommend(
        RecommendationRequest(
            customer=customer(),
            candidates=[
                action("segment", eligible_segments={"nuevo"}),
                action("risk", operational_risk=0.9),
            ],
        )
    )
    assert not result.recommendations
    assert set(result.excluded) == {"segment", "risk"}


def test_no_contact_excludes_every_action_and_vulnerability_requires_review() -> None:
    blocked = RecommendationEngine().recommend(
        RecommendationRequest(customer=customer(contact_allowed=False), candidates=[action("A")])
    )
    assert blocked.excluded["A"].startswith("El cliente no autorizó")

    reviewed = RecommendationEngine().recommend(
        RecommendationRequest(customer=customer(vulnerable_customer=True), candidates=[action("A")])
    )
    assert reviewed.recommendations[0].requires_human_approval


def test_ties_use_stable_action_identifier_order() -> None:
    result = RecommendationEngine().recommend(
        RecommendationRequest(customer=customer(), candidates=[action("Z"), action("A")])
    )
    assert [item.action_id for item in result.recommendations] == ["A", "Z"]
