# Apunte docente - Que es RAG y como explicar el agente de NovaRetail

## Idea central para abrir la explicacion

Un LLM por si solo responde con base en patrones aprendidos durante entrenamiento y en el contexto que el usuario le entrega en el prompt.

Eso es util para explicar conceptos generales, redactar y estructurar ideas. Pero en una empresa aparece un problema:

> El modelo no conoce automaticamente los documentos internos de la organizacion.

Por ejemplo, si preguntamos:

```text
Por que cayo el margen bruto en Q3 en NovaRetail?
```

un modelo sin contexto puede responder con causas generales:

- mayores costos,
- descuentos,
- cambios en mix de producto,
- presion competitiva.

La respuesta puede sonar razonable, pero no necesariamente esta basada en los documentos reales de NovaRetail.

RAG aparece para resolver ese problema.

---

## Que es RAG

RAG significa Retrieval-Augmented Generation.

En espanol puede entenderse como:

> Generacion aumentada por recuperacion de informacion.

La idea es simple:

1. Antes de responder, el sistema busca informacion relevante.
2. Esa informacion se recupera desde documentos, bases de conocimiento o reportes.
3. El modelo recibe esos fragmentos como contexto.
4. El modelo responde usando esa evidencia.

```{mermaid}
flowchart LR
    A[Pregunta del usuario] --> B[Recuperar informacion relevante]
    B --> C[Fragmentos de documentos]
    C --> D[Prompt aumentado con contexto]
    D --> E[LLM]
    E --> F[Respuesta basada en evidencia]
```

Una forma corta de explicarlo:

```text
RAG = buscar primero + responder despues
```

O, en terminos de Inteligencia de Negocio:

```text
RAG = busqueda semantica sobre conocimiento empresarial + respuesta generada por un LLM
```

---

## Por que RAG es importante para agentes

En sesiones anteriores construimos agentes que podian:

- recibir una pregunta,
- usar un rol,
- seguir instrucciones,
- ejecutar herramientas,
- consultar datos externos.

RAG agrega una nueva capacidad:

> consultar conocimiento documental antes de responder.

Esto es clave porque muchas decisiones empresariales no dependen solo de datos estructurados. Tambien dependen de documentos:

- reportes ejecutivos,
- politicas comerciales,
- contratos,
- manuales de procesos,
- definiciones de KPIs,
- actas de comites,
- documentos de cumplimiento.

Un agente sin RAG puede sonar inteligente.

Un agente con RAG puede ser mas trazable porque puede decir:

- que documento consulto,
- que fragmentos uso,
- que evidencia encontro,
- que no pudo responder por falta de informacion.

---

## Comparacion: LLM sin RAG vs agente con RAG

| Pregunta | LLM sin RAG | Agente con RAG |
|---|---|---|
| Por que cayo el margen bruto? | Da causas generales posibles | Busca el reporte Q3 y detecta descuentos y costos logisticos |
| Como se define churn mensual? | Usa una definicion comun | Consulta el diccionario de KPIs de NovaRetail |
| Se puede aprobar un descuento de 20%? | Responde con criterio general | Consulta la politica comercial de descuentos |
| Cual fue el EBITDA de Q3? | Puede inventar o inferir | Debe decir que no hay evidencia si el documento no lo contiene |

La diferencia principal no es que RAG haga al modelo mas creativo. La diferencia es que lo conecta con fuentes especificas.

---

## Como funciona RAG paso a paso

Un sistema RAG tiene dos momentos: indexacion y consulta.

## 1. Indexacion

La indexacion ocurre antes de responder preguntas. Es el proceso de preparar los documentos para busqueda.

Pasos:

1. Cargar documentos.
2. Dividirlos en fragmentos o chunks.
3. Convertir cada chunk en un embedding.
4. Guardar embeddings y metadatos en una base vectorial.

```{mermaid}
flowchart LR
    A[Documentos internos] --> B[Chunks]
    B --> C[Embeddings]
    C --> D[Base vectorial]

    A1[Reporte Q3] --> A
    A2[Politica descuentos] --> A
    A3[Diccionario KPIs] --> A
```

En nuestro caso, los documentos son:

- `reporte_comercial_q3_2026.md`
- `politica_descuentos_2026.md`
- `definiciones_kpi_comerciales.md`

Cada documento se divide en chunks. Cada chunk tiene:

- `chunk_id`,
- texto,
- fuente,
- seccion,
- posicion.

Esto permite recuperar evidencia y mostrar de donde salio.

---

## 2. Consulta

La consulta ocurre cuando el usuario hace una pregunta.

Pasos:

1. El usuario formula una pregunta.
2. La pregunta se convierte en embedding.
3. La base vectorial busca chunks semanticamente cercanos.
4. Los chunks recuperados se insertan en el prompt.
5. El LLM genera una respuesta usando ese contexto.

