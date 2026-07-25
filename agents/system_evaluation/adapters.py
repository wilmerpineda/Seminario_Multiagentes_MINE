from __future__ import annotations

import time
from typing import Protocol

import httpx

from agents.business_intelligence.contracts import BIQueryRequest, QueryFilters
from agents.business_intelligence.workflow import BusinessIntelligenceWorkflow

from .contracts import EvaluationCase, ObservedResponse


class SystemUnderTest(Protocol):
    name: str

    def execute(self, case: EvaluationCase) -> ObservedResponse: ...


class InProcessSession8Adapter:
    name = "session8-bi-in-process"

    def __init__(self, workflow: BusinessIntelligenceWorkflow | None = None):
        self.workflow = workflow or BusinessIntelligenceWorkflow()

    def execute(self, case: EvaluationCase) -> ObservedResponse:
        started = time.perf_counter()
        try:
            request = BIQueryRequest(
                question=case.question,
                filters=QueryFilters(**case.filters),
            )
            result = self.workflow.run(request)
            return ObservedResponse(
                case_id=case.case_id,
                status="completed",
                intent=result.intent,
                summary=result.executive_summary,
                rows=result.rows,
                evidence=result.evidence,
                traces=[trace.model_dump(mode="json") for trace in result.traces],
                latency_ms=(time.perf_counter() - started) * 1000,
                raw=result.model_dump(mode="json"),
            )
        except Exception as exc:
            return ObservedResponse(
                case_id=case.case_id,
                status="failed",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=f"{type(exc).__name__}: {exc}",
            )


class HttpSession8Adapter:
    name = "session8-bi-http"

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "session8-local-key",
        timeout: float = 20,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def execute(self, case: EvaluationCase) -> ObservedResponse:
        started = time.perf_counter()
        try:
            response = httpx.post(
                f"{self.base_url}/v1/query",
                headers={"X-API-Key": self.api_key},
                json={"question": case.question, "filters": case.filters},
                timeout=self.timeout,
            )
            if response.status_code in {400, 403, 422}:
                return ObservedResponse(
                    case_id=case.case_id,
                    status="refused",
                    summary=response.text,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
            response.raise_for_status()
            payload = response.json()
            return ObservedResponse(
                case_id=case.case_id,
                status="completed",
                intent=payload.get("intent"),
                summary=payload.get("executive_summary", ""),
                rows=payload.get("rows", []),
                evidence=payload.get("evidence", []),
                traces=payload.get("traces", []),
                latency_ms=(time.perf_counter() - started) * 1000,
                raw=payload,
            )
        except Exception as exc:
            return ObservedResponse(
                case_id=case.case_id,
                status="failed",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=f"{type(exc).__name__}: {exc}",
            )

