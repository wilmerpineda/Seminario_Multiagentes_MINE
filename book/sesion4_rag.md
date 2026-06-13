# Sesion 4 - Introduccion a RAG para Agentes Empresariales

## De agentes con herramientas a agentes con conocimiento documental

En la sesion anterior vimos que un agente puede mejorar sus respuestas cuando no depende solamente del conocimiento interno del modelo. Un agente con herramientas puede consultar datos, ejecutar calculos y producir evidencia antes de responder.

RAG lleva esa misma idea al mundo documental. En vez de pedirle al modelo que recuerde informacion, le damos la capacidad de buscar fragmentos relevantes en documentos y responder usando ese contexto.

La pregunta de negocio de esta sesion no es:

> Como hacemos que un modelo responda mas bonito?

La pregunta importante es:

> Como hacemos que un agente responda con evidencia de la organizacion y no con conocimiento general?

```text
Agente con herramientas =
Modelo
+
Funciones externas
+
Resultados observables
+
Respuesta final
```

```text
Agente RAG =
Modelo
+
Documentos
+
Busqueda semantica
+
Contexto recuperado
+
Respuesta basada en evidencia
```

---

## Caso guia de la sesion

Durante la practica construiremos un asistente para una empresa ficticia llamada NovaRetail.

El agente tendra acceso a tres documentos internos:

- un reporte comercial del Q3 2026,
- una politica comercial de descuentos,
- un diccionario de KPIs comerciales.

Como ejercicio adicional, los estudiantes tambien podran incorporar documentos
complementarios sobre logistica y retencion de clientes para ampliar el caso.

El objetivo no sera preguntarle al agente "que es RAG", sino usar RAG para responder preguntas que un equipo de Inteligencia de Negocios podria recibir antes de un comite:

```text
Por que pudo caer el margen bruto en Q3?
```

```text
Que clientes deberia priorizar el equipo comercial para reducir churn?
```

```text
Podemos aprobar un descuento de 20% sin validacion financiera?
```

```text
Como se define churn mensual en esta empresa?
```

Estas preguntas son interesantes porque combinan lenguaje natural, documentos dispersos y necesidad de trazabilidad.

Un LLM sin RAG podria responder con buenas practicas generales. Un agente RAG debe buscar los documentos internos, recuperar evidencia y responder con base en ella.

---

## Objetivos de aprendizaje

Al finalizar esta sesion, el estudiante estara en capacidad de:

1. Explicar por que los LLMs pueden alucinar cuando no tienen contexto suficiente.
2. Entender que es Retrieval-Augmented Generation y como se conecta con agentes empresariales.
3. Comprender de forma intuitiva que son embeddings y busqueda semantica.
4. Disenar un flujo basico para consultar documentos empresariales con RAG.
5. Reconocer casos de uso, riesgos y buenas practicas para asistentes documentales.

---

## Limitaciones de los LLMs

Los modelos de lenguaje son utiles para redactar, resumir, clasificar, explicar y razonar sobre texto. Sin embargo, tienen limitaciones importantes en contextos empresariales:

- No conocen los documentos internos de una empresa.
- Pueden tener informacion desactualizada.
- Pueden responder con seguridad aunque no tengan evidencia suficiente.
- No siempre distinguen entre hecho, suposicion e inferencia.
- No pueden verificar por si mismos una politica, contrato o reporte si no reciben ese contenido.

Este problema es especialmente critico en Inteligencia de Negocios porque las respuestas deben estar conectadas con evidencia.

Para un profesional de BI, el riesgo no es solo que el modelo se equivoque. El riesgo es que una respuesta convincente termine influyendo una decision de precios, retencion, presupuesto o cumplimiento sin haber consultado la fuente correcta.

---

## Hallucinations

Una hallucination ocurre cuando el modelo genera una respuesta plausible pero falsa, incompleta o no sustentada.

Ejemplo:

```text
Usuario:
Segun nuestra politica interna, cuantos dias de vacaciones tiene un empleado nuevo?

Modelo sin contexto:
Un empleado nuevo normalmente tiene 15 dias habiles de vacaciones al ano.
```

El problema no es que la frase suene mal. El problema es que el modelo no vio la politica real de la empresa. Puede estar mezclando conocimiento general, patrones comunes y suposiciones.

En una organizacion, una respuesta asi puede causar riesgos legales, operativos o reputacionales.

---

## Falta de contexto empresarial

Las empresas operan con informacion especifica:

- politicas internas,
- contratos,
- reportes financieros,
- manuales de procesos,
- definiciones de KPIs,
- actas de comites,
- documentos de cumplimiento,
- bases de conocimiento de soporte.

Un LLM general no tiene acceso automatico a esa informacion. Si queremos que responda sobre la empresa, debemos conectarlo con las fuentes relevantes.

---

## Que es RAG

RAG significa Retrieval-Augmented Generation. En espanol, generacion aumentada por recuperacion.

La idea central es simple: antes de responder, el agente busca informacion relevante en una base documental.

1. El usuario hace una pregunta.
2. El sistema busca documentos o fragmentos relevantes.
3. Esos fragmentos se entregan al modelo como contexto.
4. El modelo genera una respuesta usando la evidencia recuperada.

```{mermaid}
flowchart LR
    A[Pregunta del usuario] --> B[Busqueda semantica]
    B --> C[Fragmentos relevantes]
    C --> D[Prompt aumentado]
    D --> E[LLM]
    E --> F[Respuesta con evidencia]
```

RAG no hace que el modelo "sepa" los documentos para siempre. RAG recupera informacion en el momento de la consulta y la usa como contexto temporal.

En terminos de BI:

```text
RAG = motor de busqueda semantica + LLM + reglas de respuesta con evidencia
```

El valor no esta solo en responder. El valor esta en responder con la fuente correcta.

---

## Por que RAG es valioso en agentes

Un agente empresarial normalmente necesita tres capacidades:

| Capacidad | Sin RAG | Con RAG |
|---|---|---|
| Conocimiento interno | Depende de lo que el usuario copie en el prompt | Recupera fragmentos de documentos internos |
| Trazabilidad | Baja o manual | Puede mostrar chunks y fuentes usadas |
| Actualizacion | Depende del entrenamiento del modelo | Depende de los documentos indexados |
| Control de riesgo | El modelo puede improvisar | Se puede obligar a responder solo con evidencia |
| Utilidad para BI | Explica conceptos generales | Ayuda a responder preguntas sobre reportes, politicas y KPIs |

RAG convierte al agente en una interfaz conversacional sobre conocimiento empresarial. Esto es especialmente util cuando la informacion existe, pero esta distribuida en PDFs, reportes, politicas, actas o wikis.

---

## RAG no es solo pegar documentos en el prompt

Una forma simple de dar contexto al modelo es copiar un documento completo dentro del prompt. Esto puede funcionar con textos pequenos, pero falla cuando:

- hay muchos documentos,
- los documentos son largos,
- el contexto permitido por el modelo es limitado,
- la pregunta solo necesita una parte del documento,
- se requiere trazabilidad sobre la fuente usada.

RAG resuelve esto dividiendo documentos en fragmentos, indexandolos y recuperando solo las partes mas relevantes para cada pregunta.

---

## Arquitectura conceptual de RAG

Un sistema RAG basico tiene dos grandes momentos: indexacion y consulta.

## Indexacion

En la indexacion preparamos los documentos para que puedan ser buscados.

1. Cargar documentos.
2. Dividirlos en chunks o fragmentos.
3. Crear embeddings para cada chunk.
4. Guardar los embeddings en una base vectorial.

```{mermaid}
flowchart LR
    A[Documentos] --> B[Chunks]
    B --> C[Embeddings]
    C --> D[Base vectorial]
```

## Consulta

En la consulta usamos la pregunta del usuario para recuperar contexto.

1. Convertir la pregunta en embedding.
2. Buscar chunks semanticamente cercanos.
3. Construir un prompt con esos chunks.
4. Pedir al modelo una respuesta basada en evidencia.

```{mermaid}
flowchart LR
    A[Pregunta] --> B[Embedding de pregunta]
    B --> C[Busqueda en base vectorial]
    C --> D[Chunks relevantes]
    D --> E[Respuesta del LLM]
```

---

## Que son embeddings

Un embedding es una representacion numerica de un texto.

La intuicion de negocio es:

> textos con significados parecidos quedan cerca en un espacio numerico.

Por ejemplo, estas preguntas son distintas en palabras, pero cercanas en significado:

```text
Que es RAG?
Como funciona la generacion aumentada por recuperacion?
Como puede un agente consultar documentos antes de responder?
```

Un sistema de busqueda por palabras clave podria fallar si no aparecen las mismas palabras. Una busqueda semantica intenta encontrar fragmentos relacionados por significado.

---

## Busqueda semantica frente a busqueda por palabras clave

