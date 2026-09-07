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

    # Recorre de la vela más reciente hacia atrás para quedarse con el gap
    # más próximo a la confirmación (el más relevante para la entrada actual).
    for i in range(confirmation_index, start - 1, -1):
        if i < 2 or i >= len(data):
            continue
        left = data.iloc[i - 2]
        current = data.iloc[i]
        left_high, left_low = _float(left.get("high")), _float(left.get("low"))
        cur_high, cur_low = _float(current.get("high")), _float(current.get("low"))
        if None in (left_high, left_low, cur_high, cur_low):
            continue

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

        age_candles = confirmation_index - i
        if age_candles > max(0, int(config.max_age_candles)):
            continue

        if config.require_alignment_with_zone and zone_low is not None and zone_high is not None:
            if gap_high < zone_low or gap_low > zone_high:
                continue

        # Un FVG ya completamente relleno antes de la vela de confirmación
        # perdió su función de imán de precio: no aporta como confluencia.
        filled = False
        future = data.iloc[i + 1:confirmation_index]
        for _, row in future.iterrows():
            row_low, row_high = _float(row.get("low")), _float(row.get("high"))
            if row_low is None or row_high is None:
                continue
            if gap_direction == "bullish" and row_low <= gap_low:
                filled = True
                break
            if gap_direction == "bearish" and row_high >= gap_high:
                filled = True
                break
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
            "fvg_rejection_reason": None,
        })
        return result

    result["fvg_rejection_reason"] = "NO_ALIGNED_FVG_FOUND"
    return result
