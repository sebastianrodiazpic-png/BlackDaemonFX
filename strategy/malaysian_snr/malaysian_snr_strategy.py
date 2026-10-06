"""Estrategia de Trading Institucional: Malaysian SNR (Support & Resistance Malayo).

Estrategia independiente enfocada en:
1. Break: Punto de unión de cuerpos consecutivos (Close[t-1] y Open[t]).
2. Patrón A / V: Envolventes que marcan crestas (Resistencia) y valles (Soporte).
3. Fresh vs No Fresh: Ruptura con cuerpo sólido (Continuación) vs Mecha de manipulación (Reversión).
4. Escenarios Auditados de 2 Años:
   - Escenario 1: Ruptura Clásica Fresh -> Retest al nivel Break en M15.
   - Escenario 3: Fractalidad (HCH / Quiebre estructural acelerado).
5. Doble Pierna Asimétrica:
   - Pierna 1: TP1 mínimo 1:2.0 RR (50% de la posición).
   - Pierna 2: Corredora contextual (TP2 1:2.5, TP3 1:3.5, TP4 1:5.0) con Break-Even automático al tocar TP1.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from strategy.malaysian_snr.config import MalaysianSNRConfig
from config.symbol_policy import is_direction_allowed


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


class MalaysianSNRStrategy:
    """Implementación de la estrategia Malaysian SNR para análisis en tiempo real."""

    def __init__(self, data_provider, config: MalaysianSNRConfig | None = None):
        self.provider = data_provider
        self.config = config or MalaysianSNRConfig()

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        if now.tzinfo is None:
            now = now.tz_localize("UTC")

        base_response = {
            "valid": False,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "action": "WAITING_MALAYSIAN_SNR",
            "reason": "NO_SETUP_CONFIRMED",
            "symbol": symbol,
        }

        # Obtener velas H1 y M15
        try:
            raw_h1 = self.provider.get_candles(symbol, self.config.structure_timeframe, count=80)
            raw_m15 = self.provider.get_candles(symbol, self.config.entry_timeframe, count=60)
        except Exception as exc:
            return {**base_response, "reason": f"PROVIDER_ERROR: {exc}"}

        if raw_h1 is None or len(raw_h1) < 25 or raw_m15 is None or len(raw_m15) < 20:
            return {**base_response, "reason": "INSUFFICIENT_CANDLES"}

        df_h1 = raw_h1.copy()
        df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
        df_h1 = df_h1[df_h1["time"] <= now].sort_values("time").reset_index(drop=True)

        df_m15 = raw_m15.copy()
        df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
        df_m15 = df_m15[df_m15["time"] <= now].sort_values("time").reset_index(drop=True)

        if len(df_h1) < 20 or len(df_m15) < 15:
            return {**base_response, "reason": "INSUFFICIENT_HISTORICAL_DATA"}

        df_h1["atr"] = compute_atr(df_h1, 14)
        df_h1["adx"] = compute_adx(df_h1, 14)

        current_atr = float(df_h1["atr"].iloc[-1]) if not pd.isna(df_h1["atr"].iloc[-1]) else 1.0
        current_adx = float(df_h1["adx"].iloc[-1]) if not pd.isna(df_h1["adx"].iloc[-1]) else 20.0

        # Identificar niveles A/V y Breaks en H1
        h1_levels = []
        for i in range(2, len(df_h1) - 1):
            prev = df_h1.iloc[i - 1]
            curr = df_h1.iloc[i]
            # Patrón A (Resistencia envolvente)
            if prev["close"] > prev["open"] and curr["close"] < curr["open"]:
                if curr["close"] <= prev["open"]:
                    h1_levels.append({
                        "type": "A_RESISTANCE",
                        "level": max(prev["high"], curr["high"]),
                        "break_level": prev["close"],  # Cierre anterior = unión de cuerpos
                        "time": curr["time"],
                        "idx": i,
                    })
            # Patrón V (Soporte envolvente)
            elif prev["close"] < prev["open"] and curr["close"] > curr["open"]:
                if curr["close"] >= prev["open"]:
                    h1_levels.append({
                        "type": "V_SUPPORT",
                        "level": min(prev["low"], curr["low"]),
                        "break_level": prev["close"],  # Cierre anterior = unión de cuerpos
                        "time": curr["time"],
                    })

        last_h1 = df_h1.iloc[-1]
        h1_body = abs(last_h1["close"] - last_h1["open"])
        h1_span = last_h1["high"] - last_h1["low"]
        body_ratio = (h1_body / h1_span) if h1_span > 0 else 0.0

        # Últimas velas M15 para entrada
        last_m15 = df_m15.iloc[-1]
        entry_price = float(last_m15["close"])

        # -------------------------------------------------------------
        # ESCENARIO 1: Ruptura Clásica (Fresh Breakout en H1 -> Retest en M15)
        # -------------------------------------------------------------
        if self.config.enable_scenario_1_continuation:
            for lvl in reversed(h1_levels[-25:]):
                lvl_price = lvl["level"]
                break_price = lvl["break_level"]

                # Ruptura Alcista Fresh
                if lvl["type"] == "A_RESISTANCE":
                    upper_wick = last_h1["high"] - last_h1["close"]
                    upper_wick_ratio = (upper_wick / h1_span) if h1_span > 0 else 0.0
                    if (
                        last_h1["close"] > lvl_price
                        and body_ratio >= self.config.minimum_body_ratio
                        and upper_wick_ratio <= self.config.maximum_breakout_wick_ratio
                    ):
                        if is_direction_allowed(symbol, "BUY"):
                            sl = float(last_h1["low"]) - (0.20 * current_atr)
                            risk_dist = abs(entry_price - sl)
                            if risk_dist > 0:
                                return self._build_confirmed_signal(
                                    symbol=symbol,
                                    direction="BUY",
                                    scenario="ESC_1_CONTINUATION",
                                    entry_price=entry_price,
                                    stop_loss=sl,
                                    risk_dist=risk_dist,
                                    adx=current_adx,
                                    body_ratio=body_ratio,
                                    ref_level=lvl_price,
                                    break_level=break_price,
                                )

                # Ruptura Bajista Fresh
                elif lvl["type"] == "V_SUPPORT":
                    lower_wick = last_h1["close"] - last_h1["low"]
                    lower_wick_ratio = (lower_wick / h1_span) if h1_span > 0 else 0.0
                    if (
                        last_h1["close"] < lvl_price
                        and body_ratio >= self.config.minimum_body_ratio
                        and lower_wick_ratio <= self.config.maximum_breakout_wick_ratio
                    ):
                        if is_direction_allowed(symbol, "SELL"):
                            sl = float(last_h1["high"]) + (0.20 * current_atr)
                            risk_dist = abs(sl - entry_price)
                            if risk_dist > 0:
                                return self._build_confirmed_signal(
                                    symbol=symbol,
                                    direction="SELL",
                                    scenario="ESC_1_CONTINUATION",
                                    entry_price=entry_price,
                                    stop_loss=sl,
                                    risk_dist=risk_dist,
                                    adx=current_adx,
                                    body_ratio=body_ratio,
                                    ref_level=lvl_price,
                                    break_level=break_price,
                                )

        # -------------------------------------------------------------
        # ESCENARIO 3: Fractalidad (HCH / Quiebre Estructural Rápido)
        # -------------------------------------------------------------
        if self.config.enable_scenario_3_fractal and len(df_h1) >= 4:
            c_prev2 = df_h1.iloc[-3]
            c_prev1 = df_h1.iloc[-2]
            c_curr = df_h1.iloc[-1]

            # Fractal Bullish HCH
            if c_prev1["low"] < c_prev2["low"] and c_curr["close"] > c_curr["open"]:
                f_body = c_curr["close"] - c_curr["open"]
                f_span = c_curr["high"] - c_curr["low"]
                if f_span > 0 and (f_body / f_span) >= 0.55 and c_curr["close"] > c_prev2["high"]:
                    if is_direction_allowed(symbol, "BUY"):
                        sl = float(c_prev1["low"]) - (0.15 * current_atr)
                        risk_dist = abs(entry_price - sl)
                        if risk_dist > 0:
                            return self._build_confirmed_signal(
                                symbol=symbol,
                                direction="BUY",
                                scenario="ESC_3_FRACTAL",
                                entry_price=entry_price,
                                stop_loss=sl,
                                risk_dist=risk_dist,
                                adx=current_adx,
                                body_ratio=f_body / f_span,
                                ref_level=float(c_prev2["high"]),
                                break_level=float(c_prev1["close"]),
                            )

            # Fractal Bearish HCH
            elif c_prev1["high"] > c_prev2["high"] and c_curr["close"] < c_curr["open"]:
                f_body = c_curr["open"] - c_curr["close"]
                f_span = c_curr["high"] - c_curr["low"]
                if f_span > 0 and (f_body / f_span) >= 0.55 and c_curr["close"] < c_prev2["low"]:
                    if is_direction_allowed(symbol, "SELL"):
                        sl = float(c_prev1["high"]) + (0.15 * current_atr)
                        risk_dist = abs(sl - entry_price)
                        if risk_dist > 0:
                            return self._build_confirmed_signal(
                                symbol=symbol,
                                direction="SELL",
                                scenario="ESC_3_FRACTAL",
                                entry_price=entry_price,
                                stop_loss=sl,
                                risk_dist=risk_dist,
                                adx=current_adx,
                                body_ratio=f_body / f_span,
                                ref_level=float(c_prev2["low"]),
                                break_level=float(c_prev1["close"]),
                            )

        return base_response

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
    ) -> dict:
        """Construye el payload completo de señal dual con targets asimétricos y features para IA."""
        # 1. TP1: 1:1.0 RR (Requisito fundamental)
        tp1_price = entry_price + (self.config.tp1_min_rr * risk_dist) if direction == "BUY" else entry_price - (self.config.tp1_min_rr * risk_dist)

        # 2. Asignación contextual de la corredora
        if scenario == "ESC_1_CONTINUATION" and adx >= self.config.adx_tp4_threshold and body_ratio >= self.config.body_ratio_tp4_threshold:
            runner_target_name = "TP4"
            runner_rr = self.config.tp4_runner_rr  # 1:4.0 RR
        elif adx >= self.config.adx_tp3_threshold:
            runner_target_name = "TP3"
            runner_rr = self.config.tp3_runner_rr  # 1:3.0 RR
        else:
            runner_target_name = "TP2"
            runner_rr = self.config.tp2_runner_rr  # 1:2.0 RR

        tp2_price = entry_price + (runner_rr * risk_dist) if direction == "BUY" else entry_price - (runner_rr * risk_dist)

        # Vector de features para inferencia y meta-etiquetado continuo de IA
        ai_features = {
            "adx": round(adx, 2),
            "adx_regime": 1.0 if adx >= 25.0 else 0.0,
            "body_ratio": round(body_ratio, 3),
            "scenario_is_fractal": 1.0 if scenario == "ESC_3_FRACTAL" else 0.0,
            "risk_distance": round(risk_dist, 5),
            "is_buy": 1.0 if direction == "BUY" else 0.0,
            "runner_expected_rr": runner_rr,
        }

        signal = {
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "symbol": symbol,
            "direction": direction,
            "scenario": scenario,
            "entry_time": datetime.now(timezone.utc).isoformat(),
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
            "body_ratio": round(body_ratio, 2),
            "ref_level": round(ref_level, 5),
            "break_level": round(break_level, 5),
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
