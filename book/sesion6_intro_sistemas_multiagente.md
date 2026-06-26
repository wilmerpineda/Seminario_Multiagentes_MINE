# Sesion 6 - Introduccion a Sistemas Multiagente

## De agentes individuales a equipos de agentes

En las sesiones anteriores construimos agentes con herramientas y agentes RAG.
Esos agentes ya podian consultar informacion externa, recuperar evidencia de
documentos y generar respuestas mas trazables que un modelo usado de forma
aislada.

Sin embargo, muchos problemas empresariales no son una sola tarea. Un analisis
real suele incluir investigacion, planeacion, escritura, validacion, revision de
riesgos y ajustes. Pedirle todo eso a un unico agente puede funcionar en
ejercicios pequenos, pero se vuelve fragil cuando la tarea crece.

La pregunta guia de esta sesion es:

```text
Cuando conviene dividir el trabajo entre varios agentes especializados?
```

Un sistema multiagente no es simplemente ejecutar varios prompts. Es una
arquitectura donde varios agentes, cada uno con un rol definido, colaboran para
resolver una tarea comun.

```text
Agente individual =
Modelo
+ Prompt
+ Herramientas
+ Respuesta
```

```text
Sistema multiagente =
Varios agentes especializados
+ Roles
+ Tareas
+ Coordinacion
+ Delegacion
+ Revision cruzada
+ Resultado integrado
```

---

## Objetivos de aprendizaje

Al finalizar esta sesion, el estudiante estara en capacidad de:

1. Explicar por que una tarea compleja puede beneficiarse de multiples agentes.
2. Diferenciar roles especializados como Planner, Researcher, Writer y Reviewer.
3. Disenar un flujo simple de coordinacion y delegacion entre agentes.
4. Reconocer patrones basicos de colaboracion multiagente.
5. Comparar de forma introductoria frameworks modernos como CrewAI y AutoGen.
6. Construir un primer flujo multiagente colaborativo en Python.

---

## Por que multiples agentes

Un agente unico puede recibir una instruccion amplia como:

```text
Analiza el caso de NovaRetail, investiga evidencia, redacta una recomendacion y
revisa si la respuesta esta sustentada.
```

El problema es que esa instruccion mezcla responsabilidades distintas:

- decidir que pasos seguir,
- buscar informacion,
- seleccionar evidencia,
- redactar una respuesta,
- verificar consistencia,
- detectar riesgos,
- y proponer ajustes.

Cuando todo vive dentro de un solo agente, es mas dificil observar que parte del
proceso fallo. Si la respuesta final es debil, puede ser porque el plan fue malo,
porque la evidencia recuperada no era suficiente, porque la redaccion exagero o
porque nadie reviso las limitaciones.

Un sistema multiagente permite separar responsabilidades.

| Responsabilidad | Agente unico | Sistema multiagente |
|---|---|---|
| Planeacion | Mezclada con la respuesta | Planner define pasos explicitos |
| Busqueda de evidencia | Puede ser superficial | Researcher se enfoca en fuentes |
| Redaccion | Combina hechos y estilo | Writer sintetiza evidencia |
| Control de calidad | Puede omitirse | Reviewer revisa riesgos y soporte |
| Trazabilidad | Mas dificil de auditar | Cada agente deja una salida intermedia |
| Escalabilidad | Prompt cada vez mas grande | Roles y tareas se pueden ampliar |

La ventaja principal no es que "mas agentes siempre sean mejores". La ventaja es
la division controlada del trabajo.

---

## Cuando no conviene usar multiples agentes

Los sistemas multiagente agregan complejidad. No conviene usarlos para todo.

Un agente unico suele ser suficiente cuando:

- la tarea es corta,
- el contexto es pequeno,
- no se requiere revision cruzada,
- no hay varias fuentes que comparar,
- o la salida esperada es simple.

Un sistema multiagente empieza a tener sentido cuando:

- la tarea tiene varias etapas claras,
- se necesita evidencia y revision,
- hay que combinar datos, documentos y criterio experto,
- se quiere auditar el proceso,
- o se necesitan roles con objetivos en tension.

Ejemplo de objetivos en tension:

- Writer quiere producir una recomendacion clara.
- Reviewer quiere evitar afirmaciones no sustentadas.
- Planner quiere completar el flujo.
- Researcher quiere traer evidencia suficiente antes de concluir.

Esa tension bien disenada mejora la calidad del resultado.

---

## Roles especializados

