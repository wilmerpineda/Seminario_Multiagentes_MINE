# Retos evaluados - Sesion 7

Cada equipo construye un plugin Codex instalable que contiene un workflow
multiagente. Los CSV y `model_base.py` ya estan preparados para concentrar el
trabajo en supervision, delegacion, revision y despliegue.

## Reglas comunes

El plugin debe incluir:

- `.codex-plugin/plugin.json` valido.
- Una skill con criterios claros de activacion.
- Un script de entrada ejecutable.
- Supervisor, tres especialistas y Reviewer como roles separados.
- Dos especialistas ejecutados en paralelo.
- Contratos estructurados y una prueba automatizada.
- App Streamlit que importe el mismo motor del plugin.
- Dockerfile conectado al Ollama anfitrion.
- Aprobacion humana antes de bloquear o conceder una oferta costosa.

No se acepta simular el multiagente escribiendo todos los roles en una sola
llamada al modelo.

## Equipo 1 - Fraude

Dataset: `fraud/transactions.csv`. Objetivo: `is_fraud`.

Agentes requeridos:

1. Supervisor de fraude.
2. Analista transaccional que consulta el clasificador.
3. Analista de politicas y limites.
4. Investigador de senales sospechosas.
5. Reviewer independiente.

La politica minima debe escalar una transaccion cuando la probabilidad sea alta
o cuando la combinacion de monto y senales requiera revision. Bloquear exige
aprobacion humana.

## Equipo 2 - Abandono

Dataset: `churn/customers.csv`. Objetivo: `churned`.

Agentes requeridos:

1. Supervisor de retencion.
2. Analista de comportamiento.
3. Analista de valor del cliente.
4. Especialista en ofertas.
5. Reviewer independiente.

La politica debe combinar riesgo, valor esperado y costo de la oferta. Los
incentivos superiores al limite definido por el equipo exigen aprobacion.

## Comandos de entrega

Cada equipo crea su scaffold en una copia o rama del repositorio:

```powershell
python <plugin-creator>/scripts/create_basic_plugin.py <nombre-plugin> `
  --path plugins `
  --marketplace-path .agents/plugins/marketplace.json `
  --with-skills --with-scripts --with-marketplace
```

La demostracion debe incluir un caso normal, uno critico, la instalacion en
Codex y `docker compose up --build`.
