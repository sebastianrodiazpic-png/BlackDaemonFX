"""Configuración de la Estrategia Malaysian SNR.

Los replays heredados no validan rentabilidad de la versión causal actual.
- Escenario 1 permanece deshabilitado por defecto.
- Filtro de cuerpo sólido mínimo (>= 50%) y mecha reducida (<= 30%).
- Gestión Dual-Leg:
  - Entrada 1: TP1 mínimo 1:2.0 RR.
  - Entrada 2: Runner contextual (TP2 1:2.5, TP3 1:3.0, TP4 1:4.0).
  - Al tocar TP1: Mover Stop Loss de Entrada 2 a Break-Even + spread buffer.
"""

import os
from dataclasses import dataclass
from strategy.malaysian_snr.runtime_settings import DEFAULT_FRACTAL_MIN_BODY_RATIO, DEFAULT_FRACTAL_MAX_ENTRY_DISTANCE_ATR


# Versión con la que se registran las operaciones de MSNR en mercados reales (criterio de su prueba demo).
MSNR_REAL_STRATEGY_VERSION = "msnr-real-markets-v1"


def instruments_tab_control_enabled(config=None) -> bool:
    """/Instruments como único control de Malaysian SNR: el campo de la config o DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL."""
    value = getattr(config, "instruments_tab_control", None)
    if value is not None:
        return bool(value)
    return os.getenv("DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL", "on").strip().lower() not in ("0", "false", "off")

