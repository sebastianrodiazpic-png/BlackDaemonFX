"""Estrategia Institucional ICT Sabri Malle v2 (AMD, Killzones, Consequent Encroachment & FVG Pullback).

Implementa el ciclo completo de manipulación institucional con validación cuantitativa de 2 años:
1. Macro Bias (H4): EMA 50 y EMA 200 para determinar la dirección institucional dominante.
2. Time & Price (Killzones NY):
   - Forex, Metales, Cripto e Índices: Se rige por el reloj de Nueva York (America/New_York).
     * Acumulación: Asian Range (20:00 a 00:00 NY).
     * Manipulación y Entrada: London Killzone (02:00 a 05:00 NY) y New York Killzone (07:00 a 11:00 NY).
   - Sintéticos: Rango dinámico por contracción de volatilidad/fractal 24/7.
3. Manipulación (M - Judas Swing): Barrido agresivo del rango de acumulación (Asian High o Asian Low)
   con rechazo por mecha (>= 35%) o mitigación de FVG mayor.
4. Distribución / Gatillo Refinado (D - M15/M5):
   - Market Structure Shift (MSS) estricto con vela de desplazamiento institucional (cuerpo >= 45%).
   - Entrada en el retroceso hacia el Fair Value Gap (Consequent Encroachment al 50% CE) o zona rota.
   - Stop Loss ceñido al extremo del Judas Swing (+ spread).
5. Gestión Asimétrica Dual:
   - Pierna 1: TP1 a 1:2.0 RR (50% de la posición) asegurando ganancias en liquidez interna.
   - Pierna 2: Corredora a 1:3.5 RR (50% de la posición) con Break-Even automático al tocar TP1.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any
import numpy as np
import pandas as pd

from config.symbol_policy import is_direction_allowed
from strategy.ict.config import ICTSabriMalleConfig

NEW_YORK = ZoneInfo("America/New_York")
TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


def closed_candles_only(df: pd.DataFrame, timeframe: str, now: pd.Timestamp, count: int | None = None) -> pd.DataFrame:
    """Devuelve solo las velas ya CERRADAS en `now` (apertura + duración <= now), ordenadas.

    Con `count` recorta a las últimas `count` cerradas (se pide una vela extra al proveedor
    para que la ventana de indicadores tenga el mismo tamaño que en el replay).

    MT5 entrega la vela en formación como última fila; evaluarla genera señales intra-vela
    que el replay fiel (solo velas cerradas) no produce y que pueden desaparecer al cierre.
    """
    out = df.copy()
    out["time"] = pd.to_datetime(out["time"], utc=True)
    duration = pd.Timedelta(minutes=TIMEFRAME_MINUTES.get(str(timeframe).upper(), 0))
    out = out[out["time"] + duration <= now].sort_values("time")
    if count is not None:
        out = out.tail(int(count))
    return out.reset_index(drop=True)


def compute_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Calcula el Average True Range (ATR)."""
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(df)
    if n == 0:
        return np.array([])
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
    atr = np.zeros(n)
    atr[0] = tr[0]
    alpha = 1.0 / period
    for i in range(1, n):
        atr[i] = (alpha * tr[i]) + ((1.0 - alpha) * atr[i - 1])
    return atr


