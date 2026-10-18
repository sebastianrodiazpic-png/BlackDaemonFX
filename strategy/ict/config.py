"""Configuración para la estrategia institucional ICT (Sabri Malle - AMD & FVG Rejection v2)."""
from dataclasses import dataclass


@dataclass
class ICTSabriMalleConfig:
    strategy_name: str = "ICT_SABRI_MALLE"
    strategy_version: str = "ict-sabri-malle-v1"
    macro_timeframe: str = "H4"
    structure_timeframe: str = "H1"
    entry_timeframe: str = "M15"
    
    # Filtro Horario y Killzones Institucionales (New York Time)
    killzone_filter_enabled: bool = True
    asian_range_start_ny: int = 20  # 20:00 NY
    asian_range_end_ny: int = 0     # 00:00 NY
    london_kz_start_ny: int = 2     # 02:00 NY
    london_kz_end_ny: int = 5       # 05:00 NY
    ny_kz_start_ny: int = 7         # 07:00 NY
    ny_kz_end_ny: int = 11          # 11:00 NY
    # Replay fiel (365d, sin lookahead): Londres +0.18R/trade (n=238), NY 07-11 -0.16R/trade (n=434).
    ny_killzone_enabled: bool = True
    forex_ny_killzone_enabled: bool = True  # Permite a Forex operar también en New York Killzone
    london_close_reversal_enabled: bool = True  # Ventana 11:00-12:30 NY (Toni Maura M15 FVG reversal)
    silver_bullet_enabled: bool = True  # Ventanas Silver Bullet (03-04, 10-11, 14-15 NY)
    
    # Cierre de Mercado y Guardias de Rollover (Forex, Metales, Índices)
    market_closure_filter_enabled: bool = True
    friday_close_cutoff_ny: int = 14  # No abrir órdenes viernes después de 14:00 NY
    weekend_filter_enabled: bool = True
    rollover_guard_enabled: bool = True
    rollover_start_ny_hour: int = 16
    rollover_start_ny_minute: int = 45
    rollover_end_ny_hour: int = 17
    rollover_end_ny_minute: int = 45

    # Detección Estructural y Manipulación (AMD / Judas Swing / OB 5 Estrellas)
    range_lookback: int = 24
    min_atr_factor: float = 0.5
    max_atr_factor: float = 5.0
    min_rejection_wick_ratio: float = 0.35
    synthetics_min_rejection_wick_ratio: float = 0.25
    synthetics_rolling_lookback_bars: int = 8  # Rango fractal dinámico para sintéticos 24/7
    
    # Order Block 5 Estrellas (Sabri Malle Video 9)
    ob_five_star_enabled: bool = True
    ob_lookback_bars: int = 30
    
    # Macro Bias H4 Flexible (Sabri Malle Video 8 EMA 100 / EMA 50-200)
    macro_ema_period: int = 100
    macro_bias_flexible: bool = True
    
    # Ruptura Estructural Estricta (MSS) y FVG Consequent Encroachment
    strict_mss_body_ratio: float = 0.45
    fvg_consequent_encroachment_ratio: float = 0.50
    fvg_consequent_encroachment_entry: bool = True
    fvg_lookback_bars: int = 40
    fibo_discount_premium_filter: bool = True
    
    # Gestión Asimétrica Dual y Salidas
    min_rr_planned: float = 1.0
    tp1_rr: float = 1.0
    runner_rr: float = 2.0
    be_trigger_rr: float = 1.0
    be_trigger_rr_fast: float = 1.0  # Break-Even opcional a 1.0R (Video 9)
    leg1_risk_ratio: float = 0.5
    leg2_risk_ratio: float = 0.5
    min_body_ratio: float = 0.40
    
    # Sintéticos (Operativa 24/7 sin Killzones bancarias)
    synthetics_24_7_enabled: bool = True
    synthetics_use_volatility_squeeze: bool = True
    synthetics_squeeze_lookback: int = 20

    # Opción A: SMT Divergence (Smart Money Technique)
    smt_divergence_enabled: bool = True
    smt_score_bonus: float = 15.0
    smt_lookback_bars: int = 16

    # Opción B: Cascada Fractal M5 Timing en Sintéticos
    m5_cascade_timing_enabled: bool = True
    m5_cascade_timeframe: str = "M5"

    # Opción C: Inversion FVG (iFVG) y Balanced Price Range (BPR)
    ifvg_bpr_enabled: bool = True
    ifvg_lookback_bars: int = 24
    ifvg_bpr_require_gbdt_filter: bool = True

