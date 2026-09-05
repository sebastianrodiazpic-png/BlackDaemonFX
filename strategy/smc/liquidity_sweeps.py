"""Deteccion de barridos de liquidez (liquidity sweeps / stop hunts).

Un barrido es la trampa clasica: el precio perfora un nivel donde se acumulan
stops, los ejecuta, y vuelve a cerrar del lado contrario. Es una senal de
reversion de alta calidad y en el pipeline actua como DISPARADOR del setup.

Vinculaciones:
- Es importado por `strategy.execution.trade_pipeline.run_pipeline`, que lo
  ejecuta inmediatamente despues de
  `strategy.smc.liquidity.detect_liquidity_levels`.
- `trade_pipeline._latest_sweep` consulta las columnas `bullish_sweep` /
  `bearish_sweep` para asociar el barrido mas reciente a cada setup.
- No importa ningun otro modulo del proyecto: solo depende de pandas.
"""

import pandas as pd


def detect_liquidity_sweeps(df):
    """
    Detecta barridos de liquidez.

    Bearish Sweep:
        - El precio supera un nivel de Buy-Side Liquidity.
        - La vela cierra nuevamente por debajo del nivel.

    Bullish Sweep:
        - El precio rompe por debajo de Sell-Side Liquidity.
        - La vela cierra nuevamente por encima del nivel.

    Proceso: mantiene dos listas de niveles ACTIVOS que va alimentando segun
    avanza en el tiempo, de forma que una vela solo puede barrer niveles ya
    conocidos en ese momento (no hay mirada al futuro). Cuando un nivel se
    barre se ELIMINA de la lista, asi que cada nivel genera como maximo un
    barrido. El `break` limita ademas a un barrido por direccion y por vela.

    Args:
        df: DataFrame con `buy_side_liquidity`, `sell_side_liquidity` y
            `liquidity_level` ya calculados por
            `strategy.smc.liquidity.detect_liquidity_levels`.

    Returns:
        Una COPIA del DataFrame con `bullish_sweep`, `bearish_sweep` y
        `sweep_level` (el precio del nivel barrido).

    Vinculaciones:
    - `strategy.execution.trade_pipeline` marca con estas columnas la casilla
      `sweep_ok` del checklist del setup.
    """

    df = df.copy()

    df["bullish_sweep"] = False
    df["bearish_sweep"] = False
    df["sweep_level"] = None

    # Obtener todos los niveles conocidos hasta cada momento
    active_buy_levels = []
    active_sell_levels = []

    for i in range(len(df)):

        current_high = df["high"].iloc[i]
        current_low = df["low"].iloc[i]
        current_close = df["close"].iloc[i]

        # ----------------------------------------------------
        # AGREGAR NUEVOS NIVELES DE LIQUIDEZ
        # ----------------------------------------------------

        if df["buy_side_liquidity"].iloc[i]:

            level = df["liquidity_level"].iloc[i]

            if pd.notna(level):
                active_buy_levels.append(level)

        if df["sell_side_liquidity"].iloc[i]:

            level = df["liquidity_level"].iloc[i]

            if pd.notna(level):
                active_sell_levels.append(level)

        # ----------------------------------------------------
        # BEARISH SWEEP
        # ----------------------------------------------------

        for level in active_buy_levels.copy():

            # El precio barre por encima
            if current_high > level:

                # Pero cierra nuevamente debajo
                if current_close < level:

                    df.loc[
                        df.index[i],
                        "bearish_sweep"
                    ] = True

                    df.loc[
                        df.index[i],
                        "sweep_level"
                    ] = level

                    # El nivel ya fue consumido
                    active_buy_levels.remove(level)

                    break

        # ----------------------------------------------------
        # BULLISH SWEEP
        # ----------------------------------------------------

        for level in active_sell_levels.copy():

            # El precio barre por debajo
            if current_low < level:

                # Pero cierra nuevamente arriba
                if current_close > level:

                    df.loc[
                        df.index[i],
                        "bullish_sweep"
                    ] = True

                    df.loc[
                        df.index[i],
                        "sweep_level"
                    ] = level

                    # El nivel ya fue consumido
                    active_sell_levels.remove(level)

                    break

    return df