import pandas as pd


def detect_liquidity_levels(df, tolerance=0.0015):
    """
    Detecta zonas potenciales de liquidez.

    Buy-side liquidity:
        Swing Highs con precios similares.

    Sell-side liquidity:
        Swing Lows con precios similares.

    tolerance:
        Diferencia porcentual máxima para considerar
        dos niveles como aproximadamente iguales.
    """

    df = df.copy()

    df["buy_side_liquidity"] = False
    df["sell_side_liquidity"] = False

    df["liquidity_level"] = None

    # ========================================================
    # OBTENER SWING HIGHS
    # ========================================================

    swing_highs = df[df["swing_high"]]

    previous_high = None
    previous_high_index = None

    for index, row in swing_highs.iterrows():

        current_high = row["high"]

        if previous_high is not None:

            difference = abs(
                current_high - previous_high
            ) / previous_high

            if difference <= tolerance:

                # Liquidez sobre máximos
                df.loc[index, "buy_side_liquidity"] = True
                df.loc[
                    previous_high_index,
                    "buy_side_liquidity"
                ] = True

                liquidity_price = (
                    current_high + previous_high
                ) / 2

                df.loc[index, "liquidity_level"] = (
                    liquidity_price
                )

                df.loc[
                    previous_high_index,
                    "liquidity_level"
                ] = liquidity_price

        previous_high = current_high
        previous_high_index = index

    # ========================================================
    # OBTENER SWING LOWS
    # ========================================================

    swing_lows = df[df["swing_low"]]

    previous_low = None
    previous_low_index = None

    for index, row in swing_lows.iterrows():

        current_low = row["low"]

        if previous_low is not None:

            difference = abs(
                current_low - previous_low
            ) / previous_low

            if difference <= tolerance:

                # Liquidez bajo mínimos
                df.loc[index, "sell_side_liquidity"] = True
                df.loc[
                    previous_low_index,
                    "sell_side_liquidity"
                ] = True

                liquidity_price = (
                    current_low + previous_low
                ) / 2

                df.loc[index, "liquidity_level"] = (
                    liquidity_price
                )

                df.loc[
                    previous_low_index,
                    "liquidity_level"
                ] = liquidity_price

        previous_low = current_low
        previous_low_index = index

    return df