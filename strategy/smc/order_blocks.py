import pandas as pd


def detect_order_blocks(df, lookback=20):
    """Detecta Order Blocks y conserva el evento estructural que los valida.

    Un Bullish OB es la última vela bajista antes de un CHOCH/BOS alcista.
    Un Bearish OB es la última vela alcista antes de un CHOCH/BOS bajista.

    El DataFrame completo se conserva para no perder la secuencia temporal. Las
    columnas ``ob_*`` sólo contienen valores en las velas que realmente son OB.
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
