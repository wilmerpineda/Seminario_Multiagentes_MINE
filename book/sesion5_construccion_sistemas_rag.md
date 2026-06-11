# Sesion 5 - Construccion de Sistemas RAG

## De un demo RAG a un chatbot documental

En la sesion 4 construimos un asistente RAG con documentos internos simulados de
NovaRetail. La idea central fue entender que un agente empresarial no deberia
responder solo desde conocimiento general: debe recuperar evidencia y usarla para
generar una respuesta trazable.

En esta sesion llevamos esa arquitectura a un escenario mas cercano a un sistema
real: un chatbot que puede cargar documentos PDF, crear una base vectorial local,
recuperar fragmentos relevantes y evaluar si la respuesta esta sustentada.

La pregunta guia cambia de:

```text
Como funciona RAG?
```

a:

```text
Como construimos un chatbot empresarial que responda sobre documentos reales?
```

---

## Caso guia

Construiremos un chatbot para consultar reportes publicos utiles para analisis
de negocio, politica publica, transformacion digital o inteligencia artificial.

Fuentes sugeridas:

- World Bank Open Knowledge Repository: repositorio oficial de acceso abierto del
  Banco Mundial.
- Publicaciones abiertas de la OCDE.
- Stanford AI Index Report, si se quiere trabajar sobre tendencias de IA.

La recomendacion para clase es usar uno o dos PDFs pequenos o secciones
extractadas. El objetivo no es indexar miles de paginas, sino observar el flujo
completo de un sistema RAG.

---

## Objetivos de aprendizaje

Al finalizar esta sesion, el estudiante estara en capacidad de:

1. Procesar documentos PDF para convertirlos en texto consultable.
2. Dividir documentos en chunks con metadatos de fuente y pagina.
3. Construir una base vectorial local como memoria documental.
4. Integrar recuperacion documental con generacion de respuestas.
5. Evaluar respuestas por relevancia, grounding y precision documental.
6. Reconocer riesgos practicos en chatbots empresariales sobre informacion interna.

---

## Arquitectura del sistema

```{mermaid}
flowchart LR
    A[PDFs publicos] --> B[Extraccion de texto]
    B --> C[Chunking por paginas y parrafos]
    C --> D[Embeddings con Ollama]
    D --> E[ChromaDB local]
    F[Pregunta del usuario] --> G[Busqueda vectorial]
    E --> G
    G --> H[Contexto recuperado]
    H --> I[Prompt aumentado]
    I --> J[LLM local]
    J --> K[Respuesta con fuentes]
```

El sistema tiene dos momentos:

- Indexacion: preparar documentos y guardarlos en la base vectorial.
- Consulta: recuperar evidencia y generar una respuesta sustentada.

---

## Procesamiento de documentos

Los PDFs no son automaticamente conocimiento util para un modelo. Primero deben
pasar por un flujo de preparacion:

1. Extraer texto por pagina.
2. Normalizar espacios y saltos de linea.
3. Dividir en fragmentos manejables.
4. Guardar metadatos: fuente, pagina, posicion y chunk.

La pagina es un metadato importante porque permite volver al documento original.
En un sistema empresarial real, tambien se agregarian fecha, version, area,
permisos y estado de vigencia.

---

## Chunking y recuperacion de contexto

El chunking define que evidencia vera el modelo. Si el chunk es demasiado grande,
la respuesta puede recibir ruido. Si es demasiado pequeno, puede perder contexto.

Para esta practica usaremos:

- chunks de alrededor de 1200 caracteres,
- solapamiento pequeno entre chunks,
- metadatos de pagina,
- recuperacion de los 5 chunks mas cercanos.

El estudiante debe experimentar con `top_k` y tamano de chunk para observar como
cambia la evidencia recuperada.

---

## Base vectorial como memoria documental

ChromaDB se usara como base vectorial local. En esta sesion no buscamos construir
infraestructura de produccion, sino entender el patron:

```text
Texto -> embedding -> almacenamiento vectorial -> busqueda por similitud
```

La memoria documental no es memoria conversacional. La base vectorial guarda
fragmentos de documentos; el historial del chat guarda interacciones del usuario.
Ambas memorias pueden coexistir, pero resuelven problemas distintos.

---

## Chatbot empresarial

La aplicacion Streamlit permitira:

- cargar PDFs o Markdown,
- indexar documentos,
- hacer preguntas en lenguaje natural,
- ver la respuesta del modelo,
- inspeccionar los chunks recuperados,
- revisar una evaluacion simple de grounding.

Comando sugerido:

```bash
streamlit run apps/sesion5_rag_chatbot.py
```

Modelos locales sugeridos:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

---

## Evaluacion de respuestas

Una respuesta RAG no se evalua solo por sonar bien. Debe responder:

- Relevancia: responde la pregunta del usuario?
- Grounding: usa informacion del contexto recuperado?
- Precision documental: evita inventar datos no presentes?
- Fuentes: cita los chunks usados?
- Limitacion: reconoce cuando la evidencia no alcanza?

Preguntas de prueba:

```text
Que argumentos presenta el documento sobre el valor de los datos para tomar decisiones?
```

```text
Que riesgos menciona el documento sobre uso de datos o IA?
```

```text
Que recomendaciones del documento serian utiles para una oficina de BI?
```

Pregunta sin evidencia esperada:

```text
Cual fue el presupuesto interno exacto de la organizacion para este proyecto?
```

El chatbot debe indicar que no tiene evidencia suficiente si esa informacion no
aparece en los documentos recuperados.

---

## Actividad practica

1. Descargar uno o dos PDFs publicos de las fuentes sugeridas.
2. Ejecutar la app Streamlit.
3. Cargar e indexar los documentos.
4. Probar preguntas con evidencia clara.
5. Probar preguntas sin evidencia.
6. Comparar chunks recuperados frente a respuesta generada.
7. Ajustar `top_k` y discutir el impacto en calidad.
8. Completar una mini-rubrica de evaluacion por respuesta.

---

## Cierre

Construir un sistema RAG implica mas que conectar un LLM a documentos. La calidad
depende de la preparacion documental, el chunking, la base vectorial, el prompt,
la trazabilidad y la evaluacion.

Para BI, el valor principal esta en convertir documentos dispersos en una
interfaz consultable, sin perder evidencia ni control sobre las fuentes.
