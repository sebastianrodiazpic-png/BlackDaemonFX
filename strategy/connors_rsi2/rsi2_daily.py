"""RSI(2) diario de Connors en los 5 índices de EE. UU. (worker RSI2) — 21-oct-2026.

Reglas idénticas a REV_D pre-registrada en tools/research_index_indicators.py (solo largos):
- Señal al cierre de la vela D1: cierre > SMA200 D1 y RSI(2) D1 < 10 (RSI de Wilder).
- Entrada a mercado al empezar la vela D1 siguiente (primer tick del día; el motor admite hasta 120 min de retraso).
- Stop de protección 2 × ATR14 D1; riesgo 1 % en dos entradas (contrato del bot): TP1 1R (50 %) y runner 2R (50 %)
  con BE tras TP1. Con DAEMONBLACKFX_RSI2_SPLIT=0, una sola posición sin objetivo real (TP lejano).
- Salida a mercado de lo que quede abierto en la apertura siguiente a la primera vela D1 cerrada con cierre > SMA5,
  o tras 10 velas D1 cerradas desde la entrada (la ejecuta el monitor de posiciones del motor).
  Replay de gestión (tools/research_rsi2_management.py): dos entradas +0,177 R/op = una posición +0,175.
Replay 2 años (21-oct-2024 → 21-oct-2026, spread y swap reales): +0,176 R/op, 145 operaciones, acierto 72 %,
año 0 +0,190 / año 1 +0,164, 4/4 semestres > 0, p azar < 0,001. Agrupado por día (los 5 índices se mueven juntos):
79 episodios, t = 1,9 -> no concluyente, por eso va a prueba demo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RSI2_STRATEGY = "CONNORS_RSI2"
RSI2_VERSION = "connors-rsi2-v1"
RSI2_SCENARIO = "RSI2_PULLBACK_ABOVE_SMA200"
RSI2_DEFAULT_SYMBOLS = ("US SP 500", "US Tech 100", "Wall Street 30", "US Small Cap 2000", "US Mid Cap 400")


def _env_symbols() -> tuple:
    raw = os.getenv("DAEMONBLACKFX_RSI2_SYMBOLS", "")
    return tuple(s.strip() for s in raw.split(",") if s.strip()) or RSI2_DEFAULT_SYMBOLS


@dataclass
class Rsi2Config:
    enabled: bool = True
    strategy_name: str = RSI2_STRATEGY
    strategy_version: str = RSI2_VERSION
    symbols: tuple = field(default_factory=_env_symbols)
    rsi_period: int = 2
    rsi_threshold: float = float(os.getenv("DAEMONBLACKFX_RSI2_THRESHOLD", "10"))
    trend_sma: int = 200
    exit_sma: int = 5
    max_hold_days: int = int(os.getenv("DAEMONBLACKFX_RSI2_MAX_DAYS", "10"))
    atr_period: int = 14
    stop_atr_multiple: float = float(os.getenv("DAEMONBLACKFX_RSI2_STOP_ATR", "2.0"))
    far_target_rr: float = 20.0
    split_execution: bool = os.getenv("DAEMONBLACKFX_RSI2_SPLIT", "1").strip().lower() in {"1", "true", "yes", "on"}
    tp1_rr: float = 1.0
    runner_rr: float = 2.0
    max_entry_delay_minutes: float = float(os.getenv("DAEMONBLACKFX_RSI2_MAX_ENTRY_DELAY_MIN", "120"))
    d1_count: int = 400
    # El motor ya evita duplicados con la clave de ejecución (también contra operaciones cerradas). Marcar la señal
    # como disparada en la estrategia impedía reintentarla si el motor la bloqueaba por algo pasajero (pico de spread,
    # máximo de posiciones): 22-oct-2026 DRIFT perdió así sus 2 primeras señales. Por defecto, sin marcado.
    setup_dedupe: bool = os.getenv("DAEMONBLACKFX_RSI2_SETUP_DEDUPE", "0").strip().lower() in {"1", "true", "yes", "on"}
    # Reglas oficiales adicionales de Larry Connors (Cumulative RSI(2) < 15 y patrón R3 de 3 días bajistas)
    cumulative_rsi2_enabled: bool = os.getenv("DAEMONBLACKFX_RSI2_CUMULATIVE_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
    cumulative_rsi2_threshold: float = float(os.getenv("DAEMONBLACKFX_RSI2_CUMULATIVE_THRESHOLD", "15.0"))
    r3_pattern_enabled: bool = os.getenv("DAEMONBLACKFX_RSI2_R3_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
    r3_rsi_ceiling: float = float(os.getenv("DAEMONBLACKFX_RSI2_R3_CEILING", "14.0"))
    require_close_below_sma5: bool = os.getenv("DAEMONBLACKFX_RSI2_REQUIRE_BELOW_SMA5", "0").strip().lower() in {"1", "true", "yes", "on"}


def _rsi(close: pd.Series, n: int) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _frame(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    numeric = pd.api.types.is_numeric_dtype(df["time"])
    df["time"] = pd.to_datetime(df["time"], utc=True, unit="s" if numeric else None)
    return df.sort_values("time").reset_index(drop=True)


def daily_indicators(d1: pd.DataFrame, cfg: Rsi2Config | None = None) -> pd.DataFrame:
    """Indicadores de la regla sobre velas D1 (mismo cálculo que el replay)."""
    cfg = cfg or Rsi2Config()
    d = d1.copy()
    c = d["close"]
    d["sma_trend"] = c.rolling(cfg.trend_sma).mean()
    d["sma_exit"] = c.rolling(cfg.exit_sma).mean()
    d["rsi2"] = _rsi(c, cfg.rsi_period)
    d["cum2_rsi2"] = d["rsi2"] + d["rsi2"].shift(1)
    d["atr"] = _atr(d, cfg.atr_period)
    base_sig = (c > d["sma_trend"]) & (d["rsi2"] < cfg.rsi_threshold)
    if getattr(cfg, "require_close_below_sma5", False):
        base_sig = base_sig & (c < d["sma_exit"])
    if getattr(cfg, "cumulative_rsi2_enabled", False):
        span = (d["high"] - d["low"]).replace(0, np.nan) if ("high" in d and "low" in d) else pd.Series(1.0, index=d.index)
        close_pos = (((c - d["low"]) / span).fillna(0.5)) if ("high" in d and "low" in d) else pd.Series(0.5, index=d.index)
        cum_sig = (
            (c > d["sma_trend"])
            & (c < d["sma_exit"])
            & (d["cum2_rsi2"] < float(getattr(cfg, "cumulative_rsi2_threshold", 15.0)))
            & (d["rsi2"] < 15.0)
            & (close_pos >= 0.25)
        )
        base_sig = base_sig | cum_sig
    if getattr(cfg, "r3_pattern_enabled", False):
        span = (d["high"] - d["low"]).replace(0, np.nan) if ("high" in d and "low" in d) else pd.Series(1.0, index=d.index)
        close_pos = (((c - d["low"]) / span).fillna(0.5)) if ("high" in d and "low" in d) else pd.Series(0.5, index=d.index)
        three_down = (c < c.shift(1)) & (c.shift(1) < c.shift(2)) & (c.shift(2) < c.shift(3))
        r3_sig = (
            (c > d["sma_trend"])
            & (c < d["sma_exit"])
            & three_down
            & (d["rsi2"] < float(getattr(cfg, "r3_rsi_ceiling", 14.0)))
            & (close_pos >= 0.30)
        )
        base_sig = base_sig | r3_sig
    d["signal"] = base_sig
    return d


def closed_daily(raw: pd.DataFrame, now) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(velas D1 cerradas en `now`, velas aún abiertas)."""
    df = _frame(raw)
    closed = df["time"] + pd.Timedelta(days=1) <= pd.Timestamp(now)
    return df[closed].reset_index(drop=True), df[~closed].reset_index(drop=True)


