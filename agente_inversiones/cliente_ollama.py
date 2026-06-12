"""Cliente Ollama para el modelo qwen2.5:32b.

Encapsula:
- Chat plano (explicaciones en lenguaje natural)
- Modo "razonador financiero" con system prompt cargado en español
"""

from __future__ import annotations

from dataclasses import dataclass

import ollama

from agente_inversiones.modelos import ResultadoInversion

_SYSTEM_PROMPT_ASESOR = """Eres un asesor financiero experto en mercado colombiano.
Tu tarea: explicar resultados de inversión (CDT, renta variable) en español claro,
cuantitativo y honesto. Reglas:
- Usa cifras con formato $#,##0.00 y tasas con cuatro decimales.
- Diferencia explícitamente TNA (Tasa Nominal Anual) y TEA (Tasa Efectiva Anual).
- Para CDT, recuerda que la retención en la fuente es 7 % sobre los rendimientos
  cuando los intereses superan los topes UVT.
- Para renta variable, NO prometas retornos: habla siempre de "expectativa" y rango.
- No inventes datos no presentes en el contexto que recibes.
"""


@dataclass(slots=True)
class ConfigOllama:
    """Configuración del cliente Ollama."""

    modelo: str = "qwen2.5:32b"
    host: str = "http://localhost:11434"
    temperatura: float = 0.2
    max_tokens: int = 1024


class ClienteOllama:
    """Wrapper simple sobre `ollama` con un par de modos."""

    def __init__(self, config: ConfigOllama | None = None) -> None:
        self.config = config or ConfigOllama()
        self._cliente = ollama.Client(host=self.config.host)

    def disponible(self) -> bool:
        """Verifica que el daemon Ollama responda y el modelo esté instalado."""
        try:
            modelos = self._cliente.list().get("models", [])
            nombres = {m.get("name", "") for m in modelos}
            return any(self.config.modelo in n for n in nombres)
        except (ConnectionError, OSError, ollama.ResponseError):
            return False

    def explicar_resultado(self, resultado: ResultadoInversion) -> str:
        """Pide al LLM una explicación cualitativa del resultado."""
        contexto = resultado.model_dump_json(indent=2)
        prompt = (
            "A partir de este resultado de simulación (JSON), redacta una "
            "explicación de máximo 8 frases para un inversionista no técnico:\n\n"
            f"{contexto}"
        )
        respuesta = self._cliente.chat(
            model=self.config.modelo,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT_ASESOR},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": self.config.temperatura,
                "num_predict": self.config.max_tokens,
            },
        )
        return respuesta["message"]["content"]

    def comparar_alternativas(self, resultados: list[ResultadoInversion]) -> str:
        """Compara varias alternativas y emite una recomendación."""
        bloques = [r.model_dump_json(indent=2) for r in resultados]
        prompt = (
            "Compara las siguientes alternativas de inversión (lista JSON) y "
            "recomienda cuál ofrece mejor relación rentabilidad/riesgo para un "
            "perfil moderado, justificando con cifras:\n\n"
            + "\n---\n".join(bloques)
        )
        respuesta = self._cliente.chat(
            model=self.config.modelo,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT_ASESOR},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": self.config.temperatura,
                "num_predict": self.config.max_tokens,
            },
        )
        return respuesta["message"]["content"]
