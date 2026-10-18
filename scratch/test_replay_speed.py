import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, build_h4_candles_from_h1, is_synthetic_asset

NEW_YORK = ZoneInfo("America/New_York")
TF_MINUTES = {"M15": 15, "H1": 60, "H4": 240}

class HistoricalProvider:
    def __init__(self, frames: dict[str, pd.DataFrame], spread: float):
        self.now = None
        self.spread = spread
        self._frames = {}
        for tf, df in frames.items():
            close_ts = (df["time"] + pd.Timedelta(minutes=TF_MINUTES[tf])).values.astype("datetime64[ns]")
            self._frames[tf] = (df.reset_index(drop=True), close_ts)

    def get_candles(self, symbol, timeframe, count=100):
        tf = str(timeframe).upper()
        if tf not in self._frames:
            return None
        df, close_ts = self._frames[tf]
        now_ts = np.datetime64(self.now.tz_convert("UTC").tz_localize(None))
        idx = int(np.searchsorted(close_ts, now_ts, side="right"))
        return df.iloc[max(0, idx - count):idx].copy()

    def get_current_tick(self, symbol):
        df, close_ts = self._frames["M15"]
        now_ts = np.datetime64(self.now.tz_convert("UTC").tz_localize(None))
        idx = int(np.searchsorted(close_ts, now_ts, side="right"))
        price = float(df["close"].iloc[max(0, idx - 1)])
        return {"bid": price, "ask": price + self.spread}

def test_symbol(symbol: str, spread: float):
    fname = symbol.replace(" ", "_")
    df_h1 = pd.read_pickle(f"data/cache_msnr/{fname}_H1.pkl")
    df_m15 = pd.read_pickle(f"data/cache_msnr/{fname}_M15.pkl")
    df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
    df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
    df_h4 = build_h4_candles_from_h1(df_h1)

    frames = {"M15": df_m15, "H1": df_h1, "H4": df_h4}
    provider = HistoricalProvider(frames, spread)
    strat = ICTSabriMalleStrategy(provider, ICTSabriMalleConfig())

    t0 = time.time()
    signals = []
    # Evaluar en cada vela M15
    # Para acelerar y ser fiel a la ejecución, cuando hay señal o trade activo avanzamos
    m15_times = df_m15["time"].values
    n_bars = len(df_m15)
    step = 1
    busy_until = 0

    for i in range(100, n_bars - 1, step):
        if i < busy_until:
            continue
        bar_time = pd.Timestamp(m15_times[i], tz="UTC")
        provider.now = bar_time + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if res.get("valid"):
            sig = res["signal"]
            signals.append((provider.now, sig["direction"], sig["entry_price"], sig["stop_loss"], sig["tp1_price"], sig["tp2_price"]))
            busy_until = i + 8  # cooldown mínimo de 2 horas (8 barras M15)

    elapsed = time.time() - t0
    print(f"[{symbol}] Evaluated {n_bars} M15 bars in {elapsed:.2f}s. Signals detected: {len(signals)}")
    return signals

if __name__ == "__main__":
    test_symbol("EURUSD", 0.00015)
    test_symbol("Volatility 75 Index", 10.0)
    test_symbol("Boom 1000 Index", 0.08)
