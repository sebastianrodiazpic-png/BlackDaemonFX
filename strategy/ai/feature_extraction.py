"""Extracción de características para el meta-etiquetado.

Todas las estrategias (SMC, ORB) se normalizan al mismo vector para que
un worker pueda entrenar y puntuar con una representación estable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import math


FEATURE_SCHEMA = "meta-features-v4"

FEATURE_NAMES: tuple[str, ...] = (
    "trade_score",
    "confirmation_percentage",
    "confirmations_ratio",
    "adx",
    "adx_normalized",
    "atr_ratio",
    "structure_aligned",
    "chart_pattern_strength",
    "chart_pattern_conflict",
    "chart_pattern_strength_delta",
    "signal_age_candles",
    "signal_age_minutes",
    "spread_ratio",
    "signal_open_age_seconds", "decision_delay_seconds", "decision_delay_available",
    "processing_seconds", "processing_available",
    "planned_rr",
    "risk_percent",
    "divergence_confirmed",
    "harmonic_confirmed",
    "h1_doji_confirmed",
    "exhaustion_reversal_confirmed",
    "orb_range_atr_ratio",
    "breakout_volume_ratio",
    "breakout_volume_available",
    "direction_buy",
    "critical_failures",
    "adx_available", "atr_available", "spread_available", "structure_available",
)


def _to_float(value: Any, default: float = 0.0) -> float:
    """Convierte cualquier valor a float seguro para el modelo.

    Blindaje imprescindible: un solo NaN o infinito en el vector de
    caracteristicas contamina el producto escalar y devuelve una
    probabilidad invalida. Los booleanos pasan a 1.0/0.0.

    Returns:
        El numero convertido, o `default` si el valor es nulo, no numerico,
        NaN o infinito.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def _available(value):
    try:
        return float(value is not None and math.isfinite(float(value)))
    except (TypeError, ValueError):
        return 0.0


def _unit_strength(value):
    """Accept native fractions and explicitly older percent-style values."""
    value = _to_float(value)
    return value / 100.0 if abs(value) > 1.0 else value


def _to_bool_float(value: Any) -> float:
    """Convierte un booleano —o su representación textual— a 1.0 / 0.0.

    Acepta cadenas en ingles y espanol (`true`, `1`, `yes`, `si`, `sí`)
    porque los flags llegan desde origenes heterogeneos: dicts del pipeline,
    JSON del journal y campos de configuracion.
    """
    if isinstance(value, str):
        return 1.0 if value.strip().lower() in {"true", "1", "yes", "si", "sí"} else 0.0
    return 1.0 if bool(value) else 0.0


def _first(*values, default=None):
    """Devuelve el primer valor presente, saltando `None` y cadenas vacías.

    Permite leer una misma caracteristica desde varias claves alternativas,
    ya que el nombre del campo varia segun la estrategia que genere la senal.

    ATENCION: el cero SI se considera presente, de modo que un valor
    legitimamente nulo no se sustituye por la alternativa.
    """
    for value in values:
        if value not in (None, ""):
            return value
    return default


def _structure_alignment(direction: str, structure_break: Any) -> float:
    """Mide si la estructura de mercado apoya o contradice la dirección.

    Traduce el texto del BOS/CHOCH (`bos_bullish`, `choch_bearish`, …) a un
    valor comparable entre estrategias. Es una de las caracteristicas mas
    informativas: recoge justo la contradiccion estructural que provoco el
    cierre prematuro que dio origen a este motor.

    Args:
        direction: `BUY` o `SELL`.
        structure_break: descripcion textual de la ruptura estructural.

    Returns:
        `1.0` si la estructura acompana, `-1.0` si contradice, `0.0` si es
        ambigua o falta el dato.

    Vinculaciones:
    - Alimenta la caracteristica `structure_alignment` de `FEATURE_NAMES`.
    - El texto lo produce `strategy.smc.choch_bos.detect_choch_bos`.
    """
    direction = str(direction or "").upper()
    text = str(structure_break or "").upper()
    if direction not in {"BUY", "SELL"} or not text:
        return 0.0
    bullish = any(token in text for token in ("BULLISH", "BUY", "UP"))
    bearish = any(token in text for token in ("BEARISH", "SELL", "DOWN"))
    if direction == "BUY":
        return 1.0 if bullish else -1.0 if bearish else 0.0
    return 1.0 if bearish else -1.0 if bullish else 0.0


