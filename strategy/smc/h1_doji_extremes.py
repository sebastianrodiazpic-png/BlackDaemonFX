from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class H1ExtremeDojiConfig:
    enabled: bool = True
    lookback_candles: int = 100
    max_age_candles: int = 2
    max_body_ratio: float = 0.10
    extreme_fraction: float = 0.15
    min_rejection_wick_ratio: float = 0.35
    bonus_points: float = 5.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if pd.notna(number) else default
    except (TypeError, ValueError):
        return default


def _empty(reason: str = "SIN_DOJI_EXTREMO_H1") -> dict[str, Any]:
    return {
        "h1_doji_enabled": True,
        "h1_doji_confirmation": False,
        "h1_doji_type": None,
        "h1_doji_direction": None,
        "h1_doji_time": None,
        "h1_doji_zone": None,
        "h1_doji_reason": reason,
        "h1_doji_body_ratio": None,
        "h1_doji_upper_wick_ratio": None,
        "h1_doji_lower_wick_ratio": None,
        "h1_doji_extreme_position": None,
        "h1_doji_age_candles": None,
    }


def detect_h1_extreme_doji(
    data: pd.DataFrame,
    *,
    direction: str,
    config: H1ExtremeDojiConfig | None = None,
) -> dict[str, Any]:
    """Detecta un Doji H1 reciente en un extremo compatible con la operación.

    BUY  -> Doji en extremo inferior/Discount con mecha inferior significativa.
    SELL -> Doji en extremo superior/Premium con mecha superior significativa.

    La detección es una confluencia opcional. No genera entradas ni invalida setups.
    """
    config = config or H1ExtremeDojiConfig()
    if not config.enabled:
        result = _empty("DETECCION_DOJI_H1_DESACTIVADA")
        result["h1_doji_enabled"] = False
        return result

    normalized = str(direction or "").upper()
    if normalized not in {"BUY", "SELL"}:
        return _empty("DIRECCION_H1_DOJI_INVALIDA")

    if data is None or data.empty or len(data) < 2:
        return _empty("DATOS_H1_INSUFICIENTES")

    frame = data.copy().reset_index(drop=True)
    required = {"time", "open", "high", "low", "close"}
    if not required.issubset(frame.columns):
        return _empty("COLUMNAS_H1_INCOMPLETAS")

    lookback = max(10, int(config.lookback_candles))
    max_age = max(0, int(config.max_age_candles))
    latest_index = len(frame) - 1
    first_candidate = max(0, latest_index - max_age)

    # Recorremos desde la vela H1 cerrada más reciente hacia atrás. Se devuelve
    # la confluencia válida más nueva para que la evidencia sea auditable.
    for index in range(latest_index, first_candidate - 1, -1):
        candle = frame.iloc[index]
        high = _safe_float(candle.get("high"))
        low = _safe_float(candle.get("low"))
        open_ = _safe_float(candle.get("open"))
        close = _safe_float(candle.get("close"))
        candle_range = high - low
        if candle_range <= 0:
            continue

        body = abs(close - open_)
        body_ratio = body / candle_range
        if body_ratio > float(config.max_body_ratio):
            continue

        upper_wick = max(high - max(open_, close), 0.0)
        lower_wick = max(min(open_, close) - low, 0.0)
        upper_ratio = upper_wick / candle_range
        lower_ratio = lower_wick / candle_range

        start = max(0, index - lookback + 1)
        window = frame.iloc[start:index + 1]
        range_high = _safe_float(candle.get("range_high"), _safe_float(window["high"].max()))
        range_low = _safe_float(candle.get("range_low"), _safe_float(window["low"].min()))
        structural_range = range_high - range_low
        if structural_range <= 0:
            continue

        zone = str(candle.get("zone") or "").lower() or None
        extreme_fraction = min(max(float(config.extreme_fraction), 0.01), 0.49)

        if normalized == "BUY":
            threshold = range_low + structural_range * extreme_fraction
            at_extreme = low <= threshold
            rejection_ok = lower_ratio >= float(config.min_rejection_wick_ratio)
            zone_ok = (zone == "discount") if zone in {"discount", "premium", "equilibrium"} else ((high + low) / 2.0) <= (range_low + range_high) / 2.0
            extreme_position = (low - range_low) / structural_range
            if not (at_extreme and rejection_ok and zone_ok):
                continue
            doji_type = "DOJI_H1_EXTREMO_ALCISTA"
            if lower_ratio >= 0.60 and upper_ratio <= 0.25:
                doji_type = "DOJI_LIBELULA_H1_EXTREMO_ALCISTA"
            reason = "DOJI_H1_EN_EXTREMO_INFERIOR_CON_RECHAZO"
        else:
            threshold = range_high - structural_range * extreme_fraction
            at_extreme = high >= threshold
            rejection_ok = upper_ratio >= float(config.min_rejection_wick_ratio)
            zone_ok = (zone == "premium") if zone in {"discount", "premium", "equilibrium"} else ((high + low) / 2.0) >= (range_low + range_high) / 2.0
            extreme_position = (range_high - high) / structural_range
            if not (at_extreme and rejection_ok and zone_ok):
                continue
            doji_type = "DOJI_H1_EXTREMO_BAJISTA"
            if upper_ratio >= 0.60 and lower_ratio <= 0.25:
                doji_type = "DOJI_LAPIDA_H1_EXTREMO_BAJISTA"
            reason = "DOJI_H1_EN_EXTREMO_SUPERIOR_CON_RECHAZO"

        time_value = pd.to_datetime(candle.get("time"), utc=True, errors="coerce")
        return {
            "h1_doji_enabled": True,
            "h1_doji_confirmation": True,
            "h1_doji_type": doji_type,
            "h1_doji_direction": normalized,
            "h1_doji_time": time_value.isoformat() if pd.notna(time_value) else None,
            "h1_doji_zone": zone.upper() if zone else ("DISCOUNT" if normalized == "BUY" else "PREMIUM"),
            "h1_doji_reason": reason,
            "h1_doji_body_ratio": round(body_ratio, 4),
            "h1_doji_upper_wick_ratio": round(upper_ratio, 4),
            "h1_doji_lower_wick_ratio": round(lower_ratio, 4),
            "h1_doji_extreme_position": round(extreme_position, 4),
            "h1_doji_age_candles": latest_index - index,
        }

    return _empty()
