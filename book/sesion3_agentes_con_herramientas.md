# Sesion 3 - Agentes con Herramientas y Automatizacion

## Agentes que pueden actuar sobre informacion externa

En la sesion anterior construimos un agente sencillo: recibia una pregunta, un contexto y algunas reglas de comportamiento, y luego generaba una respuesta usando un modelo de lenguaje. Ese tipo de agente es util para estructurar analisis, explicar resultados y mantener un estilo de respuesta consistente.

Sin embargo, en problemas reales de Inteligencia de Negocios muchas preguntas no se pueden resolver solo con el conocimiento interno del modelo. El agente necesita consultar datos, ejecutar calculos, llamar APIs, producir graficas o recuperar informacion actualizada. En esta sesion damos ese paso: pasamos de un agente que solo conversa a un agente que puede usar herramientas.

---

## Objetivos de aprendizaje

Al finalizar esta sesion, el estudiante estara en capacidad de:

1. Explicar la diferencia entre un agente basado en prompts y un agente con herramientas.
2. Entender el concepto de Tool Calling o Function Calling.
3. Disenar herramientas simples para que un agente ejecute tareas concretas.
4. Integrar funciones de Python, datos externos y resultados analiticos dentro del flujo de un agente.
5. Reconocer las ventajas y riesgos de automatizar tareas empresariales con agentes.

---

## De la sesion 2 a la sesion 3

En la sesion 2 trabajamos principalmente con Prompt Engineering, Skills y Context Engineering. La idea central era controlar el comportamiento del modelo mediante:

- un rol claro,
- un contexto de negocio,
- instrucciones explicitas,
- restricciones,
- y un formato esperado de salida.

Ese enfoque permite construir agentes utiles, pero tiene una limitacion importante: el modelo solo puede razonar con la informacion que le entregamos en el prompt. Si falta un dato, si se requiere un calculo exacto o si la informacion cambia con el tiempo, el agente puede responder de forma incompleta o, peor aun, inventar.

Un agente con herramientas cambia la arquitectura. El modelo ya no es el unico componente del sistema. Ahora el agente puede decidir que necesita ejecutar una funcion externa, recibir el resultado y usarlo como evidencia para responder.

```text
Agente de la sesion 2 =
Modelo
+ Prompt
+ Contexto
+ Reglas de respuesta
```

```text
Agente de la sesion 3 =
Modelo
+ Prompt
+ Herramientas
+ Ejecucion de funciones
+ Resultados observables
+ Respuesta final basada en evidencia
```

---

## Que es una herramienta para un agente

Una herramienta es una funcion que el agente puede usar para resolver una parte de la tarea. En terminos practicos, puede ser una funcion de Python con un nombre, una descripcion, unos parametros de entrada y una salida estructurada.

Ejemplos de herramientas en un contexto empresarial:

- Consultar precios historicos de una accion.
- Calcular indicadores financieros.
- Leer una tabla de ventas.
- Generar una grafica.
- Consultar una API externa.
- Buscar clientes con alto riesgo de abandono.
- Resumir los KPIs de una campana.
- Crear un reporte automatico.

La herramienta no reemplaza al modelo. La herramienta ejecuta una accion concreta; el modelo decide cuando usarla, interpreta sus resultados y comunica las conclusiones.

---

## Tool Calling y Function Calling

Tool Calling, tambien llamado Function Calling, es el patron mediante el cual un modelo de lenguaje solicita la ejecucion de una herramienta externa.

El flujo general es:

1. El usuario hace una pregunta.
2. El agente analiza que informacion necesita.
3. El modelo propone una o varias herramientas a ejecutar.
4. El sistema ejecuta esas herramientas en Python.
5. Los resultados vuelven al agente.
6. El modelo genera una respuesta final usando esos resultados.

```{mermaid}
flowchart LR
    A[Pregunta del usuario] --> B[Modelo planifica]
    B --> C[Seleccion de herramientas]
    C --> D[Ejecucion en Python]
    D --> E[Resultados estructurados]
    E --> F[Respuesta final]
```

La parte clave es separar dos responsabilidades:

- El modelo razona, decide y comunica.
- Las herramientas consultan, calculan o producen evidencia.

---

## Por que esto es importante en Inteligencia de Negocios

En Inteligencia de Negocios no basta con generar texto convincente. Se necesitan respuestas trazables, actualizadas y conectadas con datos. Un agente con herramientas permite acercarse a ese objetivo porque puede:

- reducir alucinaciones al basar la respuesta en resultados calculados,
- trabajar con informacion actualizada,
- automatizar pasos repetitivos de analisis,
- conectar modelos de lenguaje con APIs y bases de datos,
- producir salidas mas utiles, como tablas, graficas o indicadores,
- y separar la logica analitica del estilo de comunicacion.