def _signal_latency_seconds(signal: dict, evaluated_at: Any) -> float:
    """Segundos entre la confirmación de la señal y el momento de decisión."""
    reference = _first(
        signal.get("entry_time"),
        signal.get("signal_time"),
        signal.get("m5_confirmation_time"),
    )
    if reference is None:
        return 0.0
    try:
        signal_time = pd.to_datetime(reference, utc=True, errors="raise")
    except Exception:
        return 0.0
    try:
        if evaluated_at in (None, ""):
            now = pd.Timestamp(datetime.now(timezone.utc))
        else:
            now = pd.to_datetime(evaluated_at, utc=True, errors="raise")
    except Exception:
        now = pd.Timestamp(datetime.now(timezone.utc))
    return max(0.0, float((now - signal_time).total_seconds()))


def _elapsed(reference, evaluated_at):
    if reference is None or evaluated_at is None:
        return 0.0, 0.0
    try:
        seconds = (pd.to_datetime(evaluated_at, utc=True) - pd.to_datetime(reference, utc=True)).total_seconds()
        return (float(seconds), 1.0) if math.isfinite(seconds) and seconds >= 0 else (0.0, 0.0)
    except (ValueError, TypeError):
        return 0.0, 0.0


def extract_meta_features(
    *,
    signal: dict | None = None,
    analysis: dict | None = None,
    market: dict | None = None,
    evaluated_at: Any = None,
) -> dict[str, float]:
    """Construye el diccionario de características normalizadas de una señal."""
    signal = signal if isinstance(signal, dict) else {}
    analysis = analysis if isinstance(analysis, dict) else {}
    market = market if isinstance(market, dict) else {}

    diagnostics = analysis.get("diagnostics")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    signal_age = diagnostics.get("signal_age")
    signal_age = signal_age if isinstance(signal_age, dict) else {}

    confirmations = signal.get("confirmations")
    confirmations = confirmations if isinstance(confirmations, dict) else {}
    passed = sum(1 for value in confirmations.values() if bool(value))
    total = len(confirmations)
    confirmations_ratio = (passed / total) if total else 0.0

    critical = _first(
        signal.get("critical_confirmation_failures"),
        analysis.get("critical_confirmation_failures"),
        analysis.get("critical_failures"),
        default=[],
    )
    critical_count = float(len(critical)) if isinstance(critical, (list, tuple, set)) else 0.0

    exhaustion = _first(
        signal.get("exhaustion_reversal_shadow"),
        analysis.get("exhaustion_reversal_shadow"),
        default={},
    )
    exhaustion = exhaustion if isinstance(exhaustion, dict) else {}

    atr = _to_float(_first(signal.get("atr"), analysis.get("atr"), market.get("atr")))
    entry_price = _to_float(
        _first(signal.get("entry_price"), market.get("current_price"), market.get("entry_price"))
    )
    atr_ratio = (atr / entry_price) if entry_price > 0 and atr > 0 else 0.0

    spread_raw = market["spread"] if "spread" in market else signal.get("spread")
    spread = _to_float(spread_raw)
    spread_ratio = (spread / entry_price) if entry_price > 0 and spread > 0 else 0.0

    adx = _to_float(_first(signal.get("adx"), analysis.get("adx"), market.get("adx")))

    supporting = _unit_strength(
        _first(
            signal.get("chart_pattern_supporting_strength"),
            analysis.get("chart_pattern_supporting_strength"),
            signal.get("chart_pattern_strength"),
            analysis.get("chart_pattern_strength"),
        )
    )
    conflicting = _unit_strength(
        _first(
            signal.get("chart_pattern_conflicting_strength"),
            analysis.get("chart_pattern_conflicting_strength"),
        )
    )
    # El pipeline ya publica el delta calculado; se prefiere cuando existe.
    published_delta = _first(
        signal.get("chart_pattern_conflict_strength_delta"),
        analysis.get("chart_pattern_conflict_strength_delta"),
    )
    strength_delta = (
        _unit_strength(published_delta)
        if published_delta is not None
        else (supporting - conflicting)
    )

    features = {
        "trade_score": _to_float(_first(signal.get("trade_score"), analysis.get("trade_score"))) / 100.0,
        "confirmation_percentage": _to_float(
            _first(signal.get("confirmation_percentage"), analysis.get("confirmation_percentage"))
        ) / 100.0,
        "confirmations_ratio": float(confirmations_ratio),
        "adx": adx,
        "adx_normalized": min(adx / 50.0, 2.0) if adx > 0 else 0.0,
        "atr_ratio": atr_ratio,
        "adx_available": _available(_first(signal.get("adx"), analysis.get("adx"), market.get("adx"))),
        "atr_available": float(atr > 0),
        "spread_available": _available(spread_raw),
        "structure_available": float(_first(signal.get("m15_structure_break_type"), signal.get("structure_break"), analysis.get("structure_break")) is not None),
        "structure_aligned": _structure_alignment(
            _first(signal.get("direction"), analysis.get("direction")),
            _first(
                signal.get("m15_structure_break_type"),
                signal.get("structure_break"),
                analysis.get("structure_break"),
            ),
        ),
        "chart_pattern_strength": _unit_strength(
            _first(signal.get("chart_pattern_strength"), analysis.get("chart_pattern_strength"))
        ),
        "chart_pattern_conflict": _to_bool_float(
            _first(signal.get("chart_pattern_conflict"), analysis.get("chart_pattern_conflict"))
        ),
        "chart_pattern_strength_delta": strength_delta,
        "signal_age_candles": _to_float(signal_age.get("age_candles")),
        "signal_age_minutes": _to_float(signal_age.get("age_minutes")),
        "spread_ratio": spread_ratio,
        "signal_open_age_seconds": _signal_latency_seconds(signal, evaluated_at),
        "decision_delay_seconds": _elapsed(signal.get("confirmation_closed_at"), evaluated_at)[0],
        "decision_delay_available": _elapsed(signal.get("confirmation_closed_at"), evaluated_at)[1],
        "processing_seconds": _elapsed(signal.get("detected_at"), evaluated_at)[0],
        "processing_available": _elapsed(signal.get("detected_at"), evaluated_at)[1],
        "planned_rr": _to_float(
            _first(
                signal.get("risk_reward_ratio"),
                signal.get("risk_reward"),
                market.get("planned_rr"),
            )
        ),
        "risk_percent": _to_float(_first(market.get("risk_percent"), signal.get("risk_percent"))),
        "divergence_confirmed": _to_bool_float(
            _first(signal.get("divergence_confirmation"), analysis.get("divergence_confirmed"))
        ),
        "harmonic_confirmed": _to_bool_float(
            _first(signal.get("harmonic_confirmed"), analysis.get("harmonic_confirmed"))
        ),
        "h1_doji_confirmed": _to_bool_float(
            _first(signal.get("h1_doji_confirmation"), analysis.get("h1_doji_confirmed"))
        ),
        "exhaustion_reversal_confirmed": _to_bool_float(exhaustion.get("valid")),
        "orb_range_atr_ratio": _to_float(
            _first(
                signal.get("opening_range_atr_ratio"),
                analysis.get("opening_range_atr_ratio"),
                diagnostics.get("opening_range_atr_ratio"),
            )
        ),
        "breakout_volume_ratio": _to_float(
            _first(signal.get("breakout_volume_ratio"), analysis.get("breakout_volume_ratio"))
        ),
        "breakout_volume_available": float(math.isfinite(_to_float(_first(signal.get("breakout_volume_ratio"), analysis.get("breakout_volume_ratio")), float("nan")))),
        "direction_buy": 1.0 if str(_first(signal.get("direction"), analysis.get("direction"), default="")).upper() == "BUY" else 0.0,
        "critical_failures": critical_count,
    }
    return {name: float(features.get(name, 0.0)) for name in FEATURE_NAMES}


def feature_vector(features: dict[str, float]) -> list[float]:
    """Ordena un diccionario de características al vector canónico del modelo."""
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]
