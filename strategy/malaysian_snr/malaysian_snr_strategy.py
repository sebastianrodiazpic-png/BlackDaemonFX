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


def is_synthetic_symbol(symbol: str) -> bool:
    s = str(symbol).upper()
    synth_keywords = ["INDEX", "JUMP", "CRASH", "BOOM", "STEP", "VOLATILITY", "RANGE", "DEX"]
    return any(kw in s for kw in synth_keywords)


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

        # 1. Filtro Institucional de Sesiones (Killzones) para activos convencionales
        is_synth = is_synthetic_symbol(symbol)
        if self.config.enable_session_killzones_filter and not is_synth:
            t_float = now.hour + (now.minute / 60.0)
            in_london = (7.0 <= t_float <= 11.0)
            in_ny = (12.5 <= t_float <= 17.0)
            if not (in_london or in_ny):
                return {**base_response, "reason": "SESSION_FILTER_OUTSIDE_KILLZONE"}

        # 2. Obtener velas H1, M15 y D1 (Daily Storyline)
        try:
            raw_h1 = self.provider.get_candles(symbol, self.config.structure_timeframe, count=80)
            raw_m15 = self.provider.get_candles(symbol, self.config.entry_timeframe, count=60)
            raw_d1 = None
            if self.config.enable_daily_storyline_filter:
                raw_d1 = self.provider.get_candles(symbol, self.config.macro_timeframe, count=15)
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

        # Cálculo de Daily Storyline (sesgo macro D1 de la vela previa cerrada)
        daily_bullish = True
        if raw_d1 is not None and len(raw_d1) >= 2:
            df_d1 = raw_d1.copy()
            df_d1["time"] = pd.to_datetime(df_d1["time"], utc=True)
            df_d1 = df_d1[df_d1["time"] < now].sort_values("time").reset_index(drop=True)
            if len(df_d1) >= 1:
                prev_d1 = df_d1.iloc[-1]
                daily_bullish = bool(prev_d1["close"] > prev_d1["open"])

        df_h1["atr"] = compute_atr(df_h1, 14)
        df_h1["adx"] = compute_adx(df_h1, 14)

        current_atr = float(df_h1["atr"].iloc[-1]) if not pd.isna(df_h1["atr"].iloc[-1]) else 1.0
        current_adx = float(df_h1["adx"].iloc[-1]) if not pd.isna(df_h1["adx"].iloc[-1]) else 20.0

        # Identificar niveles A/V y Breaks en H1 con índice para tracking de Fresh
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
                        "idx": i,
                    })

        last_h1 = df_h1.iloc[-1]
        h1_body = abs(last_h1["close"] - last_h1["open"])
        h1_span = last_h1["high"] - last_h1["low"]
        body_ratio = (h1_body / h1_span) if h1_span > 0 else 0.0

        # Últimas velas M15 para entrada
        last_m15 = df_m15.iloc[-1]
        entry_price = float(last_m15["close"])
        recent_m15 = df_m15.iloc[-6:] if len(df_m15) >= 6 else df_m15

        # -------------------------------------------------------------
        # ESCENARIO 1: Ruptura Clásica (Fresh Breakout en H1 -> Retest en M15)
        # -------------------------------------------------------------
        if self.config.enable_scenario_1_continuation:
            # Filtro de régimen de mercado: en mercados planos/sin tendencia (ADX < 20)
            # las rupturas continuas sufren falsos rompimientos frecuentes.
            if current_adx >= 20.0:
                h1_total = len(df_h1)
                recent_levels = [lvl for lvl in h1_levels if 2 < (h1_total - 1 - lvl.get("idx", 0)) <= 35]
                for lvl in reversed(recent_levels):
                    lvl_price = lvl["level"]
                    break_price = lvl["break_level"]
                    lvl_idx = lvl.get("idx", 0)

                    # MEJORA 1: TRUE FRESH LEVEL TRACKING (Descartar niveles mitigados)
                    intermediate_df = df_h1.iloc[lvl_idx + 1 : h1_total - 1]

                    # Ruptura Alcista Fresh + Retest M15 (Resistencia A convertida en Soporte)
                    if lvl["type"] == "A_RESISTANCE":
                        if self.config.enable_strict_fresh_filter and len(intermediate_df) > 0:
                            if (intermediate_df["high"] >= lvl_price).any():
                                continue  # Nivel Mitigado / Unfresh

                        # MEJORA 2: DAILY STORYLINE ALIGNMENT
                        if self.config.enable_daily_storyline_filter and not daily_bullish:
                            continue

                        upper_wick = last_h1["high"] - last_h1["close"]
                        upper_wick_ratio = (upper_wick / h1_span) if h1_span > 0 else 0.0
                        if (
                            last_h1["close"] > lvl_price
                            and body_ratio >= self.config.minimum_body_ratio
                            and upper_wick_ratio <= self.config.maximum_breakout_wick_ratio
                        ):
                            # Retest M15: verificar que el precio haya testeado la zona de ruptura
                            retest_tested = any(
                                float(row["low"]) <= lvl_price + (0.35 * current_atr)
                                for _, row in recent_m15.iterrows()
                            )
                            # Antipersecución: No comprar si el precio ya se disparó más de 0.50 ATR del nivel
                            not_overextended = entry_price <= (lvl_price + (0.50 * current_atr))
                            # Defensa estructural: el precio debe mantenerse sobre el nivel de soporte
                            respects_level = entry_price >= (break_price - (0.15 * current_atr))

                            if retest_tested and not_overextended and respects_level:
                                if is_direction_allowed(symbol, "BUY"):
                                    retest_low = float(recent_m15["low"].min())
                                    sl = min(retest_low, float(last_h1["low"])) - (0.15 * current_atr)
                                    risk_dist = abs(entry_price - sl)
                                    if risk_dist > 0:
                                        # MEJORA 5: OBSTACLE AWARENESS (Nivel de resistencia superior más cercano)
                                        opp_lvls = [ol["level"] for ol in recent_levels if ol["type"] == "A_RESISTANCE" and ol["level"] > entry_price]
                                        nearest_obstacle = min(opp_lvls) if opp_lvls else 0.0

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
                                            current_atr=current_atr,
                                            obstacle_level=nearest_obstacle,
                                        )

                    # Ruptura Bajista Fresh + Retest M15 (Soporte V convertido en Resistencia)
                    elif lvl["type"] == "V_SUPPORT":
                        if self.config.enable_strict_fresh_filter and len(intermediate_df) > 0:
                            if (intermediate_df["low"] <= lvl_price).any():
                                continue  # Nivel Mitigado / Unfresh

                        # MEJORA 2: DAILY STORYLINE ALIGNMENT
                        if self.config.enable_daily_storyline_filter and daily_bullish:
                            continue

                        lower_wick = last_h1["close"] - last_h1["low"]
                        lower_wick_ratio = (lower_wick / h1_span) if h1_span > 0 else 0.0
                        if (
                            last_h1["close"] < lvl_price
                            and body_ratio >= self.config.minimum_body_ratio
                            and lower_wick_ratio <= self.config.maximum_breakout_wick_ratio
                        ):
                            # Retest M15: verificar que el precio haya retesteado la zona
                            retest_tested = any(
                                float(row["high"]) >= lvl_price - (0.35 * current_atr)
                                for _, row in recent_m15.iterrows()
                            )
                            # Antipersecución: No vender si el precio ya se desplomó más de 0.50 ATR del nivel
                            not_overextended = entry_price >= (lvl_price - (0.50 * current_atr))
                            # Defensa estructural: el precio debe mantenerse bajo el nivel de resistencia
                            respects_level = entry_price <= (break_price + (0.15 * current_atr))

                            if retest_tested and not_overextended and respects_level:
                                if is_direction_allowed(symbol, "SELL"):
                                    retest_high = float(recent_m15["high"].max())
                                    sl = max(retest_high, float(last_h1["high"])) + (0.15 * current_atr)
                                    risk_dist = abs(sl - entry_price)
                                    if risk_dist > 0:
                                        # MEJORA 5: OBSTACLE AWARENESS (Nivel de soporte inferior más cercano)
                                        opp_lvls = [ol["level"] for ol in recent_levels if ol["type"] == "V_SUPPORT" and ol["level"] < entry_price]
                                        nearest_obstacle = max(opp_lvls) if opp_lvls else 0.0

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
                                            current_atr=current_atr,
                                            obstacle_level=nearest_obstacle,
                                        )

        # -------------------------------------------------------------
        # MEJORA 4: QUASIMODO (QM) ESTRUCTURAL DE SWING (Left Shoulder Retest)
        # -------------------------------------------------------------
        if self.config.enable_quasimodo_pattern and len(df_h1) >= 6:
            c1 = df_h1.iloc[-5]
            c2 = df_h1.iloc[-4]
            c3 = df_h1.iloc[-3]
            c4 = df_h1.iloc[-2]
            c5 = df_h1.iloc[-1]

            # Bullish QM: Low (c1) -> High (c2) -> Lower Low sweep (c3) -> Higher High break (c4) -> Retest Left Shoulder (c5)
            if (
                c3["low"] < c1["low"]
                and c4["close"] > c2["high"]
                and c5["low"] <= c1["low"] + (0.25 * current_atr)
                and c5["close"] > c1["low"]
            ):
                if is_direction_allowed(symbol, "BUY") and (not self.config.enable_daily_storyline_filter or daily_bullish):
                    sl = float(c3["low"]) - (0.10 * current_atr)
                    risk_dist = abs(entry_price - sl)
                    if risk_dist > 0:
                        return self._build_confirmed_signal(
                            symbol=symbol,
                            direction="BUY",
                            scenario="ESC_3_QUASIMODO",
                            entry_price=entry_price,
                            stop_loss=sl,
                            risk_dist=risk_dist,
                            adx=current_adx,
                            body_ratio=body_ratio,
                            ref_level=float(c1["low"]),
                            break_level=float(c2["high"]),
                            current_atr=current_atr,
                            obstacle_level=float(c2["high"]),
                        )

            # Bearish QM: High (c1) -> Low (c2) -> Higher High sweep (c3) -> Lower Low break (c4) -> Retest Left Shoulder (c5)
            elif (
                c3["high"] > c1["high"]
                and c4["close"] < c2["low"]
                and c5["high"] >= c1["high"] - (0.25 * current_atr)
                and c5["close"] < c1["high"]
            ):
                if is_direction_allowed(symbol, "SELL") and (not self.config.enable_daily_storyline_filter or not daily_bullish):
                    sl = float(c3["high"]) + (0.10 * current_atr)
                    risk_dist = abs(sl - entry_price)
                    if risk_dist > 0:
                        return self._build_confirmed_signal(
                            symbol=symbol,
                            direction="SELL",
                            scenario="ESC_3_QUASIMODO",
                            entry_price=entry_price,
                            stop_loss=sl,
                            risk_dist=risk_dist,
                            adx=current_adx,
                            body_ratio=body_ratio,
                            ref_level=float(c1["high"]),
                            break_level=float(c2["low"]),
                            current_atr=current_atr,
                            obstacle_level=float(c2["low"]),
                        )

        # -------------------------------------------------------------
        # ESCENARIO 3: Fractalidad Clásica (HCH / Quiebre Estructural Rápido)
        # -------------------------------------------------------------
        if self.config.enable_scenario_3_fractal and len(df_h1) >= 4:
            c_prev2 = df_h1.iloc[-3]
            c_prev1 = df_h1.iloc[-2]
            c_curr = df_h1.iloc[-1]

            # Fractal Bullish HCH (Ruptura de Clavicular + Retest M15 de Hombro Derecho)
            if c_prev1["low"] < c_prev2["low"] and c_curr["close"] > c_curr["open"]:
                f_body = c_curr["close"] - c_curr["open"]
                f_span = c_curr["high"] - c_curr["low"]
                neckline = float(c_prev2["high"])
                # Retest M15: verificar que el retroceso haya testeado la zona clavicular
                retest_tested = any(
                    float(row["low"]) <= neckline + (0.35 * current_atr)
                    for _, row in recent_m15.iterrows()
                )
                not_overextended = entry_price <= (neckline + (0.40 * current_atr))
                respects_neckline = entry_price >= (neckline - (0.15 * current_atr))
                if (
                    f_span > 0
                    and (f_body / f_span) >= 0.55
                    and c_curr["close"] > neckline
                    and retest_tested
                    and not_overextended
                    and respects_neckline
                ):
                    if is_direction_allowed(symbol, "BUY") and (not self.config.enable_daily_storyline_filter or daily_bullish):
                        retest_low = float(recent_m15["low"].min())
                        sl = min(retest_low, float(c_curr["low"])) - (0.15 * current_atr)
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
                                ref_level=neckline,
                                break_level=float(c_prev1["close"]),
                                current_atr=current_atr,
                            )

            # Fractal Bearish HCH (Ruptura de Clavicular + Retest M15 de Hombro Derecho)
            elif c_prev1["high"] > c_prev2["high"] and c_curr["close"] < c_curr["open"]:
                f_body = c_curr["open"] - c_curr["close"]
                f_span = c_curr["high"] - c_curr["low"]
                neckline = float(c_prev2["low"])
                # Retest M15: verificar que el retroceso haya testeado la zona clavicular
                retest_tested = any(
                    float(row["high"]) >= neckline - (0.35 * current_atr)
                    for _, row in recent_m15.iterrows()
                )
                not_overextended = entry_price >= (neckline - (0.40 * current_atr))
                respects_neckline = entry_price <= (neckline + (0.15 * current_atr))
                if (
                    f_span > 0
                    and (f_body / f_span) >= 0.55
                    and c_curr["close"] < neckline
                    and retest_tested
                    and not_overextended
                    and respects_neckline
                ):
                    if is_direction_allowed(symbol, "SELL") and (not self.config.enable_daily_storyline_filter or not daily_bullish):
                        retest_high = float(recent_m15["high"].max())
                        sl = max(retest_high, float(c_curr["high"])) + (0.15 * current_atr)
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
                                ref_level=neckline,
                                break_level=float(c_prev1["close"]),
                                current_atr=current_atr,
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
        current_atr: float = 0.0,
        obstacle_level: float = 0.0,
    ) -> dict:
        """Construye el payload completo de señal dual con targets asimétricos y features para IA."""
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
            dist_to_obs = abs(obstacle_level - entry_price) / risk_dist
            if 1.8 < dist_to_obs < runner_rr:
                runner_rr = round(dist_to_obs - 0.2, 1)

        tp2_price = entry_price + (runner_rr * risk_dist) if direction == "BUY" else entry_price - (runner_rr * risk_dist)

        # Score cuantitativo y porcentaje de confirmación
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
            "adx": round(adx, 2),
            "atr": round(current_atr, 5) if current_atr > 0 else round(risk_dist / max(1.0, runner_rr), 5),
            "trade_score": round(trade_score, 2),
            "confirmation_percentage": round(conf_pct, 2),
            "structure_break": f"{scenario}_{direction}",
            "body_ratio": round(body_ratio, 2),
            "ref_level": round(ref_level, 5),
            "break_level": round(break_level, 5),
            "obstacle_level": round(obstacle_level, 5),
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
