"""Clasificacion de la estructura de mercado (HH / HL / LH / LL) y tendencia.

Traduce los pivotes crudos a la nomenclatura SMC y deduce si el mercado esta
alcista, bajista o neutro. Es el filtro direccional del bot: define si se
buscan compras o ventas.

Vinculaciones:
- Es importado por `strategy.execution.trade_pipeline.run_pipeline`, que lo
  ejecuta justo despues de `strategy.smc.swings.detect_swings`.
- Es importado por `strategy.execution.multi_timeframe`, donde determina la
  tendencia H1 que actua como sesgo HTF (Higher Time Frame) y puede bloquear
  entradas contrarias.
- No importa ningun otro modulo del proyecto: solo depende de pandas.
"""

import pandas as pd


def classify_market_structure(df):
    """
    Clasifica los Swing High y Swing Low detectados.

    Swing High:
        HH = Higher High
        LH = Lower High

    Swing Low:
        HL = Higher Low
        LL = Lower Low

    Proceso: recorre las velas en orden cronologico manteniendo memoria del
    ultimo swing high y del ultimo swing low vistos, y compara cada pivote
    nuevo contra su antecesor del mismo tipo. El PRIMER pivote de cada tipo
    queda sin clasificar (`None`) porque no tiene referencia previa.

    Args:
        df: DataFrame que YA debe traer las columnas booleanas `swing_high` y
            `swing_low` producidas por `strategy.smc.swings.detect_swings`.

    Returns:
        Una COPIA del DataFrame con la columna `structure`, que vale `HH`,
        `LH`, `HL`, `LL` o `None` en las velas que no son pivote.

    Vinculaciones:
    - Su columna `structure` la consumen `get_current_trend` (en este mismo
      modulo) y `strategy.smc.choch_bos.detect_choch_bos`.
    """

    df = df.copy()

    # Columnas para clasificar estructura
    df["structure"] = None

    previous_swing_high = None
    previous_swing_low = None

    for i in range(len(df)):

        # ====================================================
        # SWING HIGH
        # ====================================================

        if df["swing_high"].iloc[i]:

            current_high = df["high"].iloc[i]

            if previous_swing_high is not None:

                if current_high > previous_swing_high:
                    df.loc[df.index[i], "structure"] = "HH"

                elif current_high < previous_swing_high:
                    df.loc[df.index[i], "structure"] = "LH"

            previous_swing_high = current_high

        # ====================================================
        # SWING LOW
        # ====================================================

        if df["swing_low"].iloc[i]:

            current_low = df["low"].iloc[i]

            if previous_swing_low is not None:

                if current_low > previous_swing_low:
                    df.loc[df.index[i], "structure"] = "HL"

                elif current_low < previous_swing_low:
                    df.loc[df.index[i], "structure"] = "LL"

            previous_swing_low = current_low

    return df


def get_current_trend(df):
    """
    Intenta determinar la tendencia actual según
    los últimos puntos de estructura.

    Proceso: toma los ULTIMOS 4 puntos de estructura no nulos y busca
    coexistencia de patrones. Si aparecen HH y HL juntos la tendencia es
    alcista; si aparecen LH y LL es bajista.

    Atencion a dos comportamientos que conviene tener presentes al depurar:
    - Con menos de 4 puntos de estructura devuelve `UNKNOWN`, no `NEUTRAL`.
      Son estados distintos: `UNKNOWN` significa "faltan datos" y `NEUTRAL`
      significa "hay datos pero no hay patron claro".
    - La comprobacion alcista se evalua ANTES que la bajista, asi que en una
      ventana ambigua que contenga HH, HL, LH y LL a la vez gana `BULLISH`.

    Args:
        df: DataFrame con la columna `structure` ya calculada por
            `classify_market_structure`.

    Returns:
        Una de estas cuatro cadenas: `BULLISH`, `BEARISH`, `NEUTRAL` o
        `UNKNOWN`.

    Vinculaciones:
    - Lo llama `strategy.execution.trade_pipeline.run_pipeline` para fijar la
      direccion permitida del setup.
    - Lo llama `strategy.execution.multi_timeframe` para calcular el sesgo H1
      que despues viaja en el analisis como `h1_trend`.
    """

    structure_points = df[
        df["structure"].notna()
    ].copy()

    if len(structure_points) < 4:
        return "UNKNOWN"

    last_structures = structure_points[
        "structure"
    ].tail(4).tolist()

    # Estructura alcista
    if (
        "HH" in last_structures
        and "HL" in last_structures
    ):
        return "BULLISH"

    # Estructura bajista
    if (
        "LH" in last_structures
        and "LL" in last_structures
    ):
        return "BEARISH"

    return "NEUTRAL"