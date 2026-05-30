# Financial Research Agent

Agente de investigacion financiera para consultar datos de Yahoo Finance,
calcular metricas de rendimiento y riesgo, generar visualizaciones e interpretar
resultados con un modelo local via Ollama.

## Instalacion

```bash
python -m poetry install
python -m poetry run python -m ipykernel install --user --name financial-research-agent --display-name "Financial Research Agent"
```

If the project folder is moved, run the kernel registration command again so
Jupyter points to the current `.venv` path.

## Uso basico

```python
from agents.financial_research_agent.agent import FinancialResearchAgent

agent = FinancialResearchAgent(model_name="qwen2.5:3b")

response = agent.analyze(
    user_question="Compare el rendimiento y el riesgo de AAPL, MSFT y SPY durante el ultimo ano.",
)

print(response.tool_plan)
print(response.tool_results)
print(response.content)
```