En esta sesion usaremos cuatro roles base.

## Planner

El Planner define el plan de trabajo. Su tarea no es responder el caso completo,
sino dividirlo en pasos concretos.

Preguntas que debe resolver:

- Que informacion se necesita?
- Que agente debe hacer cada parte?
- En que orden se ejecutan las tareas?
- Que entregable final se espera?

Salida esperada:

```text
Plan de trabajo con pasos, responsables y criterios de exito.
```

## Researcher

El Researcher busca informacion relevante y la organiza como evidencia. En un
sistema real podria usar RAG, APIs, bases de datos, herramientas de busqueda o
documentos internos.

Preguntas que debe resolver:

- Que evidencia responde la pregunta?
- Que fuentes son relevantes?
- Que informacion falta?
- Que fragmentos deben citarse?

Salida esperada:

```text
Hallazgos con fuentes, datos relevantes y limitaciones.
```

## Writer

El Writer convierte el plan y la evidencia en una respuesta clara. Su funcion es
integrar, no inventar.

Preguntas que debe resolver:

- Cual es la conclusion principal?
- Como se organiza la respuesta para el usuario?
- Que recomendaciones son accionables?
- Que evidencia respalda cada afirmacion?

Salida esperada:

```text
Borrador ejecutivo con recomendacion, justificacion y proximos pasos.
```

## Reviewer

El Reviewer evalua la respuesta antes de entregarla. Busca afirmaciones sin
soporte, riesgos, contradicciones y omisiones.

Preguntas que debe resolver:

- La respuesta usa la evidencia disponible?
- Hay afirmaciones no sustentadas?
- Faltan limitaciones?
- La recomendacion es demasiado fuerte para la evidencia?

Salida esperada:

```text
Revision con observaciones, decision de aprobacion y ajustes sugeridos.
```

---

## Coordinacion y delegacion

La coordinacion define como se comunican los agentes y como avanza el trabajo.

El ejemplo implementado en esta sesion es principalmente secuencial. Primero se
recupera evidencia del caso NovaRetail y despues los agentes trabajan uno tras
otro. Esto hace que el flujo sea facil de explicar, depurar y evaluar en clase.

```{mermaid}
flowchart LR
    U([Usuario / Comite]):::user
    Q[Pregunta de negocio]:::input

    subgraph K[Contexto empresarial]
        D1[(Reporte comercial)]:::data
        D2[(Acta logistica)]:::data
        D3[(Politica / KPIs)]:::data
    end

    R0[Recuperacion de evidencia<br/>selecciona chunks relevantes]:::retrieval

    subgraph S[Flujo multiagente secuencial]
        P[Planner<br/>Define plan, pasos y criterios]:::planner
        R[Researcher<br/>Organiza hallazgos, fuentes y vacios]:::researcher
        W[Writer<br/>Redacta borrador ejecutivo]:::writer
        V[Reviewer<br/>Revisa soporte, riesgos y limites]:::reviewer
        F[Final Writer<br/>Entrega respuesta ajustada]:::final
    end

    O([Respuesta final<br/>con recomendacion y fuentes]):::output

    U --> Q
    Q --> R0
    D1 --> R0
    D2 --> R0
    D3 --> R0

    Q --> P
    R0 --> R
    P --> R
    R --> W
    W --> V
    R --> V
    R0 --> V
    V --> F
    R --> F
    R0 --> F
    F --> O

    classDef user fill:#eef2ff,stroke:#4f46e5,stroke-width:2px,color:#111827;
    classDef input fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#111827;
    classDef data fill:#ecfdf5,stroke:#059669,stroke-width:1.5px,color:#064e3b;
    classDef retrieval fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12;
    classDef planner fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a;
    classDef researcher fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef writer fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f;
    classDef reviewer fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d;
    classDef final fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764;
    classDef output fill:#f0fdf4,stroke:#15803d,stroke-width:2.5px,color:#052e16;
```

Lectura del flujo:

- `Planner`: recibe la pregunta y define el plan de trabajo. No responde la
  pregunta final.
- `Researcher`: recibe el plan y la evidencia recuperada. Produce hallazgos,
  fuentes usadas y vacios de informacion.
- `Writer`: recibe plan y hallazgos. Redacta un primer borrador ejecutivo.
- `Reviewer`: recibe borrador, hallazgos y evidencia original. Revisa si hay
  afirmaciones no sustentadas, riesgos omitidos o exceso de confianza.