| Aspecto | Palabras clave | Busqueda semantica |
|---|---|---|
| Busca | Coincidencias literales | Significado similar |
| Funciona bien cuando | El usuario usa los mismos terminos del documento | El usuario pregunta con lenguaje natural |
| Riesgo | No encuentra sinonimos o ideas equivalentes | Recupera fragmentos semanticamente cercanos pero no exactos |
| Uso empresarial | Busqueda documental tradicional | Asistentes conversacionales sobre conocimiento interno |

Lo importante es entender que la busqueda semantica no reemplaza toda validacion. Solo mejora la recuperacion de contexto.

---

## Que es un chunk

Un chunk es un fragmento de documento que se indexa de manera independiente.

Si los chunks son demasiado grandes:

- recuperan mucho ruido,
- consumen demasiado contexto,
- dificultan identificar la fuente exacta.

Si los chunks son demasiado pequenos:

- pierden contexto,
- pueden ser ambiguos,
- no contienen suficiente informacion para responder.

Una buena practica inicial es dividir por secciones y mantener metadatos como:

- fuente,
- titulo de seccion,
- identificador del chunk,
- posicion dentro del documento.

---

## Base vectorial

Una base vectorial almacena embeddings y permite buscar vectores cercanos.

En esta sesion usaremos una base vectorial local para mantener un flujo simple:

- indexar los fragmentos de la sesion,
- consultar los fragmentos relevantes,
- mostrar que evidencia recibio el agente,
- generar una respuesta con trazabilidad.

En sistemas reales, una empresa podria usar bases vectoriales administradas, motores de busqueda hibrida o integraciones con plataformas documentales.

## Guia rapida: instalar ChromaDB

Para las sesiones 4 y 5 usaremos ChromaDB como base vectorial local. La
dependencia ya esta declarada en el `pyproject.toml` del repositorio, por lo que
la forma recomendada de instalarla es ejecutar:

```bash
poetry install
```

Si no se esta usando Poetry, se puede instalar directamente con `pip`:

```bash
pip install chromadb
```

Para verificar que quedo instalada:

```bash
python -c "import chromadb; print(chromadb.__version__)"
```

Ademas de ChromaDB, el agente necesita Ollama para generar embeddings y
respuestas locales:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

Si aparece un error como `chromadb is required for semantic retrieval`, significa
que el ambiente de Python desde el que se esta ejecutando el notebook no tiene
ChromaDB instalado. En ese caso, revisar que Jupyter este usando el mismo
ambiente donde se ejecuto `poetry install` o instalar `chromadb` en el kernel
activo.

---

## Consulta documental

Un asistente RAG no debe responder solo porque el modelo "cree" saber algo. Debe responder con base en los documentos recuperados.

Flujo recomendado:

1. Recibir la pregunta.
2. Recuperar fragmentos relevantes.
3. Revisar si la evidencia alcanza.
4. Responder usando solo esa evidencia.
5. Citar o listar las fuentes usadas.
6. Indicar limitaciones cuando el documento no contenga la respuesta.

Ejemplo de regla:

```text
Si el contexto recuperado no contiene evidencia suficiente, responde:
"No tengo evidencia suficiente en los documentos recuperados para responder con certeza."
```

---

## Caso empresarial 1: asistente de contratos

Un equipo legal puede consultar contratos para responder preguntas como:

- Cual es la fecha de terminacion?
- Existen clausulas de renovacion automatica?
- Que obligaciones tiene el proveedor?
- Hay penalidades por incumplimiento?

Riesgo principal: el agente no debe inventar clausulas. Debe citar el fragmento contractual usado.

---

## Caso empresarial 2: asistente de politicas corporativas

Recursos Humanos o soporte interno puede usar RAG para responder preguntas sobre:

- vacaciones,
- beneficios,
- gastos reembolsables,
- trabajo remoto,
- seguridad de la informacion.

Riesgo principal: las politicas cambian. El sistema debe controlar version y fecha de los documentos.

---

## Caso empresarial 3: asistente sobre reportes ejecutivos

Un equipo de BI puede consultar reportes mensuales:

- Que explica la caida de ventas?
- Cuales fueron los principales riesgos?
- Que recomendaciones se hicieron en el comite anterior?
- Que KPIs cambiaron respecto al mes pasado?

Riesgo principal: confundir datos de periodos diferentes o mezclar conclusiones de reportes no comparables.

---

## Buenas practicas

Un sistema RAG empresarial debe:

