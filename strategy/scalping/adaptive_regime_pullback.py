from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


ARPS_STRATEGY_NAME = "ARPS_SYNTHETIC_SCALPER"
ARPS_STRATEGY_VERSION = "arps-synthetic-v3-adaptive-regime"


@dataclass(frozen=True)
class AdaptiveRegimePullbackConfig:
    regime_timeframe: str = "M15"
    setup_timeframe: str = "M5"
    trigger_timeframe: str = "M1"
    regime_candles: int = 260
    setup_candles: int = 220
    trigger_candles: int = 220
    fast_ema: int = 50
    slow_ema: int = 200
    pullback_ema_fast: int = 20
    pullback_ema_slow: int = 50
    atr_period: int = 14
    adx_period: int = 14
    minimum_adx: float = 20.0
    adaptive_adx_enabled: bool = True
    adaptive_adx_floor: float = 16.0
    adaptive_adx_percentile: float = 0.35
    adaptive_adx_lookback: int = 160
    minimum_ema_gap_atr_ratio: float = 0.08
    minimum_ema_slope_atr_ratio: float = 0.02
    atr_percentile_low: float = 0.30
    atr_percentile_high: float = 0.85
    atr_stop_buffer: float = 0.20
    minimum_rr: float = 1.5
    bos_lookback: int = 12
    maximum_trigger_age_bars: int = 1
    maximum_spread_atr_ratio: float = 0.12


def _closed_frame(raw: pd.DataFrame | None) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()
    frame = raw.copy()
    required = {"time", "open", "high", "low", "close"}
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    frame["time"] = pd.to_datetime(frame["time"], utc=True, errors="coerce")
    for name in ("open", "high", "low", "close"):
        frame[name] = pd.to_numeric(frame[name], errors="coerce")
    frame = frame.dropna(subset=list(required)).sort_values("time").drop_duplicates("time")
    # MT5 entrega normalmente la vela en formación como último registro.
    return frame.iloc[:-1].copy().reset_index(drop=True) if len(frame) > 1 else pd.DataFrame()


