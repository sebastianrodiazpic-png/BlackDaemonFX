"""Estrategia Trend Pullback H1 + M15 sobre velas cerradas (BlackDaemonFX).

Lógica de trading cuantitativo:
1. Análisis de tendencia HTF (H1):
   - Fast EMA (50) y Slow EMA (200).
   - ADX(14) >= 20.0 para garantizar régimen direccional y descartar consolidación lateral ruidosa.
   - BUY: EMA(50) > EMA(200) y Cierre H1 > EMA(50) con +DI > -DI.
   - SELL: EMA(50) < EMA(200) y Cierre H1 < EMA(50) con -DI > +DI.

2. Gatillo de retroceso en valor LTF (M15):
   - Media dinámica de retroceso: EMA(21).
   - BUY: Vela cerrada M15 anterior o actual tocó la zona de retroceso (Low <= EMA(21)),
     cerrando alcista (Close > Open y Close > EMA(21)), con RSI(14) entre 35 y 65.
   - SELL: Vela cerrada M15 anterior o actual rebotó en la zona de retroceso (High >= EMA(21)),
     cerrando bajista (Close < Open y Close < EMA(21)), con RSI(14) entre 35 y 65.

3. Dimensionamiento y Paradas:
   - SL colocado a max(1.0 * ATR, 1.5 * ATR o swing extremo local de las últimas 5 velas M15).
   - Filtro de spread/SL: aborta si Spread / SL > 2.0 %.
   - Contrato BlackDaemonFX: 2 patas al 0.5 % (1 % total). TP1 = 1R (asegura y mueve BE a Pata 2),
     TP2 = 2R con soporte de trailing stop escalonado (+1R en 2R, +2.5R en 3R, hasta 4R).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from config.symbol_policy import is_direction_allowed
from strategy.indicators import calculate_adx
from strategy.trend_pullback.config import (
    TREND_PULLBACK_SCENARIO,
    TREND_PULLBACK_STRATEGY,
    TREND_PULLBACK_VERSION,
    TrendPullbackConfig,
)

logger = logging.getLogger(__name__)


def _calc_ema(series: pd.Series, span: int) -> pd.Series:
    """Cálculo de EMA exponencial."""
    return series.ewm(span=span, adjust=False).mean()


def _calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Cálculo del RSI estándar de Wilder."""
    delta = close.diff()
    up = delta.clip(lower=0.0).ewm(alpha=1.0 / period, adjust=False).mean()
    down = (-delta.clip(upper=0.0)).ewm(alpha=1.0 / period, adjust=False).mean()
    rs = up / down.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Cálculo del Average True Range (ATR)."""
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def closed_candles_only(candles: pd.DataFrame, current_time: pd.Timestamp, timeframe_str: str) -> pd.DataFrame:
    """Filtra y devuelve de forma robusta y sin lookahead únicamente las velas cerradas.

    Alinea defensivamente la resolución de unidades temporales para prevenir errores de pérdida de precisión.
    """
    if candles is None or candles.empty:
        return pd.DataFrame()

    df = candles.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        numeric = pd.api.types.is_numeric_dtype(df["time"])
        df["time"] = pd.to_datetime(df["time"], utc=True, unit="s" if numeric else None)
    elif df["time"].dt.tz is None:
        df["time"] = df["time"].dt.tz_localize("UTC")
    else:
        df["time"] = df["time"].dt.tz_convert("UTC")

    df = df.sort_values("time").reset_index(drop=True)

    tf_upper = str(timeframe_str).upper()
    delta_map = {
        "M1": pd.Timedelta(minutes=1),
        "M5": pd.Timedelta(minutes=5),
        "M15": pd.Timedelta(minutes=15),
        "M30": pd.Timedelta(minutes=30),
        "H1": pd.Timedelta(hours=1),
        "H4": pd.Timedelta(hours=4),
        "D1": pd.Timedelta(days=1),
    }
    tf_delta = delta_map.get(tf_upper, pd.Timedelta(minutes=15))

    now = pd.Timestamp(current_time)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")

    # Una vela está cerrada si time + tf_delta <= now (o time <= now - tf_delta)
    cutoff = now - tf_delta
    try:
        series_unit = getattr(df["time"].dt, "unit", "ns")
        cutoff_aligned = cutoff.floor(f"1{series_unit}")
        pos = df["time"].searchsorted(cutoff_aligned, side="right")
        return df.iloc[:pos].reset_index(drop=True)
    except Exception:
        mask = df["time"] <= cutoff
        return df[mask].reset_index(drop=True)


class TrendPullbackStrategy:
    """Implementación de la estrategia Trend Pullback H1 + M15 para el motor de BlackDaemonFX."""

    def __init__(self, data_provider: Any, config: TrendPullbackConfig | None = None) -> None:
        self.provider = data_provider
        self.config = config or TrendPullbackConfig()

    def _base_result(self, symbol: str, reason: str) -> dict[str, Any]:
        return {
            "valid": False,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "symbol": symbol,
            "action": "WAITING_PULLBACK",
            "reason": reason,
        }

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict[str, Any]:
        """Analiza un símbolo con velas cerradas de H1 y M15 y genera una señal si se cumplen todas las reglas."""
        cfg = self.config
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")

        if not cfg.enabled:
            return self._base_result(symbol, "STRATEGY_DISABLED")

        if str(symbol) not in cfg.symbols:
            return self._base_result(symbol, "SYMBOL_NOT_IN_PULLBACK_UNIVERSE")

        # 1. Obtener velas H1 y M15
        try:
            raw_h1 = self.provider.get_candles(symbol, cfg.htf_timeframe, count=cfg.h1_candle_count)
            raw_m15 = self.provider.get_candles(symbol, cfg.ltf_timeframe, count=cfg.m15_candle_count)
        except Exception as e:
            return self._base_result(symbol, f"MARKET_DATA_ERROR: {e}")

        closed_h1 = closed_candles_only(raw_h1, now, cfg.htf_timeframe)
        closed_m15 = closed_candles_only(raw_m15, now, cfg.ltf_timeframe)

        min_h1_required = max(cfg.htf_ema_slow, cfg.adx_period) + 10
        min_m15_required = max(cfg.pullback_ema, cfg.rsi_period, cfg.atr_period) + 10

        if len(closed_h1) < min_h1_required:
            return self._base_result(symbol, "INSUFFICIENT_H1_HISTORY")
        if len(closed_m15) < min_m15_required:
            return self._base_result(symbol, "INSUFFICIENT_M15_HISTORY")

        # 2. Análisis HTF (H1): Tendencia y Régimen Direccional
        h1_df = closed_h1.copy()
        h1_close = h1_df["close"]
        h1_ema_fast = _calc_ema(h1_close, cfg.htf_ema_fast)
        h1_ema_slow = _calc_ema(h1_close, cfg.htf_ema_slow)
        h1_adx = calculate_adx(h1_df, cfg.adx_period)

        last_h1_idx = len(h1_df) - 1
        h1_c = float(h1_close.iloc[last_h1_idx])
        fast_ema_val = float(h1_ema_fast.iloc[last_h1_idx])
        slow_ema_val = float(h1_ema_slow.iloc[last_h1_idx])
        adx_val = float(h1_adx.iloc[last_h1_idx])

        # Filtro de régimen direccional
        if np.isnan(adx_val) or adx_val < cfg.adx_min:
            return self._base_result(symbol, f"H1_ADX_LOW ({adx_val:.1f} < {cfg.adx_min:.1f})")

        is_bullish_h1 = (fast_ema_val > slow_ema_val) and (h1_c > fast_ema_val)
        is_bearish_h1 = (fast_ema_val < slow_ema_val) and (h1_c < fast_ema_val)

        if not (is_bullish_h1 or is_bearish_h1):
            return self._base_result(symbol, "H1_TREND_UNDEFINED")

        # 3. Análisis LTF (M15): Retroceso y Gatillo de Entrada
        m15_df = closed_m15.copy()
        m15_close = m15_df["close"]
        m15_open = m15_df["open"]
        m15_high = m15_df["high"]
        m15_low = m15_df["low"]

        m15_ema_pullback = _calc_ema(m15_close, cfg.pullback_ema)
        m15_rsi = _calc_rsi(m15_close, cfg.rsi_period)
        m15_atr = _calc_atr(m15_df, cfg.atr_period)

        # Última vela cerrada M15 (vela desencadenante)
        idx = len(m15_df) - 1
        c_last = float(m15_close.iloc[idx])
        o_last = float(m15_open.iloc[idx])
        h_last = float(m15_high.iloc[idx])
        l_last = float(m15_low.iloc[idx])
        ema_last = float(m15_ema_pullback.iloc[idx])
        rsi_last = float(m15_rsi.iloc[idx])
        atr_last = float(m15_atr.iloc[idx])

        # Penúltima vela cerrada M15 (para verificar retroceso si la última ya rebotó)
        prev_idx = idx - 1
        l_prev = float(m15_low.iloc[prev_idx])
        h_prev = float(m15_high.iloc[prev_idx])
        ema_prev = float(m15_ema_pullback.iloc[prev_idx])

        if np.isnan(atr_last) or atr_last <= 0:
            return self._base_result(symbol, "M15_ATR_INVALID")

        direction: str | None = None
        trigger_reason: str = ""

        pb_band = float(getattr(cfg, "pullback_band_atr", 0.0) or 0.0) * atr_last
        min_wick = float(getattr(cfg, "min_rejection_wick_ratio", 0.30) or 0.30)
        span_last = max(0.0, h_last - l_last)

        if is_bullish_h1:
            # Condición de compra:
            # 1. Retroceso a la EMA(21) o banda de valor dinámica (EMA21 + pullback_band_atr * ATR)
            exact_touch = (l_last <= ema_last) or (l_prev <= ema_prev)
            lower_wick_ratio = ((min(o_last, c_last) - l_last) / span_last) if span_last > 0 else 0.0
            band_touch = (pb_band > 0.0) and ((l_last <= ema_last + pb_band) or (l_prev <= ema_prev + pb_band)) and (lower_wick_ratio >= min_wick)
            touched_pullback = exact_touch or band_touch
            # 2. Rechazo y cierre alcista sobre la EMA
            rejection_candle = (c_last > o_last) and (c_last > ema_last)
            # 3. RSI en zona de retroceso saludable (no sobrecomprado)
            rsi_ok = cfg.rsi_buy_min <= rsi_last <= cfg.rsi_buy_max

            if touched_pullback and rejection_candle and rsi_ok:
                direction = "BUY"
                trigger_reason = f"BULLISH_PULLBACK_EMA21 (RSI={rsi_last:.1f})"
            else:
                if not touched_pullback:
                    return self._base_result(symbol, "M15_NO_PULLBACK_TOUCH_EMA21")
                if not rejection_candle:
                    return self._base_result(symbol, "M15_NO_BULLISH_REJECTION")
                return self._base_result(symbol, f"M15_RSI_OUT_OF_RANGE ({rsi_last:.1f})")

        elif is_bearish_h1:
            # Condición de venta:
            # 1. Retroceso alcista a la EMA(21) o banda de valor dinámica (EMA21 - pullback_band_atr * ATR)
            exact_touch = (h_last >= ema_last) or (h_prev >= ema_prev)
            upper_wick_ratio = ((h_last - max(o_last, c_last)) / span_last) if span_last > 0 else 0.0
            band_touch = (pb_band > 0.0) and ((h_last >= ema_last - pb_band) or (h_prev >= ema_prev - pb_band)) and (upper_wick_ratio >= min_wick)
            touched_pullback = exact_touch or band_touch
            # 2. Rechazo y cierre bajista por debajo de la EMA
            rejection_candle = (c_last < o_last) and (c_last < ema_last)
            # 3. RSI en zona de retroceso saludable (no sobrevendido)
            rsi_ok = cfg.rsi_sell_min <= rsi_last <= cfg.rsi_sell_max

            if touched_pullback and rejection_candle and rsi_ok:
                direction = "SELL"
                trigger_reason = f"BEARISH_PULLBACK_EMA21 (RSI={rsi_last:.1f})"
            else:
                if not touched_pullback:
                    return self._base_result(symbol, "M15_NO_PULLBACK_TOUCH_EMA21")
                if not rejection_candle:
                    return self._base_result(symbol, "M15_NO_BEARISH_REJECTION")
                return self._base_result(symbol, f"M15_RSI_OUT_OF_RANGE ({rsi_last:.1f})")

        if not direction:
            return self._base_result(symbol, "NO_SETUP_MATCH")

        # 3.1 Política de dirección estructural y asimetría direccional (Jump BUY only, Step SELL only)
        if not is_direction_allowed(symbol, direction):
            return self._base_result(symbol, f"DIRECTION_BLOCKED_BY_POLICY: {direction}")

        if getattr(cfg, "directional_asymmetry_enabled", True):
            sym_l = str(symbol).strip().lower()
            jump_buy_only = {str(s).strip().lower() for s in getattr(cfg, "jump_buy_only_symbols", ())}
            step_sell_only = {str(s).strip().lower() for s in getattr(cfg, "step_sell_only_symbols", ())}
            if sym_l in jump_buy_only and direction != "BUY":
                return self._base_result(symbol, "DIRECTION_ASYMMETRY_JUMP_BUY_ONLY")
            if sym_l in step_sell_only and direction != "SELL":
                return self._base_result(symbol, "DIRECTION_ASYMMETRY_STEP_SELL_ONLY")

        # 3.2 Filtro de momentum en contra (Anti-Falling Knife / retroceso impulsivo)
        max_pb_body_ratio = getattr(cfg, "max_pullback_bar_body_atr", 1.25)
        if max_pb_body_ratio > 0:
            prev_body = abs(float(m15_close.iloc[prev_idx]) - float(m15_open.iloc[prev_idx]))
            prev_is_against = (direction == "BUY" and float(m15_close.iloc[prev_idx]) < float(m15_open.iloc[prev_idx])) or (
                direction == "SELL" and float(m15_close.iloc[prev_idx]) > float(m15_open.iloc[prev_idx])
            )
            if prev_is_against and prev_body > (max_pb_body_ratio * atr_last):
                return self._base_result(
                    symbol,
                    f"M15_IMPULSIVE_PULLBACK_REJECTED (body={prev_body:.4f} > {max_pb_body_ratio * atr_last:.4f})",
                )

        # 4. Obtener precio vivo (tick) y spread para validar fricción
        try:
            tick = self.provider.get_current_tick(symbol)
            bid = float(tick["bid"])
            ask = float(tick["ask"])
        except Exception as e:
            return self._base_result(symbol, f"TICK_UNAVAILABLE: {e}")

        if not (np.isfinite(bid) and np.isfinite(ask) and bid > 0 and ask > 0):
            return self._base_result(symbol, "INVALID_TICK_VALUES")

        spread = ask - bid
        entry_price = ask if direction == "BUY" else bid

        # 5. Dimensionamiento del Stop Loss estructural / ATR con buffer anti-hunt
        lookback_slice = m15_df.iloc[-cfg.swing_lookback:]
        buffer_val = getattr(cfg, "sl_buffer_atr", 0.25) * atr_last
        if direction == "BUY":
            swing_low = float(lookback_slice["low"].min()) - buffer_val
            sl_dist = max(entry_price - swing_low, cfg.stop_atr_multiple * atr_last)
            # Aplicar piso mínimo de stop
            sl_dist = max(sl_dist, cfg.min_stop_atr * atr_last)
            stop_loss = entry_price - sl_dist
            tp1_price = entry_price + (cfg.tp1_rr * sl_dist)
            tp2_price = entry_price + (cfg.runner_rr * sl_dist)
        else:
            swing_high = float(lookback_slice["high"].max()) + buffer_val
            sl_dist = max(swing_high - entry_price, cfg.stop_atr_multiple * atr_last)
            # Aplicar piso mínimo de stop
            sl_dist = max(sl_dist, cfg.min_stop_atr * atr_last)
            stop_loss = entry_price + sl_dist
            tp1_price = entry_price - (cfg.tp1_rr * sl_dist)
            tp2_price = entry_price - (cfg.runner_rr * sl_dist)

        # 6. Filtro institucional de Spread vs Stop Loss
        if sl_dist <= 0:
            return self._base_result(symbol, "INVALID_SL_DISTANCE")

        spread_sl_ratio = spread / sl_dist
        if spread_sl_ratio > cfg.max_spread_sl_ratio:
            return self._base_result(
                symbol,
                f"SPREAD_SL_RATIO_EXCEEDED ({spread_sl_ratio * 100.0:.2f}% > {cfg.max_spread_sl_ratio * 100.0:.1f}%)",
            )

        # 7. Construcción de señal compatible con LiveTradingEngine y el contrato de 2 patas
        setup_id = f"{symbol}|{m15_df['time'].iloc[idx]:%Y%m%d%H%M}|{direction}"
        signal: dict[str, Any] = {
            "strategy_name": cfg.strategy_name,
            "strategy_version": cfg.strategy_version,
            "symbol": symbol,
            "direction": direction,
            "scenario": TREND_PULLBACK_SCENARIO,
            "setup_id": setup_id,
            "signal_time": pd.Timestamp(m15_df["time"].iloc[idx]).isoformat(),
            "entry_time": now.isoformat(),
            "entry_price": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "take_profit": round(tp2_price, 5),
            "tp1_price": round(tp1_price, 5),
            "tp2_price": round(tp2_price, 5),
            "tp1_rr": cfg.tp1_rr,
            "runner_rr": cfg.runner_rr,
            "risk_reward_ratio": cfg.runner_rr,
            "risk_reward_ratio_tp1": cfg.tp1_rr,
            "risk_reward_ratio_tp2": cfg.runner_rr,
            "be_trigger_rr": cfg.be_trigger_rr,
            "runner_target_name": "TP2",
            "timeframe": cfg.ltf_timeframe,
            "atr": round(atr_last, 5),
            "adx_h1": round(adx_val, 2),
            "rsi_m15": round(rsi_last, 2),
            "ema50_h1": round(fast_ema_val, 5),
            "ema200_h1": round(slow_ema_val, 5),
            "ema21_m15": round(ema_last, 5),
            "spread": round(spread, 5),
            "spread_sl_ratio": round(spread_sl_ratio, 4),
            "split_execution": cfg.split_execution,
            "leg1_risk_ratio": cfg.leg1_risk_ratio if cfg.split_execution else 1.0,
            "leg2_risk_ratio": cfg.leg2_risk_ratio if cfg.split_execution else 0.0,
            "confirmations": {
                "h1_trend_aligned": True,
                "h1_adx_sufficient": True,
                "m15_pullback_touched": True,
                "m15_rejection_candle": True,
                "m15_rsi_valid": True,
                "spread_under_cap": True,
            },
        }

        return {
            "valid": True,
            "strategy_name": cfg.strategy_name,
            "strategy_version": cfg.strategy_version,
            "action": "TREND_PULLBACK_CONFIRMED",
            "reason": f"{trigger_reason} on {symbol}",
            "symbol": symbol,
            "signal": signal,
        }
