"""Deteccion de CHOCH (Change of Character) y BOS (Break of Structure).

Es el nucleo estructural del bot: distingue un giro de tendencia (CHOCH) de
una continuacion (BOS). Estas dos senales son las UNICAS invalidaciones que el
motor acepta para cerrar una posicion abierta de forma anticipada, tras la
correccion que separo "estructura" de "frescura de senal".

Vinculaciones:
- Es importado por `strategy.execution.trade_pipeline.run_pipeline`, que lo
  ejecuta tras clasificar la estructura y ANTES de `detect_order_blocks` (que
  necesita las columnas de ruptura que genera aqui).
- Es importado por `strategy.execution.runner_extension_manager` para decidir
  si un runner sigue teniendo estructura a favor.
- Las columnas `bos_bullish`/`bos_bearish`/`choch_*` las lee tambien
  `strategy.execution.live_trading_engine._analysis_invalidation_exit` para
  determinar si una posicion abierta quedo estructuralmente invalidada.
- No importa ningun otro modulo del proyecto: solo depende de pandas.
"""

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

    Detalles del proceso que conviene conocer al depurar:
    - La ruptura se valida por CIERRE (`close`), no por mecha. Un pico que
      perfora el nivel pero cierra por debajo NO cuenta como ruptura.
    - Cada nivel se CONSUME al romperse (`last_swing_high = None`), de modo
      que el mismo swing no puede generar dos rupturas.
    - La estructura inicial se infiere del primer pivote encontrado: si
      aparece antes un swing high se asume `bearish`, y si aparece antes un
      swing low se asume `bullish`. Es deliberado: coloca el precio "por
      debajo" del maximo o "por encima" del minimo, que es la posicion desde
      la que ese nivel puede romperse.
    - Ambos bloques de ruptura se evaluan en la misma iteracion, asi que una
      vela muy amplia podria marcar ruptura alcista y bajista a la vez.

    Args:
        df: DataFrame que YA debe traer `swing_high` y `swing_low` de
            `strategy.smc.swings.detect_swings`, ademas de `high/low/close`.

    Returns:
        Una COPIA del DataFrame con las columnas booleanas `choch_bullish`,
        `choch_bearish`, `bos_bullish`, `bos_bearish` y con
        `structure_break_level` (el precio del nivel que se rompio).

    Vinculaciones:
    - Su salida es requisito de `strategy.smc.order_blocks.detect_order_blocks`,
      que lanza `ValueError` si estas columnas no existen.
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