@dataclass
class MalaysianSNRConfig:
    enabled: bool = True
    strategy_name: str = "MALAYSIAN_SNR"
    strategy_version: str = "msnr-v3.2-hybrid-alchemist"
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
    retest_window_minutes: int = int(os.getenv("DAEMONBLACKFX_MSNR_RETEST_WINDOW_MINUTES", "90"))
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
    enable_fakeout_trap: bool = os.getenv("DAEMONBLACKFX_MSNR_FAKEOUT_TRAP", "1").strip().lower() in ("1", "true", "on")  # Barridos fakeout activados con absorción
    dynamic_retest_buffer_enabled: bool = os.getenv("DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER", "0").strip().lower() in ("1", "true", "on")  # Buffer dinámico ATR H1 (0.20 ATR)
    dynamic_retest_buffer_atr: float = float(os.getenv("DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER_ATR", "0.20"))  # Tolerancia dinámica de 0.20 ATR H1
    min_sl_atr_h1: float = float(os.getenv("DAEMONBLACKFX_MSNR_MIN_SL_ATR_H1", "0.0"))  # Piso estructural opcional de SL en sintéticos
    max_fakeout_penetration_atr: float = 0.60      # Penetración máxima permitida en Fakeout Trap (0.60 ATR)
    fakeout_min_wick_ratio: float = 0.50           # Absorción mínima de mecha en Fakeout Trap (>= 50%)
    enable_m15_micro_stop: bool = False             # Stop Loss micro-estructural anclado a mecha M15
    m15_micro_stop_buffer_atr: float = 0.10        # Buffer protector sobre extremo de mecha M15 (0.10 ATR)
    m15_micro_stop_min_risk_atr: float = 0.20      # Piso mínimo de riesgo micro para evitar stops sub-spread (0.20 ATR)
    enable_runner_trailing_lock: bool = True       # SIN EFECTO: ningún código la lee. El runner MSNR usa la extensión progresiva del motor (2R→+1R, 3R→+2,5R)
    enable_h1_ema_confluence: bool = True          # Confluencia dinámica con EMA 50 en H1
    h1_ema_period: int = 50                        # Periodo de la EMA dinámica (50)
    h1_ema_tolerance_atr: float = 0.40             # Tolerancia de proximidad hacia la EMA 50 (0.40 ATR)
    enable_obstacle_awareness: bool = True         # Ajuste dinámico de TP2 al detectar Key Level contrario intermedio
    min_obstacle_rr: float = float(os.getenv("DAEMONBLACKFX_MSNR_MIN_OBSTACLE_RR", "2.0"))  # Clearance mínimo exigido hacia el obstáculo D1 opuesto (>= 2.0R base)
    directional_asymmetry_enabled: bool = os.getenv("DAEMONBLACKFX_MSNR_DIRECTIONAL_ASYMMETRY", "0").strip().lower() in ("1", "true", "on")
    jump_buy_only_symbols: tuple = tuple(s.strip() for s in os.getenv("DAEMONBLACKFX_MSNR_JUMP_BUY_ONLY", "Jump 50 Index,Jump 75 Index").split(",") if s.strip())
    step_sell_only_symbols: tuple = tuple(s.strip() for s in os.getenv("DAEMONBLACKFX_MSNR_STEP_SELL_ONLY", "Step Index 200,Step Index 400,Step Index 500").split(",") if s.strip())
    
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
    ai_incompatible_policy: str = 'observe'  # solo DEMO; ver runtime_settings.DEFAULT_AI_INCOMPATIBLE_POLICY
    ai_min_probability: float = 0.47
    ai_min_probability_forex: float = 0.55
    ai_min_probability_gold: float = 0.55
    ai_min_probability_volatility: float = 0.47
    ai_min_net_expectancy_r: float = 0.05
    enable_candidate_audit: bool = True
    observe_candidate_outcomes: bool = True
    candidate_outcome_hours: int = 24
    enable_scenario_3_fractal: bool = os.getenv("DAEMONBLACKFX_MSNR_ENABLE_FRACTAL", "1").strip().lower() in ("1", "true", "on")  # Escenario 3 Fractal M15/H1
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

    # Variante C2 (Staging): Tope de Stop Loss en unidades ATR (<= 1.2 en Forex/Metales, <= 1.5 en Sintéticos y Wall Street 30)
    min_adx: float = 30.0
    # Solo sintéticos: los mercados reales tienen expectativa negativa en el replay fiel de 2 años.
    synthetics_only: bool = False
    # Mercados reales en PRUEBA DEMO (25-oct-2026, decisión del usuario). Replay fiel 3 años con spread de ticks: elegir
    # con el pasado los instrumentos de bajo coste (spread/SL mediano <= 2 %) fue positivo en los 3 saltos (+0,104 /
    # +0,079 / +0,112 R/op, no concluyente). Estos símbolos pasan aunque synthetics_only sea True, usan los ajustes POR
    # DEFECTO (los de la base, con Breaker Pair y Pinbar en live, perdían en Forex) y la sesión `real_market_session_policy`.
    real_market_symbols: tuple = tuple(s.strip() for s in os.getenv(
        "DAEMONBLACKFX_MSNR_REAL_SYMBOLS",
        # Decisión del usuario (25-oct-2026): acierto > 47 % en el replay con el cierre de las 16:45 NY, más los
        # forex con acierto > 47 % en el replay fiel de 3 años (NZDUSD ... CHFJPY).
        "Germany 40,XAUUSD,USDJPY,GBPUSD,NZDUSD,GBPCAD,CADCHF,EURGBP,GBPCHF,CADJPY,GBPJPY"
    ).split(",") if s.strip())
    real_markets_enabled: bool = os.getenv("DAEMONBLACKFX_MSNR_REAL_MARKETS", "demo_test").strip().lower() not in ("off", "0", "false")
    real_market_default_settings: bool = True
    # Asia → Nueva York (decisión del usuario): entradas desde la apertura de Tokio hasta 3 h antes del rollover de NY
    # (17:00 NY), para no pagar swap; el motor además cierra Forex, índices y metales a las 16:45 NY.
    real_market_session_policy: str = os.getenv("DAEMONBLACKFX_MSNR_REAL_SESSION", "asia_to_ny").strip()
    # Horario por activo ("SÍMBOLO:política,..."). Por defecto EURUSD con Londres + NY (legacy_utc): con acierto > 47 %
    # solo en ese horario (53 %); con Asia → NY 39 %. Germany 40, XAUUSD y USDJPY superan en ambos (Londres + NY cae
    # dentro de Asia → NY) y GBPUSD solo en Asia → NY: usan la política general.
    # Los forex añadidos por acierto > 47 % (25-oct-2026) se midieron en Londres + NY: también usan legacy_utc.
    real_market_session_overrides: str = os.getenv(
        "DAEMONBLACKFX_MSNR_REAL_SESSION_OVERRIDES",
        "NZDUSD:legacy_utc,GBPCAD:legacy_utc,CADCHF:legacy_utc,"
        "EURGBP:legacy_utc,GBPCHF:legacy_utc,CADJPY:legacy_utc,GBPJPY:legacy_utc").strip()
    # Escenario H4→H1 (strategy/malaysian_snr/h4h1_confirmation.py). El motor lo activa según
    # DAEMONBLACKFX_MSNR_H4H1 (demo_test = solo DEMO); runner a 2R como en el replay.
    enable_h4h1_confirmation: bool = False
    h4h1_runner_rr: float = 2.0
    # El escenario H4→H1 solo se evalúa en sintéticos (validado ahí). False permite medirlo en mercados reales.
    h4h1_synthetics_only: bool = True
    # /Instruments como único control (25-oct-2026, decisión del usuario): se ignoran el «modo propio del activo»
    # (`asset_modes`) y los símbolos adicionales de los ajustes en la base; qué se escanea y opera lo decide solo la
    # selección de la pestaña Malaysian SNR. DAEMONBLACKFX_MSNR_INSTRUMENTS_CONTROL=off restaura los modos por activo.
    # None = lo decide la variable en cada ciclo (instruments_tab_control_enabled).
    instruments_tab_control: bool | None = None
    # Instrumentos podados (acierto <= 45% en el replay fiel); el motor pasa config/strategy_config.py:MSNR_WR45_PRUNED.
    excluded_symbols: tuple = ()
    enable_c2_fx_metals_atr_cap: bool = False
    c2_fx_metals_max_sl_atr: float = 1.2
    c2_default_max_sl_atr: float = 1.5

    # Selección histórica conservada; 23 activos canónicos rentables/marginales.
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


def msnr_c2_staging_config(**overrides) -> MalaysianSNRConfig:
    """Devuelve la configuración de Staging para Malaysian SNR Variante C2 (60.6% WR, +37.64R)."""
    params = dict(
        min_adx=30.0,
        enable_c2_fx_metals_atr_cap=True,
        c2_fx_metals_max_sl_atr=1.2,
        c2_default_max_sl_atr=1.5,
        continuation_min_adx=30.0,
    )
    params.update(overrides)
    return MalaysianSNRConfig(**params)

