"""Centinela de Regímenes de Mercado (Capa 1: Escudo Macro / Protector).

Evalúa el clima general y estructural del activo antes de que la estrategia
técnica o el meta-labeler puntual generen o ejecuten órdenes.

Identifica cuatro regímenes principales:
- STABLE_TREND: Tendencia direccional firme y baja/moderada fricción.
- CLEAN_RANGE: Rango armónico u oscilación limpia (ideal para Malaysian SNR).
- HIGH_VOLATILITY: Expansión volátil aprovechable con gestión de riesgo prudente.
- TOXIC_NOISE: Choppiness extremo, barrido errático de mechas bidireccionales,
               o explosión de spread. En modo FILTER veta la apertura en el símbolo.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

REGIME_STABLE_TREND = "STABLE_TREND"
REGIME_CLEAN_RANGE = "CLEAN_RANGE"
REGIME_HIGH_VOLATILITY = "HIGH_VOLATILITY"
REGIME_TOXIC_NOISE = "TOXIC_NOISE"

MODE_OFF = "OFF"
MODE_OBSERVE = "OBSERVE"
MODE_FILTER = "FILTER"


@dataclass
class MarketRegimeConfig:
    """Configuración operativa del centinela de regímenes."""

    enabled: bool = True
    # OBSERVE evalúa y registra sin vetar; FILTER bloquea si el régimen es TOXIC_NOISE.
    mode: str = MODE_FILTER
    choppiness_period: int = 14
    choppiness_toxic_threshold: float = 61.8
    adx_toxic_threshold: float = 18.0
    atr_spike_threshold: float = 2.2
    wick_noise_threshold: float = 0.40
    spread_stress_threshold: float = 2.5
    # Por defecto, protege a Forex con mayor celo en modo FILTER si hay ruido
    forex_strict_filter: bool = True
    # Si no hay suficientes velas, no bloquear operativas
    min_candles_required: int = 30


@dataclass
class MarketRegimeMetrics:
    """Métricas numéricas calculadas para el activo."""

    atr: float = 0.0
    atr_baseline: float = 0.0
    atr_ratio: float = 1.0
    choppiness_index: float = 50.0
    adx: float = 20.0
    wick_noise_ratio: float = 0.35
    spread_ratio: float = 1.0
    candles_evaluated: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MarketRegimeClassification:
    """Diagnóstico cualitativo del régimen del mercado."""

    regime: str = REGIME_CLEAN_RANGE
    is_toxic: bool = False
    confidence: float = 0.80
    primary_factor: str = "BALANCED_CONDITIONS"
    description: str = "Condiciones de mercado operables."
    metrics: MarketRegimeMetrics = field(default_factory=MarketRegimeMetrics)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["metrics"] = self.metrics.to_dict()
        return result


@dataclass
class MarketRegimeDecision:
    """Decisión ejecutable por el motor de trading."""

    symbol: str
    allowed: bool
    mode: str
    regime: str
    is_toxic: bool
    reason: str
    evaluated_at: str
    classification: MarketRegimeClassification

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        res["classification"] = self.classification.to_dict()
        return res


def compute_regime_metrics(
    df: pd.DataFrame,
    current_spread: float | None = None,
    baseline_spread: float | None = None,
    period: int = 14,
) -> MarketRegimeMetrics:
    """Calcula las métricas estructurales de régimen sobre velas cerradas."""
    if df is None or len(df) < max(period + 5, 20):
        return MarketRegimeMetrics()

    highs = df["high"].values.astype(float)
    lows = df["low"].values.astype(float)
    closes = df["close"].values.astype(float)
    opens = df["open"].values.astype(float) if "open" in df.columns else closes

    n = len(df)
    # 1. True Range
    tr = np.zeros(n, dtype=float)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    # 2. ATR actual y Baseline histórico (media de 50 periodos de ATR o total disponible)
    atr_window = min(period, n)
    recent_atr = float(np.mean(tr[-atr_window:]))
    baseline_window = min(max(50, period * 2), n)
    baseline_atr = float(np.mean(tr[-baseline_window:]))
    atr_ratio = (recent_atr / baseline_atr) if baseline_atr > 1e-12 else 1.0

    # 3. Choppiness Index (CI)
    # CI = 100 * LOG10( SUM(TR, n) / ( MAX(High, n) - MIN(Low, n) ) ) / LOG10(n)
    chop_window = min(period, n)
    sum_tr = float(np.sum(tr[-chop_window:]))
    max_h = float(np.max(highs[-chop_window:]))
    min_l = float(np.min(lows[-chop_window:]))
    span = max_h - min_l

    if span > 1e-12 and chop_window > 1:
        raw_ratio = sum_tr / span
        if raw_ratio > 0:
            ci = 100.0 * (math.log10(raw_ratio) / math.log10(chop_window))
            ci = float(np.clip(ci, 0.0, 100.0))
        else:
            ci = 50.0
    else:
        ci = 50.0

    # 4. ADX simplificado y robusto
    # +DM y -DM
    plus_dm = np.zeros(n, dtype=float)
    minus_dm = np.zeros(n, dtype=float)
    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

    p_dm_sum = float(np.sum(plus_dm[-atr_window:]))
    m_dm_sum = float(np.sum(minus_dm[-atr_window:]))
    tr_sum = max(sum_tr, 1e-12)

    plus_di = 100.0 * (p_dm_sum / tr_sum)
    minus_di = 100.0 * (m_dm_sum / tr_sum)
    di_sum = plus_di + minus_di
    dx = (100.0 * abs(plus_di - minus_di) / di_sum) if di_sum > 1e-12 else 0.0
    adx = float(np.clip(dx, 0.0, 100.0))

    # 5. Wick-to-body noise ratio (recientes 10 velas)
    wick_candles = min(10, n)
    wicks = []
    for i in range(n - wick_candles, n):
        c_high = highs[i]
        c_low = lows[i]
        c_open = opens[i]
        c_close = closes[i]
        c_span = max(c_high - c_low, 1e-12)
        upper_wick = c_high - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_low
        wicks.append((upper_wick + lower_wick) / c_span)
    wick_ratio = float(np.mean(wicks)) if wicks else 0.35

    # 6. Spread ratio
    spread_ratio = 1.0
    if current_spread is not None and baseline_spread is not None and baseline_spread > 1e-12:
        spread_ratio = float(current_spread / baseline_spread)

    return MarketRegimeMetrics(
        atr=round(recent_atr, 6),
        atr_baseline=round(baseline_atr, 6),
        atr_ratio=round(atr_ratio, 4),
        choppiness_index=round(ci, 2),
        adx=round(adx, 2),
        wick_noise_ratio=round(wick_ratio, 4),
        spread_ratio=round(spread_ratio, 3),
        candles_evaluated=n,
    )


def classify_market_regime(
    metrics: MarketRegimeMetrics,
    symbol: str = "",
    config: MarketRegimeConfig | None = None,
) -> MarketRegimeClassification:
    """Clasifica el régimen en base a las métricas y umbrales configurados."""
    cfg = config or MarketRegimeConfig()
    sym = (symbol or "").upper()

    # Detección de activos Forex y Sintéticos
    is_forex = any(pair in sym for pair in ("EUR", "USD", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF")) and not any(k in sym for k in ("BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"))
    is_synthetic = any(k in sym for k in ("BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP", "1S", "HZ", "INDEX")) or not is_forex

    # En sintéticos de Deriv, la micro-volatilidad y mechas son intrínsecas a las cotizaciones deterministas 24/7.
    # Suavizamos los umbrales de Whipsaw y Choppiness en un 20-25% para evitar bloquear tendencias legítimas,
    # mientras mantenemos la protección estricta en Forex y Oro.
    wick_noise_thresh = cfg.wick_noise_threshold * 1.25 if is_synthetic else cfg.wick_noise_threshold
    atr_spike_thresh = cfg.atr_spike_threshold * 1.20 if is_synthetic else cfg.atr_spike_threshold
    whip_extreme_thresh = 0.78 if is_synthetic else 0.70
    chop_extreme_thresh = 76.0 if is_synthetic else 72.0
    chop_toxic_thresh = (cfg.choppiness_toxic_threshold + 6.0) if is_synthetic else cfg.choppiness_toxic_threshold
    adx_toxic_thresh = (cfg.adx_toxic_threshold - 3.0) if is_synthetic else cfg.adx_toxic_threshold

    # Criterios de TOXIC_NOISE
    # 1. Congestión caótica (Choppiness muy alto o alta congestión con ruido de mechas)
    is_chaotic_choppy = (
        metrics.choppiness_index >= chop_extreme_thresh
        or (
            metrics.choppiness_index >= chop_toxic_thresh
            and (metrics.adx <= adx_toxic_thresh or metrics.wick_noise_ratio >= wick_noise_thresh)
        )
    )
    # 2. Barrido excesivo de mechas (whipsaw / caza de stops en ambas direcciones)
    is_whip_spike = (
        metrics.wick_noise_ratio >= whip_extreme_thresh
        or (
            metrics.atr_ratio >= atr_spike_thresh
            and metrics.wick_noise_ratio >= wick_noise_thresh
        )
        or (
            metrics.wick_noise_ratio >= wick_noise_thresh
            and metrics.adx <= adx_toxic_thresh
        )
    )
    # 3. Spread disparado
    is_spread_stressed = metrics.spread_ratio >= cfg.spread_stress_threshold

    if is_spread_stressed:
        return MarketRegimeClassification(
            regime=REGIME_TOXIC_NOISE,
            is_toxic=True,
            confidence=0.90,
            primary_factor="SPREAD_STRESS_SPIKE",
            description=f"Spread anómalo ({metrics.spread_ratio:.2f}x de lo normal). Riesgo alto de deslizamiento.",
            metrics=metrics,
        )

    if is_whip_spike:
        return MarketRegimeClassification(
            regime=REGIME_TOXIC_NOISE,
            is_toxic=True,
            confidence=0.85,
            primary_factor="ERRATIC_WHIPSAW_VOLATILITY",
            description=(
                f"Volatilidad ATR disparada ({metrics.atr_ratio:.2f}x) con "
                f"predominio de mechas ({metrics.wick_noise_ratio*100:.1f}%). Barridos bidireccionales tóxicos."
            ),
            metrics=metrics,
        )

    if is_chaotic_choppy:
        return MarketRegimeClassification(
            regime=REGIME_TOXIC_NOISE,
            is_toxic=True,
            confidence=0.82,
            primary_factor="HIGH_CHOPPINESS_LOW_MOMENTUM",
            description=(
                f"Mercado altamente congestionado y ruidoso (CI: {metrics.choppiness_index:.1f}, "
                f"ADX: {metrics.adx:.1f}). Falsos rompimientos frecuentes."
            ),
            metrics=metrics,
        )

    # 4. Tendencia limpia
    if metrics.choppiness_index < 42.0 or (metrics.adx >= 25.0 and metrics.atr_ratio <= 1.8):
        return MarketRegimeClassification(
            regime=REGIME_STABLE_TREND,
            is_toxic=False,
            confidence=0.80,
            primary_factor="CLEAR_DIRECTIONAL_FLOW",
            description=f"Tendencia limpia y estructurada (ADX: {metrics.adx:.1f}, CI: {metrics.choppiness_index:.1f}).",
            metrics=metrics,
        )

    # 5. Volatilidad alta pero direccional
    if metrics.atr_ratio > 1.8 and metrics.adx >= 22.0:
        return MarketRegimeClassification(
            regime=REGIME_HIGH_VOLATILITY,
            is_toxic=False,
            confidence=0.75,
            primary_factor="HIGH_EXPANSION_VOLATILITY",
            description=f"Expansión de alta volatilidad aprovechable (ATR Ratio: {metrics.atr_ratio:.2f}).",
            metrics=metrics,
        )

    # 6. Rango limpio (entorno óptimo para reversiones y Malaysian SNR)
    return MarketRegimeClassification(
        regime=REGIME_CLEAN_RANGE,
        is_toxic=False,
        confidence=0.78,
        primary_factor="STABLE_EQUILIBRIUM_RANGE",
        description=(
            f"Rango de equilibrio estable y oscilación limpia (CI: {metrics.choppiness_index:.1f}, "
            f"Wick Ratio: {metrics.wick_noise_ratio*100:.1f}%)."
        ),
        metrics=metrics,
    )


class MarketRegimeSentinel:
    """Guardián en tiempo real de regímenes de mercado para el motor de trading."""

    def __init__(self, config: MarketRegimeConfig | None = None) -> None:
        self.config = config or MarketRegimeConfig()

    def evaluate_symbol(
        self,
        symbol: str,
        df_h1: pd.DataFrame | None,
        current_spread: float | None = None,
        baseline_spread: float | None = None,
    ) -> MarketRegimeDecision:
        """Determina si el símbolo es operable bajo las condiciones actuales de régimen."""
        now_iso = datetime.now(timezone.utc).isoformat()

        if not self.config.enabled or self.config.mode == MODE_OFF:
            return MarketRegimeDecision(
                symbol=symbol,
                allowed=True,
                mode=self.config.mode,
                regime=REGIME_CLEAN_RANGE,
                is_toxic=False,
                reason="REGIME_SENTINEL_DISABLED",
                evaluated_at=now_iso,
                classification=MarketRegimeClassification(),
            )

        if df_h1 is None or len(df_h1) < self.config.min_candles_required:
            return MarketRegimeDecision(
                symbol=symbol,
                allowed=True,
                mode=self.config.mode,
                regime=REGIME_CLEAN_RANGE,
                is_toxic=False,
                reason="INSUFFICIENT_DATA_ALLOW_DEFAULT",
                evaluated_at=now_iso,
                classification=MarketRegimeClassification(),
            )

        metrics = compute_regime_metrics(
            df_h1,
            current_spread=current_spread,
            baseline_spread=baseline_spread,
            period=self.config.choppiness_period,
        )
        classification = classify_market_regime(metrics, symbol=symbol, config=self.config)

        # Regla de veto en modo FILTER
        if self.config.mode == MODE_FILTER and classification.is_toxic:
            allowed = False
            reason = f"MARKET_REGIME_TOXIC_BLOCKED:{classification.primary_factor}"
        else:
            allowed = True
            reason = (
                f"MARKET_REGIME_OBSERVED_TOXIC:{classification.primary_factor}"
                if classification.is_toxic
                else f"MARKET_REGIME_ACCEPTED:{classification.regime}"
            )

        return MarketRegimeDecision(
            symbol=symbol,
            allowed=allowed,
            mode=self.config.mode,
            regime=classification.regime,
            is_toxic=classification.is_toxic,
            reason=reason,
            evaluated_at=now_iso,
            classification=classification,
        )
