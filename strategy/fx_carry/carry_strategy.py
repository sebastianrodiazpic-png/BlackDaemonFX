"""Carry en Forex G10 con el swap real del broker (worker CARRY) — 24-oct-2026.

Reglas (las de C0 en tools/research_fx_carry_mt5.py):
- Universo: los 28 pares G10 del broker (USD, EUR, JPY, GBP, CHF, AUD, NZD, CAD).
- Carry neto anual de cada par = el mejor de sus dos swaps (largo / corto) en puntos × punto / precio × 360.
  El lado del carry es el del swap mayor (se compra la divisa de tipo alto).
- Cada mes se operan los `top_n` (3) pares de mayor carry neto positivo, en el lado del carry.
- Entrada a mercado al empezar el mes: dentro de `entry_window_hours` desde la primera vela M15 del mes.
- Stop de protección 3 × ATR20 D1 (velas D1 cerradas antes del mes). Contrato del bot: 1 % en dos entradas, TP1 1R y
  runner TP2 2R con BE tras TP1 y extensión progresiva TP3/TP4 (la gestiona el motor).
- Salida a mercado de lo que quede al cambiar de mes (rebalanceo; la ejecuta el monitor del motor).
Replay solo con MT5 (ene-2025 → oct-2026, swap actual, orientativo): +0,225 R/op en 63 operaciones (azar +0,023).
"""
from __future__ import annotations

import itertools
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

