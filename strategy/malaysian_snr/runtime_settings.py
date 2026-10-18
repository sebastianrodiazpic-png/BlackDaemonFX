"""Validation shared by persisted preferences, HTTP controls and live analysis."""
import math
from copy import deepcopy
from .universe import CATALOG_SYMBOLS

DEFAULT_FRACTAL_MIN_BODY_RATIO = 0.50
DEFAULT_FRACTAL_MAX_ENTRY_DISTANCE_ATR = 0.50

ADDITIONAL_SYMBOLS = ('Jump 50 Index', 'Jump 100 Index', 'Jump 75 Index', 'Volatility 75 (1s) Index')
MSNR_DEFAULT_SETTINGS = {
    'breaker_pair_mode': 'shadow',
    'breaker_pair_min_body_ratio': .50,
    'breaker_pair_min_displacement_atr': .50,
    'retest_pinbar_mode': 'shadow',
    'retest_pinbar_min_wick_ratio': .55,
    'retest_pinbar_min_close_ratio': .75,
    # The pilot did not justify replacing the primary session / obstacle rules.
    'session_policy': 'legacy_utc',
    'obstacle_av_definition': 'engulfing',
    'h4_obstacle_mode': 'shadow',
    'enable_synthetic_daily_storyline_filter': False,
    'fractal_min_body_ratio': DEFAULT_FRACTAL_MIN_BODY_RATIO,
    'fractal_max_entry_distance_atr': DEFAULT_FRACTAL_MAX_ENTRY_DISTANCE_ATR,
    'additional_symbols': list(ADDITIONAL_SYMBOLS[:2]),
    'additional_symbols_mode': 'shadow',
    'continuation_mode': 'live',
    'continuation_max_entry_distance_atr': 0.50,
    'continuation_maximum_breakout_wick_ratio': 0.25,
    'qm_max_entry_distance_atr': 0.50,
    'asset_modes': {},
    'm5_symbol_modes': {},
    'continuation_symbol_modes': {},
    'step_min_adx': 25.0,
    'step_symbol_min_adx': {},
    'research_min_frequency_ratio': 1.05,
    'research_min_resolved_trades': 50,
    'research_min_win_rate_improvement_pp': 1.0,
    'continuation_min_body_ratio': .50,
    'continuation_min_adx': 20.,
    'continuation_fresh_only': True,
    'continuation_direct_trigger': True,
    'retest_window_minutes': 360,
    'confirmation_tolerance_bars': 2,
    'confirmation_tolerance_max_atr': 0.35,
    'enable_setup_diagnostics': True,
    'enable_structure_cache': True,
    'prioritize_pending_retests': True,
    'analysis_outside_entry_lock': True,
    'av_entry_mode': 'shadow',
    'av_entry_definition': 'body_turns',
    'role_flip_mode': 'shadow',
    'role_flip_max_changes': 1,
    'role_flip_min_displacement_atr': .20,
    'qm_extended_mode': 'shadow',
    'qm_extended_swing_window': 8,
    'qm_extended_min_head_depth_atr': .20,
    'macro_structure_mode': 'shadow',
    'macro_bias_method': 'd1_structure',
    'macro_pivot_radius': 2,
    'gap_mode': 'shadow',
    'gap_timeframe': 'H1',
    'gap_min_size_atr': .05,
    'gap_min_ticks': 2,
    'gap_min_spread_multiple': 2.,
    'adaptive_history_enabled': True,
    'history_min_h1': 28,
    'history_min_d1': 30,
    'history_max_request': 320,
    'm5_confirmation_mode': 'shadow',
    'recovery_window_minutes': 90,
    'recovery_min_body_ratio': 0.35,
    'h4_neutral_fallback_mode': 'shadow',
    'ai_mode': 'filter',
    'ai_incompatible_policy': 'block',
    'ai_min_probability': 0.47,
    'ai_min_probability_forex': 0.55,
    'ai_min_probability_gold': 0.55,
    'ai_min_probability_volatility': 0.47,
    'ai_min_net_expectancy_r': 0.05,
    'enable_candidate_audit': True,
    'observe_candidate_outcomes': True,
    'candidate_outcome_hours': 24,
    'enable_fakeout_trap': True,
    'max_fakeout_penetration_atr': 0.60,
    'fakeout_min_wick_ratio': 0.50,
    'enable_qmc_pattern': True,
    'enable_m15_micro_stop': True,
    'enable_runner_trailing_lock': True,
    'enable_h1_ema_confluence': True,
}


def msnr_default_settings():
    return deepcopy(MSNR_DEFAULT_SETTINGS)


