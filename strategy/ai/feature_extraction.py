"""Extracción de características para el meta-etiquetado.

Todas las estrategias (SMC, ORB, ARPS) se normalizan al mismo vector para que
un worker pueda entrenar y puntuar con una representación estable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


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
    "latency_seconds",
    "planned_rr",
    "risk_percent",
    "divergence_confirmed",
    "harmonic_confirmed",
    "h1_doji_confirmed",
    "critical_failures",
)


def _to_float(value: Any, default: float = 0.0) -> float:
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


def _to_bool_float(value: Any) -> float:
    if isinstance(value, str):
        return 1.0 if value.strip().lower() in {"true", "1", "yes", "si", "sí"} else 0.0
    return 1.0 if bool(value) else 0.0


def _first(*values, default=None):
    for value in values:
        if value not in (None, ""):
            return value
    return default


def _structure_alignment(direction: str, structure_break: Any) -> float:
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

    atr = _to_float(_first(signal.get("atr"), analysis.get("atr"), market.get("atr")))
    entry_price = _to_float(
        _first(signal.get("entry_price"), market.get("current_price"), market.get("entry_price"))
    )
    atr_ratio = (atr / entry_price) if entry_price > 0 and atr > 0 else 0.0

    spread = _to_float(_first(market.get("spread"), signal.get("spread")))
    spread_ratio = (spread / entry_price) if entry_price > 0 and spread > 0 else 0.0

    adx = _to_float(_first(signal.get("adx"), analysis.get("adx"), market.get("adx")))

    supporting = _to_float(
        _first(
            signal.get("chart_pattern_supporting_strength"),
            analysis.get("chart_pattern_supporting_strength"),
            signal.get("chart_pattern_strength"),
            analysis.get("chart_pattern_strength"),
        )
    )
    conflicting = _to_float(
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
        _to_float(published_delta) / 100.0
        if published_delta is not None
        else (supporting - conflicting) / 100.0
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
        "structure_aligned": _structure_alignment(
            _first(signal.get("direction"), analysis.get("direction")),
            _first(
                signal.get("m15_structure_break_type"),
                signal.get("structure_break"),
                analysis.get("structure_break"),
            ),
        ),
        "chart_pattern_strength": _to_float(
            _first(signal.get("chart_pattern_strength"), analysis.get("chart_pattern_strength"))
        ) / 100.0,
        "chart_pattern_conflict": _to_bool_float(
            _first(signal.get("chart_pattern_conflict"), analysis.get("chart_pattern_conflict"))
        ),
        "chart_pattern_strength_delta": strength_delta,
        "signal_age_candles": _to_float(signal_age.get("age_candles")),
        "signal_age_minutes": _to_float(signal_age.get("age_minutes")),
        "spread_ratio": spread_ratio,
        "latency_seconds": _signal_latency_seconds(signal, evaluated_at),
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
        "critical_failures": critical_count,
    }
    return {name: float(features.get(name, 0.0)) for name in FEATURE_NAMES}


def feature_vector(features: dict[str, float]) -> list[float]:
    """Ordena un diccionario de características al vector canónico del modelo."""
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]
