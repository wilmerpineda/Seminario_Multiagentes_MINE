"""Calculadora de renta variable — Monte Carlo bajo Movimiento Browniano Geométrico.

Modelo (estándar para acciones/ETF):
    S_T = S_0 · exp((μ − σ²/2)·T + σ·√T·Z),   Z ~ N(0,1)

Donde:
    μ = retorno esperado anual (decimal, p.ej. 0.12)
    σ = volatilidad anual (decimal, p.ej. 0.20)
    T = horizonte en años (derivado del plazo + periodicidad)

Si el usuario no envía volatilidad, se cae a un modelo determinístico (compuesto).
"""

from __future__ import annotations

import numpy as np

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


@registrar_calculadora("renta_variable")
class CalculadoraRentaVariable(CalculadoraBase):
    """Simula trayectorias con GBM y reporta VF esperado + percentiles."""

    _SEMILLA_DEFECTO = 42

    @validar_entrada
    @medir_tiempo
    @log_operacion("Cálculo Renta Variable (Monte Carlo)")
    def calcular(self, entrada: EntradaInversion) -> ResultadoInversion:
        """Calcula VF esperado y distribución para renta variable."""
        i_per = self.tasa_periodica(entrada.tasa, entrada.tipo_tasa, entrada.periodicidad)
        tea = self.tasa_efectiva_anual(i_per, entrada.periodicidad)
        m = entrada.periodicidad.periodos_por_anio
        anios = entrada.plazo_periodos / m
        vp = entrada.monto

        if entrada.volatilidad is None or entrada.volatilidad == 0:
            # Caso determinístico: compuesto puro
            vf_esperado = vp * (1 + i_per) ** entrada.plazo_periodos
            detalles: dict = {"modelo": "deterministico", "n_simulaciones": 0}
        else:
            n_sim = entrada.n_simulaciones or 10_000
            sigma = entrada.volatilidad
            mu = tea  # usamos la TEA como retorno esperado anual

            rng = np.random.default_rng(self._SEMILLA_DEFECTO)
            z = rng.standard_normal(n_sim)
            s_t = vp * np.exp((mu - 0.5 * sigma**2) * anios + sigma * np.sqrt(anios) * z)

            vf_esperado = float(np.mean(s_t))
            detalles = {
                "modelo": "monte_carlo_gbm",
                "n_simulaciones": n_sim,
                "volatilidad": sigma,
                "vf_mediana": float(np.median(s_t)),
                "vf_p05": float(np.percentile(s_t, 5)),
                "vf_p95": float(np.percentile(s_t, 95)),
                "prob_perdida": float(np.mean(s_t < vp)),
            }

        return ResultadoInversion(
            tipo=TipoInversion.RENTA_VARIABLE,
            valor_presente=vp,
            valor_futuro=vf_esperado,
            rentabilidad=vf_esperado - vp,
            rentabilidad_porcentual=(vf_esperado / vp - 1) * 100,
            tasa_periodica=i_per,
            tasa_efectiva_anual=tea,
            tipo_tasa_origen=entrada.tipo_tasa,
            periodicidad=entrada.periodicidad,
            plazo_periodos=entrada.plazo_periodos,
            plazo_anios=anios,
            detalles=detalles,
        )
