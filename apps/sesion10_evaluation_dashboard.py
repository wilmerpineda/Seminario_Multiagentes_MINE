from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from agents.system_evaluation import (
    DEFAULT_CONTROLS,
    DEFAULT_RISKS,
    EvaluationSuite,
    HttpSession8Adapter,
    InProcessSession8Adapter,
    load_cases,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_FILE = PROJECT_ROOT / "data" / "session10" / "evaluation_cases.jsonl"


def build_adapter(mode: str):
    if mode == "API HTTP":
        return HttpSession8Adapter(
            base_url=os.getenv("BI_API_URL", "http://localhost:8000"),
            api_key=os.getenv("API_KEY", "session8-local-key"),
        )
    return InProcessSession8Adapter()


def result_rows(run) -> list[dict]:
    rows = []
    for result in run.results:
        for metric in result.metrics:
            rows.append(
                {
                    "Caso": result.case.case_id,
                    "Título": result.case.title,
                    "Categoría": result.case.category,
                    "Métrica": metric.metric,
                    "Pasa": metric.passed,
                    "Puntaje": metric.score,
                    "Severidad": metric.severity,
                    "Detalle": metric.detail,
                    "Latencia ms": round(result.response.latency_ms, 2),
                }
            )
    return rows


def governance_package(run) -> dict:
    return {
        "system_card": {
            "name": run.system_name,
            "purpose": "Analítica B2B educativa con datos sintéticos.",
            "prohibited_uses": [
                "Decisiones automáticas irreversibles",
                "Tratamiento de datos personales reales",
                "Inferencias causales sin diseño experimental",
            ],
        },
        "evaluation": run.model_dump(mode="json"),
        "risks": [risk.model_dump(mode="json") for risk in DEFAULT_RISKS],
        "controls": [control.model_dump(mode="json") for control in DEFAULT_CONTROLS],
        "incident_protocol": [
            "Contener o desactivar la capacidad afectada.",
            "Preservar trazas sin ampliar la exposición de datos.",
            "Notificar a responsables de dominio, seguridad y privacidad.",
            "Evaluar impacto por personas y cohortes.",
            "Corregir, reevaluar, documentar y autorizar la reactivación.",
        ],
    }


def main() -> None:
    st.set_page_config(
        page_title="Sesión 10 · Evaluación y gobernanza",
        page_icon="🛡️",
        layout="wide",
    )
    st.title("Evaluación, riesgos y gobernanza de sistemas IA")
    st.caption(
        "Banco reproducible sobre el sistema BI de la sesión 8. Los datos y precios son didácticos."
    )

    cases = load_cases(CASE_FILE)
    with st.sidebar:
        st.header("Configuración")
        mode = st.radio("Sistema bajo prueba", ["En proceso", "API HTTP"])
        categories = st.multiselect(
            "Categorías",
            sorted({case.category for case in cases}),
            default=sorted({case.category for case in cases}),
        )
        input_rate = st.number_input("USD / millón de tokens de entrada", 0.0, 100.0, 0.0)
        output_rate = st.number_input("USD / millón de tokens de salida", 0.0, 100.0, 0.0)
        budget = st.number_input("Presupuesto por suite (USD)", 0.0, 100.0, 0.10)
        execute = st.button("Ejecutar evaluación", type="primary", width="stretch")

    selected = [case for case in cases if case.category in categories]
    if execute:
        suite = EvaluationSuite(
            build_adapter(mode),
            input_cost_per_million=input_rate,
            output_cost_per_million=output_rate,
            budget=budget,
        )
        with st.spinner("Ejecutando casos normales y adversariales..."):
            st.session_state["evaluation_run"] = suite.run(selected)

    run = st.session_state.get("evaluation_run")
    if not run:
        st.info("Seleccione categorías y ejecute la evaluación.")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Caso": case.case_id,
                        "Título": case.title,
                        "Categoría": case.category,
                        "Cohorte": case.cohort.name if case.cohort else "—",
                    }
                    for case in selected
                ]
            ),
            width="stretch",
            hide_index=True,
        )
        return

    passed_cases = sum(result.passed for result in run.results)
    columns = st.columns(5)
    columns[0].metric("Casos aprobados", f"{passed_cases}/{len(run.results)}")
    columns[1].metric("Peor cohorte", run.worst_cohort or "Sin cohortes")
    columns[2].metric("Brecha", f"{run.disparity_gap:.1%}")
    columns[3].metric("Costo estimado", f"USD {run.cost.estimated_cost:.4f}")
    columns[4].metric(
        "Presupuesto", "Excedido" if run.cost.budget_exceeded else "Dentro del límite"
    )

    overview, cohorts, risks, traces = st.tabs(
        ["Resultados", "Cohortes", "Riesgos y controles", "Trazas"]
    )
    frame = pd.DataFrame(result_rows(run))

    with overview:
        st.subheader("Métricas por caso")
        st.dataframe(frame, width="stretch", hide_index=True)
        if run.aggregate_scores:
            st.bar_chart(pd.Series(run.aggregate_scores, name="Puntaje"))

    with cohorts:
        st.subheader("El promedio global no es suficiente")
        if run.cohort_scores:
            cohort_frame = pd.DataFrame(
                [{"Cohorte": name, "Tasa de aprobación": score} for name, score in run.cohort_scores.items()]
            )
            st.dataframe(cohort_frame, width="stretch", hide_index=True)
            st.bar_chart(cohort_frame.set_index("Cohorte"))
        else:
            st.info("Los casos ejecutados no contienen cohortes.")

    with risks:
        st.subheader("Registro de riesgos")
        st.dataframe(
            pd.DataFrame([risk.model_dump() for risk in DEFAULT_RISKS]),
            width="stretch",
            hide_index=True,
        )
        st.subheader("Controles y lugar de aplicación")
        st.dataframe(
            pd.DataFrame([control.model_dump() for control in DEFAULT_CONTROLS]),
            width="stretch",
            hide_index=True,
        )
        package = governance_package(run)
        st.download_button(
            "Descargar paquete de gobernanza",
            json.dumps(package, ensure_ascii=False, indent=2, default=str),
            file_name=f"governance-{run.run_id}.json",
            mime="application/json",
        )

    with traces:
        for result in run.results:
            with st.expander(f"{result.case.case_id} · {result.case.title}"):
                st.write(f"Estado: **{result.response.status}**")
                st.dataframe(
                    pd.DataFrame(result.response.traces),
                    width="stretch",
                    hide_index=True,
                )
                if result.response.error:
                    st.error(result.response.error)


if __name__ == "__main__":
    main()
