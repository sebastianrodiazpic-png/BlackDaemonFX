"""Confirmación de convicción de entrada por volumen de la vela M5.

Compara el volumen de la vela de confirmación (la misma que evalúa
`strategy.smc.confirmation_engine.evaluate_m5_confirmation`) contra el
promedio de las `lookback` velas previas. Una vela de confirmación con poco
volumen relativo sugiere baja participación real y mayor probabilidad de
trampa de liquidez; con volumen alto (`spike_multiplier` veces el promedio)
sugiere convicción institucional genuina detrás del movimiento.

Este es el mismo criterio que ya usaba `strategy.orb.new_york_orb` para la
vela de ruptura del Opening Range (`_breakout_volume_confirmed`,
`require_breakout_volume_confirmation`), ahora extendido como confluencia
del motor SMC compartido (Sintéticos/Forex/Gold) siguiendo el patrón de
`fair_value_gap.py`/`round_number_levels.py`: un detector puro + config
inmutable + integración por `confirmation_engine`.

A diferencia de esas confluencias opcionales, esta se activa OBLIGATORIA
(`require_pattern=True`) por defecto en las cuatro estrategias (ver
`strategy.execution.live_trading_engine.LiveTradingConfig.require_volume_confirmation`),
por decisión explícita: sin participación de volumen medible, la entrada se
rechaza salvo que el símbolo no publique volumen fiable (ver
`volume_reliable` más abajo).

Cómo desactivarla (documentado también en el propio campo de config):
- Por perfil de bot: `LiveTradingConfig.volume_confirmation_enabled=False`
  o `require_volume_confirmation=False` (deja de ser un gate, pasa a ser
  solo un bonus de score informativo).
- Ver `strategy.execution.live_trading_engine.LiveTradingConfig` y
  `strategy.execution.trade_pipeline.PipelineConfig` para los campos
  `volume_confirmation_*` expuestos por perfil.

Vinculaciones:
- Lo importa `strategy.smc.confirmation_engine`, que llama a
  `detect_volume_confirmation` y usa `volume_confirmed` tanto para el bonus
  de score como, si `require_pattern` está activo, como gate de rechazo.
- Reutiliza `strategy.smc.volume_utils.select_volume_column` /
  `has_reliable_volume`, compartido con `strategy.orb.new_york_orb`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategy.smc.volume_utils import has_reliable_volume, select_volume_column


@dataclass(frozen=True)
class VolumeConfirmationConfig:
    """Parámetros de confirmación por volumen. Inmutable para reproducibilidad.

    Campos:
    - `enabled`: si es False el detector devuelve la estructura vacía
      (`volume_confirmed=False`, `volume_rejection_reason="VOLUME_CONFIRMATION_DISABLED"`)
      y no participa ni como bonus ni como gate.
    - `lookback`: cuántas velas previas a la de confirmación se usan como
      referencia de volumen "normal".
    - `spike_multiplier`: la vela de confirmación debe alcanzar al menos
      `promedio_referencia * spike_multiplier` para considerarse respaldada
      por volumen. 1.0 = igual al promedio; valores > 1.0 exigen un repunte.
    - `bonus_points`: puntos que suma al score si está confirmado (aplica
      siempre que `enabled=True`, sea o no obligatorio).
    - `require_pattern`: si es True (por defecto), su ausencia rechaza la
      entrada como fallo estructural. Si es False, es confluencia opcional
      (solo bonus, no bloquea).
    - `skip_gate_without_reliable_volume`: si es True (recomendado y valor
      por defecto), cuando el símbolo/broker no publica ninguna columna de
      volumen real (`real_volume`/`tick_volume`/`volume` con suma > 0) el
      gate NO rechaza la entrada (se marca `volume_reliable=False` y se
      omite el requisito), para no penalizar símbolos sintéticos o brokers
      que no reportan volumen. El bonus tampoco se otorga en ese caso.
    """
    enabled: bool = True
    lookback: int = 20
    spike_multiplier: float = 1.0
    bonus_points: float = 5.0
    require_pattern: bool = True
    skip_gate_without_reliable_volume: bool = True


def detect_volume_confirmation(
    data: pd.DataFrame,
    confirmation_index: int,
    config: VolumeConfirmationConfig | None = None,
) -> dict[str, Any]:
    """Evalúa si la vela de confirmación tiene respaldo de volumen suficiente.

    Proceso:
    1. Si está deshabilitado, devuelve la estructura vacía.
    2. Resuelve la mejor columna de volumen disponible
       (`strategy.smc.volume_utils.select_volume_column`).
    3. Si el símbolo no publica volumen fiable
       (`strategy.smc.volume_utils.has_reliable_volume` es False), marca
       `volume_reliable=False` y, según `skip_gate_without_reliable_volume`,
       no rechaza por este motivo (el llamador debe respetar
       `volume_confirmed=False` sin sumarlo a fallos obligatorios cuando
       `volume_reliable` es False y `skip_gate_without_reliable_volume=True`).
    4. Compara el volumen de la vela de confirmación contra el promedio de
       las `lookback` velas previas.

    Args:
        data: DataFrame con OHLC y alguna columna de volumen.
        confirmation_index: índice de la vela de confirmación evaluada.
        config: parámetros; si es `None` usa los de fábrica.

    Returns:
        Dict con `volume_confirmation_enabled`, `volume_confirmed`,
        `volume_reliable`, `volume_value`, `volume_reference_avg`,
        `volume_ratio`, `volume_rejection_reason`.

    Vinculaciones:
    - La llama `strategy.smc.confirmation_engine.evaluate_m5_confirmation`.
    """
    config = config or VolumeConfirmationConfig()
    result: dict[str, Any] = {
        "volume_confirmation_enabled": bool(config.enabled),
        "volume_confirmed": False,
        "volume_reliable": False,
        "volume_value": None,
        "volume_reference_avg": None,
        "volume_ratio": None,
        "volume_rejection_reason": None,
    }
    if not config.enabled:
        result["volume_rejection_reason"] = "VOLUME_CONFIRMATION_DISABLED"
        return result

    if confirmation_index < 0 or confirmation_index >= len(data):
        result["volume_rejection_reason"] = "INVALID_CONFIRMATION_INDEX"
        return result

    reliable = has_reliable_volume(data)
    result["volume_reliable"] = reliable
    if not reliable:
        result["volume_rejection_reason"] = "NO_RELIABLE_VOLUME_DATA"
        return result

    volume = select_volume_column(data)
    lookback = max(1, int(config.lookback))
    start = max(0, confirmation_index - lookback)
    reference = volume.iloc[start:confirmation_index]
    if reference.empty:
        result["volume_rejection_reason"] = "INSUFFICIENT_VOLUME_HISTORY"
        return result

    current_volume = float(volume.iloc[confirmation_index])
    reference_avg = float(reference.mean())
    result["volume_value"] = current_volume
    result["volume_reference_avg"] = reference_avg

    if reference_avg <= 0:
        result["volume_rejection_reason"] = "ZERO_REFERENCE_VOLUME"
        return result

    ratio = current_volume / reference_avg
    result["volume_ratio"] = ratio

    if ratio >= max(0.0, float(config.spike_multiplier)):
        result["volume_confirmed"] = True
    else:
        result["volume_rejection_reason"] = "VOLUME_BELOW_REQUIRED_MULTIPLE"
    return result
