from __future__ import annotations

import hmac
import logging
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path

from agents.business_intelligence import BIQueryRequest, BusinessIntelligenceWorkflow
from agents.business_intelligence.catalog import public_catalog
from agents.business_intelligence.contracts import BIQueryResult, ExplainRequest


app = FastAPI(title="Sesión 8 - API multiagente BI", version="1.0.0", docs_url=None, description="Consulta KPIs B2B mediante SQL de solo lectura, agentes especializados y evidencia auditable.")
# The bundled offline Swagger UI supports OpenAPI 3.0.x, not 3.1.
app.openapi_version = "3.0.3"
app.mount("/docs-assets", StaticFiles(directory=str(swagger_ui_path)), name="swagger-assets")
logger = logging.getLogger("session8.api")


@app.get("/docs", include_in_schema=False)
def offline_docs():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - OpenAPI", swagger_js_url="/docs-assets/swagger-ui-bundle.js", swagger_css_url="/docs-assets/swagger-ui.css")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("API_KEY", "session8-local-key")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="API key inválida.")


def workflow() -> BusinessIntelligenceWorkflow:
    return BusinessIntelligenceWorkflow()


@app.get("/health")
def health() -> dict[str, str]:
    try:
        workflow().database.health()
        return {"status": "ok"}
    except Exception as exc:
        logger.exception("Cloud SQL health check failed")
        raise HTTPException(status_code=503, detail="Base de datos no disponible.") from exc


@app.get("/v1/metadata/kpis", dependencies=[Depends(require_api_key)])
def kpis() -> list[dict[str, object]]:
    return public_catalog()


@app.post("/v1/query", response_model=BIQueryResult, dependencies=[Depends(require_api_key)])
def query(request: BIQueryRequest) -> BIQueryResult:
    try:
        return workflow().run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Business intelligence workflow failed")
        raise HTTPException(status_code=503, detail="No fue posible completar el análisis.") from exc


@app.post("/v1/explain", dependencies=[Depends(require_api_key)])
def explain(request: ExplainRequest) -> dict[str, object]:
    values = list(request.metrics.values())
    if not values:
        raise HTTPException(status_code=400, detail="Se requiere al menos una métrica.")
    return {"title": request.title, "summary": f"El conjunto contiene {len(values)} indicadores, con promedio {sum(values) / len(values):,.2f}.", "evidence": request.metrics, "context": request.context}


@app.get("/v1/runs/{run_id}", response_model=BIQueryResult, dependencies=[Depends(require_api_key)])
def run(run_id: str) -> BIQueryResult:
    try:
        return workflow().get_run(run_id)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="Ejecución no encontrada.")