def exit_due(d1_raw: pd.DataFrame, entry_time, now, cfg: Rsi2Config | None = None) -> str | None:
    """Motivo de salida si ya toca cerrar: cierre D1 > SMA5 en una vela cerrada desde la de entrada, o 10 velas."""
    cfg = cfg or Rsi2Config()
    closed, _ = closed_daily(d1_raw, now)
    if closed.empty:
        return None
    entry_day = pd.Timestamp(entry_time)
    entry_day = (entry_day.tz_localize("UTC") if entry_day.tzinfo is None else entry_day.tz_convert("UTC")).normalize()
    d = daily_indicators(closed, cfg)
    held = d[d["time"] >= entry_day]
    if held.empty:
        return None
    if (held["close"] > held["sma_exit"]).any():
        return "RSI2_CLOSE_ABOVE_SMA5"
    if len(held) >= cfg.max_hold_days:
        return "RSI2_MAX_HOLD_DAYS"
    return None


class ConnorsRsi2Strategy:
    def __init__(self, data_provider, config: Rsi2Config | None = None):
        self.provider = data_provider
        self.config = config or Rsi2Config()
        self._fired: set[str] = set()

    def _base(self, symbol, reason):
        return {"valid": False, "strategy_name": self.config.strategy_name, "strategy_version": self.config.strategy_version,
                "symbol": symbol, "action": "WAITING_RSI2", "reason": reason}

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        cfg = self.config
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        if not cfg.enabled:
            return self._base(symbol, "STRATEGY_DISABLED")
        if str(symbol) not in cfg.symbols:
            return self._base(symbol, "RSI2_SYMBOL_NOT_ALLOWED")
        try:
            closed, forming = closed_daily(self.provider.get_candles(symbol, "D1", count=cfg.d1_count), now)
        except Exception:
            return self._base(symbol, "RSI2_MARKET_DATA_UNAVAILABLE")
        if len(closed) < cfg.trend_sma + 2:
            return self._base(symbol, "RSI2_INSUFFICIENT_HISTORY")
        d = daily_indicators(closed, cfg)
        last = d.iloc[-1]
        if not bool(last["signal"]):
            return self._base(symbol, "NO_RSI2_PULLBACK")
        # La entrada del replay es la apertura de la vela D1 siguiente: debe existir y haber empezado hace poco.
        if forming.empty:
            return self._base(symbol, "RSI2_WAITING_NEXT_DAILY_OPEN")
        day_start = forming["time"].iloc[-1]
        try:
            m15 = _frame(self.provider.get_candles(symbol, "M15", count=200))
            first_tick = m15.loc[m15["time"] >= day_start, "time"].min()
        except Exception:
            first_tick = pd.NaT
        if pd.isna(first_tick):
            return self._base(symbol, "RSI2_WAITING_NEXT_DAILY_OPEN")
        if (now - first_tick).total_seconds() / 60 > cfg.max_entry_delay_minutes:
            return self._base(symbol, "RSI2_ENTRY_WINDOW_EXPIRED")
        setup_id = f"{symbol}|{last['time']:%Y-%m-%d}"
        if cfg.setup_dedupe and setup_id in self._fired:
            return self._base(symbol, "RSI2_SETUP_ALREADY_FIRED")
        atr = float(last["atr"])
        try:
            ask = float(self.provider.get_current_tick(symbol)["ask"])
        except Exception:
            return self._base(symbol, "RSI2_TICK_UNAVAILABLE")
        if not (np.isfinite(atr) and atr > 0 and np.isfinite(ask) and ask > 0):
            return self._base(symbol, "RSI2_ATR_UNAVAILABLE")
        risk = cfg.stop_atr_multiple * atr
        split = bool(cfg.split_execution)
        tp1_rr, tp2_rr = (cfg.tp1_rr, cfg.runner_rr) if split else (cfg.far_target_rr, cfg.far_target_rr)
        self._fired.add(setup_id)
        signal = {
            "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version, "symbol": symbol,
            "direction": "BUY", "scenario": RSI2_SCENARIO, "entry_confirmation": "D1_CLOSE_RSI2_BELOW_THRESHOLD",
            "setup_id": setup_id, "signal_day": f"{last['time']:%Y-%m-%d}", "entry_time": pd.Timestamp(first_tick).isoformat(),
            "entry_price": round(ask, 5), "stop_loss": round(ask - risk, 5),
            "take_profit": round(ask + tp2_rr * risk, 5), "tp1_price": round(ask + tp1_rr * risk, 5),
            "tp2_price": round(ask + tp2_rr * risk, 5), "tp1_rr": tp1_rr, "runner_rr": tp2_rr,
            "risk_reward_ratio": tp2_rr, "risk_reward": tp2_rr, "risk_reward_ratio_tp1": tp1_rr,
            "risk_reward_ratio_tp2": tp2_rr, "runner_target_name": "TP2", "be_trigger_rr": tp1_rr,
            "timeframe": "D1", "atr": round(atr, 5), "adx": None, "rsi2": round(float(last["rsi2"]), 2),
            "sma200": round(float(last["sma_trend"]), 5), "exit_policy": "RSI2_CLOSE_ABOVE_SMA5_OR_10_DAYS",
            "max_hold_days": cfg.max_hold_days, "split_execution": split,
            **({"leg1_risk_ratio": 0.5, "leg2_risk_ratio": 0.5} if split else {}),
            "confirmations": {"trend_sma200": True, "rsi2_oversold": True},
        }
        return {"valid": True, "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version,
                "action": "RSI2_CONFIRMED", "reason": f"{RSI2_SCENARIO} ({symbol})", "symbol": symbol, "signal": signal}