```{mermaid}
flowchart LR
    A[Pregunta de negocio] --> B[Embedding de la pregunta]
    B --> C[Busqueda en ChromaDB]
    C --> D[Chunks relevantes]
    D --> E[Prompt con evidencia]
    E --> F[Qwen via Ollama]
    F --> G[Respuesta con fuentes]
```

Ejemplo:

```text
Pregunta:
Por que pudo caer el margen bruto en Q3?
```

El sistema deberia recuperar fragmentos del reporte que mencionan:

- margen bruto de Q3,
- comparacion con Q2,
- mayores descuentos,
- incremento en costos logisticos.

Luego el modelo responde usando esos fragmentos.

---

## Que son embeddings

Un embedding es una representacion numerica de un texto.

La intuicion:

> textos con significados parecidos quedan cerca en un espacio numerico.

Ejemplo:

```text
Por que bajo el margen?
Que explica la caida de rentabilidad?
Cuales fueron las causas del menor margen bruto?
```

Estas preguntas usan palabras distintas, pero buscan una idea similar. La busqueda semantica permite recuperar el fragmento correcto aunque el usuario no use exactamente las mismas palabras del documento.

```{mermaid}
flowchart TD
    A[Texto] --> B[Modelo de embeddings]
    B --> C[Vector numerico]
    C --> D[Comparacion de similitud]
    D --> E[Textos semanticamente cercanos]
```

En el notebook usamos:

- `nomic-embed-text` para embeddings,
- `ChromaDB` como base vectorial,
- `qwen2.5:3b` como modelo generador.

---

## Como explicar el agente que creamos

El agente que creamos se puede explicar como un asistente de BI con acceso controlado a documentos internos.

No es simplemente un chatbot. Tiene cuatro partes:

```{mermaid}
flowchart LR
    A[Usuario de negocio] --> B[RAGCourseAssistant]
    B --> C[ChromaCourseVectorStore]
    C --> D[Documentos NovaRetail]
    C --> E[Chunks recuperados]
    E --> F[Prompt RAG]
    F --> G[LLM local Ollama]
    G --> H[Respuesta con fuentes]
```

## 1. Documentos

Los documentos estan en:

```text
data/rag_business_case/
```

Representan conocimiento interno de NovaRetail:

- reporte comercial,
- politica de descuentos,
- definiciones de KPIs.

## 2. Chunking

El archivo `chunker.py` divide documentos en fragmentos.

Esto evita enviar documentos completos al modelo y permite recuperar solo lo relevante.

## 3. Vector store

El archivo `vector_store.py` usa ChromaDB.

Su responsabilidad es:

- crear embeddings,
- guardar chunks,
- buscar los chunks mas cercanos a una pregunta.

## 4. Agente

El archivo `agent.py` coordina el flujo:

1. carga documentos,
2. construye chunks,
3. indexa en ChromaDB,
4. recibe preguntas,
5. recupera contexto,
6. llama al modelo,
7. entrega respuesta y fuentes.

---

## Flujo completo del agente

```{mermaid}
sequenceDiagram
    participant U as Usuario
    participant A as Agente RAG
    participant V as ChromaDB
    participant L as LLM

    U->>A: Hace una pregunta de negocio
    A->>V: Busca chunks relevantes
    V-->>A: Devuelve fragmentos y metadatos
    A->>L: Envia pregunta + contexto recuperado
    L-->>A: Genera respuesta basada en evidencia
    A-->>U: Respuesta + fuentes usadas
```

---

## Como narrarlo en clase

Una secuencia clara para explicarlo:

1. Primero mostrar el problema:

```text
Un modelo general puede responder sobre margen, churn o descuentos, pero no conoce la informacion interna de NovaRetail.
```

2. Luego mostrar la solucion:

```text
RAG permite que el agente busque primero en documentos internos y responda despues.
```

3. Despues mostrar la arquitectura:

```text
Documentos -> chunks -> embeddings -> ChromaDB -> recuperacion -> prompt aumentado -> respuesta.
```

4. Luego ejecutar una pregunta:

```text
Por que pudo caer el margen bruto en Q3?
```

5. Antes de mostrar la respuesta final, inspeccionar los chunks recuperados.

Esto es importante pedagogicamente porque los estudiantes ven que el agente no "adivina": recupera evidencia.

6. Finalmente probar una pregunta sin evidencia:

```text
Cual fue el EBITDA de NovaRetail en Q3?
```

La respuesta correcta no es inventar. La respuesta correcta es reconocer que los documentos disponibles no contienen esa informacion.

---

## Mensaje clave para los estudiantes

RAG no reemplaza los dashboards, las bases de datos ni la analitica tradicional.

RAG agrega una capa conversacional sobre conocimiento no estructurado.

Es valioso cuando:

- la informacion esta en documentos,
- los usuarios preguntan en lenguaje natural,
- se necesita trazabilidad,
- se quiere reducir alucinaciones,
- el agente debe reconocer limites de evidencia.

La idea central:

> Un agente RAG no deberia responder porque "sabe". Deberia responder porque encontro evidencia.

