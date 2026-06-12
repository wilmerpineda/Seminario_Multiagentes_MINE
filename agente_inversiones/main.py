"""CLI ejecutable del agente. Uso:

    poetry run agente cdt --monto 10000000 --tasa 0.12 --tipo-tasa efectiva_anual \\
                          --periodicidad mensual --plazo 12

    poetry run agente variable --monto 10000000 --tasa 0.15 \\
                               --volatilidad 0.20 --periodicidad anual --plazo 5

    poetry run agente comparar
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agente_inversiones.agente import AgenteInversion
from agente_inversiones.modelos import (
    EntradaInversion,
    Periodicidad,
    TipoInversion,
    TipoTasa,
)

app = typer.Typer(add_completion=False, help="Agente de simulación de inversiones (CDT y RV).")
console = Console()
agente = AgenteInversion()


def _imprimir(resultado, explicacion: str) -> None:
    tabla = Table(title=f"Resultado :: {resultado.tipo.value.upper()}", show_lines=True)
    tabla.add_column("Concepto", style="cyan")
    tabla.add_column("Valor", style="green", justify="right")
    tabla.add_row("Valor presente",        f"${resultado.valor_presente:,.2f}")
    tabla.add_row("Valor futuro",          f"${resultado.valor_futuro:,.2f}")
    tabla.add_row("Rentabilidad",          f"${resultado.rentabilidad:,.2f}")
    tabla.add_row("Rentabilidad %",        f"{resultado.rentabilidad_porcentual:.2f} %")
    tabla.add_row("Tasa periódica",        f"{resultado.tasa_periodica * 100:.4f} %")
    tabla.add_row("TEA equivalente",       f"{resultado.tasa_efectiva_anual * 100:.4f} %")
    tabla.add_row("Tipo tasa origen",      resultado.tipo_tasa_origen.value)
    tabla.add_row("Periodicidad",          resultado.periodicidad.value)
    tabla.add_row("Plazo",                 f"{resultado.plazo_periodos} periodos "
                                           f"({resultado.plazo_anios:.2f} años)")
    console.print(tabla)
    if resultado.detalles:
        console.print(Panel(str(resultado.detalles), title="Detalles", border_style="dim"))
    console.print(Panel(explicacion, title="Explicación del agente", border_style="magenta"))


@app.command()
def cdt(
    monto: float = typer.Option(..., help="Capital invertido"),
    tasa: float = typer.Option(..., help="Tasa en decimal (12 % = 0.12)"),
    tipo_tasa: TipoTasa = typer.Option(TipoTasa.EFECTIVA_ANUAL, help="nominal | efectiva_anual"),
    periodicidad: Periodicidad = typer.Option(Periodicidad.MENSUAL),
    plazo: int = typer.Option(..., help="Plazo en número de periodos"),
    sin_llm: bool = typer.Option(False, help="No invocar Ollama"),
) -> None:
    """Simula un CDT."""
    entrada = EntradaInversion(
        tipo=TipoInversion.CDT, monto=monto, tasa=tasa, tipo_tasa=tipo_tasa,
        periodicidad=periodicidad, plazo_periodos=plazo,
    )
    resultado, explicacion = agente.simular_y_explicar(entrada, usar_llm=not sin_llm)
    _imprimir(resultado, explicacion)


@app.command()
def variable(
    monto: float = typer.Option(...),
    tasa: float = typer.Option(..., help="Retorno esperado anual (decimal)"),
    volatilidad: float = typer.Option(0.20, help="Volatilidad anual (decimal)"),
    periodicidad: Periodicidad = typer.Option(Periodicidad.ANUAL),
    plazo: int = typer.Option(..., help="Plazo en periodos"),
    n_simulaciones: int = typer.Option(10_000, help="Trayectorias Monte Carlo"),
    sin_llm: bool = typer.Option(False),
) -> None:
    """Simula renta variable (Monte Carlo GBM)."""
    entrada = EntradaInversion(
        tipo=TipoInversion.RENTA_VARIABLE, monto=monto, tasa=tasa,
        tipo_tasa=TipoTasa.EFECTIVA_ANUAL, periodicidad=periodicidad,
        plazo_periodos=plazo, volatilidad=volatilidad, n_simulaciones=n_simulaciones,
    )
    resultado, explicacion = agente.simular_y_explicar(entrada, usar_llm=not sin_llm)
    _imprimir(resultado, explicacion)


@app.command()
def comparar(sin_llm: bool = typer.Option(False)) -> None:
    """Demo: compara un CDT vs un portafolio de renta variable."""
    cdt_e = EntradaInversion(
        tipo=TipoInversion.CDT, monto=10_000_000, tasa=0.115,
        tipo_tasa=TipoTasa.EFECTIVA_ANUAL, periodicidad=Periodicidad.MENSUAL,
        plazo_periodos=12,
    )
    rv_e = EntradaInversion(
        tipo=TipoInversion.RENTA_VARIABLE, monto=10_000_000, tasa=0.14,
        tipo_tasa=TipoTasa.EFECTIVA_ANUAL, periodicidad=Periodicidad.ANUAL,
        plazo_periodos=1, volatilidad=0.22, n_simulaciones=20_000,
    )
    resultados, recomendacion = agente.comparar([cdt_e, rv_e], usar_llm=not sin_llm)
    for r in resultados:
        _imprimir(r, "")
    console.print(Panel(recomendacion, title="Recomendación", border_style="yellow"))


if __name__ == "__main__":
    app()