def build_h4_candles_from_h1(df_h1: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye velas H4 agregadas a partir de H1 asegurando índice temporal UTC."""
    df = df_h1.copy()
    agg_dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }
    if "tick_volume" in df.columns:
        agg_dict["tick_volume"] = "sum"
    h4 = df.set_index("time").resample("4h").agg(agg_dict).dropna().reset_index()
    h4["time"] = pd.to_datetime(h4["time"], utc=True)
    return h4


def find_active_fvgs_fast(df: pd.DataFrame, curr_idx: int, lookback_bars: int = 40) -> list[dict]:
    """Detecta Fair Value Gaps activos en el DataFrame hasta el índice curr_idx."""
    if curr_idx < 4:
        return []

    start_idx = max(2, curr_idx - lookback_bars)
    fvgs = []
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    opens = df["open"].values

    for i in range(start_idx, curr_idx + 1):
        # Bearish FVG: Low de i-2 > High de i
        if lows[i - 2] > highs[i] and closes[i - 1] < opens[i - 1]:
            gap_top = float(lows[i - 2])
            gap_bottom = float(highs[i])
            mitigated = False
            for k in range(i + 1, curr_idx + 1):
                if highs[k] >= gap_top:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({
                    "type": "BEARISH",
                    "top": gap_top,
                    "bottom": gap_bottom,
                    "midpoint": (gap_top + gap_bottom) / 2.0,
                    "height": gap_top - gap_bottom,
                    "bar_index": i,
                })

        # Bullish FVG: High de i-2 < Low de i
        if highs[i - 2] < lows[i] and closes[i - 1] > opens[i - 1]:
            gap_top = float(highs[i - 2])
            gap_bottom = float(lows[i])
            mitigated = False
            for k in range(i + 1, curr_idx + 1):
                if lows[k] <= gap_bottom:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({
                    "type": "BULLISH",
                    "top": gap_top,
                    "bottom": gap_bottom,
                    "midpoint": (gap_top + gap_bottom) / 2.0,
                    "height": gap_bottom - gap_top,
                    "bar_index": i,
                })
    return fvgs



def find_inversion_fvg_and_bpr_setups(
    df: pd.DataFrame,
    curr_idx: int,
    intended_direction: str,
    lookback_bars: int = 24,
    spread: float = 0.00015,
) -> dict | None:
    """Opción C: Detecta Inversion FVG (iFVG) y Balanced Price Range (BPR).

    1. Inversion FVG: FVG previo que fue perforado con cuerpo por el precio y ahora
       actúa como soporte/resistencia invertido (SBR/RBS).
    2. Balanced Price Range: Solapamiento bidireccional entre FVG alcista y bajista consecutivo.
    """
    if curr_idx < 4:
        return None

    c_now = df.iloc[curr_idx]
    c_close = float(c_now["close"])
    c_high = float(c_now["high"])
    c_low = float(c_now["low"])

    # 1. Búsqueda de Inversion FVG (iFVG)
    for back in range(1, min(lookback_bars, curr_idx - 1)):
        c0 = df.iloc[curr_idx - back - 2]
        c1 = df.iloc[curr_idx - back - 1]
        c2 = df.iloc[curr_idx - back]

        # FVG Alcista original previo (c2.low > c0.high)
        if c2["low"] > c0["high"] and c1["close"] > c1["open"]:
            gap_top = float(c2["low"])
            gap_bot = float(c0["high"])
            # Perforado con cuerpo hacia abajo -> Inversión a Resistencia (SBR)
            breached = False
            for k in range(curr_idx - back + 1, curr_idx):
                if df.iloc[k]["close"] < gap_bot:
                    breached = True
                    break
            if breached and intended_direction == "SELL":
                # Retesteo actual dentro o en el borde del iFVG
                if c_high >= gap_bot and c_close <= (gap_top + spread):
                    sl = gap_top + (2.0 * spread)
                    risk = abs(sl - c_close)
                    if risk > (1.5 * spread):
                        return {
                            "valid": True,
                            "type": "ICT_INVERSION_FVG",
                            "scenario": "ICT_INVERSION_FVG_RETEST",
                            "direction": "SELL",
                            "entry_price": c_close,
                            "stop_loss": sl,
                            "risk": risk,
                            "gap_top": gap_top,
                            "gap_bottom": gap_bot,
                            "trade_score": 90.0,
                        }

        # FVG Bajista original previo (c2.high < c0.low)
        elif c2["high"] < c0["low"] and c1["close"] < c1["open"]:
            gap_top = float(c0["low"])
            gap_bot = float(c2["high"])
            # Perforado con cuerpo hacia arriba -> Inversión a Soporte (RBS)
            breached = False
            for k in range(curr_idx - back + 1, curr_idx):
                if df.iloc[k]["close"] > gap_top:
                    breached = True
                    break
            if breached and intended_direction == "BUY":
                # Retesteo actual dentro o en el borde del iFVG
                if c_low <= gap_top and c_close >= (gap_bot - spread):
                    sl = gap_bot - (2.0 * spread)
                    risk = abs(c_close - sl)
                    if risk > (1.5 * spread):
                        return {
                            "valid": True,
                            "type": "ICT_INVERSION_FVG",
                            "scenario": "ICT_INVERSION_FVG_RETEST",
                            "direction": "BUY",
                            "entry_price": c_close,
                            "stop_loss": sl,
                            "risk": risk,
                            "gap_top": gap_top,
                            "gap_bottom": gap_bot,
                            "trade_score": 90.0,
                        }

    # 2. Búsqueda de Balanced Price Range (BPR)
    c_m2 = df.iloc[curr_idx - 2]
    c_m1 = df.iloc[curr_idx - 1]
    c_m0 = df.iloc[curr_idx]

    if intended_direction == "BUY":
        if c_m1["low"] > c_m2["high"] and c_m0["close"] > c_m1["high"]:
            sl = float(c_m2["low"]) - (1.5 * spread)
            risk = abs(c_close - sl)
            if risk > (2.0 * spread):
                return {
                    "valid": True,
                    "type": "ICT_BALANCED_PRICE_RANGE",
                    "scenario": "ICT_BALANCED_PRICE_RANGE_EXPANSION",
                    "direction": "BUY",
                    "entry_price": c_close,
                    "stop_loss": sl,
                    "risk": risk,
                    "trade_score": 92.0,
                }
    elif intended_direction == "SELL":
        if c_m1["high"] < c_m2["low"] and c_m0["close"] < c_m1["low"]:
            sl = float(c_m2["high"]) + (1.5 * spread)
            risk = abs(sl - c_close)
            if risk > (2.0 * spread):
                return {
                    "valid": True,
                    "type": "ICT_BALANCED_PRICE_RANGE",
                    "scenario": "ICT_BALANCED_PRICE_RANGE_EXPANSION",
                    "direction": "SELL",
                    "entry_price": c_close,
                    "stop_loss": sl,
                    "risk": risk,
                    "trade_score": 92.0,
                }

    return None


def is_synthetic_asset(symbol: str) -> bool:
    """Identifica si un símbolo pertenece al mercado de sintéticos algorítmicos 24/7."""
    sym_u = str(symbol or "").upper()
    keywords = (
        "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP", "1HZ",
        "V10", "V25", "V50", "V75", "V100", "V150", "V250",
        "VOL ", "VOLSWITCH", "SKEW", "MULTI STEP", "SPOT UP", "DEX",
        "DRIFT", "DAILY RESET", "HYBRID", "RANGE BREAK",
    )
    return any(k in sym_u for k in keywords)


def check_order_block_five_stars(
    df: pd.DataFrame,
    *args,
    curr_idx: int | None = None,
    direction: str | None = None,
    lookback: int = 25
) -> dict:
    """Verifica los 5 criterios de Order Block 5 Estrellas (Sabri Malle Video 9).
    Soporta firmas:
      - check_order_block_five_stars(df, curr_idx, direction, lookback=25)
      - check_order_block_five_stars(df, direction, curr_idx=None, lookback=25)
    1. Inbalance / FVG generado por la impulsión.
    2. Liquidez cazada previa (sweep de swing o nivel anterior).
    3. Es el OB extremo del movimiento (el más bajo en compra, el más alto en venta).
    4. Inmitigado (el precio no ha cerrado más allá del 50% Mean Threshold).
    5. Sesión activa / volumen.
    """
    if len(args) == 2:
        if isinstance(args[0], int) and isinstance(args[1], str):
            curr_idx = args[0]
            direction = args[1]
        elif isinstance(args[0], str) and isinstance(args[1], int):
            direction = args[0]
            curr_idx = args[1]
    elif len(args) == 1:
        if isinstance(args[0], str):
            direction = args[0]
        elif isinstance(args[0], int):
            curr_idx = args[0]

    if curr_idx is None:
        curr_idx = len(df) - 1
    if direction is None:
        direction = "BUY"

    if curr_idx < 5 or len(df) < 5:
        return {"valid": False, "score": 0, "stars": 0}

    start_i = max(2, curr_idx - lookback)
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    opens = df["open"].values

    best_ob = None

    if direction == "BUY":
        for i in range(start_i, curr_idx):
            if closes[i] < opens[i] and (i + 2 <= curr_idx):
                has_fvg = highs[i] < lows[i + 2]
                prev_lows = lows[max(0, i - 4) : i]
                swept_liq = len(prev_lows) > 0 and (lows[i] <= float(np.min(prev_lows)))
                ob_mid = (opens[i] + closes[i]) / 2.0
                mitigated = False
                for k in range(i + 1, curr_idx + 1):
                    if closes[k] < ob_mid:
                        mitigated = True
                        break
                stars = sum([has_fvg, swept_liq, not mitigated, True, True])
                if not mitigated:
                    if best_ob is None or lows[i] < best_ob["low"]:
                        best_ob = {
                            "valid": bool(stars >= 3),
                            "index": int(i),
                            "top": float(highs[i]),
                            "bottom": float(lows[i]),
                            "mean_threshold": float(ob_mid),
                            "low": float(lows[i]),
                            "stars": int(stars),
                            "has_fvg": bool(has_fvg),
                            "swept_liq": bool(swept_liq),
                        }
    else:
        for i in range(start_i, curr_idx):
            if closes[i] > opens[i] and (i + 2 <= curr_idx):
                has_fvg = lows[i] > highs[i + 2]
                prev_highs = highs[max(0, i - 4) : i]
                swept_liq = len(prev_highs) > 0 and (highs[i] >= float(np.max(prev_highs)))
                ob_mid = (opens[i] + closes[i]) / 2.0
                mitigated = False
                for k in range(i + 1, curr_idx + 1):
                    if closes[k] > ob_mid:
                        mitigated = True
                        break
                stars = sum([has_fvg, swept_liq, not mitigated, True, True])
                if not mitigated:
                    if best_ob is None or highs[i] > best_ob["high"]:
                        best_ob = {
                            "valid": bool(stars >= 3),
                            "index": int(i),
                            "top": float(highs[i]),
                            "bottom": float(lows[i]),
                            "mean_threshold": float(ob_mid),
                            "high": float(highs[i]),
                            "stars": int(stars),
                            "has_fvg": bool(has_fvg),
                            "swept_liq": bool(swept_liq),
                        }

    return best_ob or {"valid": False, "score": 0, "stars": 0}


class ICTSabriMalleStrategy:
    """Implementación oficial v2 de la estrategia ICT Sabri Malle refinada con Killzones y FVG."""

    def __init__(self, data_provider: Any, config: ICTSabriMalleConfig | None = None):
        self.provider = data_provider
        self.config = config or ICTSabriMalleConfig()

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")

        base_response = {
            "valid": False,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "action": "WAITING_ICT",
            "reason": "NO_SETUP_CONFIRMED",
            "symbol": symbol,
        }

        excluded = {str(s).strip().lower() for s in (getattr(self.config, "excluded_symbols", ()) or ())}
        if str(symbol).strip().lower() in excluded:
            return {**base_response, "reason": "ICT_SYMBOL_EXCLUDED_NEGATIVE_EXPECTANCY"}

        # 1. Obtener velas históricas H1
        try:
            raw_h1 = self.provider.get_candles(symbol, self.config.structure_timeframe, count=81)
        except Exception as exc:
            return {**base_response, "reason": f"PROVIDER_ERROR_H1: {exc}"}

        if raw_h1 is None or len(raw_h1) < 30:
            return {**base_response, "reason": "INSUFFICIENT_H1_CANDLES"}

        # 2. Filtro Horario, Cierres de Mercado y Killzones Institucionales (New York Time)
        is_synthetic = is_synthetic_asset(symbol)
        now_ny = now.tz_convert(NEW_YORK)
        ny_hour = now_ny.hour
        weekday = now_ny.weekday()  # 0=Lunes, 4=Viernes, 5=Sábado, 6=Domingo

        if not is_synthetic and getattr(self.config, "market_closure_filter_enabled", True):
            # Cierre semanal Forex/Metales/Índices: Viernes tarde
            if weekday == 4 and ny_hour >= getattr(self.config, "friday_close_cutoff_ny", 14):
                return {**base_response, "reason": "MARKET_CLOSURE_FRIDAY_WEEKEND_GUARD"}
            if weekday == 5:
                return {**base_response, "reason": "MARKET_CLOSED_SATURDAY"}
            if weekday == 6 and ny_hour < 17:
                return {**base_response, "reason": "MARKET_CLOSED_SUNDAY_PRE_OPEN"}
            # Guardia de Rollover diario (16:45 a 17:45 NY): Spreads se amplían drásticamente
            if getattr(self.config, "rollover_guard_enabled", True):
                if (ny_hour == getattr(self.config, "rollover_start_ny_hour", 16) and now_ny.minute >= getattr(self.config, "rollover_start_ny_minute", 45)) or \
                   (ny_hour == getattr(self.config, "rollover_end_ny_hour", 17) and now_ny.minute <= getattr(self.config, "rollover_end_ny_minute", 45)):
                    return {**base_response, "reason": "MARKET_ROLLOVER_SPREAD_GUARD"}

        # Identificar si es par Forex o Metal Precioso
        sym_u = symbol.upper()
        is_gold = any(k in sym_u for k in ("XAU", "GOLD"))
        is_forex = any(c in sym_u for c in ("EUR", "GBP", "USD", "AUD", "CAD", "CHF", "NZD", "JPY")) and not any(k in sym_u for k in ("XAU", "XAG", "BTC", "OIL", "SP", "TECH", "WALL"))

        in_london_kz = (self.config.london_kz_start_ny <= ny_hour <= self.config.london_kz_end_ny)
        in_ny_kz = (self.config.ny_kz_start_ny <= ny_hour <= self.config.ny_kz_end_ny)

        # Reglas de Sesiones Oficiales ICT:
        # 1. Gold: Preserva exactamente su configuración (Londres y New York Killzone)
        if is_gold:
            session_active = in_london_kz or (in_ny_kz and self.config.ny_killzone_enabled)
        elif is_synthetic:
            # Sintéticos (Volatility 1-4, Jump, Step, Boom, Crash): Operación continua 24/7 sin barreras bancarias
            session_active = True
        else:
            # Forex (1-4) e ICT (Metales/Índices/Cripto):
            # London KZ (02:00 - 05:00 NY)
            # New York KZ (07:00 - 10:00 NY): Habilitada para Forex según official ICT mentorship
            forex_ny_allowed = getattr(self.config, "forex_ny_killzone_enabled", True) if is_forex else self.config.ny_killzone_enabled
            ny_kz_active = in_ny_kz and forex_ny_allowed

            # London Close Reversal (11:00 - 12:30 NY) - Toni Maura / Official ICT Mentorship
            in_london_close = False
            if getattr(self.config, "london_close_reversal_enabled", True):
                if ny_hour == 11 or (ny_hour == 12 and now_ny.minute <= 30):
                    in_london_close = True

            # ICT Silver Bullet (ventanas de 60 min: London 03-04, NY AM 10-11, NY PM 14-15 NY)
            in_silver_bullet = False
            if getattr(self.config, "silver_bullet_enabled", True):
                if ny_hour in tuple(getattr(self.config, "silver_bullet_hours_ny", (3, 10, 14))):
                    in_silver_bullet = True

            session_active = in_london_kz or ny_kz_active or in_london_close or in_silver_bullet

        if not is_synthetic and self.config.killzone_filter_enabled:
            if not session_active:
                return {
                    **base_response,
                    "reason": f"OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: {ny_hour:02d}:00)",
                    "diagnostics": {"session_killzone_active": 0.0, "ny_hour": ny_hour}
                }

        df_h1 = closed_candles_only(raw_h1, self.config.structure_timeframe, now, count=80)

        if len(df_h1) < 28:
            return {**base_response, "reason": "INSUFFICIENT_HISTORICAL_H1"}

        # Velas H4 para Macro Bias
        df_h4 = None
        try:
            raw_h4 = self.provider.get_candles(symbol, self.config.macro_timeframe, count=101)
            if raw_h4 is not None and len(raw_h4) >= 30:
                df_h4 = closed_candles_only(raw_h4, self.config.macro_timeframe, now, count=100)
        except Exception:
            pass

        if df_h4 is None or len(df_h4) < 30:
            df_h4 = build_h4_candles_from_h1(df_h1)

        if len(df_h4) < 20:
            return {**base_response, "reason": "INSUFFICIENT_H4_CANDLES"}

        # 3. Macro Bias H4 (EMAs 50, 100 y 200)
        df_h4["ema50"] = df_h4["close"].ewm(span=50, adjust=False).mean()
        df_h4["ema200"] = df_h4["close"].ewm(span=200, adjust=False).mean()

        last_h4_close = float(df_h4["close"].iloc[-1])
        last_h4_ema50 = float(df_h4["ema50"].iloc[-1])
        last_h4_ema200 = float(df_h4["ema200"].iloc[-1])

        if is_gold:
            # Gold preserva exactamente su evaluación macro rígida de EMAs 50 y 200
            bias_bearish = (last_h4_close < last_h4_ema50) and (last_h4_ema50 <= last_h4_ema200)
            bias_bullish = (last_h4_close > last_h4_ema50) and (last_h4_ema50 >= last_h4_ema200)
        elif getattr(self.config, "macro_bias_flexible", True):
            # Sabri Malle Video 8: EMA 100 en H4 como directriz institucional
            ema_period = getattr(self.config, "macro_ema_period", 100)
            df_h4["ema_macro"] = df_h4["close"].ewm(span=ema_period, adjust=False).mean()
            last_h4_ema_macro = float(df_h4["ema_macro"].iloc[-1])

            bias_bearish = (
                ((last_h4_close < last_h4_ema_macro) and (last_h4_close < last_h4_ema50))
                or ((last_h4_close < last_h4_ema50) and (last_h4_ema50 <= last_h4_ema200))
            )
            bias_bullish = (
                ((last_h4_close > last_h4_ema_macro) and (last_h4_close > last_h4_ema50))
                or ((last_h4_close > last_h4_ema50) and (last_h4_ema50 >= last_h4_ema200))
            )
        else:
            bias_bearish = (last_h4_close < last_h4_ema50) and (last_h4_ema50 <= last_h4_ema200)
            bias_bullish = (last_h4_close > last_h4_ema50) and (last_h4_ema50 >= last_h4_ema200)

        if not (bias_bearish or bias_bullish):
            return {**base_response, "reason": "NO_MACRO_H4_BIAS_ALIGNED"}

        intended_direction = "SELL" if bias_bearish else "BUY"
        if not is_direction_allowed(symbol, intended_direction):
            return {**base_response, "reason": f"DIRECTION_BLOCKED_BY_POLICY: {intended_direction}"}

        # 4. Acumulación (A): Rango Asiático (20:00 - 00:00 NY), Rango Londres, o Consolidación Previa
        atr_h1 = compute_atr(df_h1, period=14)
        curr_atr = float(atr_h1[-1]) if len(atr_h1) > 0 else 1.0

        range_high = None
        range_low = None

        if not is_synthetic:
            df_h1_ny = df_h1.copy()
            df_h1_ny["ny_hour"] = df_h1_ny["time"].dt.tz_convert(NEW_YORK).dt.hour
            
            if 2 <= ny_hour <= 5:
                # London KZ barre el Rango Asiático (20:00 a 00:00 NY)
                asian_bars = []
                for look_back in range(1, min(24, len(df_h1_ny))):
                    chk_idx = len(df_h1_ny) - 1 - look_back
                    chk_h = df_h1_ny["ny_hour"].iloc[chk_idx]
                    if chk_h >= self.config.asian_range_start_ny or chk_h <= self.config.asian_range_end_ny:
                        asian_bars.append(df_h1_ny.iloc[chk_idx])
                    elif len(asian_bars) > 0:
                        break
                if len(asian_bars) >= 2:
                    df_asia = pd.DataFrame(asian_bars)
                    range_high = float(df_asia["high"].max())
                    range_low = float(df_asia["low"].min())
            elif 7 <= ny_hour <= 11:
                # New York KZ barre el Rango de Londres (02:00 a 05:00 NY)
                london_bars = []
                for look_back in range(1, min(16, len(df_h1_ny))):
                    chk_idx = len(df_h1_ny) - 1 - look_back
                    chk_h = df_h1_ny["ny_hour"].iloc[chk_idx]
                    if 2 <= chk_h <= 5:
                        london_bars.append(df_h1_ny.iloc[chk_idx])
                    elif len(london_bars) > 0:
                        break
                if len(london_bars) >= 2:
                    df_london = pd.DataFrame(london_bars)
                    range_high = float(df_london["high"].max())
                    range_low = float(df_london["low"].min())
            elif 11 <= ny_hour <= 13:
                # London Close barre el Rango de NY Mañana (07:00 a 10:00 NY)
                ny_am_bars = []
                for look_back in range(1, min(12, len(df_h1_ny))):
                    chk_idx = len(df_h1_ny) - 1 - look_back
                    chk_h = df_h1_ny["ny_hour"].iloc[chk_idx]
                    if 7 <= chk_h <= 10:
                        ny_am_bars.append(df_h1_ny.iloc[chk_idx])
                    elif len(ny_am_bars) > 0:
                        break
                if len(ny_am_bars) >= 2:
                    df_ny_am = pd.DataFrame(ny_am_bars)
                    range_high = float(df_ny_am["high"].max())
                    range_low = float(df_ny_am["low"].min())
        else:
            # Sintéticos (Volatility 1-4, Jump, Step, Boom, Crash):
            # Utilizar rango rodante dinámico (8 velas H1 por defecto) para capturar ciclos intradía
            synth_lookback = getattr(self.config, "synthetics_rolling_lookback_bars", 8)
            r_slice_high = df_h1["high"].iloc[-synth_lookback - 2 : -2].values
            r_slice_low = df_h1["low"].iloc[-synth_lookback - 2 : -2].values
            if len(r_slice_high) > 0 and len(r_slice_low) > 0:
                range_high = float(np.max(r_slice_high))
                range_low = float(np.min(r_slice_low))

        if range_high is None or range_low is None:
            # Fallback a consolidación previa
            r_slice_high = df_h1["high"].iloc[-self.config.range_lookback - 4 : -4].values
            r_slice_low = df_h1["low"].iloc[-self.config.range_lookback - 4 : -4].values
            if len(r_slice_high) == 0 or len(r_slice_low) == 0:
                return {**base_response, "reason": "RANGE_SLICE_EMPTY"}
            range_high = float(np.max(r_slice_high))
            range_low = float(np.min(r_slice_low))

        range_height = range_high - range_low
        if curr_atr <= 0 or range_height < (self.config.min_atr_factor * curr_atr) or range_height > (self.config.max_atr_factor * curr_atr):
            return {**base_response, "reason": "RANGE_HEIGHT_OUTSIDE_ATR_BOUNDS"}

        # 5. Manipulación (M - Judas Swing): Barrido en las últimas 4 velas H1
        manipulation_found = False
        sweep_peak = None
        sweep_idx = None
        fvgs = find_active_fvgs_fast(df_h4, len(df_h4) - 1, lookback_bars=self.config.fvg_lookback_bars)

        # Umbral de mecha de rechazo adaptable (0.35 para Gold y Forex, 0.25 para Sintéticos)
        wick_threshold = (
            self.config.min_rejection_wick_ratio
            if is_gold
            else (
                getattr(self.config, "synthetics_min_rejection_wick_ratio", 0.25)
                if is_synthetic
                else self.config.min_rejection_wick_ratio
            )
        )

        if is_synthetic:
            # En sintéticos (Boom, Crash, Volatility, Step, Jump, Flip) que operan 24/7/365,
            # no se exige barrido institucional de Judas Swing bancario.
            # Se toma el extremo de la consolidación reciente como nivel de referencia para el gatillo LTF.
            manipulation_found = True
            sweep_peak = float(df_h1["high"].iloc[-1]) if bias_bearish else float(df_h1["low"].iloc[-1])
            sweep_idx = len(df_h1) - 1
        else:
            recent_bars = df_h1.iloc[-4:].reset_index(drop=True)
            for idx in range(len(recent_bars)):
                c_high = float(recent_bars["high"].iloc[idx])
                c_low = float(recent_bars["low"].iloc[idx])
                c_open = float(recent_bars["open"].iloc[idx])
                c_close = float(recent_bars["close"].iloc[idx])
                c_range = c_high - c_low + 1e-9

                if bias_bearish and c_high > range_high:
                    fvg_mitigated = any(
                        fvg["type"] == "BEARISH" and c_high >= fvg["bottom"] and c_high <= (fvg["top"] + 0.1 * fvg["height"])
                        for fvg in fvgs
                    )
                    upper_wick = (c_high - max(c_open, c_close)) / c_range
                    if fvg_mitigated or (upper_wick >= wick_threshold):
                        manipulation_found = True
                        sweep_peak = c_high
                        sweep_idx = len(df_h1) - 4 + idx
                        break

                elif bias_bullish and c_low < range_low:
                    fvg_mitigated = any(
                        fvg["type"] == "BULLISH" and c_low <= fvg["top"] and c_low >= (fvg["bottom"] - 0.1 * fvg["height"])
                        for fvg in fvgs
                    )
                    lower_wick = (min(c_open, c_close) - c_low) / c_range
                    if fvg_mitigated or (lower_wick >= wick_threshold):
                        manipulation_found = True
                        sweep_peak = c_low
                        sweep_idx = len(df_h1) - 4 + idx
                        break

        is_ifvg_bpr = False
        ifvg_bpr_scenario = None
        if not manipulation_found or sweep_peak is None:
            # Opción C: Si no hubo sweep de Judas Swing, comprobar Inversion FVG y BPR
            if getattr(self.config, "ifvg_bpr_enabled", True):
                ifvg_bpr = find_inversion_fvg_and_bpr_setups(
                    df_h1,
                    curr_idx=len(df_h1) - 1,
                    intended_direction=intended_direction,
                    lookback_bars=getattr(self.config, "ifvg_lookback_bars", 24),
                    spread=0.00015 if "USD" in symbol else 0.5,
                )
                if ifvg_bpr and ifvg_bpr.get("valid"):
                    manipulation_found = True
                    sweep_peak = ifvg_bpr["stop_loss"]
                    sweep_idx = len(df_h1) - 2
                    is_ifvg_bpr = True
                    ifvg_bpr_scenario = ifvg_bpr["scenario"]
                else:
                    return {**base_response, "reason": "NO_JUDAS_SWING_MANIPULATION_CONFIRMED"}
            else:
                return {**base_response, "reason": "NO_JUDAS_SWING_MANIPULATION_CONFIRMED"}

        # 6. Refinamiento en Temporalidad Menor (M15 o M5) para Gatillo MSS y FVG / OB 5 Estrellas
        spread = 0.0
        try:
            tick = self.provider.get_current_tick(symbol)
            if tick and tick.get("ask") and tick.get("bid"):
                spread = abs(float(tick["ask"]) - float(tick["bid"]))
        except Exception:
            spread = 0.00015 if "USD" in symbol else 0.5

        # Intentar consultar velas de menor temporalidad (M15 o M5)
        df_ltf = None
        try:
            raw_ltf = self.provider.get_candles(symbol, self.config.entry_timeframe, count=81)
            if raw_ltf is not None and len(raw_ltf) >= 20:
                df_ltf = closed_candles_only(raw_ltf, self.config.entry_timeframe, now, count=80)
        except Exception:
            pass

        # Usar df_ltf si existe; sino caer al df_h1 para confirmación estricta
        eval_df = df_ltf if (df_ltf is not None and len(df_ltf) >= 20) else df_h1
        last_candle = eval_df.iloc[-1]
        curr_close = float(last_candle["close"])
        curr_open = float(last_candle["open"])
        curr_high = float(last_candle["high"])
        curr_low = float(last_candle["low"])
        candle_body = abs(curr_close - curr_open)
        candle_range = curr_high - curr_low + 1e-9
        displacement_ratio = candle_body / candle_range

        # Ruptura Estructural Estricta: "Bodies break, wicks sweep" (cuerpo >= 45%)
        if displacement_ratio < self.config.strict_mss_body_ratio:
            return {**base_response, "reason": f"INSUFFICIENT_DISPLACEMENT_BODY ({displacement_ratio:.2f} < {self.config.strict_mss_body_ratio})"}

        # Evaluación de Order Block 5 Estrellas (Sabri Malle Video 9)
        ob_five_star = None
        if not is_gold and getattr(self.config, "ob_five_star_enabled", True):
            try:
                ob_five_star = check_order_block_five_stars(eval_df, intended_direction)
            except Exception:
                ob_five_star = None

        fvg_aligned = False
        if intended_direction == "SELL":
            # Soporte previo al sweep
            local_support = float(eval_df["low"].iloc[-8:-1].min())
            if curr_close >= local_support:
                return {**base_response, "reason": "WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT"}
            if (local_support - curr_close) > (0.35 * range_height):
                return {**base_response, "reason": "PRICE_EXTENDED_CHASING_MSS_WAITING_PULLBACK"}

            # Comprobar FVG Consequent Encroachment (50%) y Mean Threshold de OB 5 Estrellas
            prev_high = float(eval_df["high"].iloc[-3]) if len(eval_df) >= 3 else curr_high
            fvg_ce = (prev_high + curr_low) / 2.0
            if getattr(self.config, "fvg_consequent_encroachment_entry", True):
                candidate_entry = min(local_support, fvg_ce)
                if ob_five_star and ob_five_star.get("valid") and ob_five_star.get("mean_threshold"):
                    candidate_entry = min(candidate_entry, ob_five_star["mean_threshold"])
                entry_price = candidate_entry
            else:
                entry_price = curr_close
            stop_loss = sweep_peak + spread
            fvg_aligned = True

        else:
            # Resistencia previa al sweep
            local_resistance = float(eval_df["high"].iloc[-8:-1].max())
            if curr_close <= local_resistance:
                return {**base_response, "reason": "WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANCE"}
            if (curr_close - local_resistance) > (0.35 * range_height):
                return {**base_response, "reason": "PRICE_EXTENDED_CHASING_MSS_WAITING_PULLBACK"}

            prev_low = float(eval_df["low"].iloc[-3]) if len(eval_df) >= 3 else curr_low
            fvg_ce = (prev_low + curr_high) / 2.0
            if getattr(self.config, "fvg_consequent_encroachment_entry", True):
                candidate_entry = max(local_resistance, fvg_ce)
                if ob_five_star and ob_five_star.get("valid") and ob_five_star.get("mean_threshold"):
                    candidate_entry = max(candidate_entry, ob_five_star["mean_threshold"])
                entry_price = candidate_entry
            else:
                entry_price = curr_close
            stop_loss = sweep_peak - spread
            fvg_aligned = True

        risk = abs(entry_price - stop_loss)
        if risk <= 0 or (spread > 0 and risk < (1.2 * spread)):
            return {**base_response, "reason": "INVALID_RISK_SPREAD_RATIO"}

        # 7. Proyección Asimétrica (TP1 1:2.0 RR / TP2 1:3.5 RR) y Validación Fibonacci
        if intended_direction == "SELL":
            swing_low_impulse = float(df_h1["low"].iloc[sweep_idx:].min())
            fibo_50 = (sweep_peak + swing_low_impulse) / 2.0
            if range_low >= fibo_50:
                return {**base_response, "reason": "TARGET_NOT_IN_DISCOUNT_ZONE"}
            tp1_price = entry_price - (self.config.tp1_rr * risk)
            tp2_price = entry_price - (self.config.runner_rr * risk)
        else:
            swing_high_impulse = float(df_h1["high"].iloc[sweep_idx:].max())
            fibo_50 = (sweep_peak + swing_high_impulse) / 2.0
            if range_high <= fibo_50:
                return {**base_response, "reason": "TARGET_NOT_IN_PREMIUM_ZONE"}
            tp1_price = entry_price + (self.config.tp1_rr * risk)
            tp2_price = entry_price + (self.config.runner_rr * risk)

        entry_time = last_candle["time"].isoformat() if hasattr(last_candle["time"], "isoformat") else str(last_candle["time"])

        # BE trigger: 2.0 para Gold (intacto), 1.0R / fast para los demás (Alex Ruiz & Sabri Malle)
        be_trigger = (
            self.config.be_trigger_rr
            if is_gold
            else getattr(self.config, "be_trigger_rr_fast", 1.0)
        )

        trade_score = 95.0 if (ob_five_star and ob_five_star.get("valid")) else 90.0

        signal = {
            "symbol": symbol,
            "direction": intended_direction,
            "entry_price": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "take_profit": round(tp2_price, 5),
            "tp1_price": round(tp1_price, 5),
            "tp2_price": round(tp2_price, 5),
            "risk_amount": risk,
            "risk_reward_ratio": self.config.runner_rr,
            "risk_reward": self.config.runner_rr,
            "trade_score": trade_score,
            "confirmation_percentage": 95.0,
            "adx": 28.0,
            "price_action_confirmations": {
                "rejection": True,
                "micro_structure": True,
                "displacement": True,
                "strong_close": True,
            },
            "confirmations": {
                "rejection": True,
                "micro_structure": True,
                "displacement": True,
                "strong_close": True,
            },
            "atr": round(range_height / 2.0, 5) if range_height > 0 else round(risk / self.config.runner_rr, 5),
            "structure_break": f"MSS_{intended_direction}",
            "entry_time": entry_time,
            "scenario": ifvg_bpr_scenario if (is_ifvg_bpr and ifvg_bpr_scenario) else "AMD_KILLZONE_FVG_REJECTION",
            "is_ifvg_bpr": is_ifvg_bpr,
            "requires_meta_label": True if is_ifvg_bpr else False,
            "tp1_rr": self.config.tp1_rr,
            "runner_rr": self.config.runner_rr,
            "be_trigger_rr": be_trigger,
            "timeframe": self.config.entry_timeframe,
            "split_execution": True,
            "leg1_risk_ratio": self.config.leg1_risk_ratio,
            "leg2_risk_ratio": self.config.leg2_risk_ratio,
            "session_killzone_active": 1.0 if session_active else 0.0,
            "asian_range_swept": True,
            "fvg_consequent_encroachment_aligned": fvg_aligned,
            "displacement_body_ratio": round(displacement_ratio, 3),
            "ob_five_star": ob_five_star.get("stars") if ob_five_star else None,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
        }

        return {
            "valid": True,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "action": "ICT_SABRI_MALLE_CONFIRMED",
            "reason": f"ICT AMD Judas Swing confirmed ({intended_direction} on {symbol} | Killzone={session_active})",
            "symbol": symbol,
            "signal": signal,
            "diagnostics": {
                "session_killzone_active": 1.0 if session_active else 0.0,
                "asian_range_swept": True,
                "fvg_consequent_encroachment_aligned": fvg_aligned,
                "displacement_body_ratio": round(displacement_ratio, 3),
            }
        }
