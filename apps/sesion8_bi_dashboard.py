from __future__ import annotations

import os

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st


API_URL = os.getenv("BI_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("API_KEY", "session8-local-key")


def call_api(path: str, payload: dict) -> dict:
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{API_URL}{path}", json=payload, headers={"X-API-Key": API_KEY})
        response.raise_for_status()
        return response.json()


def api_error_message(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.ConnectError):
        return f"No se encontró la API en {API_URL}. Iníciala con: uvicorn apps.sesion8_bi_api:app --reload"
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return str(exc.response.json().get("detail", exc))
        except ValueError:
            return str(exc)
    return str(exc)


def main() -> None:
    st.set_page_config(page_title="Sesión 8 - BI multiagente", layout="wide")
    st.title("B2B Intelligence: analítica aumentada")
    st.caption("SQL seguro, KPIs auditables, insights y explicación ejecutiva")
    with st.sidebar:
        st.header("Filtros")
        region = st.selectbox("Región", ["Todas", "Andina", "Caribe", "Pacífica", "Centro"])
        start_date = st.date_input("Desde", value=None)
        end_date = st.date_input("Hasta", value=None)
    question = st.text_area("Pregunta de negocio", "¿Cómo evolucionaron los ingresos por región?")
    if st.button("Analizar", type="primary"):
        payload = {"question": question, "start_date": start_date.isoformat() if start_date else None, "end_date": end_date.isoformat() if end_date else None, "filters": {"region": None if region == "Todas" else region}}
        try:
            with st.spinner("Coordinando agentes..."):
                st.session_state.result = call_api("/v1/query", payload)
        except httpx.HTTPError as exc:
            st.error(f"La API no pudo completar el análisis: {api_error_message(exc)}")
    result = st.session_state.get("result")
    if not result:
        st.info("Formula una pregunta para iniciar el workflow.")
        return
    for index, metric in enumerate(result["kpis"]):
        st.metric(metric["label"], f"{metric['value']:,.2f} {metric['unit']}")
    frame = pd.DataFrame(result["rows"])
    if not frame.empty:
        chart = result["chart"]
        if chart["x"] in frame and chart["y"] in frame:
            figure = px.line(frame, x=chart["x"], y=chart["y"], color="region" if "region" in frame else None, markers=True) if chart["type"] == "line" else px.bar(frame, x=chart["x"], y=chart["y"], color="region" if "region" in frame else None)
            st.plotly_chart(figure, use_container_width=True)
        st.dataframe(frame, use_container_width=True, hide_index=True)
    st.subheader("Explicación ejecutiva")
    st.write(result["executive_summary"])
    with st.expander("Evidencia, SQL y trazas"):
        st.code(result["sql"], language="sql")
        st.write(result["evidence"])
        st.dataframe(pd.DataFrame(result["traces"]), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
