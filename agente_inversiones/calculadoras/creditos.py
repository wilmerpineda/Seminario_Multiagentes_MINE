from agente_inversiones.calculadoras.base import CalculadoraBase
from agente_inversiones.decoradores import log_operacion, medir_tiempo, registrar_calculadora, validar_entrada
from agente_inversiones.modelos import EntradaInversion, ResultadoInversion, TipoInversion

@registrar_calculadora("credito")
class CalculadoraCredito(CalculadoraBase):
    """Calcula la cuota y los intereses de un préstamo."""

    @validar_entrada
    @medir_tiempo
    @log_operacion("Cálculo Crédito")
    def calcular(self, entrada: EntradaInversion) -> ResultadoInversion:
        i_per = self.tasa_periodica(entrada.tasa, entrada.tipo_tasa, entrada.periodicidad)
        n = entrada.plazo_periodos
        vp = entrada.monto  

        # Fórmula de cuota fija
        if i_per > 0:
            cuota = vp * (i_per * (1 + i_per)**n) / ((1 + i_per)**n - 1)
        else:
            cuota = vp / n 

        monto_total_pagar = cuota * n
        intereses_totales = monto_total_pagar - vp
        tea = self.tasa_efectiva_anual(i_per, entrada.periodicidad)

        return ResultadoInversion(
            tipo=TipoInversion.CREDITO,
            valor_presente=vp,
            valor_futuro=-monto_total_pagar,  
            rentabilidad=-intereses_totales,  
            rentabilidad_porcentual=-(intereses_totales / vp) * 100,
            tasa_periodica=i_per,
            tasa_efectiva_anual=tea,
            tipo_tasa_origen=entrada.tipo_tasa,
            periodicidad=entrada.periodicidad,
            plazo_periodos=n,
            plazo_anios=n / entrada.periodicidad.periodos_por_anio,
            detalles={"cuota_por_periodo": float(cuota), "intereses_totales": float(intereses_totales)}
        )