Por ejemplo, ante la pregunta:

```text
Compara el comportamiento de AAPL, MSFT y SPY durante el ultimo ano y genera una recomendacion para un comite de inversiones.
```

Un agente sencillo podria responder con conocimiento general. Un agente con herramientas puede descargar datos historicos, calcular retornos, volatilidad, drawdown, correlaciones y generar una grafica antes de redactar la conclusion.

---

## Arquitectura del agente financiero

El agente `financial_research_agent` construido para esta sesion sigue una arquitectura simple pero potente:

```text
financial_research_agent
|
+-- agent.py          -> Orquesta el flujo del agente
+-- prompts.py        -> Define instrucciones del sistema y prompts
+-- tools.py          -> Contiene herramientas ejecutables
+-- tool_registry.py  -> Expone el registro de herramientas
+-- market_data.py    -> Funciones de consulta y preparacion de datos
+-- plots.py          -> Utilidades para visualizacion
```

El flujo conceptual es:

1. El usuario formula una pregunta financiera.
2. El agente pide al modelo un plan de herramientas.
3. El plan se representa como JSON.
4. El registro de herramientas ejecuta cada funcion solicitada.
5. Los resultados se entregan de nuevo al modelo.
6. El modelo produce una respuesta ejecutiva con evidencia.

---

## Registro de herramientas

Un registro de herramientas es una capa de control. En vez de permitir que el modelo ejecute cualquier cosa, se le ofrece un catalogo limitado de funciones permitidas.

Esto es importante por tres razones:

- Seguridad: el agente solo puede usar herramientas autorizadas.
- Claridad: cada herramienta tiene una responsabilidad definida.
- Trazabilidad: podemos saber que herramienta se ejecuto y con que argumentos.

Una herramienta bien disenada debe tener:

- nombre claro,
- descripcion comprensible,
- parametros esperados,
- validaciones basicas,
- salida estructurada,
- y errores explicitos cuando algo falla.

---

## Ventajas frente al agente sencillo

El agente de la sesion 2 era adecuado para razonar sobre un contexto ya preparado. El agente de la sesion 3 es mas adecuado cuando la tarea exige accion.

| Criterio | Agente sesion 2 | Agente sesion 3 |
|---|---|---|
| Fuente principal | Prompt y contexto | Prompt, herramientas y resultados |
| Capacidad de calculo | Limitada al texto entregado | Ejecuta funciones externas |
| Datos actualizados | Depende del usuario | Puede consultar APIs |
| Trazabilidad | Media | Mayor, por resultados de herramientas |
| Automatizacion | Baja | Alta |
| Riesgo de inventar datos | Mayor si falta contexto | Menor si las herramientas devuelven evidencia |

La ventaja principal no es que el agente "sepa mas", sino que puede hacer mas: consultar, calcular, transformar y producir artefactos analiticos.

---

## Riesgos y buenas practicas

Agregar herramientas tambien agrega responsabilidad. Un agente con herramientas puede cometer errores si:

- selecciona una herramienta inadecuada,
- envia parametros mal formados,
- interpreta mal el resultado,
- consulta una fuente incompleta,
- o presenta una conclusion sin advertir limitaciones.

Buenas practicas:

- Mantener herramientas pequenas y especificas.
- Validar entradas y salidas.
- Registrar el plan de herramientas ejecutado.
- Separar hechos, supuestos y recomendaciones.
- Mostrar limitaciones cuando los datos no sean suficientes.
- Evitar que el modelo ejecute codigo arbitrario.

---

## Actividad practica

Durante la practica se propone:

1. Ejecutar el notebook del agente financiero.
2. Revisar el plan JSON de herramientas que propone el modelo.
3. Identificar que herramientas se ejecutan y que resultados producen.
4. Comparar una respuesta sin herramientas contra una respuesta con herramientas.
5. Proponer una nueva herramienta para un caso de negocio propio.

Ejemplos de herramientas que los estudiantes pueden proponer:

- una herramienta para leer ventas por region,
- una herramienta para calcular crecimiento mensual,
- una herramienta para detectar clientes atipicos,
- una herramienta para resumir indicadores de cartera,
- o una herramienta para generar una grafica ejecutiva.

---

## Cierre

Los agentes con herramientas son el puente entre los modelos de lenguaje y los sistemas analiticos reales. Para una organizacion, su valor aparece cuando el agente deja de ser solo una interfaz conversacional y se convierte en una capa capaz de ejecutar tareas, consultar informacion y producir evidencia para la toma de decisiones.

Este patron sera fundamental para las siguientes sesiones del curso, especialmente cuando integremos recuperacion documental, workflows y sistemas multiagente con roles especializados.
