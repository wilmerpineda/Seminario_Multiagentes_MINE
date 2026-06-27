from __future__ import annotations

import json

import pandas as pd
import pytest
from pydantic import ValidationError

from agents.intelligent_workflow.analytics import (
    generate_campaign_data,
    simulate_discount_scenarios,
    train_discount_model,
)
from agents.intelligent_workflow.contracts import RandomForestConfig, WorkflowRequest
from agents.intelligent_workflow.workflow import IntelligentWorkflow


class FakeStructuredLLM:
    def chat(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
        properties = schema.get("properties", {})
        if "tasks" in properties:
            return json.dumps({"tasks": ["Calcular escenarios", "Revisar politicas", "Evaluar riesgo"]})
        if "selected_discount_pct" in properties:
            return json.dumps(
                {
                    "selected_discount_pct": 10,
                    "rationale": "Este escenario equilibra demanda, margen y riesgo.",
                    "controls": ["Piloto controlado", "Aprobacion humana"],
                }
            )
        if "approved" in properties:
            return json.dumps({"approved": True, "issues": [], "revision_instructions": ""})
        if "answer" in properties:
            return json.dumps({"answer": "El reporte recomienda un piloto controlado.", "citations": ["politica_descuentos_2026.md"]})
        if "Policy Analyst" in system_prompt:
            sources = ["politica_descuentos_2026.md"]
        elif "Operations Risk Analyst" in system_prompt:
            sources = ["acta_comite_logistica_q3_2026.md"]
        else:
            sources = ["session7_discount_campaigns.csv", "RandomForestRegressor"]
        return json.dumps({"summary": "Hallazgo validado por el agente.", "evidence_sources": sources, "risks": ["Validar en un piloto."]})


@pytest.fixture(scope="module")
def campaign_data(tmp_path_factory) -> pd.DataFrame:
    path = tmp_path_factory.mktemp("session7") / "campaigns.csv"
    return generate_campaign_data(path, rows=500, seed=17)


def test_random_forest_config_rejects_unsafe_values() -> None:
    with pytest.raises(ValidationError):
        RandomForestConfig(n_estimators=10)


def test_model_training_is_reproducible(campaign_data: pd.DataFrame) -> None:
    config = RandomForestConfig(n_estimators=50, random_state=7)
    first = train_discount_model(campaign_data, config)
    second = train_discount_model(campaign_data, config)

    assert first.metrics.test_mae == second.metrics.test_mae
    assert first.metrics.test_r2 == second.metrics.test_r2
    assert first.metrics.feature_importance


def test_scenarios_apply_discount_to_revenue(campaign_data: pd.DataFrame) -> None:
    bundle = train_discount_model(campaign_data, RandomForestConfig(n_estimators=50))
    scenarios = simulate_discount_scenarios(campaign_data, bundle, "Pereira", "Alto valor", [0, 20])

    assert [item.discount_pct for item in scenarios] == [0, 20]
    assert scenarios[0].expected_revenue > scenarios[1].expected_revenue
    assert all(item.expected_margin < item.expected_revenue for item in scenarios)


def test_workflow_runs_supervisor_parallel_roles_and_reviewer(campaign_data: pd.DataFrame) -> None:
    bundle = train_discount_model(campaign_data, RandomForestConfig(n_estimators=50))
    workflow = IntelligentWorkflow(llm=FakeStructuredLLM())
    request = WorkflowRequest(
        question="Que descuento debe probar NovaRetail sin deteriorar su margen?",
        discount_options=[0, 10, 20],
        forest=RandomForestConfig(n_estimators=50),
    )

    result = workflow.run(request, model_bundle=bundle)

    assert result.review.approved
    assert {item.agent_name for item in result.findings} == {
        "Data Analyst",
        "Operations Risk Analyst",
        "Policy Analyst",
    }
    assert len(result.sources) >= 3
    assert any(event.stage == "reviewer" for event in result.trace)
    assert "Fuentes" in result.report_markdown
    selected = next(item for item in result.scenarios if item.discount_pct == 10)
    assert f"${selected.expected_margin:,.0f}" in result.report_markdown


def test_follow_up_uses_a_completed_result(campaign_data: pd.DataFrame) -> None:
    bundle = train_discount_model(campaign_data, RandomForestConfig(n_estimators=50))
    workflow = IntelligentWorkflow(llm=FakeStructuredLLM())
    result = workflow.run(
        WorkflowRequest(question="Que escenario de descuento protege mejor el margen?", forest=RandomForestConfig(n_estimators=50)),
        model_bundle=bundle,
    )

    answer = workflow.answer_follow_up(result, "Que control se recomienda?")

    assert "piloto" in answer.answer.lower()
    assert answer.citations == ["politica_descuentos_2026.md"]
