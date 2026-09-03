import pandas as pd


def detect_swings(df, left=3, right=3):
    """
    Detecta Swing High y Swing Low.

    left: número de velas a comparar a la izquierda.
    right: número de velas a comparar a la derecha.
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