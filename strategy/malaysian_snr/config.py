"""Configuración de la Estrategia Malaysian SNR.

Basada en los hallazgos cuantitativos del análisis de 2 años (207,520 trades):
- Priorización exclusiva de Escenario 1 (Ruptura Fresh + Retest al Break) y Escenario 3 (Fractalidad HCH).
- Filtro de cuerpo sólido mínimo (>= 50%) y mecha reducida (<= 30%).
- Gestión Dual-Leg:
  - Entrada 1: TP1 mínimo 1:2.0 RR.
  - Entrada 2: Runner contextual (TP2 1:2.5, TP3 1:3.5, TP4 1:5.0).
  - Al tocar TP1: Mover Stop Loss de Entrada 2 a Break-Even + spread buffer.
"""

from dataclasses import dataclass, field


@dataclass
class MalaysianSNRConfig:
    enabled: bool = True
    strategy_name: str = "MALAYSIAN_SNR"
    strategy_version: str = "msnr-v1.0"
    
    # Marcos temporales
    structure_timeframe: str = "H1"
    entry_timeframe: str = "M15"
    
    # Parámetros de detección de velas Fresh
    minimum_body_ratio: float = 0.50
    maximum_breakout_wick_ratio: float = 0.30
    level_lookback_candles: int = 40
    min_separation_hours: float = 3.0
    
    # Escenarios habilitados (basado en auditoría de 2 años)
    enable_scenario_1_continuation: bool = True
    enable_scenario_3_fractal: bool = True
    enable_scenario_2_reversal: bool = False  # Desactivado por PnL negativo en 2 años
    enable_scenario_5_fvg: bool = False       # Desactivado por baja expectativa en 2 años
    
    # Ratios Riesgo:Beneficio
    tp1_min_rr: float = 1.0
    tp2_runner_rr: float = 2.0
    tp3_runner_rr: float = 3.0
    tp4_runner_rr: float = 4.0
    
    # Umbrales para extensión de corredora
    adx_tp3_threshold: float = 22.0
    adx_tp4_threshold: float = 28.0
    body_ratio_tp4_threshold: float = 0.65
    
    # Gestión de riesgo
    risk_percent_total: float = 1.0  # 1% total de la cuenta
    leg1_risk_ratio: float = 0.5     # 50% del riesgo (0.5%)
    leg2_risk_ratio: float = 0.5     # 50% del riesgo (0.5%)
    be_spread_buffer_multiplier: float = 1.5
