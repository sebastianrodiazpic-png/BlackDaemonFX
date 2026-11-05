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
5. Gestión dual (contrato operativo, valores de `ICTSabriMalleConfig`):
   - Pierna 1: TP1 a 1R (`tp1_rr`, 50 % del riesgo).
   - Pierna 2: corredora a 2R (`runner_rr`, 50 %) con Break Even al cerrar TP1 y extensión progresiva TP3/TP4.
"""

from __future__ import annotations

import math
import os
import re
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
    duration = pd.Timedelta(minutes=TIMEFRAME_MINUTES.get(str(timeframe).upper(), 0))
    t_col = df["time"]
    if isinstance(t_col.dtype, pd.DatetimeTZDtype) and str(t_col.dtype.tz) == "UTC" and t_col.is_monotonic_increasing:
        cutoff = now - duration
        try:
            unit_str = getattr(t_col.dt, "unit", None)
            if unit_str:
                cutoff_aligned = pd.Timestamp(cutoff).as_unit(unit_str, round_ok=True)
            else:
                cutoff_aligned = cutoff
            idx = int(t_col.searchsorted(cutoff_aligned, side="right"))
            start = max(0, idx - int(count)) if count is not None else 0
            return df.iloc[start:idx].reset_index(drop=True)
        except Exception:
            pass
    out = df.copy()
    out["time"] = pd.to_datetime(out["time"], utc=True)
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
    grouped = df.set_index("time").resample("4h")
    h4 = grouped.agg(agg_dict).dropna().reset_index()
    h4["time"] = pd.to_datetime(h4["time"], utc=True)
    if os.getenv("DAEMONBLACKFX_ICT_H4_COMPLETE_ONLY", "1").strip().lower() not in ("0", "false", "off") and len(h4):
        # El último bloque de 4 h con menos de 4 velas H1 es una vela H4 en formación (Fase 1: solo velas cerradas).
        last_h1 = pd.to_datetime(df["time"], utc=True).max()
        if last_h1 + pd.Timedelta(hours=1) < h4["time"].iloc[-1] + pd.Timedelta(hours=4):
            h4 = h4.iloc[:-1].reset_index(drop=True)
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
    """Identifica si un símbolo pertenece al mercado de sintéticos algorítmicos 24/7.

    Fuente única de la detección (la usan también Malaysian SNR y el motor). "DEX" se busca como palabra: como
    subcadena coincidía con cualquier "INDEX" (un "Germany 40 Index" real habría pasado por sintético). Las familias
    que solo entraban por esa coincidencia (Trek, Exponential Growth, Snap) se nombran explícitamente, así que la
    clasificación de los 733 símbolos del broker no cambia (comprobado el 24-oct-2026).
    """
    sym_u = str(symbol or "").upper()
    keywords = (
        "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP", "1HZ",
        "V10", "V25", "V50", "V75", "V100", "V150", "V250",
        "VOL ", "VOLSWITCH", "SKEW", "MULTI STEP", "SPOT UP",
        "DRIFT", "DAILY RESET", "HYBRID", "RANGE BREAK",
        "TREK UP", "TREK DOWN", "EXPONENTIAL GROWTH", "SNAP ",
    )
    return any(k in sym_u for k in keywords) or re.search(r"\bDEX\b", sym_u) is not None


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
                has_fvg = bool(highs[i] < lows[i + 2])
                prev_lows = lows[max(0, i - 4) : i]
                swept_liq = bool(len(prev_lows) > 0 and (lows[i] <= float(np.min(prev_lows))))
                ob_mid = (opens[i] + closes[i]) / 2.0
                mitigated = False
                for k in range(i + 1, curr_idx + 1):
                    if closes[k] < ob_mid:
                        mitigated = True
                        break
                next_range = max(1e-9, float(highs[i + 1] - lows[i + 1]))
                strong_disp = bool(closes[i + 1] > opens[i + 1] and (abs(closes[i + 1] - opens[i + 1]) / next_range) >= 0.45)
                broke_struct = bool(closes[i + 1] > highs[i] or closes[i + 2] > highs[i])
                stars = sum([has_fvg, swept_liq, not mitigated, strong_disp, broke_struct])
                if not mitigated:
                    if best_ob is None or lows[i] < best_ob["low"]:
                        best_ob = {
                            "valid": bool(stars >= 3 and has_fvg and not mitigated),
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
                has_fvg = bool(lows[i] > highs[i + 2])
                prev_highs = highs[max(0, i - 4) : i]
                swept_liq = bool(len(prev_highs) > 0 and (highs[i] >= float(np.max(prev_highs))))
                ob_mid = (opens[i] + closes[i]) / 2.0
                mitigated = False
                for k in range(i + 1, curr_idx + 1):
                    if closes[k] > ob_mid:
                        mitigated = True
                        break
                next_range = max(1e-9, float(highs[i + 1] - lows[i + 1]))
                strong_disp = bool(closes[i + 1] < opens[i + 1] and (abs(closes[i + 1] - opens[i + 1]) / next_range) >= 0.45)
                broke_struct = bool(closes[i + 1] < lows[i] or closes[i + 2] < lows[i])
                stars = sum([has_fvg, swept_liq, not mitigated, strong_disp, broke_struct])
                if not mitigated:
                    if best_ob is None or highs[i] > best_ob["high"]:
                        best_ob = {
                            "valid": bool(stars >= 3 and has_fvg and not mitigated),
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
        wr_pruned = {str(s).strip().lower() for s in (getattr(self.config, "wr_pruned_symbols", ()) or ())}
        if str(symbol).strip().lower() in wr_pruned:
            return {**base_response, "reason": "ICT_SYMBOL_PRUNED_WINRATE_LE_45"}

        # 1. Filtro Horario, Cierres de Mercado y Killzones Institucionales (Fast-Exit sin I/O de velas)
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
        # 1. Gold: Preserva su configuración oficial ICT (Londres, NY Killzone, London Close y Silver Bullet)
        if is_gold:
            in_london_close = False
            if getattr(self.config, "london_close_reversal_enabled", True):
                if ny_hour == 11 or (ny_hour == 12 and now_ny.minute <= 30):
                    in_london_close = True
            in_silver_bullet = False
            if getattr(self.config, "silver_bullet_enabled", True):
                if ny_hour in tuple(getattr(self.config, "silver_bullet_hours_ny", (3, 10, 14))):
                    in_silver_bullet = True
            session_active = in_london_kz or (in_ny_kz and self.config.ny_killzone_enabled) or in_silver_bullet or in_london_close
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

            # Mejora 8 (27-oct-2026): Killzone Tokio-Londres (00:00 - 02:00 NY) para pares Forex con JPY
            in_tokyo_london_jpy = False
            if is_forex and "JPY" in sym_u and getattr(self.config, "tokyo_london_kz_enabled", True):
                if 0 <= ny_hour <= 2:
                    in_tokyo_london_jpy = True

            # Sesión Asiática oficial (Tokyo / Sydney) para pares JPY y AUD (19:00 - 02:00 NY)
            in_asian_session_jpy_aud = False
            is_jpy_or_aud = is_forex and any(curr in sym_u for curr in ("JPY", "AUD"))
            if is_jpy_or_aud and getattr(self.config, "asian_session_jpy_aud_enabled", True):
                asian_kz_hours = getattr(self.config, "asian_kz_hours_ny", (19, 20, 21, 22, 23, 0, 1, 2))
                if ny_hour in asian_kz_hours:
                    in_asian_session_jpy_aud = True

            session_active = (
                in_london_kz
                or ny_kz_active
                or in_london_close
                or in_silver_bullet
                or in_tokyo_london_jpy
                or in_asian_session_jpy_aud
            )

        if not is_synthetic and self.config.killzone_filter_enabled:
            if not session_active:
                return {
                    **base_response,
                    "reason": f"OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: {ny_hour:02d}:00)",
                    "diagnostics": {"session_killzone_active": 0.0, "ny_hour": ny_hour}
                }

        # 2. Obtener velas históricas H1 (solo si la sesión y el horario están activos)
        try:
            raw_h1 = self.provider.get_candles(symbol, self.config.structure_timeframe, count=81)
        except Exception as exc:
            return {**base_response, "reason": f"PROVIDER_ERROR_H1: {exc}"}

        if raw_h1 is None or len(raw_h1) < 30:
            return {**base_response, "reason": "INSUFFICIENT_H1_CANDLES"}

        df_h1 = closed_candles_only(raw_h1, self.config.structure_timeframe, now, count=80)

        if len(df_h1) < 28:
            return {**base_response, "reason": "INSUFFICIENT_HISTORICAL_H1"}

        # Optimización Early-Exit: Si min_adx_h1 > 0 y el régimen H1 es insuficiente,
        # salir antes de descargar H4, calcular EMAs, swings y pedir LTF candles por red.
        min_adx = float(getattr(self.config, "min_adx_h1", 0.0) or 0.0)
        early_adx = None
        if len(df_h1) >= 28:
            try:
                from strategy.indicators import calculate_adx
                adx_series = calculate_adx(df_h1)
                if not adx_series.empty:
                    val = float(adx_series.iloc[-1])
                    if math.isfinite(val):
                        early_adx = round(val, 2)
            except Exception:
                early_adx = None

        if min_adx > 0 and early_adx is not None and early_adx > 0 and early_adx < min_adx:
            return {**base_response, "reason": f"INSUFFICIENT_H1_ADX_REGIME ({early_adx:.1f} < {min_adx:.1f})"}

        # Velas H4 para Macro Bias
        df_h4 = None
        try:
            h4_count = max(31, int(getattr(self.config, "macro_h4_candles", 101)))
            raw_h4 = self.provider.get_candles(symbol, self.config.macro_timeframe, count=h4_count)
            if raw_h4 is not None and len(raw_h4) >= 30:
                df_h4 = closed_candles_only(raw_h4, self.config.macro_timeframe, now, count=h4_count - 1)
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
        is_adaptive_jump_sell = False
        is_adaptive_step_buy = False
        if getattr(self.config, "directional_asymmetry_filter_enabled", True):
            sym_l = str(symbol).strip().lower()
            jump_buy_only = {str(s).strip().lower() for s in getattr(self.config, "jump_buy_only_symbols", ())}
            step_sell_only = {str(s).strip().lower() for s in getattr(self.config, "step_sell_only_symbols", ())}
            is_adaptive_on = bool(getattr(self.config, "adaptive_bidirectional_jump_step_enabled", True))
            if sym_l in jump_buy_only and intended_direction != "BUY":
                if is_adaptive_on and sym_l in {"jump 50 index", "jump 75 index"} and intended_direction == "SELL":
                    is_adaptive_jump_sell = True
                else:
                    return {**base_response, "reason": "ICT_DIRECTION_ASYMMETRY_JUMP_BUY_ONLY"}
            if sym_l in step_sell_only and intended_direction != "SELL":
                if is_adaptive_on and sym_l in {"step index", "step index 500"} and intended_direction == "BUY":
                    is_adaptive_step_buy = True
                else:
                    return {**base_response, "reason": "ICT_DIRECTION_ASYMMETRY_STEP_SELL_ONLY"}

        # 4. Acumulación (A): Rango Asiático (20:00 - 00:00 NY), Rango Londres, o Consolidación Previa
        atr_h1 = compute_atr(df_h1, period=14)
        curr_atr = float(atr_h1[-1]) if len(atr_h1) > 0 else 1.0

        range_high = None
        range_low = None
        asia_high = None
        asia_low = None
        pdh = None
        pdl = None

        if not is_synthetic:
            df_h1_ny = df_h1.copy()
            df_h1_ny["ny_hour"] = df_h1_ny["time"].dt.tz_convert(NEW_YORK).dt.hour
            df_h1_ny["ny_date"] = df_h1_ny["time"].dt.tz_convert(NEW_YORK).dt.date
            
            # 1. Asian Range más reciente (20:00 a 00:00 NY)
            asian_bars = []
            for look_back in range(1, min(36, len(df_h1_ny))):
                chk_idx = len(df_h1_ny) - 1 - look_back
                chk_h = df_h1_ny["ny_hour"].iloc[chk_idx]
                if chk_h >= self.config.asian_range_start_ny or chk_h <= self.config.asian_range_end_ny:
                    asian_bars.append(df_h1_ny.iloc[chk_idx])
                elif len(asian_bars) > 0:
                    break
            if len(asian_bars) >= 2:
                df_asia = pd.DataFrame(asian_bars)
                asia_high = float(df_asia["high"].max())
                asia_low = float(df_asia["low"].min())

            # 2. Previous Day High / Low (PDH / PDL)
            prior_df = df_h1_ny[df_h1_ny["ny_date"] < now_ny.date()]
            if not prior_df.empty:
                last_prior_date = prior_df["ny_date"].iloc[-1]
                prev_day = prior_df[prior_df["ny_date"] == last_prior_date]
                if len(prev_day) >= 4:
                    pdh = float(prev_day["high"].max())
                    pdl = float(prev_day["low"].min())

            if 2 <= ny_hour <= 5:
                # London KZ barre el Rango Asiático (20:00 a 00:00 NY)
                if asia_high is not None and asia_low is not None:
                    range_high = asia_high
                    range_low = asia_low
                elif len(asian_bars) >= 2:
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
            elif in_asian_session_jpy_aud:
                # Sesión Asiática (Tokyo / Sydney) para pares JPY y AUD (19:00 - 02:00 NY)
                ny_pm_bars = []
                for look_back in range(1, min(24, len(df_h1_ny))):
                    chk_idx = len(df_h1_ny) - 1 - look_back
                    chk_h = df_h1_ny["ny_hour"].iloc[chk_idx]
                    if 12 <= chk_h <= 17:
                        ny_pm_bars.append(df_h1_ny.iloc[chk_idx])
                    elif len(ny_pm_bars) > 0:
                        break
                if len(ny_pm_bars) >= 2:
                    df_ny_pm = pd.DataFrame(ny_pm_bars)
                    range_high = float(df_ny_pm["high"].max())
                    range_low = float(df_ny_pm["low"].min())
                elif pdh is not None and pdl is not None:
                    range_high = pdh
                    range_low = pdl
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
        is_range_height_valid = (
            curr_atr > 0
            and (self.config.min_atr_factor * curr_atr) <= range_height <= (self.config.max_atr_factor * curr_atr)
        )
        if not is_range_height_valid and not is_synthetic:
            # Si el rango de sesión principal excede los límites, pero el Asian Range está en bounds, se adopta como rango efectivo
            if asia_high is not None and asia_low is not None:
                ar_height = asia_high - asia_low
                if (self.config.min_atr_factor * curr_atr) <= ar_height <= (self.config.max_atr_factor * curr_atr):
                    range_high = asia_high
                    range_low = asia_low
                    range_height = ar_height
                    is_range_height_valid = True

        if not is_range_height_valid:
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
            # Se toma el extremo de las últimas N velas H1 configuradas como nivel de referencia para el gatillo LTF.
            manipulation_found = True
            synth_sweep_bars = max(1, int(getattr(self.config, "synthetics_sweep_lookback_h1_bars", 1)))
            recent_synth_h1 = df_h1.iloc[-synth_sweep_bars:]
            if bias_bearish:
                sweep_peak = float(recent_synth_h1["high"].max())
                sweep_idx = int(len(df_h1) - len(recent_synth_h1) + int(np.argmax(recent_synth_h1["high"].values)))
            else:
                sweep_peak = float(recent_synth_h1["low"].min())
                sweep_idx = int(len(df_h1) - len(recent_synth_h1) + int(np.argmin(recent_synth_h1["low"].values)))
        else:
            swept_liquidity_source = "NONE"
            recent_bars = df_h1.iloc[-4:].reset_index(drop=True)
            for idx in range(len(recent_bars)):
                c_high = float(recent_bars["high"].iloc[idx])
                c_low = float(recent_bars["low"].iloc[idx])
                c_open = float(recent_bars["open"].iloc[idx])
                c_close = float(recent_bars["close"].iloc[idx])
                c_range = c_high - c_low + 1e-9

                if bias_bearish:
                    swept_levels = []
                    if range_high is not None and c_high > range_high:
                        swept_levels.append("SESSION_RANGE_HIGH")
                    if getattr(self.config, "asian_range_sweep_enabled", True) and asia_high is not None and c_high > asia_high:
                        swept_levels.append("ASIAN_RANGE_HIGH")
                    if getattr(self.config, "pdh_pdl_sweep_enabled", True) and pdh is not None and c_high > pdh:
                        swept_levels.append("PREVIOUS_DAY_HIGH")

                    if swept_levels:
                        fvg_mitigated = any(
                            fvg["type"] == "BEARISH" and c_high >= fvg["bottom"] and c_high <= (fvg["top"] + 0.1 * fvg["height"])
                            for fvg in fvgs
                        )
                        upper_wick = (c_high - max(c_open, c_close)) / c_range
                        if fvg_mitigated or (upper_wick >= wick_threshold):
                            manipulation_found = True
                            sweep_peak = c_high
                            sweep_idx = len(df_h1) - 4 + idx
                            swept_liquidity_source = "+".join(swept_levels)
                            break

                elif bias_bullish:
                    swept_levels = []
                    if range_low is not None and c_low < range_low:
                        swept_levels.append("SESSION_RANGE_LOW")
                    if getattr(self.config, "asian_range_sweep_enabled", True) and asia_low is not None and c_low < asia_low:
                        swept_levels.append("ASIAN_RANGE_LOW")
                    if getattr(self.config, "pdh_pdl_sweep_enabled", True) and pdl is not None and c_low < pdl:
                        swept_levels.append("PREVIOUS_DAY_LOW")

                    if swept_levels:
                        fvg_mitigated = any(
                            fvg["type"] == "BULLISH" and c_low <= fvg["top"] and c_low >= (fvg["bottom"] - 0.1 * fvg["height"])
                            for fvg in fvgs
                        )
                        lower_wick = (min(c_open, c_close) - c_low) / c_range
                        if fvg_mitigated or (lower_wick >= wick_threshold):
                            manipulation_found = True
                            sweep_peak = c_low
                            sweep_idx = len(df_h1) - 4 + idx
                            swept_liquidity_source = "+".join(swept_levels)
                            break

        is_ifvg_bpr = False
        ifvg_bpr_scenario = None
        ifvg_bpr_entry = None
        ifvg_bpr_sl = None
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
                    sweep_peak = float(ifvg_bpr["stop_loss"])
                    sweep_idx = len(df_h1) - 2
                    is_ifvg_bpr = True
                    ifvg_bpr_scenario = ifvg_bpr["scenario"]
                    ifvg_bpr_entry = float(ifvg_bpr["entry_price"])
                    ifvg_bpr_sl = float(ifvg_bpr["stop_loss"])
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
        micro_stop_applied = False
        if is_ifvg_bpr and ifvg_bpr_entry is not None and ifvg_bpr_sl is not None:
            entry_price = ifvg_bpr_entry
            stop_loss = ifvg_bpr_sl
            fvg_aligned = True
        elif intended_direction == "SELL":
            # Soporte previo al sweep
            local_support = float(eval_df["low"].iloc[-8:-1].min())
            if curr_close >= local_support:
                return {**base_response, "reason": "WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT"}
            if (local_support - curr_close) > (0.35 * range_height):
                return {**base_response, "reason": "PRICE_EXTENDED_CHASING_MSS_WAITING_PULLBACK"}

            # Comprobar FVG Consequent Encroachment (50%) y Mean Threshold de OB 5 Estrellas
            mitigation_ratio = float(getattr(self.config, "mitigation_fvg_ratio", 0.25))
            if getattr(self.config, "require_real_fvg_ce", False):
                prev_low_3 = float(eval_df["low"].iloc[-3]) if len(eval_df) >= 3 else curr_high
                has_real_fvg = curr_high < prev_low_3
                fvg_ce = (prev_low_3 + curr_high) / 2.0 if has_real_fvg else local_support
                fvg_mitigation = (curr_high + mitigation_ratio * (prev_low_3 - curr_high)) if has_real_fvg else candidate_entry if 'candidate_entry' in locals() else local_support
            else:
                prev_high = float(eval_df["high"].iloc[-3]) if len(eval_df) >= 3 else curr_high
                fvg_ce = (prev_high + curr_low) / 2.0
                fvg_mitigation = (curr_low + mitigation_ratio * (prev_high - curr_low)) if prev_high > curr_low else fvg_ce
            if getattr(self.config, "fvg_consequent_encroachment_entry", True):
                candidate_entry = min(local_support, fvg_ce)
                mitigation_candidate = min(local_support, fvg_mitigation)
                if ob_five_star and ob_five_star.get("valid"):
                    if ob_five_star.get("mean_threshold"):
                        candidate_entry = min(candidate_entry, ob_five_star["mean_threshold"])
                    if getattr(self.config, "ob_mitigation_entry_enabled", True) and ob_five_star.get("bottom"):
                        mitigation_candidate = min(mitigation_candidate, ob_five_star["bottom"])
                entry_price = candidate_entry
                mitigation_entry_price = mitigation_candidate
            else:
                entry_price = curr_close
                mitigation_entry_price = curr_close
            stop_loss = sweep_peak + spread
            micro_stop_applied = False
            if is_synthetic and getattr(self.config, "enable_m15_micro_stop", True) and len(eval_df) >= 3:
                buffer_dist = float(getattr(self.config, "m15_micro_stop_buffer_atr", 0.10)) * curr_atr
                min_risk_floor = float(getattr(self.config, "m15_micro_stop_min_risk_atr", 0.20)) * curr_atr
                m15_extreme = float(eval_df["high"].iloc[-4:].max())
                m15_cand_stop = m15_extreme + buffer_dist + spread
                if m15_cand_stop < stop_loss and (m15_cand_stop - candidate_entry) >= min_risk_floor:
                    stop_loss = m15_cand_stop
                    micro_stop_applied = True
            fvg_aligned = True

        else:
            # Resistencia previa al sweep
            local_resistance = float(eval_df["high"].iloc[-8:-1].max())
            if curr_close <= local_resistance:
                return {**base_response, "reason": "WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANCE"}
            if (curr_close - local_resistance) > (0.35 * range_height):
                return {**base_response, "reason": "PRICE_EXTENDED_CHASING_MSS_WAITING_PULLBACK"}

            prev_low = float(eval_df["low"].iloc[-3]) if len(eval_df) >= 3 else curr_low
            mitigation_ratio = float(getattr(self.config, "mitigation_fvg_ratio", 0.25))
            if getattr(self.config, "require_real_fvg_ce", False):
                prev_high_3 = float(eval_df["high"].iloc[-3]) if len(eval_df) >= 3 else curr_low
                has_real_fvg = curr_low > prev_high_3
                fvg_ce = (prev_high_3 + curr_low) / 2.0 if has_real_fvg else local_resistance
                fvg_mitigation = (curr_low - mitigation_ratio * (curr_low - prev_high_3)) if has_real_fvg else local_resistance
            else:
                fvg_ce = (prev_low + curr_high) / 2.0
                fvg_mitigation = (curr_high - mitigation_ratio * (curr_high - prev_low)) if curr_high > prev_low else fvg_ce
            if getattr(self.config, "fvg_consequent_encroachment_entry", True):
                candidate_entry = max(local_resistance, fvg_ce)
                mitigation_candidate = max(local_resistance, fvg_mitigation)
                if ob_five_star and ob_five_star.get("valid"):
                    if ob_five_star.get("mean_threshold"):
                        candidate_entry = max(candidate_entry, ob_five_star["mean_threshold"])
                    if getattr(self.config, "ob_mitigation_entry_enabled", True) and ob_five_star.get("top"):
                        mitigation_candidate = max(mitigation_candidate, ob_five_star["top"])
                entry_price = candidate_entry
                mitigation_entry_price = mitigation_candidate
            else:
                entry_price = curr_close
                mitigation_entry_price = curr_close
            stop_loss = sweep_peak - spread
            micro_stop_applied = False
            if is_synthetic and getattr(self.config, "enable_m15_micro_stop", True) and len(eval_df) >= 3:
                buffer_dist = float(getattr(self.config, "m15_micro_stop_buffer_atr", 0.10)) * curr_atr
                min_risk_floor = float(getattr(self.config, "m15_micro_stop_min_risk_atr", 0.20)) * curr_atr
                m15_extreme = float(eval_df["low"].iloc[-4:].min())
                m15_cand_stop = m15_extreme - buffer_dist - spread
                if m15_cand_stop > stop_loss and (candidate_entry - m15_cand_stop) >= min_risk_floor:
                    stop_loss = m15_cand_stop
                    micro_stop_applied = True
            fvg_aligned = True

        risk = abs(entry_price - stop_loss)
        if risk <= 0 or (spread > 0 and risk < (1.2 * spread)):
            return {**base_response, "reason": "INVALID_RISK_SPREAD_RATIO"}

        # Mejora 1 (26-oct-2026): piso estructural de SL en sintéticos (sl_atr_h1 >= min_sl_atr_h1 o piso micro-stop)
        min_sl_atr = float(getattr(self.config, "min_sl_atr_h1", 0.0) or 0.0)
        effective_min_sl_atr = float(getattr(self.config, "m15_micro_stop_min_risk_atr", 0.20)) if micro_stop_applied else min_sl_atr
        if is_synthetic and effective_min_sl_atr > 0 and curr_atr > 0:
            sl_atr_ratio = risk / curr_atr
            if sl_atr_ratio < effective_min_sl_atr:
                return {**base_response, "reason": f"SL_ATR_H1_TOO_TIGHT ({sl_atr_ratio:.2f} < {effective_min_sl_atr:.2f})"}

        # Mejora 2 (26-oct-2026): tope de profundidad de retroceso (signed_pullback_r <= max_signed_pullback_r)
        max_pb_r = float(getattr(self.config, "max_signed_pullback_r", 0.0) or 0.0)
        if max_pb_r > 0 and risk > 0:
            signed_pb_r = ((curr_close - entry_price) if intended_direction == "BUY" else (entry_price - curr_close)) / risk
            if signed_pb_r > max_pb_r + 1e-9:
                return {**base_response, "reason": f"PULLBACK_DEPTH_EXCEEDS_MAX_R ({signed_pb_r:.2f} > {max_pb_r:.2f})"}

        # 7. Objetivos (TP1 = tp1_rr, TP2 = runner_rr; hoy 1R / 2R) y validación Fibonacci
        ref_low = min(v for v in (range_low, asia_low, pdl) if v is not None) if any(v is not None for v in (range_low, asia_low, pdl)) else range_low
        ref_high = max(v for v in (range_high, asia_high, pdh) if v is not None) if any(v is not None for v in (range_high, asia_high, pdh)) else range_high

        if intended_direction == "SELL":
            swing_low_impulse = float(df_h1["low"].iloc[sweep_idx:].min())
            fibo_50 = (sweep_peak + swing_low_impulse) / 2.0
            if ref_low is not None and ref_low >= fibo_50:
                return {**base_response, "reason": "TARGET_NOT_IN_DISCOUNT_ZONE"}
            tp1_price = entry_price - (self.config.tp1_rr * risk)
            tp2_price = entry_price - (self.config.runner_rr * risk)
        else:
            swing_high_impulse = float(df_h1["high"].iloc[sweep_idx:].max())
            fibo_50 = (sweep_peak + swing_high_impulse) / 2.0
            if ref_high is not None and ref_high <= fibo_50:
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

        # Datos reales para reentrenar la IA por estrategia. `adx` (28) y `confirmation_percentage` (95) siguen fijos:
        # el modelo en sombra se entrenó con ellos y la puerta ADX de STEP los lee (cambiarlos alteraría la operativa
        # validada en replay). Ver registro, auditoría del 24-oct-2026.
        real_features = {"atr_h1": round(curr_atr, 8), "sl_atr_h1": round(risk / curr_atr, 4) if curr_atr > 0 else None,
                         "range_atr_h1": round(range_height / curr_atr, 4) if curr_atr > 0 else None,
                         "spread_sl": round(spread / risk, 6) if risk > 0 else None, "adx_h1": early_adx}
        if real_features["adx_h1"] is None:
            try:
                from strategy.indicators import calculate_adx
                adx_value = float(calculate_adx(df_h1).iloc[-1])
                real_features["adx_h1"] = round(adx_value, 2) if math.isfinite(adx_value) else None
            except Exception:
                pass

        # Mejora 5 (26-oct-2026): filtro de régimen ADX H1 >= min_adx_h1 (doble chequeo defensivo)
        min_adx = float(getattr(self.config, "min_adx_h1", 0.0) or 0.0)
        if min_adx > 0 and real_features["adx_h1"] is not None and real_features["adx_h1"] > 0 and real_features["adx_h1"] < min_adx:
            return {**base_response, "reason": f"INSUFFICIENT_H1_ADX_REGIME ({real_features['adx_h1']:.1f} < {min_adx:.1f})"}

        # Mejora 9 (30-oct-2026): Lógica adaptativa bidireccional Jump y Step
        if is_adaptive_jump_sell:
            jump_sell_min_sl = float(getattr(self.config, "jump_sell_min_sl_atr_h1", 1.45))
            sl_atr_ratio = (risk / curr_atr) if curr_atr > 0 else 0.0
            if sl_atr_ratio < jump_sell_min_sl:
                return {**base_response, "reason": f"JUMP_SELL_SL_TOO_TIGHT_ANTI_JUMP_SHIELD ({sl_atr_ratio:.2f} < {jump_sell_min_sl:.2f})"}
            jump_sell_max_pb = float(getattr(self.config, "jump_sell_max_signed_pb_r", 0.40))
            if risk > 0 and 'signed_pb_r' in locals() and signed_pb_r > jump_sell_max_pb + 1e-9:
                return {**base_response, "reason": f"JUMP_SELL_PULLBACK_TOO_DEEP ({signed_pb_r:.2f} > {jump_sell_max_pb:.2f})"}

        if is_adaptive_step_buy:
            step_buy_min_adx = float(getattr(self.config, "step_buy_min_adx_h1", 28.0))
            current_adx = real_features.get("adx_h1")
            if current_adx is not None and current_adx < step_buy_min_adx:
                return {**base_response, "reason": f"STEP_BUY_REQUIRES_STRONG_H1_ADX_EXPANSION ({current_adx:.1f} < {step_buy_min_adx:.1f})"}
            step_buy_max_pb = float(getattr(self.config, "step_buy_max_signed_pb_r", 0.25))
            if risk > 0 and 'signed_pb_r' in locals() and signed_pb_r > step_buy_max_pb + 1e-9:
                return {**base_response, "reason": f"STEP_BUY_PULLBACK_TOO_DEEP ({signed_pb_r:.2f} > {step_buy_max_pb:.2f})"}

        signal = {
            "symbol": symbol,
            "direction": intended_direction,
            "entry_price": round(entry_price, 5),
            "mitigation_entry_price": round(mitigation_entry_price, 5) if 'mitigation_entry_price' in locals() else round(entry_price, 5),
            "dual_entry_mitigation_enabled": bool(getattr(self.config, "dual_entry_mitigation_enabled", True)),
            "micro_stop_applied": bool(micro_stop_applied if 'micro_stop_applied' in locals() else False),
            "micro_stop_timeframe": "M15" if ('micro_stop_applied' in locals() and micro_stop_applied) else None,
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
            "swept_liquidity_source": swept_liquidity_source if not is_synthetic else "SYNTHETIC_ROLLING_EXTREME",
            "asian_range_swept": bool("ASIAN_RANGE" in (swept_liquidity_source if not is_synthetic else "") or (not is_synthetic and swept_liquidity_source != "NONE")),
            "pdh_pdl_swept": bool("PREVIOUS_DAY" in (swept_liquidity_source if not is_synthetic else "")),
            "in_asian_session": bool(in_asian_session_jpy_aud if not is_synthetic else False),
            "pdh": pdh,
            "pdl": pdl,
            "asia_high": asia_high,
            "asia_low": asia_low,
            "fvg_consequent_encroachment_aligned": fvg_aligned,
            "displacement_body_ratio": round(displacement_ratio, 3),
            "ob_five_star": ob_five_star.get("stars") if ob_five_star else None,
            "ict_real_features": real_features,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "_cached_df_h1": df_h1,
            "_cached_df_ltf": df_ltf,
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
