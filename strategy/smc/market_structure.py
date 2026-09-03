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