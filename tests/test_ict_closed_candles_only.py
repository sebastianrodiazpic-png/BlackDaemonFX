"""ICT evalúa solo velas cerradas (paridad con tools/replay_ict_live_faithful.py).

En vivo MT5 entrega la vela en formación como última fila. Antes la estrategia la
evaluaba (filtro `time <= now` por hora de APERTURA) y disparaba señales intra-vela
que el replay no genera: en la demo 15-18 oct, 35 de 105 operaciones salieron de velas
que al cerrar no confirmaban la señal (-0.39 R/op frente a +0.08 R/op del resto).
"""
from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, closed_candles_only

TF_MIN = {"M15": 15, "H1": 60, "H4": 240}


def _random_walk_m15(n=3000, seed=7):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-09-01", tz="UTC")
    close = 1000 + np.cumsum(rng.normal(0, 1.5, n))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0, 1.2, n))
    return pd.DataFrame({
        "time": [start + pd.Timedelta(minutes=15 * i) for i in range(n)],
        "open": open_, "close": close,
        "high": np.maximum(open_, close) + spread, "low": np.minimum(open_, close) - spread,
        "tick_volume": rng.integers(50, 200, n),
    })


def _resample(m15, tf):
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "tick_volume": "sum"}
    return m15.set_index("time").resample(f"{TF_MIN[tf]}min").agg(agg).dropna().reset_index()


class LiveLikeProvider:
    """Como MT5: velas cerradas hasta `now` + la vela en formación (opcional) al final."""

    def __init__(self, m15, include_forming):
        self.frames = {"M15": m15, "H1": _resample(m15, "H1"), "H4": _resample(m15, "H4")}
        self.include_forming = include_forming
        self.now = None

    def get_candles(self, symbol, timeframe, count=100):
        df = self.frames[timeframe]
        dur = pd.Timedelta(minutes=TF_MIN[timeframe])
        closed = df[df["time"] + dur <= self.now]
        if self.include_forming:
            last = closed.iloc[-1]
            # Vela en formación con desplazamiento extremo: si se evaluara, alteraría la señal.
            forming = pd.DataFrame([{
                "time": last["time"] + dur, "open": last["close"], "close": last["close"] + 40.0,
                "high": last["close"] + 40.5, "low": last["close"] - 0.1, "tick_volume": 10,
            }])
            closed = pd.concat([closed, forming], ignore_index=True)
        return closed.tail(count).reset_index(drop=True)

    def get_current_tick(self, symbol):
        price = float(self.frames["M15"][self.frames["M15"]["time"] < self.now]["close"].iloc[-1])
        return {"bid": price, "ask": price + 0.1}


def test_closed_candles_only_drops_forming_bar():
    df = pd.DataFrame({"time": pd.to_datetime(["2026-10-18 22:00", "2026-10-18 22:15"], utc=True),
                       "open": [1, 2], "high": [1, 2], "low": [1, 2], "close": [1, 2]})
    now = pd.Timestamp("2026-10-18 22:18", tz="UTC")
    assert list(closed_candles_only(df, "M15", now)["time"]) == [pd.Timestamp("2026-10-18 22:00", tz="UTC")]
    assert len(closed_candles_only(df, "M15", pd.Timestamp("2026-10-18 22:30", tz="UTC"))) == 2
    assert len(closed_candles_only(df, "H1", now)) == 0


@pytest.mark.parametrize("minute_in_bar", [3, 11])
def test_forming_candle_never_changes_the_ict_decision(minute_in_bar):
    m15 = _random_walk_m15()
    cfg = ICTSabriMalleConfig()
    with_forming = LiveLikeProvider(m15, include_forming=True)
    closed_only = LiveLikeProvider(m15, include_forming=False)
    strat_live = ICTSabriMalleStrategy(with_forming, cfg)
    strat_ref = ICTSabriMalleStrategy(closed_only, cfg)
    compared = 0
    for i in range(1200, len(m15) - 2, 3):
        now = m15["time"].iloc[i] + timedelta(minutes=minute_in_bar)
        with_forming.now = closed_only.now = now
        a = strat_live.analyze_symbol("Volatility 75 Index", now_utc=now.to_pydatetime())
        b = strat_ref.analyze_symbol("Volatility 75 Index", now_utc=now.to_pydatetime())
        assert (a.get("valid"), a.get("reason"), a.get("direction")) == \
               (b.get("valid"), b.get("reason"), b.get("direction")), f"diverge en {now}"
        if a.get("valid"):
            assert a["signal"]["stop_loss"] == b["signal"]["stop_loss"]
        compared += 1
    assert compared > 500
