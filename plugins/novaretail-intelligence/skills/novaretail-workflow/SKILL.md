---
name: novaretail-workflow
description: Ejecuta el workflow multiagente de NovaRetail para comparar descuentos, margen, politicas y riesgo operativo, o consulta una ejecucion JSON ya guardada.
---

# NovaRetail Workflow

Usa esta skill cuando el usuario solicite analizar descuentos de NovaRetail,
comparar escenarios comerciales o hacer preguntas sobre un reporte previo.

## Ejecucion

1. Confirma que la solicitud indique ciudad y segmento; usa `Pereira` y
   `Alto valor` cuando no los especifique.
2. Ejecuta el wrapper desde la raiz del repositorio:

```powershell
python plugins/novaretail-intelligence/scripts/run_workflow.py run --question "<pregunta>" --city "<ciudad>" --segment "<segmento>"
```

3. Lee `RUN_FILE=<ruta>` y conserva esa ruta para preguntas posteriores.
4. Resume recomendacion, escenario, quality gate y fuentes. Declara que los
   datos son sinteticos y que la prediccion no es causal.

## Preguntas Sobre Una Ejecucion

```powershell
python plugins/novaretail-intelligence/scripts/run_workflow.py ask --run "<ruta-json>" --question "<pregunta>"
```

No respondas con cifras distintas a las presentes en el JSON. Si una fuente o
metrica no esta disponible, indicalo en vez de inferirla.

## Limites

- No ejecutes promociones ni modifiques datos empresariales.
- No presentes la prediccion como efecto causal.
- Las decisiones sensibles requieren aprobacion humana en Streamlit.