- `Final Writer`: recibe la revision, los hallazgos y la evidencia. Produce la
  respuesta final ajustada para el comite.

En esta version no hay agentes ejecutandose en paralelo. El paralelismo podria
aparecer en una extension, por ejemplo con varios `Researchers` consultando
fuentes distintas al mismo tiempo: documentos internos, datos de ventas,
indicadores logisticos y politicas comerciales.

```{mermaid}
flowchart LR
    Q[Pregunta de negocio]:::input --> P[Planner]:::planner

    P --> R1[Researcher documental]:::researcher
    P --> R2[Researcher de datos]:::researcher
    P --> R3[Researcher de riesgos]:::researcher

    R1 --> C[Consolidacion de evidencia]:::retrieval
    R2 --> C
    R3 --> C

    C --> W[Writer]:::writer
    W --> V[Reviewer]:::reviewer
    V --> F[Respuesta final]:::final

    classDef input fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#111827;
    classDef planner fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a;
    classDef researcher fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef retrieval fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12;
    classDef writer fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f;
    classDef reviewer fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d;
    classDef final fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#3b0764;
```

El primer diagrama representa el ejemplo que los estudiantes ejecutan en Python.
El segundo diagrama muestra una posible evolucion paralela, util cuando varias
fuentes pueden investigarse de forma independiente.

Tambien existen flujos mas complejos:

- Paralelo: varios Researchers consultan fuentes distintas.
- Jerarquico: un manager delega tareas y decide cuando terminar.
- Debate: dos agentes proponen posturas opuestas y un tercero sintetiza.
- Iterativo: Reviewer devuelve el borrador al Writer hasta que cumpla criterios.
- Human-in-the-loop: una persona aprueba decisiones antes de ejecutar acciones.

Para BI, el flujo secuencial con revision es un buen punto de partida porque
permite observar evidencia, razonamiento y control de calidad.

---

## Caso guia de la sesion

Trabajaremos con un caso de NovaRetail:

```text
El comite comercial quiere decidir si debe lanzar una campana agresiva de
descuentos en ciudades intermedias durante Q4 para recuperar ventas.
```

El flujo multiagente debe producir:

1. Un plan de analisis.
2. Evidencia relevante.
3. Una recomendacion ejecutiva.
4. Una revision de calidad.
5. Una respuesta final ajustada.

La idea no es que los agentes "hablen mucho". La idea es que cada rol deje un
artefacto util y verificable.

---

## Frameworks modernos

En clase usaremos un flujo propio en Python para entender primero la arquitectura.
Despues se presenta como esta idea aparece en frameworks modernos.

## CrewAI

CrewAI es un framework abierto para orquestar equipos de agentes y workflows. Su
documentacion actual organiza la arquitectura alrededor de dos conceptos:

- `Flows`: workflows estructurados, con estado, eventos y control de ejecucion.
- `Crews`: equipos de agentes autonomos que colaboran en tareas delegadas.

En una lectura practica:

```text
Flow = proceso controlado
Crew = equipo de agentes
Agent = rol especializado
Task = trabajo delegado
Tool = capacidad externa
```

CrewAI es util cuando se quiere expresar un trabajo como una combinacion de roles,
tareas y herramientas, especialmente en flujos de automatizacion empresarial.

Referencia oficial: https://docs.crewai.com/en/introduction

## AutoGen

AutoGen es un framework de Microsoft para construir agentes y aplicaciones
multiagente. Su documentacion actual separa componentes como:

- `AgentChat`: construccion de aplicaciones conversacionales con uno o varios
  agentes.
- `Core`: framework orientado a eventos para sistemas multiagente mas escalables.
- `Extensions`: integraciones con modelos, herramientas, MCP, ejecucion de codigo
  y otros servicios.
- `Studio`: interfaz web para prototipar agentes sin escribir todo el codigo.

En una lectura practica:

```text
AgentChat = prototipos conversacionales
Core = runtime multiagente/event-driven
Extensions = conectores e integraciones
Studio = exploracion visual
```

AutoGen es util cuando se quiere experimentar con conversaciones agente-agente,
patrones asincronos, herramientas y arquitecturas mas programables.

Referencia oficial: https://microsoft.github.io/autogen/stable/

---

## Comparacion introductoria

