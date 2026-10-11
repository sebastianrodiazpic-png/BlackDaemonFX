"""Estrategia de Trading Institucional: Malaysian SNR (Support & Resistance Malayo).

Estrategia independiente enfocada en:
1. Break: Punto de unión de cuerpos consecutivos (Close[t-1] y Open[t]).
2. Patrón A / V: Envolventes que marcan crestas (Resistencia) y valles (Soporte).
3. Fresh vs No Fresh: nivel sin contacto posterior de mechas antes de la ruptura.
4. Escenarios con causalidad temporal (rentabilidad pendiente de validación):
   - Escenario 1: Ruptura Clásica Fresh -> Retest al nivel Break en M15.
   - Escenario 3: Fractalidad (HCH / Quiebre estructural acelerado).
5. Doble Pierna Asimétrica:
   - Pierna 1: TP1 mínimo 1:2.0 RR (50% de la posición).
   - Pierna 2: Corredora contextual (TP2 1:2.5, TP3 1:3.0, TP4 1:4.0) con Break-Even automático al tocar TP1.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from strategy.malaysian_snr.config import MalaysianSNRConfig
from config.symbol_policy import is_direction_allowed
from strategy.malaysian_snr.validation import (closed_candles, timeframe_delta, av_levels,
                                               level_is_fresh, confirmed_retest, quasimodo_candidates)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr = pd.Series(tr).ewm(alpha=1/period, min_periods=period).mean()
    plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    return dx.ewm(alpha=1/period, min_periods=period).mean()


def is_synthetic_symbol(symbol: str) -> bool:
    s = str(symbol).upper()
    synth_keywords = ["JUMP", "CRASH", "BOOM", "STEP", "VOLATILITY", "RANGE BREAK", "DEX", "DRIFT SWITCHING", "DAILY RESET", "HYBRID", "FLIP", "VOL ", "VOLSWITCH", "SKEW", "MULTI STEP", "SPOT UP", "1HZ", "V10", "V25", "V50", "V75", "V100"]
    return any(kw in s for kw in synth_keywords)


class MalaysianSNRStrategy:
    """Implementación de la estrategia Malaysian SNR para análisis en tiempo real."""

    def __init__(self, data_provider, config: MalaysianSNRConfig | None = None):
        self.provider = data_provider
        self.config = config or MalaysianSNRConfig()

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        base = {"valid": False, "strategy_name": self.config.strategy_name,
                "strategy_version": self.config.strategy_version,
                "action": "WAITING_MALAYSIAN_SNR", "reason": "NO_SETUP_CONFIRMED", "symbol": symbol}
        if not self.config.enabled:
            return {**base, "reason": "STRATEGY_DISABLED"}
        allowed = tuple(self.config.allowed_symbols or ())
        norm = str(symbol).strip().lower().removesuffix("micro")
        if allowed and norm not in {a.strip().lower().removesuffix("micro") for a in allowed}:
            return {**base, "reason": "SYMBOL_NOT_IN_MSNR_ALLOWLIST"}
        if self.config.enable_session_killzones_filter and not is_synthetic_symbol(symbol):
            hour = now.hour + now.minute / 60.0 + now.second / 3600.0
            if not (7 <= hour < 11 or 12.5 <= hour < 17):
                return {**base, "reason": "SESSION_FILTER_OUTSIDE_KILLZONE"}
        try:
            raw_h1 = self.provider.get_candles(symbol, self.config.structure_timeframe, count=80)
            raw_m15 = self.provider.get_candles(symbol, self.config.entry_timeframe, count=60)
            raw_d1 = (self.provider.get_candles(symbol, self.config.macro_timeframe, count=40)
                      if (self.config.enable_daily_storyline_filter or getattr(self.config, 'enable_d1_storyline_levels', False)) else None)
        except Exception as exc:
            return {**base, "reason": f"PROVIDER_ERROR: {exc}"}
        try:
            h1 = closed_candles(raw_h1, self.config.structure_timeframe, now)
            m15 = closed_candles(raw_m15, self.config.entry_timeframe, now)
            d1 = closed_candles(raw_d1, self.config.macro_timeframe, now) if raw_d1 is not None else pd.DataFrame()
        except (ValueError, TypeError, KeyError) as exc:
            return {**base, "reason": f"INVALID_CANDLE_DATA: {exc}"}
        if len(h1) < 28 or len(m15) < 20:
            return {**base, "reason": "INSUFFICIENT_CLOSED_CANDLES"}
        for frame, tf in ((h1, self.config.structure_timeframe), (m15, self.config.entry_timeframe)):
            delta = timeframe_delta(tf)
            if now - (frame.iloc[-1].time + delta) >= delta:
                return {**base, "reason": f"STALE_CANDLES_{tf}"}
        daily_direction = None
        if self.config.enable_daily_storyline_filter:
            if d1.empty:
                return {**base, "reason": "MISSING_CLOSED_D1"}
            if now - (d1.iloc[-1].time + timeframe_delta(self.config.macro_timeframe)) > pd.Timedelta(days=3):
                return {**base, "reason": "STALE_CANDLES_D1"}
            prev = d1.iloc[-1]
            if prev.close == prev.open:
                return {**base, "reason": "NEUTRAL_D1_BIAS"}
            daily_direction = "BUY" if prev.close > prev.open else "SELL"
        atr, adx = float(compute_atr(h1).iloc[-1]), float(compute_adx(h1).iloc[-1])
        if not math.isfinite(atr) or atr <= 0 or not math.isfinite(adx):
            return {**base, "reason": "INVALID_INDICATORS"}
        last = h1.iloc[-1]
        span = float(last.high - last.low)
        body_ratio = float(abs(last.close - last.open) / span) if span > 0 else 0.0
        # M15 bars inside the H1 breakout cannot confirm a later retest.
        break_closed_at = last.time + timeframe_delta(self.config.structure_timeframe)
        recent_m15 = m15[m15.time >= break_closed_at].tail(6)
        if recent_m15.empty:
            return {**base, "reason": "WAITING_POST_BREAK_RETEST"}
        entry = float(recent_m15.iloc[-1].close)
        levels = av_levels(h1)
        d1_levels = av_levels(d1) if (getattr(self.config, 'enable_d1_storyline_levels', False) and d1 is not None and not d1.empty) else []
        use_crt = getattr(self.config, 'enable_crt_sweep_rejection', True)

        def allowed_direction(direction):
            return is_direction_allowed(symbol, direction) and (daily_direction is None or direction == daily_direction)

        def make_signal(direction, scenario, level, break_level, stop):
            sign = 1 if direction == "BUY" else -1
            risk_dist = sign * (entry - stop)
            if risk_dist <= 0:
                return {"valid": False, "strategy_name": self.config.strategy_name,
                        "strategy_version": self.config.strategy_version, "symbol": symbol,
                        "action": "WAITING_MALAYSIAN_SNR", "reason": "INVALID_STOP_OR_RISK_DISTANCE"}

            if getattr(self.config, 'enable_d1_storyline_levels', False) and d1_levels:
                d1_candidates = [item["level"] for item in d1_levels
                                 if item["type"] == ("A_RESISTANCE" if direction == "BUY" else "V_SUPPORT")
                                 and sign * (item["level"] - entry) > 0]
                if d1_candidates:
                    closest_d1 = min(d1_candidates) if direction == "BUY" else max(d1_candidates)
                    d1_clearance = sign * (closest_d1 - entry)
                    min_rr = getattr(self.config, 'min_obstacle_rr', 2.0)
                    if d1_clearance < min_rr * risk_dist:
                        return {"valid": False, "strategy_name": self.config.strategy_name,
                                "strategy_version": self.config.strategy_version, "symbol": symbol,
                                "action": "WAITING_MALAYSIAN_SNR", "reason": "OBSTACLE_D1_BEFORE_2R"}

            candidates = [item["level"] for item in levels
                          if item["type"] == ("A_RESISTANCE" if direction == "BUY" else "V_SUPPORT")
                          and sign * (item["level"] - entry) > 0]
            obstacle = (min(candidates) if direction == "BUY" else max(candidates)) if candidates else 0.0
            result = self._build_confirmed_signal(
                symbol=symbol, direction=direction, scenario=scenario, entry_price=entry,
                stop_loss=stop, risk_dist=sign * (entry - stop), adx=adx,
                body_ratio=body_ratio, ref_level=level, break_level=break_level,
                current_atr=atr, obstacle_level=obstacle,
                now_utc=(recent_m15.iloc[-1].time + timeframe_delta(self.config.entry_timeframe)).to_pydatetime())
            if result.get("valid"):
                result["signal"].update({"macro_bias": daily_direction,
                    "evaluated_at": now.isoformat(),
                    "macro_bias_method": "LAST_CLOSED_D1_CANDLE_DIRECTION",
                    "structure_closed_at": break_closed_at.isoformat(),
                    "confirmation_closed_at": (recent_m15.iloc[-1].time + timeframe_delta(self.config.entry_timeframe)).isoformat(),
                    "entry_confirmation": "CRT_M15_SWEEP_AND_ABSORPTION_CLOSE" if use_crt else "POST_BREAK_M15_RETEST_AND_DIRECTIONAL_CLOSE"})
            return result

        rejection = None
        if self.config.enable_scenario_1_continuation and adx >= 20:
            recent_levels = [item for item in levels
                             if 2 < len(h1) - 1 - item["idx"] <= self.config.level_lookback_candles]
            for level in reversed(recent_levels):
                direction = "BUY" if level["type"] == "A_RESISTANCE" else "SELL"
                sign = 1 if direction == "BUY" else -1
                if not allowed_direction(direction):
                    continue
                if self.config.enable_strict_fresh_filter and not level_is_fresh(h1, level):
                    continue
                wick = last.high - last.close if direction == "BUY" else last.close - last.low
                if (span <= 0 or sign * (last.close - last.open) <= 0
                        or sign * (last.close - level["level"]) <= 0
                        or body_ratio < self.config.minimum_body_ratio
                        or wick / span > self.config.maximum_breakout_wick_ratio):
                    continue
                if not confirmed_retest(recent_m15, level["level"], direction, atr,
                                        self.config.retest_tolerance_atr, self.config.max_entry_distance_atr, use_crt_trigger=use_crt):
                    continue
                stop = (min(float(recent_m15.low.min()), float(last.low)) - .15 * atr if direction == "BUY"
                        else max(float(recent_m15.high.max()), float(last.high)) + .15 * atr)
                result = make_signal(direction, "ESC_1_CONTINUATION", level["level"], level["break_level"], stop)
                if result.get("valid"):
                    return result
                rejection = result

        if self.config.enable_quasimodo_pattern:
            for pattern in quasimodo_candidates(h1, self.config.qm_swing_radius):
                direction = pattern["direction"]
                if not allowed_direction(direction):
                    continue
                if not confirmed_retest(recent_m15, pattern["shoulder"], direction, atr,
                                        self.config.retest_tolerance_atr, self.config.max_entry_distance_atr, use_crt_trigger=use_crt):
                    continue
                sign = 1 if direction == "BUY" else -1
                # A sweep beyond the head after BOS invalidates the setup.
                if (direction == "BUY" and recent_m15.low.min() <= pattern["head"]) or (direction == "SELL" and recent_m15.high.max() >= pattern["head"]):
                    continue
                result = make_signal(direction, "ESC_3_QUASIMODO", pattern["shoulder"],
                                     pattern["neckline"], pattern["head"] - sign * .10 * atr)
                if result.get("valid"):
                    return result
                rejection = result

        if self.config.enable_scenario_3_fractal:
            prev2, prev1 = h1.iloc[-3], h1.iloc[-2]
            direction = None
            if prev1.low < prev2.low and last.close > last.open and last.close > prev2.high:
                direction, neckline = "BUY", float(prev2.high)
            elif prev1.high > prev2.high and last.close < last.open and last.close < prev2.low:
                direction, neckline = "SELL", float(prev2.low)
            if direction and body_ratio >= .55 and allowed_direction(direction):
                if confirmed_retest(recent_m15, neckline, direction, atr,
                                    self.config.retest_tolerance_atr, min(.40, self.config.max_entry_distance_atr), use_crt_trigger=use_crt):
                    stop = (min(float(recent_m15.low.min()), float(last.low)) - .15 * atr if direction == "BUY"
                            else max(float(recent_m15.high.max()), float(last.high)) + .15 * atr)
                    result = make_signal(direction, "ESC_3_FRACTAL", neckline, float(prev1.close), stop)
                    if result.get("valid"):
                        return result
                    rejection = result
        return rejection or base

    def _build_confirmed_signal(
        self,
        symbol: str,
        direction: str,
        scenario: str,
        entry_price: float,
        stop_loss: float,
        risk_dist: float,
        adx: float,
        body_ratio: float,
        ref_level: float,
        break_level: float,
        current_atr: float = 0.0,
        obstacle_level: float = 0.0,
        now_utc: datetime | None = None,
    ) -> dict:
        """Construye el payload completo de señal dual con targets asimétricos y features para IA."""
        def reject(reason):
            return {"valid": False, "strategy_name": self.config.strategy_name,
                    "strategy_version": self.config.strategy_version, "symbol": symbol,
                    "action": "WAITING_MALAYSIAN_SNR", "reason": reason}

        values = (entry_price, stop_loss, risk_dist, adx, body_ratio, current_atr, obstacle_level)
        if direction not in {"BUY", "SELL"} or not all(math.isfinite(v) for v in values):
            return reject("INVALID_SIGNAL_GEOMETRY")
        sign = 1 if direction == "BUY" else -1
        actual_risk = sign * (entry_price - stop_loss)
        if actual_risk <= 0 or not math.isclose(actual_risk, risk_dist, rel_tol=1e-8, abs_tol=1e-10):
            return reject("INVALID_STOP_OR_RISK_DISTANCE")
        if not is_direction_allowed(symbol, direction):
            return reject("DIRECTION_POLICY_BLOCKED")
        # 1. TP1: Mínimo 1:2.0 RR (Requisito fundamental validado a 2 años)
        tp1_price = entry_price + (self.config.tp1_min_rr * risk_dist) if direction == "BUY" else entry_price - (self.config.tp1_min_rr * risk_dist)

        # 2. Asignación contextual de la corredora
        if scenario in ("ESC_1_CONTINUATION", "ESC_1_FRESH_C_TRADE") and adx >= self.config.adx_tp4_threshold and body_ratio >= self.config.body_ratio_tp4_threshold:
            runner_target_name = "TP4"
            runner_rr = self.config.tp4_runner_rr  # 1:4.0 RR
        elif adx >= self.config.adx_tp3_threshold:
            runner_target_name = "TP3"
            runner_rr = self.config.tp3_runner_rr  # 1:3.0 RR
        else:
            runner_target_name = "TP2"
            runner_rr = self.config.tp2_runner_rr  # 1:2.5 RR

        # Ajuste dinámico de Obstacle Awareness: si hay un obstáculo estructural previo
        if self.config.enable_obstacle_awareness and obstacle_level > 0:
            room = sign * (obstacle_level - entry_price) - self.config.obstacle_buffer_atr * current_atr
            if room < self.config.tp1_min_rr * risk_dist:
                return reject("OBSTACLE_BEFORE_MINIMUM_TP1")
            runner_rr = min(runner_rr, room / risk_dist)
        if not math.isfinite(runner_rr) or runner_rr < self.config.tp1_min_rr or self.config.tp1_min_rr <= 0:
            return reject("INVALID_TARGET_ORDER")

        tp2_price = entry_price + (runner_rr * risk_dist) if direction == "BUY" else entry_price - (runner_rr * risk_dist)

        # Heuristic rule scores, NOT calibrated probabilities of trade success.
        base_score = 75.0
        adx_bonus = min(15.0, max(0.0, (adx - 20.0) * 1.5))
        body_bonus = 10.0 if body_ratio >= 0.60 else 5.0
        trade_score = min(100.0, base_score + adx_bonus + body_bonus)
        conf_pct = 85.0 if "ESC_1" in scenario else 90.0

        # Vector de features para inferencia y meta-etiquetado continuo de IA
        ai_features = {
            "trade_score": round(trade_score, 2),
            "confirmation_percentage": round(conf_pct, 2),
            "adx": round(adx, 2),
            "adx_regime": 1.0 if adx >= 25.0 else 0.0,
            "body_ratio": round(body_ratio, 3),
            "scenario_is_fractal": 1.0 if "ESC_3" in scenario else 0.0,
            "risk_distance": round(risk_dist, 5),
            "is_buy": 1.0 if direction == "BUY" else 0.0,
            "runner_expected_rr": runner_rr,
            "obstacle_level": round(obstacle_level, 5),
        }

        signal = {
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "symbol": symbol,
            "direction": direction,
            "scenario": scenario,
            "entry_time": (now_utc or datetime.now(timezone.utc)).isoformat(),
            "entry_price": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "risk_reward_ratio": runner_rr,
            "risk_reward": runner_rr,
            "risk_reward_ratio_tp1": self.config.tp1_min_rr,
            "risk_reward_ratio_tp2": runner_rr,
            "tp1_price": round(tp1_price, 5),
            "tp1_rr": self.config.tp1_min_rr,
            "tp2_price": round(tp2_price, 5),
            "runner_target_name": runner_target_name,
            "runner_rr": runner_rr,
            "be_trigger_rr": self.config.tp1_min_rr,  # Al tocar TP1, mover SL de corredora a BE
            "timeframe": self.config.entry_timeframe,
            "momentum_adx": round(adx, 1),
            "adx": round(adx, 2),
            "atr": round(current_atr, 5) if current_atr > 0 else round(risk_dist / max(1.0, runner_rr), 5),
            "trade_score": round(trade_score, 2),
            "confirmation_percentage": round(conf_pct, 2),
            "confirmation_percentage_kind": "HEURISTIC_RULE_SCORE_NOT_PROBABILITY",
            "success_probability": None,
            "probability_status": "UNVALIDATED_FOR_CURRENT_STRATEGY_VERSION",
            "structure_break": f"{scenario}_{direction}",
            "body_ratio": round(body_ratio, 2),
            "ref_level": round(ref_level, 5),
            "break_level": round(break_level, 5),
            "obstacle_level": round(obstacle_level, 5),
            "price_action_confirmations": {"rejection": True, "micro_structure": True, "displacement": True, "strong_close": True},
            "confirmations": {"rejection": True, "micro_structure": True, "displacement": True, "strong_close": True},
            "meta_features": ai_features,
            # Configuración para el motor de ejecución de dos piernas (50% / 50%)
            "split_execution": True,
            "leg1_risk_ratio": self.config.leg1_risk_ratio,
            "leg2_risk_ratio": self.config.leg2_risk_ratio,
        }

        return {
            "valid": True,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "action": "MALAYSIAN_SNR_CONFIRMED",
            "reason": f"{scenario} confirmed ({direction} on {symbol})",
            "symbol": symbol,
            "signal": signal,
        }
