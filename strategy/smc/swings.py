"""Deteccion de pivotes (Swing High / Swing Low).

Primer eslabon del analisis SMC: casi todo lo demas (estructura de mercado,
liquidez, BOS/CHOCH, order blocks) se apoya en los pivotes que marca este
modulo. Un pivote es una vela cuyo maximo (o minimo) supera al de sus vecinas
inmediatas a izquierda y derecha.

Vinculaciones:
- Es importado por `strategy.execution.trade_pipeline` (primer paso de
  `run_pipeline`, antes de clasificar la estructura).
- Es importado por `strategy.execution.runner_extension_manager` para decidir
  si un runner puede extenderse apoyandose en el ultimo pivote.
- No importa ningun otro modulo del proyecto: solo depende de pandas.
"""

import pandas as pd


def detect_swings(df, left=3, right=3):
    """
    Detecta Swing High y Swing Low.

    left: número de velas a comparar a la izquierda.
    right: número de velas a comparar a la derecha.

    Proceso: recorre las velas desde `left` hasta `len(df) - right` y marca
    como pivote la vela cuyo extremo es estrictamente mayor (o menor) que
    todos los extremos de la ventana vecina. Las primeras `left` y las
    ultimas `right` velas nunca se marcan porque no tienen ventana completa:
    por eso un pivote solo se considera confirmado cuando han cerrado `right`
    velas posteriores.

    Args:
        df: DataFrame OHLC. Debe traer al menos las columnas `high` y `low`.
        left: numero de velas a comparar a la izquierda.
        right: numero de velas a comparar a la derecha.

    Returns:
        Una COPIA del DataFrame (no muta la entrada) con dos columnas
        booleanas nuevas: `swing_high` y `swing_low`.

    Vinculaciones:
    - Su salida alimenta a `strategy.smc.market_structure.classify_market_structure`,
      `strategy.smc.liquidity.detect_liquidity_levels` y
      `strategy.smc.choch_bos.detect_choch_bos`, que leen estas dos columnas.
    """

    df = df.copy()

    df["swing_high"] = False
    df["swing_low"] = False

    for i in range(left, len(df) - right):

        current_high = df["high"].iloc[i]
        current_low = df["low"].iloc[i]

        left_highs = df["high"].iloc[i - left:i]
        right_highs = df["high"].iloc[i + 1:i + right + 1]

        left_lows = df["low"].iloc[i - left:i]
        right_lows = df["low"].iloc[i + 1:i + right + 1]

        # Swing High
        if (
            current_high > left_highs.max()
            and current_high > right_highs.max()
        ):
            df.loc[df.index[i], "swing_high"] = True

        # Swing Low
        if (
            current_low < left_lows.min()
            and current_low < right_lows.min()
        ):
            df.loc[df.index[i], "swing_low"] = True

    return df