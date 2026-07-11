from __future__ import annotations

import re


ALLOWED_TABLES = {"sales", "customers", "sellers", "regions", "opportunities", "goals", "payments"}
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|execute|merge)\b", re.I)


class UnsafeQuery(ValueError):
    pass


def validate_read_only_sql(sql: str, max_rows: int = 500) -> str:
    cleaned = sql.strip().rstrip(";")
    if not re.match(r"^(select|with)\b", cleaned, re.I):
        raise UnsafeQuery("Solo se permiten consultas SELECT o CTE.")
    if ";" in cleaned or "--" in cleaned or "/*" in cleaned or FORBIDDEN.search(cleaned):
        raise UnsafeQuery("La consulta contiene una operación o construcción no permitida.")
    tables = {m.group(1).lower() for m in re.finditer(r"\b(?:from|join)\s+([a-z_][\w]*)", cleaned, re.I)}
    cte_names = {m.group(1).lower() for m in re.finditer(r"(?:\bwith|,)\s*([a-z_][\w]*)\s+as\s*\(", cleaned, re.I)}
    unknown = tables - ALLOWED_TABLES - cte_names
    if unknown:
        raise UnsafeQuery(f"Tablas no autorizadas: {', '.join(sorted(unknown))}")
    limit = re.search(r"\blimit\s+(\d+)\s*$", cleaned, re.I)
    if limit and int(limit.group(1)) > max_rows:
        raise UnsafeQuery(f"El límite solicitado supera {max_rows} filas.")
    if not limit:
        cleaned += f" LIMIT {max_rows}"
    return cleaned
