import pandas as pd


def detect_choch_bos(df):
    """
    Detecta Change of Character (CHOCH) y Break of Structure (BOS).

    CHOCH alcista:
        - La estructura previa era bajista.
        - El precio rompe un Swing High anterior.

    CHOCH bajista:
        - La estructura previa era alcista.
        - El precio rompe un Swing Low anterior.

    BOS alcista:
        - Después de una estructura alcista, el precio rompe
          un Swing High anterior.

    BOS bajista:
        - Después de una estructura bajista, el precio rompe
          un Swing Low anterior.
    """

    df = df.copy()

    # Columnas de resultados
    df["choch_bullish"] = False
    df["choch_bearish"] = False

    df["bos_bullish"] = False
    df["bos_bearish"] = False

    df["structure_break_level"] = None

    # Últimos niveles estructurales
    last_swing_high = None
    last_swing_low = None

    # Tendencia inicial desconocida
    current_structure = None

    for i in range(len(df)):

        current_high = df["high"].iloc[i]
        current_low = df["low"].iloc[i]
        current_close = df["close"].iloc[i]

        # --------------------------------------------------
        # DETECTAR RUPTURAS DE ESTRUCTURA
        # --------------------------------------------------

        # Rompe un Swing High
        if (
            last_swing_high is not None
            and current_close > last_swing_high
        ):

            # Si veníamos de estructura bajista
            if current_structure == "bearish":

                df.loc[
                    df.index[i],
                    "choch_bullish"
                ] = True

            # Si ya estamos en estructura alcista
            elif current_structure == "bullish":

                df.loc[
                    df.index[i],
                    "bos_bullish"
                ] = True

            # Guardar nivel roto
            df.loc[
                df.index[i],
                "structure_break_level"
            ] = last_swing_high

            # Nueva estructura
            current_structure = "bullish"

            # Consumir el nivel
            last_swing_high = None

        # Rompe un Swing Low
        if (
            last_swing_low is not None
            and current_close < last_swing_low
        ):

            # Si veníamos de estructura alcista
            if current_structure == "bullish":

                df.loc[
                    df.index[i],
                    "choch_bearish"
                ] = True

            # Si ya estamos en estructura bajista
            elif current_structure == "bearish":

                df.loc[
                    df.index[i],
                    "bos_bearish"
                ] = True

            # Guardar nivel roto
            df.loc[
                df.index[i],
                "structure_break_level"
            ] = last_swing_low

            # Nueva estructura
            current_structure = "bearish"

            # Consumir el nivel
            last_swing_low = None

        # --------------------------------------------------
        # ACTUALIZAR SWING HIGH
        # --------------------------------------------------

        if df["swing_high"].iloc[i]:

            last_swing_high = df["high"].iloc[i]

            # Si todavía no conocemos estructura
            if current_structure is None:
                current_structure = "bearish"

        # --------------------------------------------------
        # ACTUALIZAR SWING LOW
        # --------------------------------------------------

        if df["swing_low"].iloc[i]:

            last_swing_low = df["low"].iloc[i]

            # Si todavía no conocemos estructura
            if current_structure is None:
                current_structure = "bullish"

    return df