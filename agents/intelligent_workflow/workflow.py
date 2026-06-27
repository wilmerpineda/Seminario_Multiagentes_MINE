"""Supervised fan-out/fan-in workflow for session 7."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol, TypeVar
from uuid import uuid4
import json

import ollama
from pydantic import BaseModel, Field, ValidationError

from .analytics import (
    ModelBundle,
    load_campaign_data,
    simulate_discount_scenarios,
    train_discount_model,
)
from .contracts import (
    AgentFinding,
    FollowUpAnswer,
    ReviewDecision,
    TraceEvent,
    WorkflowRequest,
    WorkflowResult,
)
from .prompts import (
    DATA_ANALYST_SYSTEM,
    FOLLOW_UP_SYSTEM,
    POLICY_ANALYST_SYSTEM,
    REVIEWER_SYSTEM,
    RISK_ANALYST_SYSTEM,
    SUPERVISOR_SYSTEM,
    WRITER_SYSTEM,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCUMENTS = PROJECT_ROOT / "data" / "rag_business_case"
StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class ChatModel(Protocol):
    """Minimal model interface used by production and test implementations."""

    def chat(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> str:
        """Return a JSON string that follows schema."""


class LocalOllamaLLM:
    """Ollama adapter with native structured output support."""

    def __init__(self, model_name: str = "qwen2.5:3b", temperature: float = 0.1) -> None:
        self.model_name = model_name
        self.temperature = temperature

    def chat(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> str:
        response: dict[str, Any] = ollama.chat(
            model=self.model_name,
            format=schema,
            options={"temperature": self.temperature},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]


class SupervisorOutput(BaseModel):
    tasks: list[str] = Field(min_length=3, max_length=5)


class FindingOutput(BaseModel):
    summary: str
    evidence_sources: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ReportOutput(BaseModel):
    selected_discount_pct: int
    rationale: str
    controls: list[str] = Field(default_factory=list)
    recommendation: str = ""
    report_markdown: str = ""


class ReviewOutput(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    revision_instructions: str = ""


class IntelligentWorkflow:
    """Supervisor -> parallel specialists -> writer -> reviewer workflow."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        llm: ChatModel | None = None,
        documents_dir: str | Path = DEFAULT_DOCUMENTS,
    ) -> None:
        self.model_name = model_name
        self.llm = llm or LocalOllamaLLM(model_name)
        self.documents_dir = Path(documents_dir)

    def run(
        self,
        request: WorkflowRequest,
        model_bundle: ModelBundle | None = None,
    ) -> WorkflowResult:
        """Execute a bounded, observable workflow."""

        trace: list[TraceEvent] = []
        run_id = f"run-{uuid4().hex[:10]}"
        data = load_campaign_data()
        started = perf_counter()
        bundle = model_bundle or train_discount_model(data, request.forest)
        scenarios = simulate_discount_scenarios(
            data, bundle, request.city, request.segment, request.discount_options
        )
        trace.append(TraceEvent(stage="analytics", status="completed", detail="Modelo entrenado y escenarios calculados.", elapsed_seconds=perf_counter() - started))

        plan = self._supervise(request)
        trace.append(TraceEvent(stage="supervisor", status="completed", detail=" | ".join(plan.tasks)))
        contexts = self._document_contexts()

        jobs = {
            "Data Analyst": lambda: self._data_finding(request, bundle, scenarios),
            "Policy Analyst": lambda: self._context_finding(
                "Policy Analyst", "Politicas comerciales y restricciones.", POLICY_ANALYST_SYSTEM, request, contexts["policy"], ["politica_descuentos_2026.md", "reporte_comercial_q3_2026.md"]
            ),
            "Operations Risk Analyst": lambda: self._context_finding(
                "Operations Risk Analyst", "Riesgo logistico y operativo.", RISK_ANALYST_SYSTEM, request, contexts["risk"], ["acta_comite_logistica_q3_2026.md", "plan_retencion_clientes_q4_2026.md"]
            ),
        }
        findings: list[AgentFinding] = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(job): name for name, job in jobs.items()}
            for future in as_completed(futures):
                finding = future.result()
                findings.append(finding)
                trace.append(TraceEvent(stage=finding.agent_name, status=finding.status, detail=finding.summary[:180], elapsed_seconds=finding.elapsed_seconds))
        findings.sort(key=lambda item: item.agent_name)

        report = self._write_report(request, bundle, scenarios, findings)
        review = self._review(request, scenarios, findings, report)
        trace.append(TraceEvent(stage="reviewer", status="approved" if review.approved else "rejected", detail="; ".join(review.issues) or "Reporte aprobado."))
        if not review.approved:
            report = self._write_report(request, bundle, scenarios, findings, review.revision_instructions)
            review = self._review(request, scenarios, findings, report)
            trace.append(TraceEvent(stage="revision", status="approved" if review.approved else "requires_human_review", detail="Se ejecuto la unica revision permitida."))

        sources = sorted({source for finding in findings for source in finding.evidence_sources})
        return WorkflowResult(
            run_id=run_id,
            request=request,
            supervisor_plan=plan.tasks,
            metrics=bundle.metrics,
            scenarios=scenarios,
            findings=findings,
            review=review,
            recommendation=report.recommendation,
            report_markdown=report.report_markdown,
            sources=sources,
            trace=trace,
        )

    def answer_follow_up(self, result: WorkflowResult, question: str) -> FollowUpAnswer:
        """Answer without mutating or rerunning the completed workflow."""

        context = result.model_dump(mode="json", exclude={"trace"})
        prompt = f"Pregunta: {question}\n\nEjecucion disponible:\n{json.dumps(context, ensure_ascii=False)}"
        try:
            return self._structured_call(FollowUpAnswer, FOLLOW_UP_SYSTEM, prompt)
        except (RuntimeError, ValidationError):
            return FollowUpAnswer(answer="No fue posible generar una respuesta validada con el modelo local.", citations=[])

    def _supervise(self, request: WorkflowRequest) -> SupervisorOutput:
        prompt = f"Solicitud: {request.question}\nCiudad: {request.city}\nSegmento: {request.segment}"
        try:
            return self._structured_call(SupervisorOutput, SUPERVISOR_SYSTEM, prompt)
        except (RuntimeError, ValidationError):
            return SupervisorOutput(tasks=["Calcular escenarios", "Revisar politicas", "Evaluar riesgo operativo", "Consolidar y revisar"])

    def _data_finding(self, request: WorkflowRequest, bundle: ModelBundle, scenarios: list) -> AgentFinding:
        started = perf_counter()
        prompt = json.dumps({"question": request.question, "metrics": bundle.metrics.model_dump(), "scenarios": [item.model_dump() for item in scenarios]}, ensure_ascii=False)
        finding = self._safe_finding(
            "Data Analyst",
            "Interpreta el modelo y compara escenarios.",
            DATA_ANALYST_SYSTEM,
            prompt,
            started,
            fallback="Los escenarios fueron calculados correctamente; debe preferirse el mayor margen esperado y revisar el sobreajuste.",
            fallback_sources=["session7_discount_campaigns.csv", "RandomForestRegressor"],
            allowed_sources=["session7_discount_campaigns.csv", "RandomForestRegressor"],
        )
        positive = [item for item in scenarios if item.discount_pct > 0]
        best = max(positive or scenarios, key=lambda item: item.expected_margin)
        finding.summary = (
            f"Entre los descuentos positivos evaluados, {best.discount_pct}% conserva el mayor margen esperado: "
            f"${best.expected_margin:,.0f}, con uplift de {best.predicted_uplift_pct:.2f}% y margen relativo de {best.margin_pct:.2f}%."
        )
        return finding

    def _context_finding(self, name: str, role: str, system: str, request: WorkflowRequest, context: str, allowed_sources: list[str]) -> AgentFinding:
        started = perf_counter()
        prompt = f"Solicitud: {request.question}\n\nEvidencia disponible:\n{context}"
        return self._safe_finding(name, role, system, prompt, started, fallback="La rama contextual no pudo usar el LLM; requiere revision humana.", fallback_sources=allowed_sources, allowed_sources=allowed_sources)

    def _safe_finding(self, name: str, role: str, system: str, prompt: str, started: float, fallback: str, fallback_sources: list[str], allowed_sources: list[str]) -> AgentFinding:
        try:
            output = self._structured_call(FindingOutput, system, prompt)
            sources = [source for source in output.evidence_sources if source in allowed_sources]
            return AgentFinding(agent_name=name, role=role, summary=output.summary, evidence_sources=sources or allowed_sources, risks=output.risks, elapsed_seconds=round(perf_counter() - started, 3))
        except (RuntimeError, ValidationError):
            return AgentFinding(agent_name=name, role=role, status="degraded", summary=fallback, evidence_sources=fallback_sources, risks=["Salida del modelo no validada."], elapsed_seconds=round(perf_counter() - started, 3))

    def _write_report(self, request: WorkflowRequest, bundle: ModelBundle, scenarios: list, findings: list[AgentFinding], revision: str = "") -> ReportOutput:
        payload = {
            "question": request.question,
            "metrics": bundle.metrics.model_dump(),
            "scenarios": [item.model_dump() for item in scenarios],
            "findings": [item.model_dump() for item in findings],
            "revision": revision,
        }
        try:
            output = self._structured_call(ReportOutput, WRITER_SYSTEM, json.dumps(payload, ensure_ascii=False))
        except (RuntimeError, ValidationError):
            positive = [item for item in scenarios if item.discount_pct > 0]
            best = max(positive or scenarios, key=lambda item: item.expected_margin)
            output = ReportOutput(selected_discount_pct=best.discount_pct, rationale="El escenario equilibra margen, demanda y restricciones operativas.", controls=["Ejecutar un piloto limitado.", "Solicitar aprobacion humana antes del lanzamiento."])
        if output.selected_discount_pct not in {item.discount_pct for item in scenarios}:
            output.selected_discount_pct = max(scenarios, key=lambda item: item.expected_margin).discount_pct
        if any(character.isdigit() for character in output.rationale):
            output.rationale = "La seleccion equilibra demanda, margen esperado y restricciones operativas."
        selected = next(item for item in scenarios if item.discount_pct == output.selected_discount_pct)
        sources = sorted({source for finding in findings for source in finding.evidence_sources})
        scenario_rows = "\n".join(
            f"| {item.discount_pct}% | {item.predicted_uplift_pct:.2f}% | {item.expected_orders:,.1f} | ${item.expected_revenue:,.0f} | ${item.expected_margin:,.0f} | {item.margin_pct:.2f}% |"
            for item in scenarios
        )
        risks = sorted({risk for finding in findings for risk in finding.risks})
        output.recommendation = f"Evaluar un descuento de {selected.discount_pct}% mediante un piloto controlado."
        output.report_markdown = (
            f"# Decision\n\n{output.recommendation} {output.rationale}\n\n"
            "## Escenarios\n\n| Descuento | Uplift | Pedidos | Ingresos | Margen | Margen % |\n|---:|---:|---:|---:|---:|---:|\n"
            f"{scenario_rows}\n\n## Evidencia\n\n" + "\n".join(f"- **{item.agent_name}:** {item.summary}" for item in findings) +
            "\n\n## Riesgos\n\n" + "\n".join(f"- {risk}" for risk in risks) +
            "\n- El dataset es sintetico y la prediccion no demuestra causalidad.\n\n## Controles\n\n" +
            "\n".join(f"- {control}" for control in (output.controls or ["Piloto limitado.", "Aprobacion humana."])) +
            "\n\n## Fuentes\n\n" + "\n".join(f"- {source}" for source in sources)
        )
        return output

    def _review(self, request: WorkflowRequest, scenarios: list, findings: list[AgentFinding], report: ReportOutput) -> ReviewDecision:
        sources = sorted({source for finding in findings for source in finding.evidence_sources})
        deterministic_issues = []
        if len(sources) < 2:
            deterministic_issues.append("El reporte necesita al menos dos fuentes trazables.")
        if "Fuentes" not in report.report_markdown:
            deterministic_issues.append("Falta la seccion Fuentes.")
        payload = {"question": request.question, "scenarios": [item.model_dump() for item in scenarios], "findings": [item.model_dump() for item in findings], "report": report.model_dump(), "deterministic_issues": deterministic_issues}
        try:
            output = self._structured_call(ReviewOutput, REVIEWER_SYSTEM, json.dumps(payload, ensure_ascii=False))
            issues = deterministic_issues + output.issues
            return ReviewDecision(approved=output.approved and not issues, issues=issues, revision_instructions=output.revision_instructions or "; ".join(issues))
        except (RuntimeError, ValidationError):
            return ReviewDecision(approved=not deterministic_issues, issues=deterministic_issues, revision_instructions="; ".join(deterministic_issues))

    def _document_contexts(self) -> dict[str, str]:
        documents = {}
        if self.documents_dir.exists():
            for path in sorted(self.documents_dir.glob("*.md")):
                documents[path.name] = path.read_text(encoding="utf-8")[:5000]
        policy_names = ["politica_descuentos_2026.md", "reporte_comercial_q3_2026.md"]
        risk_names = ["acta_comite_logistica_q3_2026.md", "plan_retencion_clientes_q4_2026.md"]
        format_context = lambda names: "\n\n".join(f"FUENTE: {name}\n{documents[name]}" for name in names if name in documents)
        return {"policy": format_context(policy_names), "risk": format_context(risk_names)}

    def _structured_call(self, output_type: type[StructuredModel], system: str, prompt: str) -> StructuredModel:
        error = ""
        for _ in range(2):
            response = self.llm.chat(system, f"{prompt}\n{error}", output_type.model_json_schema())
            try:
                return output_type.model_validate_json(response)
            except ValidationError as exc:
                error = f"\nCorrige la salida segun el esquema. Error: {exc}"
        raise RuntimeError(f"Could not validate {output_type.__name__}")
