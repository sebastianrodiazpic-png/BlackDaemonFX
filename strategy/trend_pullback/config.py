"""Configuración para la estrategia Trend Pullback H1 + M15 (Sintéticos).

Estrategia cuantitativa de seguimiento de tendencia en retroceso sobre velas cerradas:
- Sesgo de tendencia en H1 con EMA(50), EMA(200) y filtro de régimen ADX(14) >= 20.
- Gatillo en M15: retroceso y rechazo dinámico sobre EMA(21) con RSI(14) en zona controlada.
- Contrato operativo BlackDaemonFX: 1 % total en 2 patas (0,5 % en TP1 a 1R + 0,5 % en TP2 a 2R
  con paso automático a Break-Even al tocar TP1 y trailing stop escalonado a 2R/3R/4R).
- Filtro de fricción institucional: tope de spread/SL al 2 % para sintéticos Deriv.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

TREND_PULLBACK_STRATEGY = "TREND_PULLBACK"
TREND_PULLBACK_VERSION = "trend-pullback-v1"
TREND_PULLBACK_SCENARIO = "TREND_PULLBACK_H1_M15"

# Activos con degradación estructural o spread tóxico en sintéticos 5y
# Activos con degradación estructural o spread tóxico, o transferidos a workers dedicados STEP y JUMP
TREND_PULLBACK_PRUNED_SYMBOLS = (
    "Crash 1000 Index",
    "Volatility 90 (1s) Index",
    "High Frequency Vol 50 Index",
    # Transferidos a workers dedicados STEP y JUMP con lógica bidireccional (>51% WR)
    "Jump 75 Index",
    "Jump 50 Index",
    "Step Index 200",
    "Step Index 400",
    "Step Index",
    "Step Index 500",
)

# Núcleo estrictamente rentable de sintéticos validado en replay multianual 5Y
# con Win Rate > 51.0 % y R neto > 0 (deriv_synthetics_5y_test_evaluation.csv).
TREND_PULLBACK_51_SYMBOLS = (
    "Crash 300 Index",          # WR 60.10 %, Net +34.50 R
    "Volatility 25 Index",       # WR 58.50 %, Net +53.30 R
    "Volatility 100 (1s) Index", # WR 57.80 %, Net +31.00 R
    "Volatility 90 Index",       # WR 57.00 %, Net +11.50 R
    "Crash 500 Index",          # WR 55.20 %, Net +23.90 R
    "VolSwitch High Vol Index",  # WR 54.70 %, Net +10.00 R
    "Jump 10 Index",             # WR 54.50 %, Net +51.60 R
    "Boom 900 Index",            # WR 54.40 %, Net +4.20 R
    "Volatility 10 Index",       # WR 53.70 %, Net +28.00 R
    "Boom 600 Index",            # WR 53.50 %, Net +6.60 R
    "Volatility 250 (1s) Index", # WR 53.30 %, Net +35.50 R
    "Jump 25 Index",             # WR 53.10 %, Net +33.30 R
    "Volatility 5 Index",        # WR 53.10 %, Net +13.50 R
    "Crash 600 Index",          # WR 52.80 %, Net +0.90 R
    "Boom 300 Index",            # WR 52.10 %, Net +24.40 R
    "Volatility 75 Index",       # WR 51.60 %, Net +10.40 R
    "Volatility 15 Index",       # WR 51.20 %, Net +0.70 R
)

DEFAULT_PULLBACK_SYMBOLS = TREND_PULLBACK_51_SYMBOLS


def _env_symbols() -> tuple[str, ...]:
    raw = os.getenv("DAEMONBLACKFX_TREND_PULLBACK_SYMBOLS", "")
    if raw.strip():
        symbols = tuple(s.strip() for s in raw.split(",") if s.strip())
    else:
        symbols = DEFAULT_PULLBACK_SYMBOLS
    pruned_set = set(TREND_PULLBACK_PRUNED_SYMBOLS)
    return tuple(s for s in symbols if s not in pruned_set)


@dataclass
class TrendPullbackConfig:
    """Parámetros configurables e interruptores de la estrategia Trend Pullback."""
    enabled: bool = os.getenv("DAEMONBLACKFX_TREND_PULLBACK_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
    strategy_name: str = TREND_PULLBACK_STRATEGY
    strategy_version: str = TREND_PULLBACK_VERSION
    symbols: tuple[str, ...] = field(default_factory=_env_symbols)

    # Parámetros HTF (H1)
    htf_timeframe: str = "H1"
    htf_ema_fast: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_HTF_FAST", "50"))
    htf_ema_slow: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_HTF_SLOW", "200"))
    adx_period: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_ADX_PERIOD", "14"))
    adx_min: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_ADX_MIN", "20.0"))

    # Parámetros LTF (M15)
    ltf_timeframe: str = "M15"
    pullback_ema: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_EMA", "21"))
    rsi_period: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_RSI_PERIOD", "14"))
    rsi_buy_min: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_RSI_BUY_MIN", "30.0"))
    rsi_buy_max: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_RSI_BUY_MAX", "70.0"))
    rsi_sell_min: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_RSI_SELL_MIN", "30.0"))
    rsi_sell_max: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_RSI_SELL_MAX", "70.0"))

    # Gestión de riesgo y paradas
    atr_period: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_ATR_PERIOD", "14"))
    stop_atr_multiple: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_STOP_ATR", "1.5"))
    min_stop_atr: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_MIN_STOP_ATR", "1.0"))
    swing_lookback: int = int(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_SWING_LOOKBACK", "5"))

    # Contrato operativo BlackDaemonFX: 2 patas al 0.5% (1% total) con BE + runner trailing
    split_execution: bool = os.getenv("DAEMONBLACKFX_TREND_PULLBACK_SPLIT", "1").strip().lower() in {"1", "true", "yes", "on"}
    leg1_risk_ratio: float = 0.5
    leg2_risk_ratio: float = 0.5
    tp1_rr: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_TP1_RR", "1.0"))
    runner_rr: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_RUNNER_RR", "2.0"))
    be_trigger_rr: float = 1.0

    # Tope institucional de spread/SL (2 % para sintéticos Deriv)
    max_spread_sl_ratio: float = float(os.getenv("DAEMONBLACKFX_TREND_PULLBACK_MAX_SPREAD_RATIO", "0.02"))

    # Asimetría direccional algorítmica (28-oct-2026): Jump BUY only y Step SELL only
    directional_asymmetry_enabled: bool = os.getenv("DAEMONBLACKFX_TPB_DIRECTIONAL_ASYMMETRY", "1").strip().lower() not in {"0", "false", "off"}
    jump_buy_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_TPB_JUMP_BUY_ONLY", "Jump 50 Index,Jump 75 Index").split(",") if s.strip()
    )
    step_sell_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_TPB_STEP_SELL_ONLY", "Step Index,Step Index 500").split(",") if s.strip()
    )

    # Filtro de momentum en contra (anti-falling knife): descarta retrocesos con vela previa > 1.25 ATR
    max_pullback_bar_body_atr: float = float(os.getenv("DAEMONBLACKFX_TPB_MAX_PB_BODY_ATR", "1.25"))

    # Buffer anti-hunt para el Stop Loss estructural (+0.25 ATR de margen al extremo del swing)
    sl_buffer_atr: float = float(os.getenv("DAEMONBLACKFX_TPB_SL_BUFFER_ATR", "0.25"))

    # Contador de velas necesarias para indicadores
    h1_candle_count: int = 300
    m15_candle_count: int = 200
