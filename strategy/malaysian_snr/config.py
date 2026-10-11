"""Configuración de la Estrategia Malaysian SNR.

Los replays heredados no validan rentabilidad de la versión causal actual.
- Escenario 1 permanece deshabilitado por defecto.
- Filtro de cuerpo sólido mínimo (>= 50%) y mecha reducida (<= 30%).
- Gestión Dual-Leg:
  - Entrada 1: TP1 mínimo 1:2.0 RR.
  - Entrada 2: Runner contextual (TP2 1:2.5, TP3 1:3.0, TP4 1:4.0).
  - Al tocar TP1: Mover Stop Loss de Entrada 2 a Break-Even + spread buffer.
"""

from dataclasses import dataclass


@dataclass
class MalaysianSNRConfig:
    enabled: bool = True
    strategy_name: str = "MALAYSIAN_SNR"
    strategy_version: str = "msnr-v2.0-augmented"
    
    # Marcos temporales
    macro_timeframe: str = "D1"
    structure_timeframe: str = "H1"
    entry_timeframe: str = "M15"
    
    # Parámetros de detección de velas Fresh
    minimum_body_ratio: float = 0.50
    maximum_breakout_wick_ratio: float = 0.25
    level_lookback_candles: int = 40
    min_separation_hours: float = 3.0
    retest_tolerance_atr: float = 0.35
    max_entry_distance_atr: float = 0.50
    obstacle_buffer_atr: float = 0.10
    qm_swing_radius: int = 2
    
    # Reglas institucionales validadas en replay de 2 años (+7.29% WR, +11.93R neto)
    enable_strict_fresh_filter: bool = True       # Nivel virgen: descarta niveles mitigados por mechas intermedias
    enable_session_killzones_filter: bool = True   # Solo operar Londres (07:00-11:00 UTC) y NY (12:30-17:00 UTC) en activos no sintéticos
    enable_daily_storyline_filter: bool = True     # Confluencia con sesgo macro D1
    enable_d1_storyline_levels: bool = True        # Storyline A/V de D1 para detección de Key Levels macro contrarios
    enable_crt_sweep_rejection: bool = True        # Candle Range Theory (CRT): M15 exige barrido de mecha + absorción de cierre
    enable_quasimodo_pattern: bool = True          # Patrón Quasimodo estructural de swing (Left Shoulder retest)
    enable_obstacle_awareness: bool = True         # Ajuste dinámico de TP2 al detectar Key Level contrario intermedio
    min_obstacle_rr: float = 2.0                   # Clearance mínimo exigido hacia el obstáculo D1 opuesto (>= 2.0R)
    
    # Escenarios habilitados
    enable_scenario_1_continuation: bool = False
    enable_scenario_3_fractal: bool = True
    enable_scenario_2_reversal: bool = False  # Desactivado por PnL negativo en 2 años
    enable_scenario_5_fvg: bool = False       # Desactivado por baja expectativa en 2 años
    
    # Ratios Riesgo:Beneficio
    tp1_min_rr: float = 2.0
    tp2_runner_rr: float = 2.5
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

    # Allowlist auditada y validada en replay causal de 2 años (60 activos, 2024-2026).
    # 23 activos que superaron la prueba cuantitativa con expectativa matemática positiva:
    allowed_symbols: tuple = (
        # Sintéticos Líderes con Expectativa Matemática Positiva (hasta +9.68R)
        "Step Index 400", "Crash 1000 Index", "Jump 25 Index", "Boom 300 Index",
        "Volatility 250 (1s) Index", "Step Index", "Jump 10 Index",
        "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 1000 Index",
        "Step Index 200", "Crash 600 Index",
        # Metales Preciosos Validados (XAGUSD 55.6% WR / +7.21R, XAUUSD +0.87R)
        "XAGUSD", "XAUUSD",
        # Forex e Índices Validados con Filtro Storyline D1 + CRT M15 (hasta 62.5% WR)
        "GBPJPY", "EURUSD", "USDJPY", "AUDNZD", "GBPUSD", "GBPAUD",
        "Wall Street 30", "EURCHF", "EURGBP",
    )

