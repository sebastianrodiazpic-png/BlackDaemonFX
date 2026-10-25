"""Sesgo nocturno de índices US (worker NIGHT) — 21-oct-2026.

Anomalía documentada: la rentabilidad de los índices US se concentra entre el cierre y la apertura de Nueva York.
Regla (validada en replay con todo el historial del broker, M30 desde ene-2024; ver REGISTRO_CAMBIOS_ESTRATEGIA.md):
- Compra al cierre de las 16:00 NY (ventana de entrada 16:00-16:15 NY, días hábiles) en US SP 500 y US Tech 100.
- Stop de protección = 1 × ATR(14) diario (velas D1 cerradas) por debajo de la entrada; el lotaje lo fija el riesgo
  del 1 % sobre esa distancia. Sin objetivo de beneficio: salida por tiempo en la apertura de las 09:30 NY del
  siguiente día hábil (la ejecuta el monitor de posiciones del motor).
Replay: +0,033 R/noche (t = 2,4), acierto 55 %, positivo en ene-oct 2024 (+0,080), y0 (+0,024) e y1 (+0,008);
stop en el 7 % de las noches, peor −2R por hueco; caída máxima −19,5 % con ambos índices al 1 %.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

NY = ZoneInfo("America/New_York")
OVERNIGHT_STRATEGY = "OVERNIGHT_DRIFT"
OVERNIGHT_VERSION = "overnight-drift-v1"
OVERNIGHT_SCENARIO = "NY_CLOSE_TO_OPEN"


@dataclass
class OvernightConfig:
    enabled: bool = True
    strategy_name: str = OVERNIGHT_STRATEGY
    strategy_version: str = OVERNIGHT_VERSION
    symbols: tuple = ("US SP 500", "US Tech 100")
    entry_hour: int = 16
    entry_minute: int = 0
    entry_window_minutes: int = 15
    exit_hour: int = 9
    exit_minute: int = 30
    atr_period: int = 14
    stop_atr_multiple: float = 1.0
    # Sin TP real: se fija lejos para que solo actúen el stop y la salida por tiempo.
    far_target_rr: float = 20.0


def _ny(ts) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
    return ts.tz_convert(NY)


def next_trading_day(day):
    nxt = pd.Timestamp(day) + pd.Timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += pd.Timedelta(days=1)
    return nxt.date()


def exit_time_for_entry(entry_time, config: OvernightConfig | None = None) -> pd.Timestamp:
    """Momento de salida (UTC): 09:30 NY del día hábil siguiente al de la entrada."""
    cfg = config or OvernightConfig()
    local = _ny(entry_time)
    day = next_trading_day(local.date())
    return pd.Timestamp(datetime(day.year, day.month, day.day, cfg.exit_hour, cfg.exit_minute), tz=NY).tz_convert("UTC")


def in_entry_window(now, config: OvernightConfig | None = None) -> bool:
    cfg = config or OvernightConfig()
    local = _ny(now)
    if local.weekday() >= 5:
        return False
    start = local.replace(hour=cfg.entry_hour, minute=cfg.entry_minute, second=0, microsecond=0)
    return start <= local < start + timedelta(minutes=cfg.entry_window_minutes)


def daily_atr(d1: pd.DataFrame, now, period: int = 14) -> float | None:
    """ATR de velas D1 ya cerradas en `now`."""
    if d1 is None or len(d1) < period + 2:
        return None
    d = d1.copy()
    d["time"] = pd.to_datetime(d["time"], utc=True)
    d = d[d["time"] + pd.Timedelta(days=1) <= pd.Timestamp(now)]
    if len(d) < period + 1:
        return None
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(period).mean().iloc[-1])
    return atr if np.isfinite(atr) and atr > 0 else None


class OvernightDriftStrategy:
    def __init__(self, data_provider, config: OvernightConfig | None = None):
        self.provider = data_provider
        self.config = config or OvernightConfig()

    def _base(self, symbol, reason):
        return {"valid": False, "strategy_name": self.config.strategy_name, "strategy_version": self.config.strategy_version,
                "symbol": symbol, "action": "WAITING_OVERNIGHT", "reason": reason}

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        cfg = self.config
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        if not cfg.enabled:
            return self._base(symbol, "STRATEGY_DISABLED")
        if str(symbol) not in cfg.symbols:
            return self._base(symbol, "OVERNIGHT_SYMBOL_NOT_ALLOWED")
        if not in_entry_window(now, cfg):
            return self._base(symbol, "OUTSIDE_NY_CLOSE_ENTRY_WINDOW")
        # Una entrada por noche: la posición abierta bloquea nuevas entradas (control de posición activa del motor)
        # y la ventana dura solo 15 minutos.
        try:
            d1 = self.provider.get_candles(symbol, "D1", count=40)
            tick = self.provider.get_current_tick(symbol)
            ask = float(tick["ask"])
        except Exception:
            return self._base(symbol, "OVERNIGHT_MARKET_DATA_UNAVAILABLE")
        atr = daily_atr(d1, now, cfg.atr_period)
        if atr is None or not np.isfinite(ask) or ask <= 0:
            return self._base(symbol, "OVERNIGHT_ATR_UNAVAILABLE")
        risk = cfg.stop_atr_multiple * atr
        stop = ask - risk
        exit_at = exit_time_for_entry(now, cfg)
        signal = {
            "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version, "symbol": symbol,
            "direction": "BUY", "scenario": OVERNIGHT_SCENARIO, "entry_confirmation": "NY_CLOSE_TIME_ENTRY",
            "entry_time": now.isoformat(), "entry_price": round(ask, 5), "stop_loss": round(stop, 5),
            "take_profit": round(ask + cfg.far_target_rr * risk, 5), "tp1_price": round(ask + cfg.far_target_rr * risk, 5),
            "tp2_price": round(ask + cfg.far_target_rr * risk, 5),
            "risk_reward_ratio": cfg.far_target_rr, "risk_reward": cfg.far_target_rr, "runner_rr": cfg.far_target_rr,
            "timeframe": "M30", "atr": round(atr, 5), "adx": None,
            "time_exit_at": exit_at.isoformat(), "exit_policy": "TIME_EXIT_NY_OPEN",
            "split_execution": False,
            "confirmations": {"time_window": True, "atr_stop": True},
        }
        return {"valid": True, "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version,
                "action": "OVERNIGHT_CONFIRMED", "reason": f"{OVERNIGHT_SCENARIO} ({symbol})", "symbol": symbol,
                "signal": signal}
