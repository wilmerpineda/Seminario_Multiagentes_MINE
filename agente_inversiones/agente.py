"""Agente orquestador: combina calculadoras (fábrica) + LLM Ollama."""

from __future__ import annotations

from agente_inversiones.calculadoras.base import FabricaCalculadoras
from agente_inversiones.cliente_ollama import ClienteOllama, ConfigOllama
from agente_inversiones.decoradores import log_operacion, medir_tiempo
from agente_inversiones.modelos import EntradaInversion, ResultadoInversion


class AgenteInversion:
    """Punto único de entrada para simular y explicar inversiones."""

    def __init__(self, config_ollama: ConfigOllama | None = None) -> None:
        self._fabrica = FabricaCalculadoras()
        self._llm = ClienteOllama(config_ollama)

    @log_operacion("Simulación")
    @medir_tiempo
    def simular(self, entrada: EntradaInversion) -> ResultadoInversion:
        """Resuelve la calculadora correcta y ejecuta el cálculo."""
        calculadora = self._fabrica.crear(entrada.tipo.value)
        return calculadora.calcular(entrada)

    def simular_y_explicar(
        self, entrada: EntradaInversion, usar_llm: bool = True
    ) -> tuple[ResultadoInversion, str]:
        """Calcula y, opcionalmente, pide explicación al LLM.

        Si Ollama no está disponible, retorna el resumen determinístico.
        """
        resultado = self.simular(entrada)
        if usar_llm and self._llm.disponible():
            explicacion = self._llm.explicar_resultado(resultado)
        else:
            explicacion = resultado.resumen()
        return resultado, explicacion

    def comparar(
        self, entradas: list[EntradaInversion], usar_llm: bool = True
    ) -> tuple[list[ResultadoInversion], str]:
        """Simula varias alternativas y produce una recomendación comparada."""
        resultados = [self.simular(e) for e in entradas]
        if usar_llm and self._llm.disponible():
            recomendacion = self._llm.comparar_alternativas(resultados)
        else:
            recomendacion = "\n\n".join(r.resumen() for r in resultados)
        return resultados, recomendacion
    
def procesar_consulta(self, consulta: str) -> str:
        """
        Interpreta una consulta en lenguaje natural y retorna la explicación del LLM.
        """
        # Prompt para extraer parámetros (puedes ajustar esto en prompts_agent.py después)
        prompt = f"Analiza esta consulta financiera: '{consulta}'. Extrae monto, tasa, plazo y tipo. Responde con un JSON limpio."
        
        # Aquí usamos el LLM para entender la intención
        # Nota: Ajusta 'chat_plano' si tu cliente tiene otro nombre (ej. 'chat')
        respuesta_json = self._llm.chat_plano(prompt) 
        
        # (Aquí iría la lógica para convertir el JSON a EntradaInversion)
        # Por ahora, para que funcione YA, llamaremos al simulador directamente:
        return self.simular_y_explicar(entrada_dummy, usar_llm=True)[1]