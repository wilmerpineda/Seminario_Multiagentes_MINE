"""Decoradores reutilizables: validación, logging, medición de tiempo y registro en fábrica.

Diseñados para envolver métodos de calculadoras y mantener el código escalable.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

from agente_inversiones.modelos import EntradaInversion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
)
logger = logging.getLogger("agente")

F = TypeVar("F", bound=Callable[..., Any])


def validar_entrada(func: F) -> F:
    """Valida que el primer argumento posicional sea un EntradaInversion válido.

    Pydantic ya valida en construcción; este decorador defiende llamadas dinámicas
    (p.ej. dict pasado por el LLM via tool calling).
    """

    @functools.wraps(func)
    def wrapper(self: Any, entrada: Any, *args: Any, **kwargs: Any) -> Any:
        if not isinstance(entrada, EntradaInversion):
            entrada = EntradaInversion.model_validate(entrada)
        return func(self, entrada, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


def medir_tiempo(func: F) -> F:
    """Mide y loguea el tiempo de ejecución del método."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - inicio) * 1000
        logger.info(f"{func.__qualname__} ejecutado en {elapsed_ms:.2f} ms")
        return resultado

    return wrapper  # type: ignore[return-value]


def log_operacion(nombre: str) -> Callable[[F], F]:
    """Loguea inicio/fin de una operación de negocio etiquetada."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"▶ INICIO :: {nombre}")
            resultado = func(*args, **kwargs)
            logger.info(f"✓ FIN    :: {nombre}")
            return resultado

        return wrapper  # type: ignore[return-value]

    return decorator


# ── Decorador de clase: registro automático en la fábrica ──────────────────────
_REGISTRO_CALCULADORAS: dict[str, type] = {}


def registrar_calculadora(clave: str) -> Callable[[type], type]:
    """Decorador de clase. Registra la calculadora en un diccionario global,
    permitiendo que la fábrica resuelva por clave sin imports manuales.

    Uso:
        @registrar_calculadora("cdt")
        class CalculadoraCDT(CalculadoraBase): ...
    """

    def decorator(cls: type) -> type:
        if clave in _REGISTRO_CALCULADORAS:
            logger.warning(f"Sobrescribiendo calculadora '{clave}'")
        _REGISTRO_CALCULADORAS[clave] = cls
        logger.info(f"Registrada calculadora '{clave}' → {cls.__name__}")
        return cls

    return decorator


def obtener_registro() -> dict[str, type]:
    """Devuelve una copia inmutable-like del registro actual."""
    return dict(_REGISTRO_CALCULADORAS)
