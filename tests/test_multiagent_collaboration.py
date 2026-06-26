from __future__ import annotations

from agents.multiagent_collaboration.agent import (
    ClassroomMultiAgentSystem,
    normalize_terms,
)


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        if "respuesta final" in system_prompt:
            return "Respuesta final: usar descuentos focalizados, no agresivos."
        if "Planner" in system_prompt:
            return "Plan: buscar evidencia, redactar y revisar."
        if "Researcher" in system_prompt:
            return "Hallazgos: hay presion de margen y restricciones logisticas."
        if "Reviewer" in system_prompt:
            return "APROBADO con ajuste: mantener recomendacion condicional."
        return "Borrador: recomendar campana focalizada con fuentes."


def test_normalize_terms_removes_common_stopwords() -> None:
    terms = normalize_terms("Debe lanzar descuentos en ciudades intermedias?")

    assert "debe" not in terms
    assert "descuentos" in terms
    assert "ciudades" in terms


def test_multiagent_system_runs_all_roles_without_ollama() -> None:
    fake_llm = FakeLLM()
    system = ClassroomMultiAgentSystem(llm=fake_llm, top_k=3)

    result = system.answer(
        "Debe NovaRetail lanzar descuentos agresivos en ciudades intermedias?"
    )

    assert len(fake_llm.calls) == 5
    assert len(result.retrieved_evidence) == 3
    assert [step.agent_name for step in result.steps] == [
        "Planner",
        "Researcher",
        "Writer",
        "Reviewer",
        "Final Writer",
    ]
    assert "descuentos focalizados" in result.final_answer.content
