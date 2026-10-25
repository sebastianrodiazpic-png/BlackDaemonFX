"""Ruptura tras compresión (Bollinger squeeze + Donchian) en Drift Switch Index 10/20/30 (worker DRIFT) — 21-oct-2026.

Reglas idénticas a la estrategia C_RUPTURA pre-registrada en tools/research_synthetic_indicators.py (BUY; SELL espejo):
- M15 (velas cerradas): en alguna de las 5 últimas velas el ancho de Bollinger(20, 2) estuvo en el 20 % más bajo de
  las 120 previas, y la última vela cerrada cierra por encima del máximo de las 20 anteriores (la previa no lo hacía).
- H1 (última vela cerrada a la hora de cierre de esa M15): cierre > EMA50.
- Entrada a mercado, stop 1,5 × ATR14 H1, TP1 1R (50 %) y runner 2R (50 %) con BE tras TP1 (contrato del bot).
Replay de 2 años (21-oct-2024 → 21-oct-2026): +0,086 R/op, t = 3,9, 2.394 operaciones, año 0 +0,062 / año 1 +0,111,
4/4 semestres > 0, p azar < 0,001; positivo en las 9 combinaciones de stop (1,0/1,5/2,0 ATR) y Donchian (10/20/40).
Mecanismo: estos índices alternan regímenes de deriva alcista, bajista y lateral; la ruptura captura su persistencia.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

DRIFT_STRATEGY = "DRIFT_BREAKOUT"
DRIFT_VERSION = "drift-breakout-v1"
DRIFT_SCENARIO = "BB_SQUEEZE_DONCHIAN_BREAKOUT"
DRIFT_DEFAULT_SYMBOLS = ("Drift Switch Index 10", "Drift Switch Index 20", "Drift Switch Index 30")


def _env_symbols() -> tuple:
    raw = os.getenv("DAEMONBLACKFX_DRIFT_SYMBOLS", "")
    return tuple(s.strip() for s in raw.split(",") if s.strip()) or DRIFT_DEFAULT_SYMBOLS


@dataclass
class DriftBreakoutConfig:
    enabled: bool = True
    strategy_name: str = DRIFT_STRATEGY
    strategy_version: str = DRIFT_VERSION
    symbols: tuple = field(default_factory=_env_symbols)
    bb_period: int = 20
    bb_std: float = 2.0
    squeeze_lookback: int = 120
    squeeze_quantile: float = 0.2
    squeeze_window: int = 5
    donchian_period: int = 20
    h1_ema_period: int = 50
    atr_period: int = 14
    stop_atr_multiple: float = float(os.getenv("DAEMONBLACKFX_DRIFT_STOP_ATR", "1.5"))
    tp1_rr: float = 1.0
    runner_rr: float = 2.0
    # El replay entra en la apertura siguiente al cierre de la señal: solo se ejecuta si la vela de señal es la
    # última cerrada y no han pasado más de estos minutos desde su cierre.
    max_signal_age_minutes: float = float(os.getenv("DAEMONBLACKFX_DRIFT_MAX_SIGNAL_AGE_MIN", "10"))
    m15_count: int = 400
    # El motor ya evita duplicados con la clave de ejecución (también contra operaciones cerradas). Marcar la señal
    # como disparada en la estrategia impedía reintentarla si el motor la bloqueaba por algo pasajero (pico de spread,
    # máximo de posiciones): 22-oct-2026 DRIFT perdió así sus 2 primeras señales. Por defecto, sin marcado.
    setup_dedupe: bool = os.getenv("DAEMONBLACKFX_DRIFT_SETUP_DEDUPE", "0").strip().lower() in {"1", "true", "yes", "on"}
    h1_count: int = 400


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _closed(raw: pd.DataFrame, minutes: int, now: pd.Timestamp) -> pd.DataFrame:
    if raw is None or len(raw) == 0:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    df = raw.copy()
    numeric = pd.api.types.is_numeric_dtype(df["time"])
    df["time"] = pd.to_datetime(df["time"], utc=True, unit="s" if numeric else None)
    df["close_time"] = df["time"] + pd.Timedelta(minutes=minutes)
    return df[df["close_time"] <= now].sort_values("time").reset_index(drop=True)


def breakout_frame(m15: pd.DataFrame, h1: pd.DataFrame, cfg: DriftBreakoutConfig | None = None) -> pd.DataFrame:
    """Columnas de la regla sobre velas cerradas; `side` = +1 BUY, -1 SELL, 0 nada (mismo cálculo que el replay)."""
    cfg = cfg or DriftBreakoutConfig()
    m = m15.copy()
    c = m["close"]
    mid = c.rolling(cfg.bb_period).mean()
    sd = c.rolling(cfg.bb_period).std(ddof=0)
    bw = (2 * cfg.bb_std * sd) / mid.abs().replace(0, np.nan)
    q = bw.shift(1).rolling(cfg.squeeze_lookback).quantile(cfg.squeeze_quantile)
    m["sqz"] = (bw <= q).astype(float).rolling(cfg.squeeze_window).max().fillna(0).astype(bool)
    m["don_hi"] = m["high"].shift(1).rolling(cfg.donchian_period).max()
    m["don_lo"] = m["low"].shift(1).rolling(cfg.donchian_period).min()
    if "close_time" not in m:
        m["close_time"] = m["time"] + pd.Timedelta(minutes=15)
    h = h1.copy()
    h["h_ema"] = _ema(h["close"], cfg.h1_ema_period)
    h["h_atr"] = _atr(h, cfg.atr_period)
    h["h_close"] = h["close"]
    if "close_time" not in h:
        h["close_time"] = h["time"] + pd.Timedelta(hours=1)
    f = pd.merge_asof(m.sort_values("close_time"), h[["close_time", "h_ema", "h_atr", "h_close"]].sort_values("close_time"),
                      on="close_time", direction="backward")
    c, c1 = f["close"], f["close"].shift(1)
    buy = f.sqz & (c > f.don_hi) & ~(c1 > f.don_hi.shift(1)) & (f.h_close > f.h_ema)
    sell = f.sqz & (c < f.don_lo) & ~(c1 < f.don_lo.shift(1)) & (f.h_close < f.h_ema)
    f["side"] = np.where(buy.fillna(False), 1, np.where(sell.fillna(False), -1, 0))
    return f


class DriftBreakoutStrategy:
    def __init__(self, data_provider, config: DriftBreakoutConfig | None = None):
        self.provider = data_provider
        self.config = config or DriftBreakoutConfig()
        self._fired: set[str] = set()

    def _base(self, symbol, reason):
        return {"valid": False, "strategy_name": self.config.strategy_name, "strategy_version": self.config.strategy_version,
                "symbol": symbol, "action": "WAITING_DRIFT_BREAKOUT", "reason": reason}

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        cfg = self.config
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        if not cfg.enabled:
            return self._base(symbol, "STRATEGY_DISABLED")
        if str(symbol) not in cfg.symbols:
            return self._base(symbol, "DRIFT_SYMBOL_NOT_ALLOWED")
        try:
            m15 = _closed(self.provider.get_candles(symbol, "M15", count=cfg.m15_count), 15, now)
            h1 = _closed(self.provider.get_candles(symbol, "H1", count=cfg.h1_count), 60, now)
        except Exception:
            return self._base(symbol, "DRIFT_MARKET_DATA_UNAVAILABLE")
        need = cfg.squeeze_lookback + cfg.bb_period + cfg.squeeze_window + 2
        if len(m15) < need or len(h1) < cfg.h1_ema_period + cfg.atr_period:
            return self._base(symbol, "DRIFT_INSUFFICIENT_HISTORY")
        f = breakout_frame(m15, h1, cfg)
        last = f.iloc[-1]
        side = int(last["side"])
        if side == 0:
            return self._base(symbol, "NO_COMPRESSION_BREAKOUT")
        age = (now - last["close_time"]).total_seconds() / 60
        if age > cfg.max_signal_age_minutes:
            return self._base(symbol, "DRIFT_SIGNAL_STALE")
        direction = "BUY" if side > 0 else "SELL"
        setup_id = f"{symbol}|{last['close_time'].isoformat()}|{direction}"
        if cfg.setup_dedupe and setup_id in self._fired:
            return self._base(symbol, "DRIFT_SETUP_ALREADY_FIRED")
        atr = float(last["h_atr"])
        try:
            tick = self.provider.get_current_tick(symbol)
            entry = float(tick["ask"] if side > 0 else tick["bid"])
        except Exception:
            return self._base(symbol, "DRIFT_TICK_UNAVAILABLE")
        if not (np.isfinite(atr) and atr > 0 and np.isfinite(entry) and entry > 0):
            return self._base(symbol, "DRIFT_ATR_UNAVAILABLE")
        risk = cfg.stop_atr_multiple * atr
        stop = entry - side * risk
        tp1 = entry + side * cfg.tp1_rr * risk
        tp2 = entry + side * cfg.runner_rr * risk
        self._fired.add(setup_id)
        signal = {
            "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version, "symbol": symbol,
            "direction": direction, "scenario": DRIFT_SCENARIO, "entry_confirmation": "M15_CLOSE_BREAKOUT_H1_EMA",
            "setup_id": setup_id, "entry_time": last["close_time"].isoformat(), "signal_close_time": last["close_time"].isoformat(),
            "entry_price": round(entry, 5), "stop_loss": round(stop, 5), "take_profit": round(tp2, 5),
            "tp1_price": round(tp1, 5), "tp2_price": round(tp2, 5), "tp1_rr": cfg.tp1_rr, "runner_rr": cfg.runner_rr,
            "risk_reward_ratio": cfg.runner_rr, "risk_reward": cfg.runner_rr,
            "risk_reward_ratio_tp1": cfg.tp1_rr, "risk_reward_ratio_tp2": cfg.runner_rr,
            "runner_target_name": "TP2", "be_trigger_rr": cfg.tp1_rr,
            "timeframe": "M15", "atr": round(atr, 5), "atr_timeframe": "H1", "adx": None,
            "donchian_level": round(float(last["don_hi"] if side > 0 else last["don_lo"]), 5),
            "h1_ema50": round(float(last["h_ema"]), 5),
            "confirmations": {"bollinger_squeeze": True, "donchian_breakout": True, "h1_ema_trend": True},
            "split_execution": True, "leg1_risk_ratio": 0.5, "leg2_risk_ratio": 0.5,
        }
        return {"valid": True, "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version,
                "action": "DRIFT_BREAKOUT_CONFIRMED", "reason": f"{DRIFT_SCENARIO} ({direction} on {symbol})",
                "symbol": symbol, "signal": signal}
