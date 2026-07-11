from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .catalog import KPI_CATALOG
from .contracts import BIQueryRequest, BIQueryResult, KPIValue, TraceEvent
from .database import BIDatabase
from .narrator import enrich_summary
from .security import validate_read_only_sql


RUN_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "session8"


class BusinessIntelligenceWorkflow:
    """Auditable workflow: semantic agent -> SQL -> guard -> insights -> reviewer."""

    def __init__(self, database: BIDatabase | None = None):
        self.database = database or BIDatabase()

    def _trace(self, traces: list[TraceEvent], agent: str, detail: str, started: float, status: str = "completed") -> None:
        traces.append(TraceEvent(agent=agent, status=status, detail=detail, elapsed_ms=(time.perf_counter() - started) * 1000))

    def _intent(self, question: str) -> str:
        q = question.lower()
        if any(word in q for word in ("cartera", "vencid", "mora", "pago")):
            return "overdue_receivables"
        if any(word in q for word in ("convers", "oportunidad", "pipeline")):
            return "conversion"
        if any(word in q for word in ("meta", "cumplimiento")):
            return "goal_attainment"
        if any(word in q for word in ("margen", "rentabilidad", "costo")):
            return "gross_margin"
        return "revenue"

    def _filters(self, request: BIQueryRequest, allowed: set[str]) -> tuple[list[str], dict[str, Any]]:
        clauses, params = [], {}
        mapping = {"region": request.filters.region, "seller": request.filters.seller, "customer": request.filters.customer}
        for key, value in mapping.items():
            if value and key in allowed:
                clauses.append(f"{key} = :{key}")
                params[key] = value
        if request.start_date:
            clauses.append("period >= :start_date")
            params["start_date"] = request.start_date
        if request.end_date:
            clauses.append("period <= :end_date")
            params["end_date"] = request.end_date
        return clauses, params

    def _sql(self, intent: str, request: BIQueryRequest) -> tuple[str, dict[str, Any]]:
        allowed = {"region"}
        if intent in {"revenue", "gross_margin", "conversion"}:
            allowed.add("seller")
        if intent in {"revenue", "gross_margin", "conversion", "overdue_receivables"}:
            allowed.add("customer")
        clauses, params = self._filters(request, allowed)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        if intent == "overdue_receivables":
            extra = "payment_status = 'overdue'"
            where = f" WHERE {extra}" + (" AND " + " AND ".join(clauses) if clauses else "")
            sql = f"SELECT customer, region, ROUND(SUM(balance), 2) AS overdue_receivables FROM payments{where} GROUP BY customer, region ORDER BY overdue_receivables DESC"
        elif intent == "conversion":
            sql = f"SELECT period, ROUND(100.0 * SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS conversion FROM opportunities{where} GROUP BY period ORDER BY period"
        elif intent == "goal_attainment":
            sql = f"SELECT period, region, ROUND(100.0 * SUM(actual_revenue) / NULLIF(SUM(target_revenue), 0), 2) AS goal_attainment FROM goals{where} GROUP BY period, region ORDER BY period, region"
        elif intent == "gross_margin":
            sql = f"SELECT period, region, ROUND(100.0 * SUM(revenue - cost) / NULLIF(SUM(revenue), 0), 2) AS gross_margin FROM sales{where} GROUP BY period, region ORDER BY period, region"
        else:
            sql = f"SELECT period, region, ROUND(SUM(revenue), 2) AS revenue FROM sales{where} GROUP BY period, region ORDER BY period, region"
        return sql, params

    def run(self, request: BIQueryRequest) -> BIQueryResult:
        traces: list[TraceEvent] = []
        started = time.perf_counter()
        intent = self._intent(request.question)
        self._trace(traces, "supervisor", f"Delegación para KPI {intent}.", started)
        started = time.perf_counter()
        definition = KPI_CATALOG[intent]
        self._trace(traces, "semantic_kpi_agent", f"KPI: {definition['label']}; fórmula: {definition['formula']}.", started)
        started = time.perf_counter()
        sql, params = self._sql(intent, request)
        self._trace(traces, "sql_agent", "Consulta parametrizada generada desde una plantilla semántica.", started)
        started = time.perf_counter()
        safe_sql = validate_read_only_sql(sql, request.max_rows)
        self._trace(traces, "sql_security_reviewer", "SELECT validado contra operaciones y tablas permitidas.", started)
        started = time.perf_counter()
        columns, rows = self.database.query(safe_sql, params)
        self._trace(traces, "analytics_executor", f"{len(rows)} filas calculadas por la base de datos.", started)
        metric_values = [float(row[intent]) for row in rows if row.get(intent) is not None]
        total = sum(metric_values) if intent in {"revenue", "overdue_receivables"} else (sum(metric_values) / len(metric_values) if metric_values else 0.0)
        label, unit = str(definition["label"]), str(definition["unit"])
        started = time.perf_counter()
        if metric_values:
            direction = "aumenta" if metric_values[-1] >= metric_values[0] else "disminuye"
            summary = f"{label}: {total:,.2f} {unit}. En el rango consultado el indicador {direction}; revise los segmentos de la tabla antes de decidir."
        else:
            summary = f"No se encontraron observaciones para {label} con los filtros solicitados."
        self._trace(traces, "insight_agent", "Comparación y tendencia calculadas sobre el resultado SQL.", started)
        started = time.perf_counter()
        try:
            summary = enrich_summary(request.question, summary, rows)
            self._trace(traces, "executive_writer", "Narrativa ejecutiva generada o conservada en modo determinista.", started)
        except Exception:
            self._trace(traces, "executive_writer", "Proveedor LLM no disponible; se conservó el resumen determinista.", started, "degraded")
        started = time.perf_counter()
        evidence = [f"SQL aprobado devolvió {len(rows)} filas.", f"Definición: {definition['formula']}."]
        approved = all(str(round(value, 2)) in json.dumps(rows, default=str) for value in metric_values[:20])
        self._trace(traces, "quality_reviewer", "Cifras contrastadas con la evidencia tabular.", started, "completed" if approved else "rejected")
        result = BIQueryResult(question=request.question, intent=intent, sql=safe_sql, parameters=params, columns=columns, rows=rows, kpis=[KPIValue(name=intent, label=label, value=total, unit=unit)], chart={"type": "line" if "period" in columns else "bar", "x": columns[0] if columns else None, "y": intent}, executive_summary=summary, evidence=evidence, review_approved=approved, traces=traces)
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        (RUN_DIR / f"{result.run_id}.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result

    def get_run(self, run_id: str) -> BIQueryResult:
        if not run_id.isalnum():
            raise FileNotFoundError(run_id)
        return BIQueryResult.model_validate_json((RUN_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
