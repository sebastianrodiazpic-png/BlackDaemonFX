"""Configuración del Motor de Criterio Humano (Human Criteria Decision Engine).

Gobierna las comprobaciones de confluencia, macroeconomía y régimen de mercado
previas a la apertura de cualquier orden para simular el juicio de un trader profesional.

REGLA FUNDAMENTAL:
    El motor de criterio evalúa la ADMISIBILIDAD y CALIDAD (Score 0-100) de la oportunidad.
    JAMÁS altera los niveles predefinidos de Stop Loss o Take Profit definidos
    por la estrategia subyacente.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


MODE_OFF = "OFF"
MODE_OBSERVE = "OBSERVE"
MODE_FILTER = "FILTER"


@dataclass
class HumanCriteriaConfig:
    """Parámetros de evaluación del criterio humano."""

    enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_ENABLED", "1").lower() in ("1", "true", "yes")
    )
    mode: str = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_MODE", MODE_FILTER).upper()
    )

    # Umbrales de Calidad (Scoring 0 a 100)
    min_score_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_MIN_SCORE", "65.0"))
    )
    elite_score_threshold: float = 80.0

    # 1. Filtros Macro y Noticias (Forex y Materias Primas)
    forex_news_guard_enabled: bool = True
    commodities_news_guard_enabled: bool = True
    news_calendar_path: str = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_NEWS_CALENDAR_PATH", "storage/dashboard/financial_news.json")
    )
    news_before_minutes: int = 25
    news_after_minutes: int = 25

    # Mapeo de sensibilidad macro por activo
    usd_sensitive_symbols: tuple[str, ...] = (
        "XAUUSD", "GOLD", "MICROXAUUSD", "XAGUSD", "SILVER",
        "USOUSD", "US OIL", "WTICOUSD", "OIL", "BRENT",
        "US TECH 100", "NAS100", "USTECH", "WALL STREET 30", "US30", "DJ30", "US500", "SPX500"
    )
    oil_event_keywords: tuple[str, ...] = (
        "crude", "oil", "petroleo", "petróleo", "opec", "opep", "eia", "inventarios", "drilling"
    )

    # 2. Filtros de Tendencia y Régimen (Índices Sintéticos)
    synthetic_trend_hunter_enabled: bool = True
    synthetic_require_h1_alignment: bool = True
    synthetic_h1_fast_ema: int = 50
    synthetic_h1_slow_ema: int = 200
    synthetic_adx_min_threshold: float = 18.0

    # Umbral de corte específico para sintéticos (Score 0-100)
    synthetic_min_score_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_SYNTHETIC_MIN_SCORE", "75.0"))
    )

    # Umbral de corte quirúrgico específico para índices de la familia STEP (Step Index 200, 400, 500 / Worker STEP Magic 26082104)
    # Validado con Replay 5 años (+71.00R en familia Step y +23.50R en Step 400 con 53.54% WR y PF 1.22)
    synthetic_step_min_score_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_STEP_MIN_SCORE", "70.0"))
    )

    # Umbral de corte específico para Malaysian SNR (Score 0-100 para rebotes en S/R)
    malaysian_snr_min_score_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_MSNR_MIN_SCORE", "60.0"))
    )

    # Filtro de asimetría direccional en spikes (Boom & Crash)
    synthetic_spike_hazard_guard_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_SPIKE_HAZARD", "1").lower() in ("1", "true", "yes")
    )
    synthetic_spike_hazard_penalty_points: float = 20.0
    synthetic_spike_hazard_veto_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_SPIKE_HAZARD_VETO", "0").lower() in ("1", "true", "yes")
    )

    # Anulación de veto por régimen tóxico si la señal presenta confirmación de absorción o desplazamiento institucional (FVG)
    absorption_regime_override_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HUMAN_CRITERIA_ABSORPTION_OVERRIDE", "1").lower() in ("1", "true", "yes")
    )

    # Desbloqueo Inteligente de Alta Convicción (ML GBDT prob >= 0.85 y expectativa >= 1.0R con confluencias técnicas >= 85%)
    # Permite flexibilizar el umbral a 70.0 pts cuando la probabilidad matemática es excelente (+503R en Jump 100, etc.)
    high_conviction_override_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HC_HIGH_CONVICTION_OVERRIDE", "1").strip().lower() in ("1", "true", "yes")
    )
    high_conviction_min_score_threshold: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HC_HIGH_CONVICTION_MIN_SCORE", "70.0"))
    )

    # Filtro anti-sobreextensión elástica respecto a media HTF (Mean Reversion Guard)
    synthetic_mean_reversion_guard_enabled: bool = True
    synthetic_max_ema_deviation_atr: float = 2.5
    synthetic_mean_reversion_penalty_points: float = 10.0

    # Filtro de racha intradía y salud del activo (Consecutive Loss Guard)
    synthetic_streak_guard_enabled: bool = True
    synthetic_streak_penalty_points: float = 10.0

    # Filtro anti-agotamiento clímax (evitar comprar en la punta de una sobreextensión)
    synthetic_climax_filter_enabled: bool = True
    synthetic_climax_atr_multiplier: float = 2.75
    synthetic_climax_body_ratio: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HC_CLIMAX_BODY_RATIO", "0.80"))
    )

    # Filtro de mecha adversa y exigencia de absorción institucional (Rejection / Absorption Guard)
    adverse_wick_veto_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HC_ADVERSE_WICK_VETO", "1").strip().lower() in ("1", "true", "yes")
    )
    max_adverse_wick_ratio: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HC_MAX_ADVERSE_WICK_RATIO", "0.40"))
    )
    min_rejection_wick_ratio: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_HC_MIN_REJECTION_WICK_RATIO", "0.20"))
    )

    # Exención de ADX para activos de microestructura por saltos o pasos discretos (Step / Jump)
    # Evita falsos negativos (+47.5 R en replay 2 años al no vetar falsamente por baja tendencia continua)
    step_jump_adx_guard_exempt: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_HC_STEP_JUMP_ADX_EXEMPT", "1").lower() in ("1", "true", "yes")
    )

    # Control de fricción de spread vs Stop Loss (Slippage / Friction Guard)
    max_spread_to_sl_ratio: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_MAX_SPREAD_TO_SL_RATIO", "0.12"))
    )
    spread_friction_veto_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_SPREAD_FRICTION_VETO_ENABLED", "1").lower() in ("1", "true", "yes")
    )

    # Filtro de ruido tóxico y consolidación lateral estrecha (Choppiness)
    synthetic_choppiness_threshold: float = 61.8

    # 3. Ponderaciones del Score en Mercados Reales (Forex / Oro / Petróleo / Índices) - Total = 100
    weight_htf_trend: float = 30.0        # Alineación de marea mayor H4/H1
    weight_macro_news: float = 25.0       # Ausencia de noticias y sesgo favorable
    weight_regime_health: float = 20.0    # Régimen sin choppiness extremo
    weight_candle_quality: float = 15.0   # Rechazo previo y sin sobreextensión clímax
    weight_spread_friction: float = 10.0  # Spread bajo vs SL y ATR

    # 4. Ponderaciones del Score Especializadas para Sintéticos (Sin puntos macro de regalo) - Total = 100
    synthetic_weight_htf_trend: float = 30.0        # Alineación y estructura en H1
    synthetic_weight_macro_news: float = 0.0        # En sintéticos no hay fundamentales (0 pts de regalo)
    synthetic_weight_regime_health: float = 25.0    # Salud del régimen y ADX robusto
    synthetic_weight_candle_quality: float = 25.0   # Rechazo institucional con mechas y anti-clímax
    synthetic_weight_streak_health: float = 10.0    # Salud intradía del activo (sin rachas perdedoras)
    synthetic_weight_spread_friction: float = 10.0  # Fricción del spread respecto al SL