def _atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous).abs(),
            (frame["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _adx(frame: pd.DataFrame, period: int) -> pd.Series:
    up = frame["high"].diff()
    down = -frame["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    atr = _atr(frame, period).replace(0.0, np.nan)
    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / atr
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / atr
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


class AdaptiveRegimePullbackStrategy:
    """Scalper 24/7 para sintéticos, aislado de la estrategia SMC existente."""

    def __init__(self, data_provider, config: AdaptiveRegimePullbackConfig | None = None):
        self.data_provider = data_provider
        self.config = config or AdaptiveRegimePullbackConfig()

    @staticmethod
    def _family_direction_allowed(symbol: str, direction: str) -> bool:
        value = str(symbol or "").lower()
        if "boom" in value and "flip" not in value:
            return direction == "BUY"
        if "crash" in value and "flip" not in value:
            return direction == "SELL"
        return direction in {"BUY", "SELL"}

    def _read(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        return _closed_frame(self.data_provider.get_candles(symbol, timeframe, count=count))

    def _effective_adx_threshold(self, adx: pd.Series) -> tuple[float, float | None]:
        """Umbral por instrumento, acotado por piso y techo configurados."""
        cfg = self.config
        configured = max(0.0, float(cfg.minimum_adx))
        floor = min(configured, max(0.0, float(cfg.adaptive_adx_floor)))
        if not bool(cfg.adaptive_adx_enabled):
            return configured, None
        history = adx.dropna().iloc[-max(30, int(cfg.adaptive_adx_lookback)):-1]
        if len(history) < 30:
            return configured, None
        percentile = min(1.0, max(0.0, float(cfg.adaptive_adx_percentile)))
        reference = float(history.quantile(percentile))
        return max(floor, min(configured, reference)), reference

    def analyze_symbol(self, symbol: str) -> dict[str, Any]:
        cfg = self.config
        frames = {
            "M15": self._read(symbol, cfg.regime_timeframe, cfg.regime_candles),
            "M5": self._read(symbol, cfg.setup_timeframe, cfg.setup_candles),
            "M1": self._read(symbol, cfg.trigger_timeframe, cfg.trigger_candles),
        }
        minimums = {"M15": cfg.slow_ema + 5, "M5": 60, "M1": 60}
        missing = [name for name, frame in frames.items() if len(frame) < minimums[name]]
        base = {
            "symbol": symbol,
            "strategy_name": ARPS_STRATEGY_NAME,
            "strategy_version": ARPS_STRATEGY_VERSION,
            "timeframes": {
                "regime": cfg.regime_timeframe,
                "setup": cfg.setup_timeframe,
                "trigger": cfg.trigger_timeframe,
            },
        }
        if missing:
            return {**base, "valid": False, "action": "ARPS_INSUFFICIENT_DATA", "reason": ",".join(missing)}

        m15, m5, m1 = frames["M15"], frames["M5"], frames["M1"]
        ema_fast = m15["close"].ewm(span=cfg.fast_ema, adjust=False).mean()
        ema_slow = m15["close"].ewm(span=cfg.slow_ema, adjust=False).mean()
        adx = _adx(m15, cfg.adx_period)
        m15_atr = _atr(m15, cfg.atr_period)
        m15_atr_now = float(m15_atr.iloc[-1]) if pd.notna(m15_atr.iloc[-1]) else 0.0
        slope = float(ema_fast.iloc[-1] - ema_fast.iloc[-4])
        ema_gap = abs(float(ema_fast.iloc[-1] - ema_slow.iloc[-1]))
        ema_gap_atr_ratio = ema_gap / m15_atr_now if m15_atr_now > 0 else 0.0
        ema_slope_atr_ratio = abs(slope) / m15_atr_now if m15_atr_now > 0 else 0.0
        ema_structure_ok = bool(
            ema_gap_atr_ratio >= float(cfg.minimum_ema_gap_atr_ratio)
            and ema_slope_atr_ratio >= float(cfg.minimum_ema_slope_atr_ratio)
        )
        if ema_structure_ok and ema_fast.iloc[-1] > ema_slow.iloc[-1] and slope > 0:
            direction = "BUY"
        elif ema_structure_ok and ema_fast.iloc[-1] < ema_slow.iloc[-1] and slope < 0:
            direction = "SELL"
        else:
            direction = None
        adx_now = float(adx.iloc[-1]) if pd.notna(adx.iloc[-1]) else 0.0
        effective_minimum_adx, adx_reference = self._effective_adx_threshold(adx)
        regime_diagnostics = {
            "direction": direction,
            "adx": adx_now,
            "minimum_adx": effective_minimum_adx,
            "configured_minimum_adx": float(cfg.minimum_adx),
            "effective_minimum_adx": effective_minimum_adx,
            "adaptive_adx_enabled": bool(cfg.adaptive_adx_enabled),
            "adaptive_adx_reference": adx_reference,
            "adaptive_adx_floor": float(cfg.adaptive_adx_floor),
            "ema_gap_atr_ratio": ema_gap_atr_ratio,
            "minimum_ema_gap_atr_ratio": float(cfg.minimum_ema_gap_atr_ratio),
            "ema_slope_atr_ratio": ema_slope_atr_ratio,
            "minimum_ema_slope_atr_ratio": float(cfg.minimum_ema_slope_atr_ratio),
            "ema_structure_ok": ema_structure_ok,
        }
        if direction is None or adx_now < effective_minimum_adx:
            return {
                **base, "valid": False, "action": "ARPS_REGIME_BLOCKED",
                "reason": "SIN_TENDENCIA_M15" if direction is None else "ADX_M15_INSUFICIENTE",
                "diagnostics": regime_diagnostics,
            }
        if not self._family_direction_allowed(symbol, direction):
            return {
                **base, "valid": False, "action": "ARPS_FAMILY_DIRECTION_BLOCKED",
                "reason": f"{symbol}_NO_PERMITE_{direction}", "direction": direction,
            }

        m5_atr = _atr(m5, cfg.atr_period)
        atr_now = float(m5_atr.iloc[-1])
        history = m5_atr.dropna().iloc[-160:]
        low = float(history.quantile(cfg.atr_percentile_low))
        high = float(history.quantile(cfg.atr_percentile_high))
        volatility_ok = bool(low <= atr_now <= high and atr_now > 0)
        spread = spread_atr_ratio = None
        try:
            tick = self.data_provider.get_current_tick(symbol)
            spread = abs(float(tick["ask"]) - float(tick["bid"]))
            spread_atr_ratio = spread / atr_now if atr_now > 0 else None
        except Exception:
            # La ejecución vuelve a validar precio/stops con el tick real. La
            # ausencia de esta métrica no inventa un spread ni genera señal falsa.
            pass
        spread_ok = bool(
            spread_atr_ratio is None
            or spread_atr_ratio <= cfg.maximum_spread_atr_ratio
        )

        m5_ema20 = m5["close"].ewm(span=cfg.pullback_ema_fast, adjust=False).mean()
        m5_ema50 = m5["close"].ewm(span=cfg.pullback_ema_slow, adjust=False).mean()
        prior = m5.iloc[-(cfg.bos_lookback + 2):-2]
        impulse = m5.iloc[-2]
        pullback = m5.iloc[-1]
        if direction == "BUY":
            broken_level = float(prior["high"].max())
            bos = float(impulse["close"]) > broken_level
            pullback_ok = (
                float(pullback["low"]) <= max(float(m5_ema20.iloc[-1]), broken_level) + 0.15 * atr_now
                and float(pullback["close"]) >= float(m5_ema50.iloc[-1])
            )
        else:
            broken_level = float(prior["low"].min())
            bos = float(impulse["close"]) < broken_level
            pullback_ok = (
                float(pullback["high"]) >= min(float(m5_ema20.iloc[-1]), broken_level) - 0.15 * atr_now
                and float(pullback["close"]) <= float(m5_ema50.iloc[-1])
            )

        # v97: la vela de rechazo ya no abre por sí sola. La siguiente vela M1
        # cerrada debe confirmar continuación para evitar señales de un solo tick.
        rejection_candle = m1.iloc[-2]
        trigger = m1.iloc[-1]
        rejection_body = abs(float(rejection_candle["close"]) - float(rejection_candle["open"]))
        trigger_body = abs(float(trigger["close"]) - float(trigger["open"]))
        trigger_range = max(float(trigger["high"]) - float(trigger["low"]), 1e-12)
        strong_body = trigger_body / trigger_range >= 0.45
        if direction == "BUY":
            rejection = (
                float(rejection_candle["close"]) > float(rejection_candle["open"])
                and (float(rejection_candle["open"]) - float(rejection_candle["low"])) >= rejection_body * 0.35
            )
            follow_through = (
                float(trigger["close"]) > float(trigger["open"])
                and float(trigger["close"]) > float(rejection_candle["close"])
            )
            stop = min(float(pullback["low"]), float(m1.iloc[-7:]["low"].min())) - cfg.atr_stop_buffer * atr_now
        else:
            rejection = (
                float(rejection_candle["close"]) < float(rejection_candle["open"])
                and (float(rejection_candle["high"]) - float(rejection_candle["open"])) >= rejection_body * 0.35
            )
            follow_through = (
                float(trigger["close"]) < float(trigger["open"])
                and float(trigger["close"]) < float(rejection_candle["close"])
            )
            stop = max(float(pullback["high"]), float(m1.iloc[-7:]["high"].max())) + cfg.atr_stop_buffer * atr_now

        confirmations = {
            "m15_ema_regime": direction is not None,
            "m15_adx_strength": adx_now >= effective_minimum_adx,
            "m5_atr_regime": volatility_ok,
            "spread_vs_atr": spread_ok,
            "m5_structure_break": bool(bos),
            "m5_pullback": bool(pullback_ok),
            "m1_rejection": bool(rejection),
            "m1_follow_through": bool(follow_through),
            "m1_strong_close": bool(strong_body),
        }
        missing_confirmations = [key for key, value in confirmations.items() if not value]
        diagnostics = {
            "direction": direction, "adx": adx_now, "atr": atr_now,
            **regime_diagnostics,
            "atr_allowed": [low, high], "confirmations": confirmations,
            "spread": spread, "spread_atr_ratio": spread_atr_ratio,
            "maximum_spread_atr_ratio": cfg.maximum_spread_atr_ratio,
            "rejection_candle_time": rejection_candle["time"].isoformat(),
            "confirmation_candle_time": trigger["time"].isoformat(),
        }
        if missing_confirmations:
            return {
                **base, "valid": False, "action": "ARPS_WAITING_SETUP",
                "reason": ",".join(missing_confirmations), "direction": direction,
                "diagnostics": diagnostics,
            }

        entry = float(trigger["close"])
        risk = entry - stop if direction == "BUY" else stop - entry
        if risk <= 0:
            return {**base, "valid": False, "action": "ARPS_INVALID_STOP", "reason": "STOP_NO_ESTRUCTURAL"}
        target = entry + risk * cfg.minimum_rr if direction == "BUY" else entry - risk * cfg.minimum_rr
        signal = {
            "symbol": symbol, "valid": True, "direction": direction,
            "entry_time": trigger["time"].to_pydatetime(), "signal_time": trigger["time"].to_pydatetime(),
            "entry_price": entry, "stop_loss": float(stop), "take_profit": float(target),
            "risk_reward_ratio": float(cfg.minimum_rr), "timeframe": cfg.trigger_timeframe,
            "strategy_name": ARPS_STRATEGY_NAME, "strategy_version": ARPS_STRATEGY_VERSION,
            "confirmations": confirmations,
            "passed_confirmations": list(confirmations), "missing_confirmations": [],
            "confirmation_percentage": 100.0, "trade_score": 100.0,
            "confirmation_decision": "ARPS_STRICT_CONFIRMED",
            "setup_reason": "M15 EMA/ADX; M5 BOS/pullback; M1 rejection + next-candle follow-through",
            "arps_diagnostics": diagnostics,
        }
        return {
            **base, "valid": True, "action": "ARPS_SIGNAL_CONFIRMED",
            "reason": "ARPS_REGIME_PULLBACK_CONFIRMED", "direction": direction,
            "signal": signal, "entry": signal, "diagnostics": diagnostics,
        }
