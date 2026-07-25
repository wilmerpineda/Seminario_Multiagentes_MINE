from .contracts import ControlRecord, RiskRecord


DEFAULT_CONTROLS = [
    ControlRecord(control_id="C01", name="Linaje, consentimiento y finalidad", kind="preventive", lifecycle_stage="data", owner="Data steward / DPO", evidence="Inventario y registro de autorización"),
    ControlRecord(control_id="C02", name="Pruebas por cohortes e intersecciones", kind="detective", lifecycle_stage="predeployment", owner="QA / responsable de dominio", evidence="Reporte de disparidad y umbrales"),
    ControlRecord(control_id="C03", name="Allowlist de herramientas y mínimo privilegio", kind="preventive", lifecycle_stage="build", owner="Ingeniería / Seguridad", evidence="Política de permisos y pruebas adversariales"),
    ControlRecord(control_id="C04", name="Quality gate con evidencia", kind="detective", lifecycle_stage="runtime", owner="Operaciones / dueño del proceso", evidence="Trazas y decisión del reviewer"),
    ControlRecord(control_id="C05", name="Aprobación humana para impactos altos", kind="preventive", lifecycle_stage="design", owner="Product owner / responsable de dominio", evidence="Matriz de autoridad"),
    ControlRecord(control_id="C06", name="Kill switch, reversión y comunicación", kind="corrective", lifecycle_stage="incident_response", owner="SRE / Comité de IA", evidence="Runbook e informe de incidente"),
]


DEFAULT_RISKS = [
    RiskRecord(risk_id="R01", category="bias", scenario="El promedio global oculta un peor desempeño interseccional.", affected_groups="Cohortes regionales, etarias o de género.", signal="Brecha entre mejor y peor cohorte.", controls=["C02", "C05"], residual_risk="medium", decision_owner="Comité de IA", review_frequency="Cada versión"),
    RiskRecord(risk_id="R02", category="privacy", scenario="Entradas o trazas exponen datos personales.", affected_groups="Titulares de los datos.", signal="Patrones de PII en prompts, respuestas o logs.", controls=["C01", "C03", "C06"], residual_risk="high", decision_owner="DPO", review_frequency="Continuo"),
    RiskRecord(risk_id="R03", category="multiagent", scenario="Un hallazgo incorrecto se propaga al consolidado.", affected_groups="Usuarios de la decisión.", signal="Evidencia perdida o reviewer inconsistente.", controls=["C04", "C05"], residual_risk="medium", decision_owner="Responsable de dominio", review_frequency="Por ejecución crítica"),
    RiskRecord(risk_id="R04", category="security", scenario="Una instrucción indirecta intenta usar herramientas fuera de alcance.", affected_groups="Organización y clientes.", signal="Llamada bloqueada o intento de exfiltración.", controls=["C03", "C04", "C06"], residual_risk="high", decision_owner="Seguridad", review_frequency="Continuo"),
    RiskRecord(risk_id="R05", category="cost", scenario="Loops o degradación por presupuesto afectan la calidad de forma desigual.", affected_groups="Usuarios con consultas complejas.", signal="Costo por caso, reintentos y tasa de fallback.", controls=["C04", "C06"], residual_risk="medium", decision_owner="Product owner / FinOps", review_frequency="Mensual"),
]
