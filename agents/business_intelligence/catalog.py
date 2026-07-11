KPI_CATALOG = {
    "revenue": {"label": "Ingresos", "unit": "COP", "formula": "SUM(revenue)", "dimensions": ["month", "region", "seller", "customer"]},
    "gross_margin": {"label": "Margen bruto", "unit": "%", "formula": "SUM(revenue-cost)/SUM(revenue)*100", "dimensions": ["month", "region", "seller"]},
    "average_ticket": {"label": "Ticket promedio", "unit": "COP", "formula": "AVG(revenue)", "dimensions": ["month", "region"]},
    "conversion": {"label": "Conversión", "unit": "%", "formula": "oportunidades ganadas/oportunidades totales*100", "dimensions": ["month", "region", "seller"]},
    "goal_attainment": {"label": "Cumplimiento de meta", "unit": "%", "formula": "ingresos/meta*100", "dimensions": ["month", "region"]},
    "overdue_receivables": {"label": "Cartera vencida", "unit": "COP", "formula": "SUM(balance) WHERE due_date < current_date", "dimensions": ["region", "customer"]},
}


def public_catalog() -> list[dict[str, object]]:
    return [{"name": name, **definition} for name, definition in KPI_CATALOG.items()]
