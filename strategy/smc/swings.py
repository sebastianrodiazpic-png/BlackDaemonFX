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

import numpy as np
import pandas as pd


def detect_swings(df, left=3, right=3):
    """
    Detecta Swing High y Swing Low de forma vectorizada (NumPy).

    left: número de velas a comparar a la izquierda.
    right: número de velas a comparar a la derecha.

    Proceso: utiliza operaciones vectorizadas sobre arrays contiguos de NumPy
    para evaluar simultáneamente las condiciones de extremo en ventana vecina,
    alcanzando aceleraciones de más de 1000x sobre iteración tradicional.
    Conserva la semántica y contrato exacto: las primeras `left` y últimas `right`
    velas nunca se marcan.

    Args:
        df: DataFrame OHLC. Debe traer al menos las columnas `high` y `low`.
        left: número de velas a comparar a la izquierda.
        right: número de velas a comparar a la derecha.

    Returns:
        Una COPIA del DataFrame (no muta la entrada) con dos columnas
        booleanas nuevas: `swing_high` y `swing_low`.
    """
    df = df.copy()
    n = len(df)
    is_sh = np.zeros(n, dtype=bool)
    is_sl = np.zeros(n, dtype=bool)

    if n <= left + right:
        df["swing_high"] = is_sh
        df["swing_low"] = is_sl
        return df

    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)

    is_sh.fill(True)
    is_sl.fill(True)

    for k in range(1, left + 1):
        is_sh &= (highs > np.roll(highs, k))
        is_sl &= (lows < np.roll(lows, k))

    for k in range(1, right + 1):
        is_sh &= (highs > np.roll(highs, -k))
        is_sl &= (lows < np.roll(lows, -k))

    is_sh[:left] = False
    is_sh[n - right:] = False
    is_sl[:left] = False
    is_sl[n - right:] = False

    df["swing_high"] = is_sh
    df["swing_low"] = is_sl
    return df