def validate_msnr_patch(settings):
    if not isinstance(settings, dict) or not settings or not set(settings) <= set(MSNR_DEFAULT_SETTINGS):
        raise ValueError('Debes enviar ajustes válidos de Malaysian SNR')
    validated = {}
    for key, value in settings.items():
        if key == 'session_policy':
            if value not in ('legacy_utc', 'market_hours'):
                raise ValueError('Selecciona horario UTC anterior u horario por mercado')
        elif key in ('breaker_pair_min_body_ratio', 'retest_pinbar_min_wick_ratio', 'retest_pinbar_min_close_ratio'):
            value = validate_fractal_min_body_ratio(value)
            if value < (.50 if key == 'retest_pinbar_min_close_ratio' else .01):
                raise ValueError('El mínimo del patrón debe ser positivo; el cierre debe recuperar al menos 50% del rango')
        elif key == 'step_symbol_min_adx':
            step_symbols=tuple(s for s in CATALOG_SYMBOLS if s.startswith('Step Index'))
            if (not isinstance(value,dict) or any(s not in step_symbols or type(v) not in (int,float)
                    or not 0<=v<=100 or not math.isfinite(v) for s,v in value.items())):
                raise ValueError('ADX propio: selecciona un Step del catálogo y un valor finito entre 0 y 100')
            value={s:float(value[s]) for s in step_symbols if s in value}
        elif key == 'step_min_adx':
            if type(value) not in (int,float) or not 0<=value<=100 or not math.isfinite(value):
                raise ValueError('ADX de ejecución Step SNR: ingresa un valor entre 0 y 100')
            value=float(value)
        elif key in ('asset_modes', 'm5_symbol_modes', 'continuation_symbol_modes'):
            if (not isinstance(value, dict) or len(value)>len(CATALOG_SYMBOLS)
                    or any(type(s) is not str or s not in CATALOG_SYMBOLS
                           or type(mode) is not str or mode not in ('off','shadow','live') for s,mode in value.items())):
                raise ValueError('Selecciona activos del catálogo SNR y modos válidos')
            value = {s:value[s] for s in CATALOG_SYMBOLS if s in value}
        elif key in ('continuation_max_entry_distance_atr', 'qm_max_entry_distance_atr'):
            value = validate_fractal_max_entry_distance_atr(value)
            if value>5:
                raise ValueError('La distancia debe estar entre 0 y 5 ATR H1')
        elif key in ('research_min_frequency_ratio', 'research_min_win_rate_improvement_pp'):
            upper = 5 if key=='research_min_frequency_ratio' else 100
            if type(value) not in (int,float) or not 0<=value<=upper or not math.isfinite(value):
                raise ValueError('Objetivo de comparación fuera de rango: frecuencia 0–500% y mejora WinRate 0–100 puntos')
            value=float(value)
        elif key == 'continuation_maximum_breakout_wick_ratio':
            value = validate_fractal_min_body_ratio(value)
        elif key == 'research_min_resolved_trades':
            if type(value) is not int or not 10<=value<=10000:
                raise ValueError('La muestra mínima debe estar entre 10 y 10000 trades resueltos')
        elif key == 'ai_mode':
            if value not in ('off', 'shadow', 'filter'):
                raise ValueError('Selecciona un modo de IA valido')
        elif key == 'ai_incompatible_policy':
            if value not in ('block', 'observe'):
                raise ValueError('Selecciona Bloquear u Observar para modelos incompatibles')
        elif key in ('history_min_h1', 'history_min_d1', 'history_max_request',
                     'recovery_window_minutes', 'candidate_outcome_hours'):
            limits = {'history_min_h1': (28, 200), 'history_min_d1': (7, 200),
                      'history_max_request': (200, 3200), 'recovery_window_minutes': (5, 120),
                      'candidate_outcome_hours': (1, 72)}
            low, high = limits[key]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{key}: ingresa un entero entre {low} y {high}')
            if key == 'recovery_window_minutes' and value % 5:
                raise ValueError('La recuperacion debe ser multiplo de 5 minutos')
        elif key.startswith('ai_min_probability') or key == 'recovery_min_body_ratio':
            value = validate_fractal_min_body_ratio(value)
            if key == 'recovery_min_body_ratio' and value<=0:
                raise ValueError('El cuerpo minimo de recuperacion debe ser mayor que cero')
        elif key == 'ai_min_net_expectancy_r':
            if type(value) not in (int, float) or not -1 <= value <= 5 or not math.isfinite(value):
                raise ValueError('Expectativa minima: ingresa un valor entre -1 y 5 R')
            value = float(value)
        elif key.endswith('_mode'):
            if value not in ('off', 'shadow', 'live'):
                raise ValueError('El modo debe ser Desactivado, Observación u Operar')
        elif key in ('av_entry_definition', 'obstacle_av_definition', 'macro_bias_method', 'gap_timeframe'):
            allowed = {'av_entry_definition': ('engulfing', 'body_turns'),
                       'obstacle_av_definition': ('engulfing', 'body_turns'),
                       'macro_bias_method': ('d1_structure', 'h4_structure', 'd1_h4_structure'),
                       'gap_timeframe': ('H1', 'H4')}
            if type(value) is not str or value not in allowed[key]:
                raise ValueError('Selecciona una opción válida para la estructura SNR')
        elif key in ('role_flip_max_changes', 'qm_extended_swing_window', 'macro_pivot_radius', 'gap_min_ticks'):
            limits = {'role_flip_max_changes': (1, 3), 'qm_extended_swing_window': (4, 12),
                       'macro_pivot_radius': (1, 5), 'gap_min_ticks': (1, 100)}
            low, high = limits[key]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{key}: ingresa un entero entre {low} y {high}')
        elif key in ('role_flip_min_displacement_atr', 'qm_extended_min_head_depth_atr',
                     'gap_min_size_atr', 'gap_min_spread_multiple', 'breaker_pair_min_displacement_atr'):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= (10 if key == 'gap_min_spread_multiple' else 5):
                raise ValueError('La distancia estructural debe ser positiva y estar dentro del límite indicado')
            value = float(value)
        elif key == 'additional_symbols':
            if not isinstance(value, list) or any(type(s) is not str or s not in ADDITIONAL_SYMBOLS for s in value):
                raise ValueError('Selecciona únicamente los activos candidatos disponibles')
            value = [s for s in ADDITIONAL_SYMBOLS if s in value]
        elif type(MSNR_DEFAULT_SETTINGS[key]) is bool:
            if type(value) is not bool:
                raise ValueError('Los interruptores deben ser verdadero o falso')
        elif key in ('fractal_min_body_ratio', 'continuation_min_body_ratio'):
            value = validate_fractal_min_body_ratio(value)
        elif key == 'fractal_max_entry_distance_atr':
            value = validate_fractal_max_entry_distance_atr(value)
        elif key == 'continuation_min_adx':
            if type(value) not in (int, float) or not 0 <= value <= 100:
                raise ValueError('El ADX mínimo debe estar entre 0 y 100')
            value = float(value)
        elif key == 'retest_window_minutes':
            if type(value) is not int or not 15 <= value <= 480:
                raise ValueError('La ventana de retest debe ser un número entero entre 15 y 480 minutos')
        elif key == 'confirmation_tolerance_bars':
            if type(value) is not int or not 0 <= value <= 5:
                raise ValueError('La tolerancia de velas debe ser un número entero entre 0 y 5')
        elif key == 'confirmation_tolerance_max_atr':
            if type(value) not in (int, float) or not 0.05 <= value <= 1.5 or not math.isfinite(value):
                raise ValueError('La distancia ATR de tolerancia debe ser entre 0.05 y 1.5')
            value = float(value)
        elif key == 'max_fakeout_penetration_atr':
            if type(value) not in (int, float) or not 0.05 <= value <= 2.0 or not math.isfinite(value):
                raise ValueError('Penetración Fakeout: ingresa un valor entre 0.05 y 2.0 ATR')
            value = float(value)
        elif key == 'fakeout_min_wick_ratio':
            value = validate_fractal_min_body_ratio(value)
            if value <= 0:
                raise ValueError('La mecha mínima de Fakeout debe ser mayor a 0')
        validated[key] = deepcopy(value)
    return validated


def validate_fractal_min_body_ratio(value):
    if type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value):
        raise ValueError('El cuerpo mínimo del Fractal H1 debe ser un porcentaje entre 0 y 100')
    return float(value)


def normalize_msnr_settings(settings):
    return validate_msnr_patch({**msnr_default_settings(), **settings})


def validate_fractal_max_entry_distance_atr(value):
    message = 'La distancia máxima de entrada Fractal debe ser un número finito mayor o igual a 0, en ATR H1'
    if type(value) not in (int, float):
        raise ValueError(message)
    try:
        value = float(value)
    except (ValueError, OverflowError):
        raise ValueError(message) from None
    if not math.isfinite(value) or value < 0:
        raise ValueError(message)
    return value
