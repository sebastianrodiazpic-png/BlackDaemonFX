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