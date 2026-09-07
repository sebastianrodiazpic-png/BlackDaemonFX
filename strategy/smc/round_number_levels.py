"""Detección de confluencia con niveles psicológicos redondos.

En XAUUSD (oro) los múltiplos de $50/$100 (2050, 2100, 2650, 2700, ...)
funcionan como imanes de precio y zonas de reacción, algo documentado
extensamente en la literatura SMC/ICT específica para gold pero que hasta
ahora no tenía ninguna representación en el motor de decisión del proyecto.

Este módulo agrega esa confluencia como bonus de score opcional (igual
patrón que `fair_value_gap.py`/`harmonic_patterns.py`): NO es un gate, solo
suma puntos cuando el precio de entrada (o el TP más cercano) cae dentro de
una tolerancia del Order Block respecto de un nivel redondo.

Vinculaciones:
- Lo importa `strategy.smc.confirmation_engine`, que llama a
  `detect_round_number_confirmation` y suma `round_number_bonus_points` al
  score si hay coincidencia.
- La configuración llega desde
  `strategy.execution.trade_pipeline.PipelineConfig` (campos
  `round_number_*`); por defecto está deshabilitado salvo que el perfil GOLD
  lo active explícitamente en `LiveTradingEngine`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RoundNumberConfig:
    """Parámetros de detección de niveles psicológicos redondos.

    Campos:
    - `enabled`: si es False el detector devuelve la estructura vacía.
    - `increment`: distancia entre niveles redondos consecutivos (50.0 para
      oro es el estándar más citado; también se usan múltiplos de 100).
    - `tolerance_price`: distancia máxima en precio entre el nivel del setup
      (OB) y el múltiplo redondo más cercano para considerarlo "alineado".
    - `bonus_points`: puntos que aporta al score si hay alineación.
    - `require_pattern`: si es True, su ausencia rechaza la entrada (por
      defecto False: es confluencia opcional).
    """
    enabled: bool = False
    increment: float = 50.0
    tolerance_price: float = 2.0
    bonus_points: float = 4.0
    require_pattern: bool = False


def _nearest_round_number(price: float, increment: float) -> float:
    if increment <= 0:
        return price
    return round(price / increment) * increment


def detect_round_number_confirmation(
    zone_low: float | None,
    zone_high: float | None,
    config: RoundNumberConfig | None = None,
) -> dict[str, Any]:
    """Evalúa si el Order Block del setup está alineado con un nivel redondo.

    Proceso: toma el punto medio de `[zone_low, zone_high]` (el Order Block
    del setup) y busca el múltiplo de `config.increment` más cercano. Si la
    distancia es menor o igual a `config.tolerance_price`, se considera
    confirmado.

    Args:
        zone_low: límite inferior del Order Block del setup.
        zone_high: límite superior del Order Block del setup.
        config: parámetros; si es `None` usa los de fábrica (desactivado).

    Returns:
        Dict con `round_number_enabled`, `round_number_confirmed`,
        `round_number_level`, `round_number_distance`,
        `round_number_rejection_reason`.

    Vinculaciones:
    - La llama `strategy.smc.confirmation_engine.evaluate_m5_confirmation`,
      que usa `round_number_confirmed` para sumar el bonus y, si
      `require_pattern` está activo, para rechazar la entrada.
    """
    config = config or RoundNumberConfig()
    result: dict[str, Any] = {
        "round_number_enabled": bool(config.enabled),
        "round_number_confirmed": False,
        "round_number_level": None,
        "round_number_distance": None,
        "round_number_rejection_reason": None,
    }
    if not config.enabled:
        result["round_number_rejection_reason"] = "ROUND_NUMBER_DISABLED"
        return result
    if zone_low is None or zone_high is None:
        result["round_number_rejection_reason"] = "MISSING_ZONE"
        return result

    midpoint = (float(zone_low) + float(zone_high)) / 2.0
    level = _nearest_round_number(midpoint, float(config.increment))
    distance = abs(midpoint - level)
    result["round_number_level"] = level
    result["round_number_distance"] = distance

    if distance <= float(config.tolerance_price):
        result["round_number_confirmed"] = True
    else:
        result["round_number_rejection_reason"] = "NO_ROUND_NUMBER_NEARBY"
    return result
