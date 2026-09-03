"""Motor de confirmación M5 para DaemonBlackFx.

El objetivo es evitar entradas por un simple toque del Order Block. La señal se
valida con rechazo, desplazamiento, micro estructura, momentum, frescura del OB
y un score explicable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategy.smc.harmonic_patterns import HarmonicConfig, detect_harmonic_confirmation
from strategy.smc.chart_patterns import ChartPatternConfig, detect_chart_pattern_confirmation


@dataclass(frozen=True)
class M5ConfirmationConfig:
    minimum_trade_score: float = 85.0
    require_rejection: bool = True
    require_displacement: bool = True
    require_micro_confirmation: bool = True
    require_momentum: bool = False
    minimum_body_ratio: float = 0.65
    minimum_rejection_wick_ratio: float = 0.30
    displacement_range_multiplier: float = 1.35
    momentum_range_multiplier: float = 1.00
    range_lookback: int = 20
    max_ob_touches: int = 1
    confirmation_mode: str = "midpoint"  # inside | midpoint | break_ob
    max_confirmation_age_candles: int = 2
    require_strong_close: bool = True
    strong_close_fraction: float = 0.30
    harmonic_enabled: bool = True
    harmonic_tolerance: float = 0.10
    harmonic_minimum_score: float = 75.0
    harmonic_bonus_points: float = 10.0
    require_harmonic: bool = False
    # Modo adaptativo: una señal puede considerarse viable con al menos 80% de
    # las confirmaciones evaluadas, siempre que todas las confirmaciones críticas
    # de estructura/contexto estén presentes.
    adaptive_confirmation_enabled: bool = True
    minimum_confirmation_ratio: float = 0.80
    minimum_viable_trade_score: float = 75.0
    # Divergencia RSI como confluencia opcional de posible ruptura/cambio de estructura.
    divergence_enabled: bool = True
    divergence_rsi_period: int = 14
    divergence_lookback_candles: int = 80
    divergence_bonus_points: float = 5.0
    # v62: patrones chartistas como confluencia SMC opcional y auditable.
    chart_patterns_enabled: bool = True
    chart_patterns_lookback: int = 80
    chart_patterns_pivot_window: int = 2
    chart_patterns_price_tolerance: float = 0.006
    chart_patterns_volatility_adjusted_tolerance: bool = True
    chart_patterns_price_tolerance_range_multiplier: float = 1.50
    chart_patterns_minimum_price_tolerance: float = 0.00010
    chart_patterns_minimum_strength: float = 0.72
    chart_patterns_bonus_points: float = 8.0
    require_chart_pattern: bool = False
    chart_pattern_secondary_conflict_penalty: float = 10.0
    block_material_chart_pattern_conflict: bool = True
    # Patrones opuestos de fuerza similar reducen el score, pero no constituyen
    # por sí solos una invalidación estructural. Sólo domina un patrón contrario
    # ausente de apoyo o claramente más fuerte.
    block_similar_chart_pattern_forces: bool = False


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
        return value if pd.notna(value) else default
    except (TypeError, ValueError):
        return default


def candle_metrics(candle: pd.Series) -> dict[str, float]:
    high = _safe_float(candle.get("high"))
    low = _safe_float(candle.get("low"))
    open_ = _safe_float(candle.get("open"))
    close = _safe_float(candle.get("close"))
    total_range = max(high - low, 0.0)
    body = abs(close - open_)
    upper_wick = max(high - max(open_, close), 0.0)
    lower_wick = max(min(open_, close) - low, 0.0)
    return {
        "range": total_range,
        "body": body,
        "body_ratio": body / total_range if total_range > 0 else 0.0,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
        "upper_wick_ratio": upper_wick / total_range if total_range > 0 else 0.0,
        "lower_wick_ratio": lower_wick / total_range if total_range > 0 else 0.0,
    }


def _average_range(data: pd.DataFrame, index: int, lookback: int) -> float:
    start = max(0, index - max(1, lookback))
    window = data.iloc[start:index]
    if window.empty:
        return 0.0
    ranges = window["high"].astype(float) - window["low"].astype(float)
    return _safe_float(ranges.mean())


def _grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    return "REJECT"




def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    period = max(2, int(period))
    delta = close.astype(float).diff()
    gains = delta.clip(lower=0.0)
    losses = (-delta.clip(upper=0.0))
    avg_gain = gains.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, pd.NA)
    result = 100.0 - (100.0 / (1.0 + rs))
    return result.fillna(50.0)


def detect_rsi_divergence(
    data: pd.DataFrame,
    *,
    confirmation_index: int,
    direction: str,
    period: int = 14,
    lookback_candles: int = 80,
) -> dict[str, Any]:
    """Detecta divergencia regular entre precio y RSI usando pivotes SMC confirmados.

    LONG: último mínimo de precio es menor, pero RSI forma un mínimo mayor.
    SHORT: último máximo de precio es mayor, pero RSI forma un máximo menor.
    La divergencia no abre trades por sí sola; sólo aporta confluencia.
    """
    if confirmation_index <= 2 or data.empty:
        return {"divergence_detected": False, "divergence_type": None, "divergence_reason": "DATOS_INSUFICIENTES"}

    end = min(int(confirmation_index), len(data) - 1)
    start = max(0, end - max(10, int(lookback_candles)))
    window = data.iloc[start:end + 1].copy()
    rsi = _rsi(data["close"], period=period)

    pivot_column = "swing_low" if direction == "long" else "swing_high"
    if pivot_column not in data.columns:
        return {"divergence_detected": False, "divergence_type": None, "divergence_reason": "SIN_PIVOTES_SMC"}

    pivot_idx = [int(i) for i in window.index[window[pivot_column].fillna(False).astype(bool)] if int(i) < end]
    if len(pivot_idx) < 2:
        return {"divergence_detected": False, "divergence_type": None, "divergence_reason": "MENOS_DE_DOS_PIVOTES"}

    first_idx, second_idx = pivot_idx[-2], pivot_idx[-1]
    if direction == "long":
        price1 = _safe_float(data.loc[first_idx, "low"])
        price2 = _safe_float(data.loc[second_idx, "low"])
        rsi1 = _safe_float(rsi.loc[first_idx], 50.0)
        rsi2 = _safe_float(rsi.loc[second_idx], 50.0)
        detected = price2 < price1 and rsi2 > rsi1
        div_type = "DIVERGENCIA_ALCISTA_REGULAR" if detected else None
    else:
        price1 = _safe_float(data.loc[first_idx, "high"])
        price2 = _safe_float(data.loc[second_idx, "high"])
        rsi1 = _safe_float(rsi.loc[first_idx], 50.0)
        rsi2 = _safe_float(rsi.loc[second_idx], 50.0)
        detected = price2 > price1 and rsi2 < rsi1
        div_type = "DIVERGENCIA_BAJISTA_REGULAR" if detected else None

    return {
        "divergence_detected": bool(detected),
        "divergence_type": div_type,
        "divergence_reason": "DIVERGENCIA_PRECIO_RSI_CONFIRMADA" if detected else "SIN_DIVERGENCIA_REGULAR",
        "divergence_first_pivot_index": first_idx,
        "divergence_second_pivot_index": second_idx,
        "divergence_price_1": price1,
        "divergence_price_2": price2,
        "divergence_rsi_1": round(rsi1, 2),
        "divergence_rsi_2": round(rsi2, 2),
    }


def evaluate_m5_confirmation(
    *,
    data: pd.DataFrame,
    setup: pd.Series,
    retest_index: int,
    confirmation_index: int,
    direction: str,
    config: M5ConfirmationConfig | None = None,
) -> dict[str, Any]:
    """Evalúa una vela candidata y devuelve un diagnóstico completamente explicable."""
    config = config or M5ConfirmationConfig()
    direction = str(direction).lower()
    candle = data.iloc[confirmation_index]
    retest = data.iloc[retest_index]
    metrics = candle_metrics(candle)
    retest_metrics = candle_metrics(retest)

    ob_high = _safe_float(setup.get("ob_high"))
    ob_low = _safe_float(setup.get("ob_low"))
    if ob_low > ob_high:
        ob_low, ob_high = ob_high, ob_low
    midpoint = (ob_high + ob_low) / 2.0

    # Un OB se considera tocado cada vez que una vela intersecta su rango.
    setup_time = pd.to_datetime(setup.get("setup_time", setup.get("time")), utc=True)
    setup_positions = data.index[data["time"] == setup_time]
    start_index = int(setup_positions[0]) + 1 if len(setup_positions) else 0
    touch_window = data.iloc[start_index:retest_index + 1]
    touches = int(((touch_window["low"].astype(float) <= ob_high) & (touch_window["high"].astype(float) >= ob_low)).sum())
    fresh_ob = touches <= max(0, int(config.max_ob_touches))

    bullish = _safe_float(candle.get("close")) > _safe_float(candle.get("open"))
    bearish = _safe_float(candle.get("close")) < _safe_float(candle.get("open"))
    directional_candle = bullish if direction == "long" else bearish

    close_value = _safe_float(candle.get("close"))
    low_value = _safe_float(candle.get("low"))
    high_value = _safe_float(candle.get("high"))
    close_location = (
        (close_value - low_value) / metrics["range"]
        if metrics["range"] > 0 else 0.5
    )
    if direction == "long":
        strong_close = directional_candle and close_location >= (1.0 - float(config.strong_close_fraction))
    else:
        strong_close = directional_candle and close_location <= float(config.strong_close_fraction)

    if direction == "long":
        rejection = retest_metrics["lower_wick_ratio"] >= config.minimum_rejection_wick_ratio and _safe_float(retest.get("close")) >= ob_low
        respects_ob = _safe_float(candle.get("close")) >= ob_low
        mode_ok = {
            "inside": respects_ob,
            "midpoint": _safe_float(candle.get("close")) >= midpoint,
            "break_ob": _safe_float(candle.get("close")) > ob_high,
        }.get(str(config.confirmation_mode).lower(), False)
    else:
        rejection = retest_metrics["upper_wick_ratio"] >= config.minimum_rejection_wick_ratio and _safe_float(retest.get("close")) <= ob_high
        respects_ob = _safe_float(candle.get("close")) <= ob_high
        mode_ok = {
            "inside": respects_ob,
            "midpoint": _safe_float(candle.get("close")) <= midpoint,
            "break_ob": _safe_float(candle.get("close")) < ob_low,
        }.get(str(config.confirmation_mode).lower(), False)

    avg_range = _average_range(data, confirmation_index, config.range_lookback)
    displacement = (
        directional_candle
        and metrics["body_ratio"] >= config.minimum_body_ratio
        and (avg_range <= 0 or metrics["range"] >= avg_range * config.displacement_range_multiplier)
    )
    momentum = (
        directional_candle
        and metrics["body_ratio"] >= config.minimum_body_ratio
        and (avg_range <= 0 or metrics["range"] >= avg_range * config.momentum_range_multiplier)
    )

    # Micro estructura: cierre direccional por encima/debajo del máximo/mínimo
    # de las últimas dos velas cerradas, no solamente de la vela inmediatamente anterior.
    prior = data.iloc[max(0, confirmation_index - 2):confirmation_index]
    prior_high = _safe_float(prior["high"].max()) if not prior.empty else 0.0
    prior_low = _safe_float(prior["low"].min()) if not prior.empty else 0.0
    if direction == "long":
        micro_structure = directional_candle and _safe_float(candle.get("close")) > prior_high
    else:
        micro_structure = directional_candle and _safe_float(candle.get("close")) < prior_low

    divergence = (
        detect_rsi_divergence(
            data,
            confirmation_index=confirmation_index,
            direction=direction,
            period=config.divergence_rsi_period,
            lookback_candles=config.divergence_lookback_candles,
        )
        if config.divergence_enabled
        else {"divergence_detected": False, "divergence_type": None, "divergence_reason": "DESACTIVADA"}
    )
    # Una divergencia sólo se considera confirmación útil si el precio demuestra
    # intención hacia ruptura mediante desplazamiento o microestructura.
    divergence_structure_pressure = bool(
        divergence.get("divergence_detected") and (displacement or micro_structure)
    )

    harmonic = detect_harmonic_confirmation(
        data,
        direction,
        HarmonicConfig(
            enabled=config.harmonic_enabled,
            tolerance=config.harmonic_tolerance,
            minimum_pattern_score=config.harmonic_minimum_score,
            bonus_points=config.harmonic_bonus_points,
            require_pattern=config.require_harmonic,
            max_d_age_candles=config.max_confirmation_age_candles + 4,
        ),
        zone_low=ob_low,
        zone_high=ob_high,
        confirmation_index=confirmation_index,
    )

    chart_pattern = detect_chart_pattern_confirmation(
        data,
        direction,
        confirmation_index,
        ChartPatternConfig(
            enabled=config.chart_patterns_enabled,
            lookback=config.chart_patterns_lookback,
            pivot_window=config.chart_patterns_pivot_window,
            price_tolerance=config.chart_patterns_price_tolerance,
            volatility_adjusted_tolerance=config.chart_patterns_volatility_adjusted_tolerance,
            price_tolerance_range_multiplier=config.chart_patterns_price_tolerance_range_multiplier,
            minimum_price_tolerance=config.chart_patterns_minimum_price_tolerance,
            minimum_strength=config.chart_patterns_minimum_strength,
            bonus_points=config.chart_patterns_bonus_points,
            require_pattern=config.require_chart_pattern,
        ),
    )

    context = {
        "h1_trend": bool(setup.get("trend_ok", False)),
        "m15_setup": True,
        "liquidity_sweep": bool(setup.get("sweep_ok", False)),
        "m15_structure": bool(setup.get("structure_break_ok", False)),
        "premium_discount": bool(setup.get("premium_discount_ok", False)),
        "fresh_order_block": fresh_ob,
        "clean_retest": True,
        "rejection": rejection,
        "displacement": displacement,
        "micro_structure": micro_structure,
        "momentum": momentum,
        "strong_close": strong_close,
        "directional_candle": directional_candle,
        "confirmation_mode_ok": mode_ok,
        "harmonic_confirmation": bool(harmonic["harmonic_confirmed"]),
        "divergence_confirmation": divergence_structure_pressure,
        "chart_pattern_confirmation": bool(chart_pattern["chart_pattern_confirmed"]),
    }

    weights = {
        "h1_trend": 15, "m15_setup": 15, "liquidity_sweep": 10,
        "m15_structure": 10, "premium_discount": 10, "fresh_order_block": 10,
        "clean_retest": 5, "rejection": 5, "displacement": 10,
        "micro_structure": 10, "momentum": 5, "strong_close": 5,
    }
    raw_score = float(sum(weights[key] for key, ok in context.items() if key in weights and ok))
    if harmonic["harmonic_confirmed"]:
        raw_score += float(config.harmonic_bonus_points)
    if divergence_structure_pressure:
        raw_score += float(config.divergence_bonus_points)
    if chart_pattern["chart_pattern_confirmed"]:
        raw_score += float(config.chart_patterns_bonus_points)

    conflict_level = str(chart_pattern.get("chart_pattern_conflict_level") or "NONE").upper()
    material_conflict_levels = {"DOMINANT_CONTRA", "CONTRA_MAS_FUERTE"}
    if bool(config.block_similar_chart_pattern_forces):
        material_conflict_levels.add("FUERZAS_SIMILARES")
    chart_conflict_blocked = bool(
        config.block_material_chart_pattern_conflict
        and chart_pattern.get("chart_pattern_conflict")
        and conflict_level in material_conflict_levels
    )
    chart_conflict_penalty = (
        float(config.chart_pattern_secondary_conflict_penalty)
        if chart_pattern.get("chart_pattern_conflict") and not chart_conflict_blocked
        else 0.0
    )
    raw_score = max(0.0, raw_score - chart_conflict_penalty)

    # v41: el score visible vuelve a ser una escala 0-100. Las confluencias
    # adicionales ya no pueden producir A+ de 105/110 ni compensar un gate crítico.
    score = min(100.0, raw_score)

    # El porcentaje de confirmación es distinto al trade_score ponderado.
    # Sólo se cuentan condiciones que realmente forman parte del análisis activo.
    evaluated_keys = [
        "h1_trend", "m15_setup", "liquidity_sweep", "m15_structure",
        "premium_discount", "fresh_order_block", "clean_retest",
        "rejection", "displacement", "micro_structure", "strong_close",
        "directional_candle", "confirmation_mode_ok",
    ]
    if config.require_momentum:
        evaluated_keys.append("momentum")
    # Un armónico opcional aporta bonus cuando existe; su ausencia no debe
    # degradar el porcentaje adaptativo ni convertir 11/13 en 11/14.
    if config.harmonic_enabled and config.require_harmonic:
        evaluated_keys.append("harmonic_confirmation")
    # v62: chart-pattern confluence is intentionally not appended to
    # evaluated_keys unless explicitly required; absence never penalizes legacy SMC.
    if config.require_chart_pattern:
        evaluated_keys.append("chart_pattern_confirmation")

    passed_keys = [key for key in evaluated_keys if bool(context.get(key, False))]
    failed_keys = [key for key in evaluated_keys if not bool(context.get(key, False))]
    confirmation_ratio = (len(passed_keys) / len(evaluated_keys)) if evaluated_keys else 0.0
    confirmation_percentage = confirmation_ratio * 100.0

    # Estas condiciones no se pueden compensar con un porcentaje alto.
    # Si falla la estructura/contexto SMC, la entrada no es viable aunque alcance 80%.
    critical_keys = [
        "h1_trend", "m15_setup", "liquidity_sweep", "m15_structure",
        "premium_discount", "fresh_order_block", "clean_retest",
        "directional_candle", "confirmation_mode_ok",
    ]
    critical_failures = [key for key in critical_keys if not bool(context.get(key, False))]

    # v41: gates estructurales dependientes del tipo de ruptura M15.
    # Un porcentaje adaptativo alto ya NO puede compensar estos faltantes.
    structure_break_type = str(setup.get("structure_break_type") or "").lower()
    structural_gate_failures = []
    if "bos" in structure_break_type and not rejection:
        structural_gate_failures.append("BOS_REQUIRES_REJECTION")
    if "choch" in structure_break_type and not micro_structure:
        structural_gate_failures.append("CHOCH_REQUIRES_MICRO_STRUCTURE")
    # v84: el modo adaptativo tampoco puede compensar falta de desplazamiento.
    if config.require_displacement and not displacement:
        structural_gate_failures.append("DISPLACEMENT_REQUIRED_FOR_LIVE_ENTRY")
    if chart_conflict_blocked:
        structural_gate_failures.append("MATERIAL_CHART_PATTERN_CONFLICT")
    critical_failures.extend(structural_gate_failures)

    required_failures = []
    if "BOS_REQUIRES_REJECTION" in structural_gate_failures:
        required_failures.append("BOS_REJECTION_NOT_CONFIRMED")
    if "CHOCH_REQUIRES_MICRO_STRUCTURE" in structural_gate_failures:
        required_failures.append("CHOCH_MICRO_STRUCTURE_NOT_CONFIRMED")
    if "DISPLACEMENT_REQUIRED_FOR_LIVE_ENTRY" in structural_gate_failures:
        required_failures.append("DISPLACEMENT_NOT_CONFIRMED")
    if "MATERIAL_CHART_PATTERN_CONFLICT" in structural_gate_failures:
        required_failures.append("CHART_PATTERN_CONFLICT_BLOCKED")
    if not fresh_ob:
        required_failures.append("ORDER_BLOCK_NOT_FRESH")
    if not mode_ok:
        required_failures.append("CONFIRMATION_MODE_NOT_SATISFIED")
    if config.require_rejection and not rejection:
        required_failures.append("REJECTION_NOT_CONFIRMED")
    if config.require_displacement and not displacement:
        required_failures.append("DISPLACEMENT_NOT_CONFIRMED")
    if config.require_micro_confirmation and not micro_structure:
        required_failures.append("MICRO_STRUCTURE_NOT_CONFIRMED")
    if config.require_momentum and not momentum:
        required_failures.append("MOMENTUM_NOT_CONFIRMED")
    if config.require_strong_close and not strong_close:
        required_failures.append("STRONG_CLOSE_NOT_CONFIRMED")
    if config.require_harmonic and not harmonic["harmonic_confirmed"]:
        required_failures.append("HARMONIC_PATTERN_NOT_CONFIRMED")
    if score < float(config.minimum_trade_score):
        required_failures.append("INSUFFICIENT_TRADE_SCORE")

    strict_valid = (not required_failures) and (not critical_failures)
    adaptive_viable = bool(
        config.adaptive_confirmation_enabled
        and not critical_failures
        and confirmation_ratio >= float(config.minimum_confirmation_ratio)
        and score >= float(config.minimum_viable_trade_score)
    )
    confirmation_valid = strict_valid or adaptive_viable

    if strict_valid:
        decision = "STRICT_CONFIRMED"
        final_reasons = []
    elif adaptive_viable:
        decision = f"ADAPTIVE_{int(round(float(config.minimum_confirmation_ratio) * 100))}_CONFIRMED"
        # Conservamos los faltantes como información, pero no como rechazo.
        final_reasons = []
    else:
        decision = "REJECTED"
        final_reasons = list(required_failures)
        if critical_failures:
            final_reasons.append("CRITICAL_CONFIRMATION_MISSING")
        if confirmation_ratio < float(config.minimum_confirmation_ratio):
            final_reasons.append("CONFIRMATION_PERCENTAGE_BELOW_THRESHOLD")
        if score < float(config.minimum_viable_trade_score):
            final_reasons.append("VIABLE_TRADE_SCORE_BELOW_THRESHOLD")
        final_reasons = list(dict.fromkeys(final_reasons))

    return {
        "trade_score": round(score, 2),
        "raw_trade_score": round(raw_score, 2),
        "chart_pattern_conflict_penalty": round(chart_conflict_penalty, 2),
        "chart_pattern_conflict_blocked": chart_conflict_blocked,
        "trade_grade": _grade(score),
        "structure_break_type": structure_break_type,
        "structural_gate_failures": structural_gate_failures,
        "confirmation_valid": confirmation_valid,
        "confirmation_decision": decision,
        "confirmation_percentage": round(confirmation_percentage, 2),
        "confirmations_passed": len(passed_keys),
        "confirmations_total": len(evaluated_keys),
        "passed_confirmations": passed_keys,
        "missing_confirmations": failed_keys,
        "critical_confirmations_ok": not critical_failures,
        "critical_confirmation_failures": critical_failures,
        "strict_rejection_reasons": required_failures,
        "rejection_reasons": final_reasons,
        "ob_touches": touches,
        "ob_fresh": fresh_ob,
        "confirmation_mode": config.confirmation_mode,
        "average_range": avg_range,
        "candle_range": metrics["range"],
        "body_ratio": metrics["body_ratio"],
        "close_location": close_location,
        "strong_close": strong_close,
        "lower_wick_ratio": metrics["lower_wick_ratio"],
        "upper_wick_ratio": metrics["upper_wick_ratio"],
        "prior_high": prior_high,
        "prior_low": prior_low,
        "confirmations": context,
        "divergence_enabled": bool(config.divergence_enabled),
        "divergence_confirmation": divergence_structure_pressure,
        "divergence_structure_pressure": divergence_structure_pressure,
        **divergence,
        **harmonic,
        **chart_pattern,
    }
