"""Streamlit control surface for the session 7 intelligent workflow."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.intelligent_workflow import IntelligentWorkflow, RandomForestConfig, WorkflowRequest
from agents.intelligent_workflow.analytics import DEFAULT_CAMPAIGN_DATA, load_campaign_data, train_discount_model


DEFAULT_QUESTION = "Que descuento debe probar NovaRetail en clientes de alto valor sin deteriorar el margen?"
BASELINE_CONFIG = RandomForestConfig()


@st.cache_resource(show_spinner=False)
def cached_model(config_json: str, data_version: float):
    del data_version
    config = RandomForestConfig.model_validate_json(config_json)
    return train_discount_model(load_campaign_data(), config)


def money(value: float) -> str:
    return f"${value / 1_000_000:,.1f} M"


def render_configuration() -> tuple[WorkflowRequest, bool]:
    data = load_campaign_data()
    with st.sidebar:
        st.header("Configuracion")
        model_name = st.text_input("Modelo Ollama", value="qwen2.5:3b")
        city = st.selectbox("Ciudad", sorted(data["city"].unique()))
        segment = st.selectbox("Segmento", sorted(data["segment"].unique()))
        discounts = st.multiselect("Escenarios de descuento", [0, 5, 10, 15, 20, 25, 30], default=[0, 5, 10, 15, 20])

        st.subheader("Random Forest")
        n_estimators = st.slider("Numero de arboles", 50, 500, 200, 50)
        depth_label = st.select_slider("Profundidad maxima", options=["Sin limite", "5", "10", "20", "30"], value="10")
        min_samples_leaf = st.slider("Minimo por hoja", 1, 10, 2)

        with st.expander("Parametros avanzados"):
            min_samples_split = st.slider("Minimo para dividir", 2, 20, 4)
            feature_label = st.selectbox("Variables por division", ["sqrt", "log2", "50%", "100%"])
            bootstrap = st.toggle("Bootstrap", value=True)
            random_state = st.number_input("Semilla", 0, 9999, 42)
            test_size = st.slider("Proporcion de prueba", 0.1, 0.4, 0.2, 0.05)

        run_clicked = st.button("Entrenar y ejecutar", type="primary", use_container_width=True, icon=":material/play_arrow:")

    max_features = {"sqrt": "sqrt", "log2": "log2", "50%": 0.5, "100%": 1.0}[feature_label]
    request = WorkflowRequest(
        question=st.session_state.get("business_question", DEFAULT_QUESTION),
        city=city,
        segment=segment,
        discount_options=discounts or [0, 5, 10, 15, 20],
        model_name=model_name,
        forest=RandomForestConfig(
            n_estimators=n_estimators,
            max_depth=None if depth_label == "Sin limite" else int(depth_label),
            min_samples_leaf=min_samples_leaf,
            min_samples_split=min_samples_split,
            max_features=max_features,
            bootstrap=bootstrap,
            random_state=int(random_state),
            test_size=test_size,
        ),
    )
    return request, run_clicked


def render_metrics(result) -> None:
    metrics = result.metrics
    columns = st.columns(4)
    columns[0].metric("MAE prueba", f"{metrics.test_mae:.2f} pp")
    columns[1].metric("R2 prueba", f"{metrics.test_r2:.3f}")
    columns[2].metric("Brecha R2", f"{metrics.overfit_gap:.3f}")
    columns[3].metric("Entrenamiento", f"{metrics.training_seconds:.2f} s")
    if metrics.overfit_gap > 0.15:
        st.warning("La diferencia entre entrenamiento y prueba sugiere posible sobreajuste.")

    scenario_frame = pd.DataFrame([item.model_dump() for item in result.scenarios])
    scenario_frame["expected_revenue"] = scenario_frame["expected_revenue"].map(money)
    scenario_frame["expected_margin"] = scenario_frame["expected_margin"].map(money)
    st.dataframe(scenario_frame, use_container_width=True, hide_index=True)

    baseline = cached_model(BASELINE_CONFIG.model_dump_json(), DEFAULT_CAMPAIGN_DATA.stat().st_mtime)
    comparison = pd.DataFrame(
        [
            {"Configuracion": "Base", "MAE": baseline.metrics.test_mae, "R2": baseline.metrics.test_r2},
            {"Configuracion": "Actual", "MAE": metrics.test_mae, "R2": metrics.test_r2},
        ]
    )
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    importance = pd.DataFrame(metrics.feature_importance.items(), columns=["Variable", "Importancia"])
    st.bar_chart(importance.set_index("Variable"))


def render_result(result) -> None:
    summary_tab, agents_tab, trace_tab, chat_tab = st.tabs(["Reporte", "Agentes", "Trazas", "Preguntar al reporte"])

    with summary_tab:
        render_metrics(result)
        st.markdown(result.report_markdown)
        if st.button("Aprobar recomendacion", icon=":material/check_circle:"):
            st.session_state.approved_run = result.run_id
        if st.session_state.get("approved_run") == result.run_id:
            st.success("Recomendacion aprobada por una persona responsable.")
        st.download_button("Descargar JSON", result.model_dump_json(indent=2), file_name=f"{result.run_id}.json", mime="application/json", icon=":material/download:")
        st.download_button("Descargar reporte", result.report_markdown, file_name=f"{result.run_id}.md", mime="text/markdown", icon=":material/download:")

    with agents_tab:
        for finding in result.findings:
            with st.expander(f"{finding.agent_name} - {finding.status}", expanded=True):
                st.write(finding.summary)
                st.caption(f"Tiempo: {finding.elapsed_seconds:.2f} s | Fuentes: {', '.join(finding.evidence_sources) or 'sin fuentes'}")
                if finding.risks:
                    st.write({"riesgos": finding.risks})

    with trace_tab:
        st.dataframe(pd.DataFrame([event.model_dump() for event in result.trace]), use_container_width=True, hide_index=True)
        st.write({"quality_gate": result.review.model_dump(), "plan_supervisor": result.supervisor_plan})

    with chat_tab:
        chat_key = f"chat_{result.run_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        for message in st.session_state[chat_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        question = st.chat_input("Pregunta sobre esta ejecucion")
        if question:
            st.session_state[chat_key].append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Consultando el reporte y sus evidencias..."):
                    answer = IntelligentWorkflow(model_name=result.request.model_name).answer_follow_up(result, question)
                content = answer.answer
                if answer.citations:
                    content += "\n\nFuentes: " + ", ".join(answer.citations)
                st.markdown(content)
            st.session_state[chat_key].append({"role": "assistant", "content": content})


def main() -> None:
    st.set_page_config(page_title="Sesion 7 - Workflow inteligente", layout="wide")
    st.title("NovaRetail: workflow inteligente de descuentos")
    st.caption("Supervisor, analistas paralelos, Random Forest, quality gate y aprobacion humana")

    question = st.text_area("Pregunta de negocio", value=st.session_state.get("business_question", DEFAULT_QUESTION), height=80)
    st.session_state.business_question = question
    request, run_clicked = render_configuration()

    if run_clicked:
        with st.status("Ejecutando workflow", expanded=True) as status:
            st.write("Entrenando Random Forest y calculando escenarios...")
            bundle = cached_model(request.forest.model_dump_json(), DEFAULT_CAMPAIGN_DATA.stat().st_mtime)
            st.write("Delegando tareas a los agentes especializados...")
            result = IntelligentWorkflow(model_name=request.model_name).run(request, model_bundle=bundle)
            st.session_state.workflow_result = result
            st.session_state.approved_run = None
            status.update(label="Workflow finalizado", state="complete", expanded=False)

    if "workflow_result" in st.session_state:
        render_result(st.session_state.workflow_result)
    else:
        st.info("Configura el modelo y ejecuta el workflow para comenzar.")


if __name__ == "__main__":
    main()
