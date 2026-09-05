"""Deteccion de Order Blocks (OB) a partir de rupturas de estructura.

Un Order Block es la ultima vela contraria antes de un movimiento que rompe la
estructura: se interpreta como la zona donde el dinero institucional dejo
ordenes pendientes. Es la ZONA DE ENTRADA del bot: el precio debe volver a
tocarla (retest) para que se busque confirmacion.

Vinculaciones:
- Es importado por `strategy.execution.trade_pipeline.run_pipeline`, que lo
  ejecuta DESPUES de `strategy.smc.choch_bos.detect_choch_bos` (necesita sus
  columnas) y ANTES de buscar el retest y la confirmacion M5.
- No importa ningun otro modulo del proyecto: solo depende de pandas.
"""

import pandas as pd


def detect_order_blocks(df, lookback=20):
    """Detecta Order Blocks y conserva el evento estructural que los valida.

    Un Bullish OB es la última vela bajista antes de un CHOCH/BOS alcista.
    Un Bearish OB es la última vela alcista antes de un CHOCH/BOS bajista.

    El DataFrame completo se conserva para no perder la secuencia temporal. Las
    columnas ``ob_*`` sólo contienen valores en las velas que realmente son OB.

    Proceso: por cada vela que marca ruptura, retrocede hasta `lookback` velas
    buscando la primera vela de color contrario al movimiento y la marca como
    OB. Guarda tambien el indice y el tiempo de la vela que rompio
    (`ob_break_index`, `ob_break_time`), lo que permite despues medir la
    FRESCURA del OB y cuantos toques ha recibido.

    Args:
        df: DataFrame OHLC que YA debe traer las columnas de ruptura
            `choch_bullish`, `choch_bearish`, `bos_bullish`, `bos_bearish`,
            ademas de `open/high/low/close/time`.
        lookback: cuantas velas hacia atras se busca la vela origen del OB.

    Returns:
        Una COPIA del DataFrame con las columnas `bullish_order_block`,
        `bearish_order_block`, `ob_high`, `ob_low`, `ob_type`,
        `ob_source_index`, `ob_break_index`, `ob_break_time` y `ob_break_type`.

    Raises:
        ValueError: si faltan las columnas de ruptura, es decir si se llamo a
            esta funcion sin ejecutar antes `detect_choch_bos`.

    Vinculaciones:
    - Consume las columnas producidas por `strategy.smc.choch_bos.detect_choch_bos`.
    - `ob_high`/`ob_low` definen la zona que evalua
      `strategy.smc.confirmation_engine.evaluate_m5_confirmation` y de la que
      `strategy.smc.risk_reward.calculate_risk_reward` deriva el Stop Loss.
    """
    df = df.copy()

    defaults = {
        "bullish_order_block": False,
        "bearish_order_block": False,
        "ob_high": float("nan"),
        "ob_low": float("nan"),
        "ob_type": None,
        "ob_source_index": float("nan"),
        "ob_break_index": float("nan"),
        "ob_break_time": pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]"),
        "ob_break_type": None,
    }
    for column, value in defaults.items():
        df[column] = value

    required = ["open", "high", "low", "close", "time", "choch_bullish", "choch_bearish", "bos_bullish", "bos_bearish"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas para detectar Order Blocks: {missing}")

    for i in range(len(df)):
        bullish_break = bool(df["choch_bullish"].iloc[i] or df["bos_bullish"].iloc[i])
        bearish_break = bool(df["choch_bearish"].iloc[i] or df["bos_bearish"].iloc[i])

        if bullish_break:
            break_type = "choch_bullish" if bool(df["choch_bullish"].iloc[i]) else "bos_bullish"
            start = max(0, i - lookback)
            for j in range(i - 1, start - 1, -1):
                if float(df["close"].iloc[j]) < float(df["open"].iloc[j]):
                    idx = df.index[j]
                    df.loc[idx, "bullish_order_block"] = True
                    df.loc[idx, "ob_high"] = float(df["high"].iloc[j])
                    df.loc[idx, "ob_low"] = float(df["low"].iloc[j])
                    df.loc[idx, "ob_type"] = "bullish"
                    df.loc[idx, "ob_source_index"] = j
                    df.loc[idx, "ob_break_index"] = i
                    df.loc[idx, "ob_break_time"] = df["time"].iloc[i]
                    df.loc[idx, "ob_break_type"] = break_type
                    break

        if bearish_break:
            break_type = "choch_bearish" if bool(df["choch_bearish"].iloc[i]) else "bos_bearish"
            start = max(0, i - lookback)
            for j in range(i - 1, start - 1, -1):
                if float(df["close"].iloc[j]) > float(df["open"].iloc[j]):
                    idx = df.index[j]
                    df.loc[idx, "bearish_order_block"] = True
                    df.loc[idx, "ob_high"] = float(df["high"].iloc[j])
                    df.loc[idx, "ob_low"] = float(df["low"].iloc[j])
                    df.loc[idx, "ob_type"] = "bearish"
                    df.loc[idx, "ob_source_index"] = j
                    df.loc[idx, "ob_break_index"] = i
                    df.loc[idx, "ob_break_time"] = df["time"].iloc[i]
                    df.loc[idx, "ob_break_type"] = break_type
                    break

    return df
