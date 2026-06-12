# 📈 Agente Financiero Inteligente (Local LLM)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-dependency%20manager-60A5FA?style=flat&logo=poetry&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

> Un agente financiero potenciado por **Inteligencia Artificial Local (Ollama)** que combina cálculos matemáticos determinísticos en Python con la capacidad explicativa y conversacional de los Modelos de Lenguaje Grande (LLMs).

Este sistema evita las *"alucinaciones"* matemáticas de la IA realizando todos los cálculos de forma estricta en el código, y utilizando el LLM exclusivamente para el análisis, extracción de datos y la redacción de informes financieros en lenguaje natural.

---

## ✨ Características Principales

| Característica | Descripción |
|---|---|
| 🧠 **IA Local y Privada** | Integración nativa con Ollama (`qwen2.5`, `llama3`) — tus datos financieros nunca salen de tu máquina |
| 🧮 **Motor Matemático Determinístico** | Calculadoras robustas para CDT (Renta Fija), Renta Variable (Monte Carlo / GBM) y Créditos |
| 🏗️ **Arquitectura Escalable** | Patrón Factory + decoradores (`@registrar_calculadora`) para agregar productos financieros sin tocar el orquestador |
| 🛡️ **Tipado Estricto** | Validación rigurosa de entradas con **Pydantic v2** |
| 💻 **Interfaz Dual** | CLI interactiva (Typer + Rich) y soporte nativo para **Jupyter Notebooks** |

---

## 🏗️ Arquitectura del Sistema

El proyecto implementa un flujo de **Tool Calling** en tres etapas:

```
Usuario (lenguaje natural)
        │
        ▼
┌──────────────────┐
│  1. EXTRACCIÓN   │  ← LLM interpreta la pregunta y extrae un JSON tipado
│   (Planificador) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. EJECUCIÓN    │  ← Fábrica dirige el JSON a la calculadora correcta
│     (Fábrica)    │     (Renta Fija / Variable / Créditos)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. SÍNTESIS     │  ← LLM redacta el informe final con los resultados
│    (Experto)     │     matemáticos inyectados via System Prompt
└──────────────────┘
        │
        ▼
  Informe en lenguaje natural
```

---

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python >= 3.10
- [Ollama](https://ollama.com/) instalado y corriendo localmente

### 1. Instalar Poetry

Poetry es el gestor de dependencias y entornos virtuales del proyecto. Si aún no lo tienes:

```bash
# Instalador oficial (recomendado — Linux / macOS / WSL)
curl -sSL https://install.python-poetry.org | python3 -

# O con pip (alternativa)
pip install poetry
```

Verifica la instalación:

```bash
poetry --version
```

> Consulta la [documentación oficial de Poetry](https://python-poetry.org/docs/) para opciones avanzadas de instalación.

### 2. Clonar e instalar dependencias

```bash
git clone https://github.com/tu-usuario/agente-inversiones.git
cd agente-inversiones
poetry install
```

Esto crea automáticamente un entorno virtual aislado e instala todas las dependencias definidas en `pyproject.toml`.

### 3. Descargar el modelo de lenguaje

```bash
ollama pull qwen2.5:3b   # Modelo base recomendado
# También puedes usar: ollama pull llama3
```

> El modelo activo se configura en `cliente_ollama.py`.

### Comandos útiles de Poetry

```bash
# Activar el entorno virtual en la terminal actual
poetry shell

# Ejecutar un comando dentro del entorno sin activarlo
poetry run python script.py

# Agregar una nueva dependencia al proyecto
poetry add nombre-paquete

# Agregar una dependencia solo para desarrollo
poetry add nombre-paquete --group dev

# Actualizar todas las dependencias
poetry update

# Ver el entorno virtual activo y su ruta
poetry env info
```

---

## 💻 Uso

### Desde la Terminal (CLI)

```bash
# Simular un CDT a 12 meses
poetry run agente cdt \
  --monto 10000000 \
  --tasa 0.12 \
  --tipo-tasa efectiva_anual \
  --periodicidad mensual \
  --plazo 12

# Simular un crédito
poetry run agente credito \
  --monto 50000000 \
  --tasa 0.22 \
  --plazo 60
```

### Desde Python / Jupyter Notebook (Lenguaje Natural)

```python
from agente_inversiones.agente import AgenteInversion
from agente_inversiones.cliente_ollama import ConfigOllama

agente = AgenteInversion(config_ollama=ConfigOllama(modelo="qwen2.5:3b"))

pregunta = "¿Cuánto termino pagando de intereses si pido 50 millones al 22% a 5 años?"
respuesta = agente.procesar_consulta(pregunta)

print(respuesta)
```

---

## 📂 Estructura del Proyecto

```
agente_inversiones/
├── __init__.py
├── agente.py            # Orquestador principal e integrador de LLM
├── cliente_ollama.py    # Cliente para la comunicación con Ollama
├── decoradores.py       # Logging, medición de tiempo y autoregistro
├── main.py              # Interfaz CLI con Typer
├── modelos.py           # Esquemas de validación Pydantic
├── prompts_agent.py     # System Prompts para guiar el comportamiento de la IA
├── calculadoras/
│   ├── base.py          # Clase abstracta y FabricaCalculadoras
│   ├── renta_fija.py    # Simulación de CDT
│   ├── renta_variable.py# Simulación con Monte Carlo / GBM
│   └── creditos.py      # Simulación de cuotas de amortización
└── Experimentos/        # Jupyter Notebooks para investigación y pruebas
```

---

## 🛠️ Cómo Agregar un Nuevo Producto Financiero

Gracias a la arquitectura **plug-and-play**, agregar una nueva calculadora (ej. Leasing) toma solo **2 pasos**:

**Paso 1 — Registrar el tipo en `modelos.py`:**
```python
# Agrega el nuevo tipo al Enum de productos
class TipoProducto(str, Enum):
    CDT = "cdt"
    CREDITO = "credito"
    LEASING = "leasing"   # ← nuevo
```

**Paso 2 — Crear la calculadora en `calculadoras/leasing.py`:**
```python
from agente_inversiones.calculadoras.base import CalculadoraBase
from agente_inversiones.decoradores import registrar_calculadora

@registrar_calculadora("leasing")
class CalculadoraLeasing(CalculadoraBase):
    def calcular(self, entrada):
        # Lógica matemática determinística aquí
        return resultado
```

> ✅ El agente reconoce la nueva calculadora **automáticamente**. No es necesario modificar el orquestador principal.

---

## 📝 Licencia

Este proyecto está bajo la **Licencia MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