- conservar trazabilidad de fuentes,
- separar respuesta de evidencia,
- mostrar limitaciones,
- evitar responder fuera del contexto recuperado,
- actualizar indices cuando cambian los documentos,
- controlar permisos de acceso,
- evaluar la calidad de la recuperacion,
- monitorear preguntas frecuentes y respuestas fallidas.

---

## Riesgos comunes

RAG reduce hallucinations, pero no las elimina.

Riesgos frecuentes:

- Recuperar documentos irrelevantes.
- Dividir mal los documentos.
- Usar documentos desactualizados.
- No controlar permisos de informacion sensible.
- Pedir al modelo que responda aunque la evidencia no sea suficiente.
- No evaluar si la respuesta esta realmente sustentada.

La calidad de un sistema RAG depende tanto de la recuperacion como de la generacion.

---

## Actividad practica

Construiremos un agente RAG para NovaRetail, una empresa ficticia de retail.

El agente tendra tres documentos internos principales:

1. `reporte_comercial_q3_2026.md`
2. `politica_descuentos_2026.md`
3. `definiciones_kpi_comerciales.md`

Como extension del ejercicio, tambien se incluyen dos documentos adicionales:

4. `acta_comite_logistica_q3_2026.md`
5. `plan_retencion_clientes_q4_2026.md`

El objetivo es que el estudiante vea la diferencia entre:

- una respuesta generica del modelo,
- una busqueda semantica sobre documentos,
- y una respuesta con evidencia recuperada.

Evolucion del ejercicio:

1. Preguntar al modelo sin RAG sobre un problema comercial.
2. Cargar documentos internos simulados.
3. Dividir los documentos en chunks.
4. Crear embeddings de los chunks.
5. Guardarlos en una base vectorial.
6. Recuperar chunks relevantes para una pregunta de negocio.
7. Generar una respuesta usando solo los chunks recuperados.
8. Evaluar si la respuesta esta sustentada en evidencia.

Preguntas sugeridas:

```text
Por que pudo caer el margen bruto en Q3?
```

```text
Que acciones deberia priorizar el equipo comercial para reducir churn?
```

```text
Un descuento de 20% puede aprobarse solo por el gerente comercial?
```

```text
Como se define churn mensual en NovaRetail?
```

Tambien se debe probar una pregunta sin evidencia suficiente:

```text
Cual fue el EBITDA de NovaRetail en Q3?
```

El agente deberia reconocer que los documentos disponibles no contienen esa informacion.

## Ejercicio adicional con nuevos documentos

Para extender la practica, los estudiantes pueden reindexar la carpeta
`data/rag_business_case` incluyendo los documentos de logistica y retencion. No
es necesario escribir codigo nuevo: basta con volver a cargar e indexar los
documentos Markdown de la carpeta y ejecutar preguntas nuevas.

Preguntas adicionales:

```text
Que ciudades intermedias deberia priorizar NovaRetail para reducir incidencias logisticas y por que?
```

```text
Que segmentos de clientes deberian recibir acciones de retencion en Q4 y que evidencia lo justifica?
```

```text
Debe NovaRetail lanzar campanas digitales agresivas en ciudades intermedias durante Q4?
```

```text
Cuando conviene ofrecer un descuento a un cliente en riesgo y cuando conviene resolver primero un problema operativo?
```

```text
Que indicadores deberia revisar semanalmente el equipo de BI para monitorear churn, logistica y descuentos?
```

Una buena respuesta RAG deberia combinar evidencia de varios documentos, por
ejemplo el reporte comercial, el acta logistica, el plan de retencion y la
politica de descuentos. Tambien deberia citar los `chunk_id` usados y reconocer
cuando la evidencia recuperada no sea suficiente.

---

## Cierre

RAG es uno de los patrones mas importantes para construir agentes empresariales porque conecta modelos de lenguaje con conocimiento especifico de la organizacion.

La idea clave no es que el modelo memorice todo. La idea es que el agente busque evidencia, la entregue al modelo y controle la respuesta para reducir invenciones.

En las siguientes sesiones, este patron servira como base para agentes mas complejos: agentes con memoria, workflows documentales y sistemas multiagente especializados.

---

## Apunte complementario

Para profundizar la explicacion conceptual y la arquitectura del agente usado en la practica, revisar:

```text
apunte_rag_y_agente_novaretail.md
```

Este apunte incluye diagramas Mermaid, una narrativa sugerida para clase y una explicacion paso a paso del agente RAG de NovaRetail.
