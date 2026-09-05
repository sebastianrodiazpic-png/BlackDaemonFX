"""Confirmacion micro de entrada sobre timeframe menor (LEGADO / SIN USO).

Busca la primera vela que confirma la direccion del setup rompiendo el extremo
de la vela anterior. Es una version temprana y simplificada de la logica que
hoy vive, mucho mas desarrollada, en
`strategy.smc.confirmation_engine.evaluate_m5_confirmation` (rechazo,
desplazamiento, momentum, frescura del OB y score explicable).

ESTADO: no lo importa NINGUN modulo del proyecto, ni de produccion ni de
tests. `detect_micro_confirmation` no aparece referenciado en ningun otro
fichero. Se conserva como referencia historica; si buscas la confirmacion que
realmente se ejecuta en vivo, mira `confirmation_engine.py`.

No confundir con el parametro `require_micro_confirmation` de
`strategy.execution.trade_pipeline.PipelineConfig`: ese lo atiende el
confirmation engine, no este modulo.

Vinculaciones:
- Ninguna. Solo depende de pandas.
"""

import pandas as pd


def detect_micro_confirmation(
    df,
    setup_type,
    start_time
):
    """Busca la primera vela que confirma la direccion del setup (LEGADO).

    Proceso: normaliza tiempos a UTC, se queda con las velas desde
    `start_time` en adelante y avanza hasta encontrar una vela que cumpla dos
    condiciones a la vez: tener el color correcto y cerrar rompiendo el
    extremo de la vela inmediatamente anterior. Devuelve la primera que
    encuentra; nunca mira hacia atras de `start_time`.

    Args:
        df: DataFrame OHLC con columna `time`.
        setup_type: `"long"` o `"short"`. Cualquier otro valor recorre las
            velas sin confirmar nada y termina devolviendo `None`.
        start_time: instante desde el que se permite confirmar (inclusive).

    Returns:
        Un dict con `confirmed`, `direction`, `time`, `price` y
        `confirmation` (`micro_bullish_break` o `micro_bearish_break`), o
        `None` si el DataFrame esta vacio, hay menos de 3 velas futuras o
        ninguna vela cumple las condiciones.

    Vinculaciones:
    - Ninguna: funcion sin llamadores en el proyecto.
    """
    if df.empty:

        return None

    data = df.copy()

    data["time"] = pd.to_datetime(
        data["time"],
        utc=True
    )

    data = (
        data
        .sort_values("time")
        .reset_index(drop=True)
    )

    start_time = pd.to_datetime(
        start_time,
        utc=True
    )

    future = data[
        data["time"] >= start_time
    ].copy()

    if len(future) < 3:

        return None

    for i in range(1, len(future)):

        current = future.iloc[i]

        previous = future.iloc[i - 1]

        current_open = float(
            current["open"]
        )

        current_close = float(
            current["close"]
        )

        previous_high = float(
            previous["high"]
        )

        previous_low = float(
            previous["low"]
        )

        if setup_type == "long":

            bullish = (
                current_close > current_open
            )

            breaks_structure = (
                current_close > previous_high
            )

            if bullish and breaks_structure:

                return {
                    "confirmed": True,
                    "direction": "long",
                    "time": current["time"],
                    "price": current_close,
                    "confirmation": "micro_bullish_break"
                }

        elif setup_type == "short":

            bearish = (
                current_close < current_open
            )

            breaks_structure = (
                current_close < previous_low
            )

            if bearish and breaks_structure:

                return {
                    "confirmed": True,
                    "direction": "short",
                    "time": current["time"],
                    "price": current_close,
                    "confirmation": "micro_bearish_break"
                }

    return None