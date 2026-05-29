# Prompt Engineering: Programando el Comportamiento de los Agentes

## Preparación del entorno

### 1. Instalar Ollama

Descargar e instalar Ollama desde:

https://ollama.com/download

Verificar instalación:

```bash
ollama --version
```

### 2. Descargar un modelo local

```bash
ollama run qwen2.5:3b
```

Alternativamente:

```bash
ollama run phi3
```

### 3. Instalar dependencias

```bash
poetry install
```

### 4. Registrar el kernel de Jupyter

```bash
poetry run python -m ipykernel install --user --name experiment-analyst-agent --display-name "Experiment Analyst Agent"
```

### 5. Verificar Ollama

```bash
ollama list
```

# ¿Por qué necesitamos Prompt Engineering?

Prompt Engineering es la disciplina que estudia cómo diseñar instrucciones para controlar el comportamiento de los modelos de lenguaje y obtener respuestas útiles, precisas y alineadas con un objetivo.

# Los componentes fundamentales de un prompt

## Rol

```text
Actúa como un analista senior de experimentación digital.
```

## Contexto

```text
Journey presenta un Activation Rate de 25.33%.
MLD presenta un Activation Rate de 23.37%.
```

## Tarea

```text
Identifica posibles causas que expliquen las diferencias observadas.
```

## Restricciones

```text
- No inventes información.
- Diferencia hechos de hipótesis.
- Utiliza lenguaje ejecutivo.
```

## Formato esperado

```text
1. Hallazgos.
2. Hipótesis.
3. Riesgos.
4. Recomendaciones.
```

# Anatomía de un agente moderno

```text
Agente =
Modelo
+
Rol
+
Contexto
+
Objetivo
+
Restricciones
+
Formato de salida
```

# ¿Qué vamos a construir hoy?

Durante esta sesión construiremos nuestro primer agente especializado utilizando:

- Ollama
- Qwen 2.5 3B
- Python
- Poetry
- Un caso empresarial de experimentación A/B en Mercado Pago

Posteriormente construiremos un agente especializado en análisis de experimentación digital.