| Criterio | CrewAI | AutoGen |
|---|---|---|
| Enfoque inicial | Roles, tareas, crews y flows | Conversaciones, runtime y agentes programables |
| Abstraccion principal | Crew y Flow | AgentChat y Core |
| Uso tipico | Automatizacion de workflows empresariales | Prototipos y sistemas multiagente flexibles |
| Curva inicial | Natural para pensar en equipos de trabajo | Natural para pensar en conversaciones entre agentes |
| Control de flujo | Flows, tareas secuenciales o jerarquicas | Patrones conversacionales y event-driven |

No hay que escoger un framework antes de entender el patron. Primero se debe
responder:

```text
Que roles necesito, que evidencia comparten y como se decide que el trabajo esta terminado?
```

---

## Construccion practica

La practica de la sesion implementa un flujo multiagente con el modelo local de
Ollama usado durante el curso:

```text
Planner -> Researcher -> Writer -> Reviewer -> Respuesta final
```

El objetivo es observar:

- como una tarea se divide en subtareas,
- que contexto recibe cada agente,
- que salida intermedia produce,
- como el Reviewer detecta problemas,
- y como se ajusta la respuesta final.

Archivos principales:

```text
agents/multiagent_collaboration/agent.py
agents/multiagent_collaboration/prompts.py
notebooks/05_multiagent_collaboration_flow.ipynb
apps/sesion6_multiagent_demo.py
```

El flujo hace cinco llamadas al modelo `qwen2.5:3b`:

1. Planner genera el plan.
2. Researcher organiza la evidencia recuperada.
3. Writer redacta un borrador.
4. Reviewer revisa soporte, riesgos y limitaciones.
5. Final Writer entrega la respuesta ajustada.

Para ejecutar desde terminal:

```bash
python apps/sesion6_multiagent_demo.py
```

Tambien se puede cambiar la pregunta:

```bash
python apps/sesion6_multiagent_demo.py --question "Que acciones deberia priorizar NovaRetail para reducir churn en Q4?"
```

La practica no requiere CrewAI ni AutoGen. Esa decision es intencional: primero
se entiende la arquitectura base y luego el mismo diseno puede migrarse a un
framework de orquestacion.

---

## Buenas practicas

Un sistema multiagente debe disenarse con controles claros:

- Definir un objetivo comun.
- Mantener roles especificos y no redundantes.
- Limitar que informacion puede modificar cada agente.
- Registrar salidas intermedias.
- Validar evidencia antes de recomendar.
- Evitar bucles infinitos de revision.
- Medir costo, latencia y calidad.
- Incorporar aprobacion humana cuando haya decisiones sensibles.

---

## Riesgos comunes

Los sistemas multiagente pueden fallar de varias formas:

- Roles mal definidos: todos hacen lo mismo.
- Delegacion excesiva: el sistema tarda mas sin mejorar calidad.
- Falta de criterio de cierre: los agentes siguen iterando.
- Autoridad confusa: nadie decide que respuesta entregar.
- Propagacion de errores: una mala evidencia contamina todo el flujo.
- Revision superficial: el Reviewer aprueba sin verificar soporte.
- Costos altos: cada agente implica mas llamadas al modelo.

El diseno debe balancear autonomia y control.

---

## Actividad practica

1. Ejecutar el notebook de la sesion.
2. Revisar la salida del Planner.
3. Inspeccionar que evidencia selecciona el Researcher.
4. Comparar el borrador del Writer con la evidencia.
5. Revisar las observaciones del Reviewer.
6. Ajustar el caso de negocio y ejecutar de nuevo.
7. Agregar un nuevo rol, por ejemplo `Risk Analyst` o `Financial Analyst`.
8. Discutir si el nuevo rol mejora la respuesta o solo agrega complejidad.

Preguntas sugeridas:

```text
Debe NovaRetail lanzar descuentos agresivos en ciudades intermedias durante Q4?
```

```text
Que acciones deberia priorizar antes de aumentar descuentos?
```

```text
Que evidencia faltaria para tomar una decision mas segura?
```

---

## Cierre

Los sistemas multiagente son utiles cuando una tarea necesita division de trabajo,
evidencia, revision y coordinacion. Para BI, su valor esta en convertir un flujo
analitico complejo en pasos observables: planear, investigar, sintetizar y
validar.

La idea central de la sesion es simple:

```text
No se agregan agentes por moda. Se agregan agentes cuando un rol separado mejora
la calidad, trazabilidad o control del proceso.
```

En las siguientes sesiones, este patron puede combinarse con RAG, herramientas,
memoria, evaluacion y frameworks de orquestacion para construir agentes
empresariales mas robustos.
