"""Calculadora de renta fija — CDT (Certificado de Depósito a Término).

Fórmulas:
    VF = VP · (1 + i_per)^n
donde i_per se obtiene desde:
    - Tasa NOMINAL  : i_per = TNA / m
    - Tasa EFECTIVA : i_per = (1 + TEA)^(1/m) − 1
con m = periodos por año (12/4/2/1).
"""

from __future__ import annotations

from agente_inversiones.calculadoras.base import CalculadoraBase
from agente_inversiones.decoradores import (
    log_operacion,
    medir_tiempo,
    registrar_calculadora,
    validar_entrada,
)
from agente_inversiones.modelos import (
    EntradaInversion,
    ResultadoInversion,
    TipoInversion,
)


@registrar_calculadora("cdt")
class CalculadoraCDT(CalculadoraBase):
    """Simula un CDT con capitalización en la periodicidad indicada."""

    @validar_entrada
    @medir_tiempo
    @log_operacion("Cálculo CDT")
    def calcular(self, entrada: EntradaInversion) -> ResultadoInversion:
        """Calcula valor futuro, rentabilidad y tasas equivalentes para un CDT."""
        i_per = self.tasa_periodica(entrada.tasa, entrada.tipo_tasa, entrada.periodicidad)
        n = entrada.plazo_periodos
        vp = entrada.monto

        vf = vp * (1 + i_per) ** n
        rentabilidad = vf - vp
        tea = self.tasa_efectiva_anual(i_per, entrada.periodicidad)
        plazo_anios = n / entrada.periodicidad.periodos_por_anio

        return ResultadoInversion(
            tipo=TipoInversion.CDT,
            valor_presente=vp,
            valor_futuro=vf,
            rentabilidad=rentabilidad,
            rentabilidad_porcentual=(vf / vp - 1) * 100,
            tasa_periodica=i_per,
            tasa_efectiva_anual=tea,
            tipo_tasa_origen=entrada.tipo_tasa,
            periodicidad=entrada.periodicidad,
            plazo_periodos=n,
            plazo_anios=plazo_anios,
            detalles={
                "formula": "VF = VP·(1+i_per)^n",
                "m_periodos_anio": entrada.periodicidad.periodos_por_anio,
            },
        )
