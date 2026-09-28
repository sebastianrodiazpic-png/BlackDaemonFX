"""Detector SMC de reversión por agotamiento en premium/discount.

Esta ruta no sustituye la estrategia de continuación. Busca un barrido de
liquidez en un extremo del dealing range H1 y exige confirmación M5 posterior
mediante desplazamiento y ruptura de microestructura. Su salida es puramente
descriptiva: el motor decide si sólo auditarla (modo SHADOW) o, en una versión
futura validada, convertirla en señal ejecutable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ExhaustionReversalConfig:
    dealing_range_lookback: int = 50
    liquidity_lookback: int = 20
    premium_threshold: float = 0.75
    discount_threshold: float = 0.25
    minimum_rejection_wick_ratio: float = 0.45
    maximum_exhaustion_body_ratio: float = 0.35
    minimum_displacement_body_ratio: float = 0.65
    displacement_range_multiplier: float = 1.20
    strong_close_fraction: float = 0.30
    volume_climax_multiplier: float = 1.20
    require_volume_when_available: bool = True


def _number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
        return parsed if pd.notna(parsed) else default
    except (TypeError, ValueError):
        return default


def _metrics(candle: pd.Series) -> dict[str, float]:
    high = _number(candle.get("high"))
    low = _number(candle.get("low"))
    open_ = _number(candle.get("open"))
    close = _number(candle.get("close"))
    total_range = max(0.0, high - low)
    body = abs(close - open_)
    upper_wick = max(0.0, high - max(open_, close))
    lower_wick = max(0.0, min(open_, close) - low)
    return {
        "range": total_range,
        "body": body,
        "body_ratio": body / total_range if total_range else 0.0,
        "upper_wick_ratio": upper_wick / total_range if total_range else 0.0,
        "lower_wick_ratio": lower_wick / total_range if total_range else 0.0,
    }


def _time(value: Any) -> str | None:
    try:
        return pd.to_datetime(value, utc=True).isoformat()
    except (TypeError, ValueError):
        return None


def detect_exhaustion_reversal(
    h1_data: pd.DataFrame,
    m5_data: pd.DataFrame,
    *,
    symbol: str,
    allowed_direction: str | None = None,
    config: ExhaustionReversalConfig | None = None,
) -> dict:
    """Evalúa las dos últimas M5 cerradas: agotamiento y confirmación.

    SELL: barrido de máximo en premium, mecha superior y cierre M5 posterior
    bajo el mínimo del agotamiento con desplazamiento bajista.
    BUY: espejo de la regla sobre un mínimo en discount.
    """
    cfg = config or ExhaustionReversalConfig()
    base = {
        "strategy_name": "SMC_EXHAUSTION_REVERSAL",
        "mode": "SHADOW",
        "symbol": str(symbol),
        "valid": False,
        "action": "NO_EXHAUSTION_REVERSAL",
        "reason": "INSUFFICIENT_CANDLES",
        "direction": None,
    }
    if h1_data is None or m5_data is None or h1_data.empty or m5_data.empty:
        return base

    h1 = h1_data.sort_values("time").drop_duplicates("time").tail(
        max(2, int(cfg.dealing_range_lookback))
    )
    m5 = m5_data.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    minimum_m5 = max(4, int(cfg.liquidity_lookback) + 2)
    if len(h1) < 2 or len(m5) < minimum_m5:
        return base

    range_high = _number(h1["high"].max())
    range_low = _number(h1["low"].min())
    range_size = range_high - range_low
    if range_size <= 0:
        return {**base, "reason": "INVALID_H1_DEALING_RANGE"}

    premium_price = range_low + range_size * float(cfg.premium_threshold)
    discount_price = range_low + range_size * float(cfg.discount_threshold)
    exhaustion = m5.iloc[-2]
    confirmation = m5.iloc[-1]
    prior = m5.iloc[-(int(cfg.liquidity_lookback) + 2):-2]
    prior_high = _number(prior["high"].max())
    prior_low = _number(prior["low"].min())
    exhaustion_metrics = _metrics(exhaustion)
    confirmation_metrics = _metrics(confirmation)
    average_range = _number(
        (m5.iloc[-(int(cfg.liquidity_lookback) + 1):-1]["high"].astype(float)
         - m5.iloc[-(int(cfg.liquidity_lookback) + 1):-1]["low"].astype(float)).mean()
    )

    volume_column = next(
        (
            column for column in ("tick_volume", "real_volume", "volume")
            if column in m5.columns and _number(m5[column].astype(float).sum()) > 0
        ),
        None,
    )
    volume_applicable = volume_column is not None
    volume_ratio = None
    volume_climax = True
    if volume_applicable:
        reference_volume = _number(prior[volume_column].astype(float).mean())
        exhaustion_volume = _number(exhaustion.get(volume_column))
        volume_ratio = exhaustion_volume / reference_volume if reference_volume > 0 else 0.0
        volume_climax = volume_ratio >= float(cfg.volume_climax_multiplier)

    exhaustion_high = _number(exhaustion.get("high"))
    exhaustion_low = _number(exhaustion.get("low"))
    exhaustion_close = _number(exhaustion.get("close"))
    confirmation_open = _number(confirmation.get("open"))
    confirmation_close = _number(confirmation.get("close"))
    confirmation_high = _number(confirmation.get("high"))
    confirmation_low = _number(confirmation.get("low"))

    sell_checks = {
        "premium_zone": exhaustion_high >= premium_price,
        "liquidity_sweep": exhaustion_high > prior_high and exhaustion_close <= prior_high,
        "exhaustion_wick": exhaustion_metrics["upper_wick_ratio"] >= float(cfg.minimum_rejection_wick_ratio),
        "small_body": exhaustion_metrics["body_ratio"] <= float(cfg.maximum_exhaustion_body_ratio),
        "directional_confirmation": confirmation_close < confirmation_open,
        "micro_choch": confirmation_close < exhaustion_low,
        "displacement": (
            confirmation_close < confirmation_open
            and confirmation_metrics["body_ratio"] >= float(cfg.minimum_displacement_body_ratio)
            and (average_range <= 0 or confirmation_metrics["range"] >= average_range * float(cfg.displacement_range_multiplier))
        ),
        "strong_close": (
            confirmation_metrics["range"] > 0
            and (confirmation_close - confirmation_low) / confirmation_metrics["range"]
            <= float(cfg.strong_close_fraction)
        ),
        "volume_climax": volume_climax,
    }
    buy_checks = {
        "discount_zone": exhaustion_low <= discount_price,
        "liquidity_sweep": exhaustion_low < prior_low and exhaustion_close >= prior_low,
        "exhaustion_wick": exhaustion_metrics["lower_wick_ratio"] >= float(cfg.minimum_rejection_wick_ratio),
        "small_body": exhaustion_metrics["body_ratio"] <= float(cfg.maximum_exhaustion_body_ratio),
        "directional_confirmation": confirmation_close > confirmation_open,
        "micro_choch": confirmation_close > exhaustion_high,
        "displacement": (
            confirmation_close > confirmation_open
            and confirmation_metrics["body_ratio"] >= float(cfg.minimum_displacement_body_ratio)
            and (average_range <= 0 or confirmation_metrics["range"] >= average_range * float(cfg.displacement_range_multiplier))
        ),
        "strong_close": (
            confirmation_metrics["range"] > 0
            and (confirmation_high - confirmation_close) / confirmation_metrics["range"]
            <= float(cfg.strong_close_fraction)
        ),
        "volume_climax": volume_climax,
    }
    if not cfg.require_volume_when_available or not volume_applicable:
        sell_checks["volume_climax"] = True
        buy_checks["volume_climax"] = True

    direction = None
    checks = None
    if all(sell_checks.values()):
        direction, checks = "SELL", sell_checks
    elif all(buy_checks.values()):
        direction, checks = "BUY", buy_checks

    common = {
        "dealing_range": {
            "range_high": range_high,
            "range_low": range_low,
            "premium_price": premium_price,
            "equilibrium": (range_high + range_low) / 2.0,
            "discount_price": discount_price,
        },
        "exhaustion_time": _time(exhaustion.get("time")),
        "confirmation_time": _time(confirmation.get("time")),
        "volume_applicable": volume_applicable,
        "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
        "sell_checks": sell_checks,
        "buy_checks": buy_checks,
    }
    if direction is None:
        return {**base, **common, "reason": "EXHAUSTION_SEQUENCE_NOT_CONFIRMED"}

    normalized_allowed = str(allowed_direction or "").upper() or None
    if normalized_allowed and direction != normalized_allowed:
        return {
            **base,
            **common,
            "direction": direction,
            "reason": f"DIRECTION_POLICY_REQUIRES_{normalized_allowed}",
            "checks": checks,
            "direction_allowed": False,
        }

    stop_loss = exhaustion_high if direction == "SELL" else exhaustion_low
    entry_price = confirmation_close
    risk_distance = abs(entry_price - stop_loss)
    equilibrium = (range_high + range_low) / 2.0
    return {
        **base,
        **common,
        "valid": risk_distance > 0,
        "action": "EXHAUSTION_REVERSAL_SHADOW_SIGNAL",
        "reason": "PREMIUM_EXHAUSTION_SELL_CONFIRMED" if direction == "SELL" else "DISCOUNT_EXHAUSTION_BUY_CONFIRMED",
        "direction": direction,
        "direction_allowed": True,
        "checks": checks,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "equilibrium_target": equilibrium,
        "risk_distance": risk_distance,
    }
