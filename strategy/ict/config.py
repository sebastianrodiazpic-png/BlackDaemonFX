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
    
    # Detección Estructural y Manipulación (AMD / Judas Swing)
    range_lookback: int = 24
    min_atr_factor: float = 0.5
    max_atr_factor: float = 5.0
    min_rejection_wick_ratio: float = 0.35
    
    # Ruptura Estructural Estricta (MSS) y FVG Consequent Encroachment
    strict_mss_body_ratio: float = 0.45
    fvg_consequent_encroachment_ratio: float = 0.50
    fvg_lookback_bars: int = 40
    
    # Gestión Asimétrica Dual y Salidas
    min_rr_planned: float = 2.0
    tp1_rr: float = 2.0
    runner_rr: float = 4.0
    be_trigger_rr: float = 2.0
    leg1_risk_ratio: float = 0.5
    leg2_risk_ratio: float = 0.5
    min_body_ratio: float = 0.40
    
    # Sintéticos (Operativa 24/7 sin Killzones bancarias)
    synthetics_use_volatility_squeeze: bool = True
    synthetics_squeeze_lookback: int = 20
