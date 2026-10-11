"""Detección de Fair Value Gaps (FVG) / imbalances como confluencia SMC.

Un FVG de 3 velas aparece cuando el rango de la vela intermedia deja un hueco
sin solapamiento entre la sombra de la vela anterior y la posterior (patrón
clásico ICT). Hasta esta versión el proyecto solo dibujaba estos huecos como
contexto visual auxiliar en el dashboard (`dashboard.smc_visual_context`), sin
que participaran en la decisión de si una entrada se confirma o se rechaza.

Este módulo lo convierte en una confluencia ponderada más, en el mismo
espíritu que `harmonic_patterns.py` y `chart_patterns.py`: aporta un bonus de
score cuando el FVG más reciente y relevante está alineado con la dirección
de la señal y aún no fue rellenado, sin bloquear ni ser obligatorio por
defecto (`require_fvg=False`).

Vinculaciones:
- Lo importa `strategy.smc.confirmation_engine`, que llama a
  `detect_fvg_confirmation` y suma `fvg_bonus_points` al score si el gap
  queda confirmado.
- La configuración llega desde
  `strategy.execution.trade_pipeline.PipelineConfig` (campos `fvg_*`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FVGConfig:
    """Parámetros de detección de Fair Value Gaps. Inmutable para reproducibilidad.

    Campos:
    - `enabled`: si es False el detector devuelve la estructura vacía.
    - `lookback`: cuántas velas hacia atrás (desde la vela de confirmación)
      se recorren buscando el FVG más reciente.
    - `max_age_candles`: antigüedad máxima (en velas) del FVG desde que se
      formó hasta la vela de confirmación; un hueco viejo ya no es relevante
      para la entrada actual.
    - `require_alignment_with_zone`: si es True, el FVG debe solaparse con el
      Order Block del setup (misma zona de interés institucional).
    - `bonus_points`: puntos que aporta al score si el FVG está confirmado.
    - `require_pattern`: si es True, su ausencia rechaza la entrada (por
      defecto False: es confluencia opcional, no gate obligatorio).
    """
    enabled: bool = True
    lookback: int = 30
    max_age_candles: int = 10
    require_alignment_with_zone: bool = False
    bonus_points: float = 6.0
    require_pattern: bool = False
    is_crash: bool = False
    min_displacement_atr_multiplier: float = 1.5
    min_fvg_atr_multiplier: float = 0.0
    min_volume_multiplier: float = 1.5
    require_volume_filter: bool = False


def _float(value: Any):
    try:
        result = float(value)
        return result if pd.notna(result) else None
    except (TypeError, ValueError):
        return None


def detect_fvg_confirmation(
    data: pd.DataFrame,
    direction: str,
    confirmation_index: int,
    config: FVGConfig | None = None,
    zone_low: float | None = None,
    zone_high: float | None = None,
    choch_indices: list[int] | None = None,
    choch_window: int | None = None,
) -> dict[str, Any]:
    """Busca el Fair Value Gap más reciente y relevante hasta `confirmation_index`.

    Proceso: recorre hacia atrás (desde `confirmation_index` hasta
    `lookback` velas antes) buscando un imbalance de 3 velas alineado con
    `direction` (alcista si `direction` es "long"/"buy", bajista si no). Se
    queda con el más reciente que:
    1. no supere `max_age_candles` de antigüedad respecto a la vela de
       confirmación;
    2. no esté ya completamente relleno por velas posteriores a su formación
       (y anteriores a `confirmation_index`);
    3. si `require_alignment_with_zone` está activo, se solape con
       `[zone_low, zone_high]` (el Order Block del setup).

    Args:
        data: DataFrame con columnas `high`, `low`, `time`.
        direction: `"long"`/`"buy"` o `"short"`/`"sell"`.
        confirmation_index: índice de la vela de confirmación evaluada.
        config: parámetros; si es `None` usa los de fábrica.
        zone_low: límite inferior del Order Block del setup (opcional).
        zone_high: límite superior del Order Block del setup (opcional).

    Returns:
        Dict con `fvg_enabled`, `fvg_confirmed`, `fvg_direction`,
        `fvg_low`, `fvg_high`, `fvg_index`, `fvg_age_candles`,
        `fvg_filled`, `fvg_rejection_reason`.

    Vinculaciones:
    - La llama `strategy.smc.confirmation_engine.evaluate_m5_confirmation`,
      que usa `fvg_confirmed` para sumar el bonus y, si `require_pattern`
      está activo, para rechazar la entrada.
    """
    result: dict[str, Any] = {
        "fvg_enabled": bool(config.enabled) if config else True,
        "fvg_confirmed": False,
        "fvg_direction": None,
        "fvg_low": None,
        "fvg_high": None,
        "fvg_index": None,
        "fvg_age_candles": None,
        "fvg_filled": False,
        "fvg_rejection_reason": None,
    }
    config = config or FVGConfig()
    result["fvg_enabled"] = bool(config.enabled)
    if not config.enabled:
        result["fvg_rejection_reason"] = "FVG_DISABLED"
        return result

    normalized_direction = "bullish" if str(direction).lower() in {"long", "buy", "bullish"} else "bearish"
    start = max(2, confirmation_index - max(1, int(config.lookback)))

    from strategy.smc.vectorized_smc import fast_compute_rolling_atr14, _check_fvg_filled

    highs_arr = data["high"].to_numpy(dtype=float) if "high" in data.columns else np.zeros(len(data))
    lows_arr = data["low"].to_numpy(dtype=float) if "low" in data.columns else np.zeros(len(data))
    closes_arr = data["close"].to_numpy(dtype=float) if "close" in data.columns else (highs_arr + lows_arr) / 2.0
    opens_arr = data["open"].to_numpy(dtype=float) if "open" in data.columns else closes_arr
    atr_arr = fast_compute_rolling_atr14(highs_arr, lows_arr, closes_arr, period=14) if "close" in data.columns else np.zeros(len(data))

    vol_col = "volume" if "volume" in data.columns else ("tick_volume" if "tick_volume" in data.columns else None)
    vols_arr = data[vol_col].to_numpy(dtype=float) if vol_col else None

    # Recorre de la vela más reciente hacia atrás para quedarse con el gap
    # más próximo a la confirmación (el más relevante para la entrada actual).
    for i in range(confirmation_index, start - 1, -1):
        # The actual CHoCH must be the middle or final candle of this gap.
        if choch_indices is not None:
            associated = any((j in (i-1, i) if choch_window is None else
                              j-choch_window <= i-2 and i <= j+choch_window)
                             for j in choch_indices)
            if not associated:
                continue
        if i < 2 or i >= len(data):
            continue

        left_high = highs_arr[i - 2]
        left_low = lows_arr[i - 2]
        cur_high = highs_arr[i]
        cur_low = lows_arr[i]

        if np.isnan(left_high) or np.isnan(left_low) or np.isnan(cur_high) or np.isnan(cur_low):
            continue

        # Normalización de mecha de spike para Crash Index (salto discreto de cotización)
        if config and config.is_crash:
            left_close, left_open = closes_arr[i - 2], opens_arr[i - 2]
            if not np.isnan(left_close) and not np.isnan(left_open):
                left_low = max(left_low, min(left_open, left_close))

        gap_direction = None
        gap_low = gap_high = None
        if cur_low > left_high:
            gap_direction = "bullish"
            gap_low, gap_high = left_high, cur_low
        elif cur_high < left_low:
            gap_direction = "bearish"
            gap_low, gap_high = cur_high, left_low
        if gap_direction is None or gap_direction != normalized_direction:
            continue

        # Filtro de desplazamiento mínimo: la vela intermedia debe superar 1.5x ATR(14)
        mid_high = highs_arr[i - 1]
        mid_low = lows_arr[i - 1]
        mid_range = max(mid_high - mid_low, 0.0) if (not np.isnan(mid_high) and not np.isnan(mid_low)) else 0.0

        min_mult = float(getattr(config, "min_displacement_atr_multiplier", 1.5) or 0.0)
        atr_14 = float(atr_arr[i - 1]) if (i - 1 < len(atr_arr) and not np.isnan(atr_arr[i - 1])) else 0.0

        if min_mult > 0.0 and atr_14 > 1e-9:
            if mid_range < (min_mult * atr_14) - 1e-9:
                continue

        # Filtro de Imbalance Strength (LuxAlgo): FVG size >= 1.2 * ATR(14)
        gap_size = max(0.0, float(gap_high - gap_low)) if (gap_high is not None and gap_low is not None) else 0.0
        min_fvg_mult = float(getattr(config, "min_fvg_atr_multiplier", 1.2) or 0.0)
        if min_fvg_mult > 0.0 and atr_14 > 1e-9:
            if gap_size < (min_fvg_mult * atr_14) - 1e-9:
                continue

        # Filtro de Volumen de Desplazamiento Institucional: Volumen de vela intermedia > 1.5 * Media(20)
        min_vol_mult = float(getattr(config, "min_volume_multiplier", 1.5) or 0.0)
        vol_ratio = 1.0
        if getattr(config, "require_volume_filter", True) and vols_arr is not None and min_vol_mult > 0.0 and i >= 22:
            prior_vol = vols_arr[max(0, i - 21):i - 1]
            if len(prior_vol) >= 10 and float(np.std(prior_vol)) > 1e-6:
                mean_vol_20 = float(np.mean(prior_vol[-20:]))
                mid_vol = vols_arr[i - 1]
                if not np.isnan(mid_vol) and mean_vol_20 > 1e-9:
                    vol_ratio = mid_vol / mean_vol_20
                    if mid_vol <= (min_vol_mult * mean_vol_20):
                        continue

        age_candles = confirmation_index - i
        if age_candles > max(0, int(config.max_age_candles)):
            continue

        if config.require_alignment_with_zone and zone_low is not None and zone_high is not None:
            if gap_high < zone_low or gap_low > zone_high:
                continue

        # Un FVG ya completamente relleno antes de la vela de confirmación
        # perdió su función de imán de precio: no aporta como confluencia.
        is_bull = (gap_direction == "bullish")
        filled = _check_fvg_filled(lows_arr, highs_arr, i + 1, confirmation_index, is_bull, gap_low, gap_high)
        if filled:
            continue

        result.update({
            "fvg_confirmed": True,
            "fvg_direction": gap_direction,
            "fvg_low": gap_low,
            "fvg_high": gap_high,
            "fvg_index": i,
            "fvg_age_candles": age_candles,
            "fvg_filled": False,
            "fvg_displacement_range": mid_range,
            "fvg_gap_size": gap_size,
            "fvg_atr_14": atr_14,
            "fvg_size_ratio": (gap_size / atr_14) if atr_14 > 1e-9 else 0.0,
            "fvg_volume_ratio": vol_ratio,
            "fvg_displacement_ratio": (mid_range / atr_14) if atr_14 > 1e-9 else 0.0,
            "fvg_rejection_reason": None,
        })
        return result


    result["fvg_rejection_reason"] = "NO_ALIGNED_FVG_FOUND"
    return result
