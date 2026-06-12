"""Modelos de datos del dominio: enums de tasas/periodos y entradas/salidas con Pydantic v2."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Periodicidad(str, Enum):
    """Periodicidad de capitalización / liquidación."""

    MENSUAL = "mensual"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"

    @property
    def periodos_por_anio(self) -> int:
        """Número de periodos por año (m)."""
        return {
            Periodicidad.MENSUAL: 12,
            Periodicidad.TRIMESTRAL: 4,
            Periodicidad.SEMESTRAL: 2,
            Periodicidad.ANUAL: 1,
        }[self]


class TipoTasa(str, Enum):
    """Naturaleza de la tasa ingresada."""

    NOMINAL = "nominal"  # TNA con capitalización en la periodicidad indicada
    EFECTIVA_ANUAL = "efectiva_anual"  # TEA


class TipoInversion(str, Enum):
    """Tipos de inversión soportados por el agente."""

    CDT = "cdt"
    RENTA_VARIABLE = "renta_variable"
    CREDITO = "credito"


class EntradaInversion(BaseModel):
    """Parámetros de entrada para una simulación de inversión."""

    tipo: TipoInversion
    monto: float = Field(..., gt=0, description="Valor presente / capital invertido")
    tasa: float = Field(..., gt=0, description="Tasa en términos decimales (0.12 = 12 %)")
    tipo_tasa: TipoTasa = TipoTasa.EFECTIVA_ANUAL
    periodicidad: Periodicidad = Periodicidad.ANUAL
    plazo_periodos: int = Field(..., gt=0, description="Plazo en número de periodos")
    # Solo aplica a renta variable:
    volatilidad: float | None = Field(default=None, ge=0, description="Volatilidad anual (σ)")
    n_simulaciones: int | None = Field(default=None, gt=0, description="Iteraciones Monte Carlo")

    @field_validator("tasa")
    @classmethod
    def _tasa_razonable(cls, v: float) -> float:
        if v > 5:
            raise ValueError("La tasa parece estar en porcentaje. Use decimal (12 % = 0.12).")
        return v


class ResultadoInversion(BaseModel):
    """Salida estandarizada de cualquier calculadora."""

    tipo: TipoInversion
    valor_presente: float
    valor_futuro: float
    rentabilidad: float  # VF - VP
    rentabilidad_porcentual: float  # (VF/VP - 1) * 100
    tasa_periodica: float  # tasa aplicada a cada periodo (decimal)
    tasa_efectiva_anual: float  # TEA equivalente
    tipo_tasa_origen: TipoTasa
    periodicidad: Periodicidad
    plazo_periodos: int
    plazo_anios: float
    detalles: dict = Field(default_factory=dict)  # extra (p.ej. percentiles MC)

    def resumen(self) -> str:
        """Resumen legible para humanos (es-CO)."""
        return (
            f"Tipo: {self.tipo.value.upper()}\n"
            f"Valor presente:        ${self.valor_presente:,.2f}\n"
            f"Valor futuro:          ${self.valor_futuro:,.2f}\n"
            f"Rentabilidad:          ${self.rentabilidad:,.2f} "
            f"({self.rentabilidad_porcentual:.2f} %)\n"
            f"Tasa origen:           {self.tipo_tasa_origen.value} "
            f"({self.periodicidad.value})\n"
            f"Tasa periódica aplic.: {self.tasa_periodica * 100:.4f} %\n"
            f"TEA equivalente:       {self.tasa_efectiva_anual * 100:.4f} %\n"
            f"Plazo:                 {self.plazo_periodos} periodos "
            f"({self.plazo_anios:.2f} años)"
        )


# Tipo auxiliar para el factory
NombreCalculadora = Literal["cdt", "renta_variable"]