CARRY_STRATEGY = "FX_CARRY"
CARRY_VERSION = "fx-carry-v1"
CARRY_SCENARIO = "MONTHLY_TOP_CARRY"
G10 = ("USD", "EUR", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD")
CARRY_DEFAULT_SYMBOLS = (
    "USDJPY", "USDCHF", "USDCAD", "EURUSD", "EURJPY", "EURGBP", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
    "GBPUSD", "GBPJPY", "GBPCHF", "GBPAUD", "GBPNZD", "GBPCAD", "CHFJPY", "AUDUSD", "AUDJPY", "AUDCHF",
    "AUDNZD", "AUDCAD", "NZDUSD", "NZDJPY", "NZDCHF", "NZDCAD", "CADJPY", "CADCHF",
)


def _env_symbols() -> tuple:
    raw = os.getenv("DAEMONBLACKFX_CARRY_SYMBOLS", "")
    return tuple(s.strip() for s in raw.split(",") if s.strip()) or CARRY_DEFAULT_SYMBOLS


def mt5_swap_reader(symbol: str) -> dict | None:
    """Swap real del broker: {'swap_long', 'swap_short', 'point', 'swap_mode', 'price'}."""
    import MetaTrader5 as mt5
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    price = float(info.bid or info.ask or 0.0)
    return {"swap_long": float(info.swap_long), "swap_short": float(info.swap_short), "point": float(info.point),
            "swap_mode": int(info.swap_mode), "price": price}


def carry_of(swap: dict | None) -> tuple[int, float]:
    """(lado, carry neto anual en tanto por uno). Solo se entiende el modo de swap en puntos (1)."""
    if not swap or int(swap.get("swap_mode", 0)) != 1 or not swap.get("price"):
        return 0, float("nan")
    per = lambda pts: pts * swap["point"] / swap["price"] * 360
    long_c, short_c = per(swap["swap_long"]), per(swap["swap_short"])
    return (1, long_c) if long_c >= short_c else (-1, short_c)


@dataclass
class CarryConfig:
    enabled: bool = True
    strategy_name: str = CARRY_STRATEGY
    strategy_version: str = CARRY_VERSION
    symbols: tuple = field(default_factory=_env_symbols)
    top_n: int = int(os.getenv("DAEMONBLACKFX_CARRY_TOP_N", "3"))
    min_carry: float = float(os.getenv("DAEMONBLACKFX_CARRY_MIN_ANNUAL", "0.0"))
    stop_atr_multiple: float = float(os.getenv("DAEMONBLACKFX_CARRY_STOP_ATR", "3.0"))
    atr_period: int = 20
    tp1_rr: float = 1.0
    runner_rr: float = 2.0
    entry_window_hours: float = float(os.getenv("DAEMONBLACKFX_CARRY_ENTRY_WINDOW_HOURS", "24"))
    ranking_cache_seconds: float = 60.0


def month_key(ts) -> str:
    ts = pd.Timestamp(ts)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return f"{ts:%Y-%m}"


def exit_due(entry_time, now) -> str | None:
    """Rebalanceo: lo que siga abierto se cierra al empezar el mes siguiente al de la entrada."""
    return "CARRY_MONTHLY_REBALANCE" if month_key(now) != month_key(entry_time) else None


def _frame(raw):
    df = raw.copy()
    numeric = pd.api.types.is_numeric_dtype(df["time"])
    df["time"] = pd.to_datetime(df["time"], utc=True, unit="s" if numeric else None)
    return df.sort_values("time").reset_index(drop=True)


class FxCarryStrategy:
    def __init__(self, data_provider, config: CarryConfig | None = None, swap_reader=mt5_swap_reader):
        self.provider = data_provider
        self.config = config or CarryConfig()
        self.swap_reader = swap_reader
        self._ranking_cache = None

    def ranking(self) -> list[tuple[str, int, float]]:
        """[(par, lado, carry anual)] ordenado de mayor a menor carry neto (caché corta)."""
        cache = self._ranking_cache
        if cache and time.monotonic() - cache[0] < self.config.ranking_cache_seconds:
            return cache[1]
        rows = []
        for s in self.config.symbols:
            try:
                side, c = carry_of(self.swap_reader(s))
            except Exception:
                side, c = 0, float("nan")
            if side and np.isfinite(c):
                rows.append((s, side, c))
        rows.sort(key=lambda r: r[2], reverse=True)
        self._ranking_cache = (time.monotonic(), rows)
        return rows

    def selected(self) -> list[tuple[str, int, float]]:
        return [r for r in self.ranking() if r[2] > self.config.min_carry][: max(0, int(self.config.top_n))]

    def _base(self, symbol, reason):
        return {"valid": False, "strategy_name": self.config.strategy_name, "strategy_version": self.config.strategy_version,
                "symbol": symbol, "action": "WAITING_CARRY", "reason": reason}

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        cfg = self.config
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        if not cfg.enabled:
            return self._base(symbol, "STRATEGY_DISABLED")
        if str(symbol) not in cfg.symbols:
            return self._base(symbol, "CARRY_SYMBOL_NOT_ALLOWED")
        pick = {s: (side, c) for s, side, c in self.selected()}
        if str(symbol) not in pick:
            return self._base(symbol, "CARRY_NOT_IN_TOP")
        side, carry = pick[str(symbol)]
        month_start = now.normalize().replace(day=1)
        try:
            m15 = _frame(self.provider.get_candles(symbol, "M15", count=3000))
            d1 = _frame(self.provider.get_candles(symbol, "D1", count=120))
        except Exception:
            return self._base(symbol, "CARRY_MARKET_DATA_UNAVAILABLE")
        first = m15.loc[m15["time"] >= month_start, "time"].min()
        if pd.isna(first):
            return self._base(symbol, "CARRY_WAITING_MONTH_OPEN")
        if (now - first).total_seconds() / 3600 > cfg.entry_window_hours:
            return self._base(symbol, "CARRY_ENTRY_WINDOW_EXPIRED")
        closed = d1[d1["time"] + pd.Timedelta(days=1) <= month_start]
        if len(closed) < cfg.atr_period + 2:
            return self._base(symbol, "CARRY_INSUFFICIENT_HISTORY")
        pc = closed["close"].shift()
        tr = pd.concat([closed.high - closed.low, (closed.high - pc).abs(), (closed.low - pc).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(cfg.atr_period).mean().iloc[-1])
        try:
            tick = self.provider.get_current_tick(symbol)
            entry = float(tick["ask"] if side > 0 else tick["bid"])
        except Exception:
            return self._base(symbol, "CARRY_TICK_UNAVAILABLE")
        if not (np.isfinite(atr) and atr > 0 and np.isfinite(entry) and entry > 0):
            return self._base(symbol, "CARRY_ATR_UNAVAILABLE")
        risk = cfg.stop_atr_multiple * atr
        direction = "BUY" if side > 0 else "SELL"
        signal = {
            "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version, "symbol": symbol,
            "direction": direction, "scenario": CARRY_SCENARIO, "entry_confirmation": "MONTH_OPEN_TOP_CARRY",
            "setup_id": f"{symbol}|{month_key(now)}|{direction}", "entry_time": pd.Timestamp(first).isoformat(),
            "carry_month": month_key(now), "carry_annual": round(carry, 6),
            "entry_price": round(entry, 6), "stop_loss": round(entry - side * risk, 6),
            "take_profit": round(entry + side * cfg.runner_rr * risk, 6), "tp1_price": round(entry + side * cfg.tp1_rr * risk, 6),
            "tp2_price": round(entry + side * cfg.runner_rr * risk, 6), "tp1_rr": cfg.tp1_rr, "runner_rr": cfg.runner_rr,
            "risk_reward_ratio": cfg.runner_rr, "risk_reward": cfg.runner_rr, "risk_reward_ratio_tp1": cfg.tp1_rr,
            "risk_reward_ratio_tp2": cfg.runner_rr, "runner_target_name": "TP2", "be_trigger_rr": cfg.tp1_rr,
            "timeframe": "D1", "atr": round(atr, 6), "adx": None, "exit_policy": "CARRY_MONTHLY_REBALANCE",
            "split_execution": True, "leg1_risk_ratio": 0.5, "leg2_risk_ratio": 0.5,
            "confirmations": {"top_carry": True, "positive_swap": True},
        }
        return {"valid": True, "strategy_name": cfg.strategy_name, "strategy_version": cfg.strategy_version,
                "action": "CARRY_CONFIRMED", "reason": f"{CARRY_SCENARIO} ({direction} {symbol}, {carry * 100:+.2f}%/año)",
                "symbol": symbol, "signal": signal}
