"""Clase base abstracta (ABC) y fábrica para calculadoras de inversión.

Patrón: cada calculadora concreta hereda de CalculadoraBase y se registra
con @registrar_calculadora("clave"). La fábrica resuelve por clave.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agente_inversiones.decoradores import obtener_registro
from agente_inversiones.modelos import (
    EntradaInversion,
    Periodicidad,
    ResultadoInversion,
    TipoTasa,
)


class CalculadoraBase(ABC):
    """Contrato común para todas las calculadoras de inversión."""

    @abstractmethod
    def calcular(self, entrada: EntradaInversion) -> ResultadoInversion:
        """Ejecuta el cálculo y retorna un ResultadoInversion."""

    # ── Utilidades compartidas de conversión de tasas ──────────────────────────
    @staticmethod
    def tasa_periodica(
        tasa: float, tipo_tasa: TipoTasa, periodicidad: Periodicidad
    ) -> float:
        """Convierte la tasa de entrada a su equivalente periódica (decimal).

        - NOMINAL: i_per = TNA / m
        - EFECTIVA_ANUAL (TEA): i_per = (1 + TEA)^(1/m) - 1
        """
        m = periodicidad.periodos_por_anio
        if tipo_tasa is TipoTasa.NOMINAL:
            return tasa / m
        # TEA
        return (1 + tasa) ** (1 / m) - 1

    @staticmethod
    def tasa_efectiva_anual(tasa_periodica: float, periodicidad: Periodicidad) -> float:
        """Calcula la TEA equivalente a una tasa periódica."""
        m = periodicidad.periodos_por_anio
        return (1 + tasa_periodica) ** m - 1


class FabricaCalculadoras:
    """Fábrica que entrega la calculadora correcta según una clave.

    Las calculadoras se autoregistran al importarse (decorador
    @registrar_calculadora). Por eso aquí forzamos los imports.
    """

    @staticmethod
    def crear(clave: str) -> CalculadoraBase:
        """Instancia la calculadora identificada por `clave`."""
        # Imports diferidos para activar los decoradores de registro:
        # pylint: disable=import-outside-toplevel,unused-import
        from agente_inversiones.calculadoras import renta_fija  # noqa: F401
        from agente_inversiones.calculadoras import renta_variable
        from agente_inversiones.calculadoras import creditos

        registro = obtener_registro()
        if clave not in registro:
            disponibles = ", ".join(sorted(registro)) or "(ninguna)"
            raise ValueError(
                f"No existe calculadora '{clave}'. Disponibles: {disponibles}"
            )
        return registro[clave]()
