---
name: b2b-bi-intelligence
description: Consulta la API multiagente B2B de la sesión 8 para analizar ingresos, margen, conversión, cumplimiento de metas y cartera, o recuperar una ejecución auditada. Usar ante preguntas ejecutivas sobre KPIs B2B que requieran SQL seguro, evidencia y trazas.
---

# B2B BI Intelligence

Consultar el servicio compartido; no calcular cifras ni inventar resultados fuera de la respuesta de la API.

## Ejecutar un análisis

1. Leer `references/api.md` para confirmar el contrato.
2. Obtener `BI_API_URL` y `API_KEY` del entorno; no mostrar la clave.
3. Ejecutar:

```powershell
python plugins/b2b-bi-intelligence/skills/b2b-bi-intelligence/scripts/query_bi.py query --question "¿Cómo evolucionaron los ingresos por región?"
```

4. Resumir el KPI, la explicación, el estado del reviewer y las evidencias.
5. Indicar que los datos del laboratorio son sintéticos y que las recomendaciones requieren validación humana.

## Recuperar una ejecución

```powershell
python plugins/b2b-bi-intelligence/skills/b2b-bi-intelligence/scripts/query_bi.py run --run-id <id>
```

No ejecutar SQL directamente, modificar la base de datos ni afirmar que una relación descriptiva es causal.
