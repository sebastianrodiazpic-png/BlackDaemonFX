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
from strategy.malaysian_snr.runtime_settings import DEFAULT_FRACTAL_MIN_BODY_RATIO, DEFAULT_FRACTAL_MAX_ENTRY_DISTANCE_ATR


@dataclass
class MalaysianSNRConfig:
    enabled: bool = True
    strategy_name: str = "MALAYSIAN_SNR"
    strategy_version: str = "msnr-v2.9-video-evidence"
    # Isolated historical configurations retain the old geometry unless opted in.
    breaker_pair_mode: str = 'off'
    breaker_pair_min_body_ratio: float = .50
    breaker_pair_min_displacement_atr: float = .50
    retest_pinbar_mode: str = 'off'
    retest_pinbar_min_wick_ratio: float = .55
    retest_pinbar_min_close_ratio: float = .75
    session_policy: str = 'legacy_utc'
    obstacle_av_definition: str = 'engulfing'
    h4_obstacle_mode: str = 'off'
    
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
    retest_window_minutes: int = 90
    entry_execution_grace_seconds: int = 60
    retest_recovery_bars: int = 3
    confirmation_tolerance_bars: int = 0
    confirmation_tolerance_max_atr: float = 0.35
    enable_zone_rejection_trigger: bool = True
    max_retest_penetration_atr: float = 0.35
    retest_min_body_ratio: float = 0.35
    enable_tested_level_entries: bool = True
    max_tested_wick_penetration_atr: float = 0.20
    tested_level_displacement_atr: float = 0.20
    
    # Reglas de selección; la rentabilidad de esta versión requiere validación nueva.
    enable_strict_fresh_filter: bool = True       # Consumidos bloqueados; una visita admite excepción reforzada configurable
    enable_session_killzones_filter: bool = True   # Solo operar Londres (07:00-11:00 UTC) y NY (12:30-17:00 UTC) en activos no sintéticos
    enable_daily_storyline_filter: bool = True     # Confluencia con sesgo macro D1
    enable_synthetic_daily_storyline_filter: bool = False  # Veto D1 opcional para sintéticos; obstáculos D1 se conservan
    enable_d1_storyline_levels: bool = True        # Storyline A/V de D1 para detección de Key Levels macro contrarios
    enable_crt_sweep_rejection: bool = True        # Candle Range Theory (CRT): M15 exige barrido de mecha + absorción de cierre
    enable_quasimodo_pattern: bool = True          # Patrón Quasimodo estructural de swing (Left Shoulder retest)
    enable_qmc_pattern: bool = True                # Quasimodo de Continuación (QMC en tendencia)
    enable_fakeout_trap: bool = True               # Módulo Fakeout Trap / Absorción de Stop Hunts
    max_fakeout_penetration_atr: float = 0.60      # Penetración máxima permitida en Fakeout Trap (0.60 ATR)
    fakeout_min_wick_ratio: float = 0.50           # Absorción mínima de mecha en Fakeout Trap (>= 50%)
    enable_m15_micro_stop: bool = False             # Stop Loss micro-estructural anclado a mecha M15
    m15_micro_stop_buffer_atr: float = 0.10        # Buffer protector sobre extremo de mecha M15 (0.10 ATR)
    m15_micro_stop_min_risk_atr: float = 0.20      # Piso mínimo de riesgo micro para evitar stops sub-spread (0.20 ATR)
    enable_runner_trailing_lock: bool = True       # Trailing escalonado protector para posición runner
    enable_h1_ema_confluence: bool = True          # Confluencia dinámica con EMA 50 en H1
    h1_ema_period: int = 50                        # Periodo de la EMA dinámica (50)
    h1_ema_tolerance_atr: float = 0.40             # Tolerancia de proximidad hacia la EMA 50 (0.40 ATR)
    enable_obstacle_awareness: bool = True         # Ajuste dinámico de TP2 al detectar Key Level contrario intermedio
    min_obstacle_rr: float = 2.0                   # Clearance mínimo exigido hacia el obstáculo D1 opuesto (>= 2.0R)
    
    # Escenarios habilitados
    enable_scenario_1_continuation: bool = False
    continuation_min_adx: float = 20.0
    continuation_max_entry_distance_atr: float = 0.50
    continuation_fresh_only: bool = True
    continuation_direct_trigger: bool = True
    enable_setup_diagnostics: bool = True
    enable_structure_cache: bool = True
    # Isolated replays retain legacy rules; runtime preferences enable observation.
    av_entry_mode: str = 'off'
    av_entry_definition: str = 'body_turns'
    role_flip_mode: str = 'off'
    role_flip_max_changes: int = 1
    role_flip_min_displacement_atr: float = .20
    qm_extended_mode: str = 'off'
    qm_extended_swing_window: int = 8
    qm_extended_min_head_depth_atr: float = .20
    macro_structure_mode: str = 'off'
    macro_bias_method: str = 'd1_structure'
    macro_pivot_radius: int = 2
    gap_mode: str = 'off'
    gap_timeframe: str = 'H1'
    gap_min_size_atr: float = .05
    gap_min_ticks: int = 2
    gap_min_spread_multiple: float = 2.
    gap_tick_size: float = 0.
    gap_spread: float = 0.
    adaptive_history_enabled: bool = True
    history_min_h1: int = 28
    history_min_d1: int = 30
    history_max_request: int = 320
    m5_confirmation_mode: str = 'off'
    recovery_window_minutes: int = 45
    recovery_min_body_ratio: float = 0.35
    h4_neutral_fallback_mode: str = 'off'
    ai_mode: str = 'filter'
    ai_incompatible_policy: str = 'block'
    ai_min_probability: float = 0.47
    ai_min_probability_forex: float = 0.55
    ai_min_probability_gold: float = 0.55
    ai_min_probability_volatility: float = 0.47
    ai_min_net_expectancy_r: float = 0.05
    enable_candidate_audit: bool = True
    observe_candidate_outcomes: bool = True
    candidate_outcome_hours: int = 24
    enable_scenario_3_fractal: bool = True
    fractal_min_body_ratio: float = DEFAULT_FRACTAL_MIN_BODY_RATIO
    fractal_max_entry_distance_atr: float = DEFAULT_FRACTAL_MAX_ENTRY_DISTANCE_ATR
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

    # Selección histórica conservada; no acredita ventaja en la versión actual.
    allowed_symbols: tuple = (
        # Sintéticos
        "Step Index 400", "Crash 1000 Index", "Jump 25 Index", "Boom 300 Index",
        "Volatility 250 (1s) Index", "Step Index", "Jump 10 Index",
        "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 1000 Index",
        "Step Index 200", "Crash 600 Index",
        # Metales
        "XAGUSD", "XAUUSD",
        # Forex e índices
        "GBPJPY", "EURUSD", "USDJPY", "AUDNZD", "GBPUSD", "GBPAUD",
        "Wall Street 30", "EURCHF", "EURGBP",
    )
