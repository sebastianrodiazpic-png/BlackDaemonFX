"""Parámetros de Alchemist MSNR. Los valores por defecto son los del pre-registro del 26-oct-2026
(REGISTRO_CAMBIOS_ESTRATEGIA.md): cambiarlos convierte la prueba en exploratoria."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlchemistConfig:
    # Niveles de alta temporalidad sobre cierres (gráfico de líneas).
    level_pivot_k: dict = field(default_factory=lambda: {"D1": 3, "H4": 3, "H1": 5})
    level_lookback_days: dict = field(default_factory=lambda: {"D1": 120, "H4": 60, "H1": 20})
    level_zone_atr: float = 0.15
    max_touches: int = 2
    flip_min_atr: float = 0.5
    flip_min_body_ratio: float = 0.5
    trend_pivot_k: int = 5  # estructura H1 para QMC
    # Quasimodo en M15.
    m15_pivot_k: int = 2
    minor_pivot_k: int = 1
    break_max_bars: int = 24
    turtle_soup_lookback: int = 3
    ce_ratio: float = 0.5  # Candle Equilibrium: fracción de la mecha del Turtle Soup
    # Orden y gestión.
    entry_mode: str = "shoulder"  # shoulder | ce | ob50
    require_confluence: bool = True
    exit_mode: str = "A"  # A: salida única + BE en exit_be_r; B: parcial en partial_r + BE
    exit_be_r: float = 2.0
    partial_r: float = 3.0
    partial_weight: float = 0.5
    limit_valid_bars: int = 16
    sl_buffer_atr: float = 0.10
    min_target_r: float = 5.0
    max_sl_pips_fx: float = 30.0
    max_sl_atr_h1_other: float = 1.0
    max_spread_sl_ratio: float = 0.05
    session_start_utc: int = 7
    session_end_utc: int = 16
    force_flat_ny: str = "16:45"
    enable_qmm: bool = True
    qmm_window_bars: int = 8
    atr_period: int = 14
