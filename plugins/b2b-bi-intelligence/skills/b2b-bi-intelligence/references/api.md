# Contrato de la API BI

- Base URL local: `http://localhost:8000`.
- Autenticación: encabezado `X-API-Key`.
- `POST /v1/query`: recibe `question`, fechas opcionales y `filters` (`region`, `seller`, `customer`).
- `GET /v1/runs/{run_id}`: recupera una ejecución persistida.

La respuesta contiene `kpis`, `rows`, `sql`, `executive_summary`, `evidence`, `review_approved` y `traces`. Tratar `review_approved=false` como análisis no aprobado.
