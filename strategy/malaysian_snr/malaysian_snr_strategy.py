"""Estrategia de Trading Institucional: Malaysian SNR (Support & Resistance Malayo).

Estrategia independiente enfocada en:
1. Break: Punto de unión de cuerpos consecutivos (Close[t-1] y Open[t]).
2. Patrón A / V: Envolventes que marcan crestas (Resistencia) y valles (Soporte).
3. Fresh vs No Fresh: nivel sin contacto posterior de mechas antes de la ruptura.
4. Escenarios con causalidad temporal (rentabilidad pendiente de validación):
   - Escenario 1: Ruptura Clásica Fresh -> Retest al nivel Break en M15.
   - Escenario 3: Fractalidad (HCH / Quiebre estructural acelerado).
5. Doble Pierna Asimétrica:
   - Pierna 1: TP1 mínimo 1:2.0 RR (50% de la posición).
   - Pierna 2: Corredora contextual (TP2 1:2.5, TP3 1:3.0, TP4 1:4.0) con Break-Even automático al tocar TP1.
"""

from __future__ import annotations
import math
import hashlib
import json
from copy import copy, deepcopy
from dataclasses import asdict, replace
from threading import RLock
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from strategy.malaysian_snr.history import useful_history
from strategy.malaysian_snr.video_rules import session_allowed, breaker_pair_candidate, track_session_liquidity, fakeout_trap_candidate, h1_ema_dynamic_confluence
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import validate_fractal_min_body_ratio, validate_fractal_max_entry_distance_atr
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, normalize_msnr_settings
from strategy.malaysian_snr.universe import resolve_symbol_settings, canonical_symbol
from config.symbol_policy import is_direction_allowed
from strategy.malaysian_snr.opportunity_rules import (structural_bias, role_flip_candidates,
    extended_quasimodo_candidates, gap_candidate)
from strategy.malaysian_snr.validation import (closed_candles, timeframe_delta, av_levels,
                                               active_av_levels, level_freshness, retest_confirmation,
                                               quasimodo_candidates, quasimodo_continuation_candidates)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr = pd.Series(tr).ewm(alpha=1/period, min_periods=period).mean()
    plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    return dx.ewm(alpha=1/period, min_periods=period).mean()


def is_synthetic_symbol(symbol: str) -> bool:
    s = str(symbol).upper()
    synth_keywords = ["JUMP", "CRASH", "BOOM", "STEP", "VOLATILITY", "RANGE BREAK", "DEX", "DRIFT SWITCHING", "DAILY RESET", "HYBRID", "FLIP", "VOL ", "VOLSWITCH", "SKEW", "MULTI STEP", "SPOT UP", "1HZ", "V10", "V25", "V50", "V75", "V100"]
    return any(kw in s for kw in synth_keywords)


def is_fx_or_metal_symbol(symbol: str) -> bool:
    """Identifica divisas Forex y Metales preciosos (XAUUSD, XAGUSD) excluyendo Sintéticos e Índices (Wall Street 30)."""
    if is_synthetic_symbol(symbol):
        return False
    s = str(symbol).strip().upper().removesuffix("MICRO")
    index_or_commodity_keywords = ("WALL STREET", "US TECH", "US SP", "US500", "US30", "NAS100", "OIL", "BRENT", "BTC", "ETH", "SOL")
    if any(kw in s for kw in index_or_commodity_keywords):
        return False
    if s in ("XAUUSD", "XAGUSD"):
        return True
    fx_ccys = ("EUR", "GBP", "USD", "JPY", "AUD", "NZD", "CAD", "CHF")
    return len(s) == 6 and s[:3] in fx_ccys and s[3:] in fx_ccys


class MalaysianSNRStrategy:
    """Implementación de la estrategia Malaysian SNR para análisis en tiempo real."""

    def __init__(self, data_provider, config: MalaysianSNRConfig | None = None, runtime_settings_loader=None):
        self.provider = data_provider
        self.config = config or MalaysianSNRConfig()
        self.runtime_settings_loader = runtime_settings_loader
        self._structure_cache = {}
        self._structure_cache_lock = RLock()

    def settings_snapshot(self):
        if self.runtime_settings_loader is not None:
            raw = self.runtime_settings_loader()
            settings = normalize_msnr_settings({k:v for k,v in raw.items() if k not in ('version','updated_at')})
            return {**settings, 'version':raw.get('version',0)}
        settings = msnr_default_settings()
        for key in settings:
            if hasattr(self.config, key):
                settings[key] = getattr(self.config, key)
        settings.update(additional_symbols=[], additional_symbols_mode='off',
            continuation_maximum_breakout_wick_ratio=self.config.maximum_breakout_wick_ratio,
            qm_max_entry_distance_atr=self.config.max_entry_distance_atr,
            continuation_mode='live' if self.config.enable_scenario_1_continuation else 'off',
            continuation_min_body_ratio=self.config.minimum_body_ratio)
        return {**normalize_msnr_settings(settings), 'version':0}

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        try:
            settings = self.settings_snapshot()
        except Exception:
            return {'valid':False, 'strategy_name':self.config.strategy_name,
                'strategy_version':self.config.strategy_version, 'symbol':symbol,
                'action':'WAITING_MALAYSIAN_SNR', 'reason':'MSNR_SETTINGS_UNAVAILABLE'}
        context = copy(self)
        settings = resolve_symbol_settings(settings, symbol)
        context.runtime_settings_loader = None
        context._runtime_controls = settings
        context._asset_mode = settings['asset_modes'].get(canonical_symbol(symbol))
        if context._asset_mode == 'off':
            return {'valid': False, 'symbol':symbol, 'strategy_name':self.config.strategy_name,
                'strategy_version':self.config.strategy_version, 'reason':'MSNR_SYMBOL_DISABLED',
                'action':'WAITING_MALAYSIAN_SNR', 'runtime_controls':settings,
                'runtime_settings_version':settings['version']}
        context._cycle_history_cache = {}
        context._runtime_settings_version = settings['version']
        extra = settings['additional_symbols'] if settings['additional_symbols_mode'] != 'off' else []
        extra = [*extra, *[name for name,mode in settings['asset_modes'].items() if mode!='off']]
        allowed = tuple(self.config.allowed_symbols or ())
        context.config = replace(self.config,
            **{k:settings[k] for k in ('breaker_pair_mode', 'breaker_pair_min_body_ratio',
                'breaker_pair_min_displacement_atr', 'retest_pinbar_mode', 'retest_pinbar_min_wick_ratio',
                'retest_pinbar_min_close_ratio', 'session_policy', 'obstacle_av_definition', 'h4_obstacle_mode',
                'av_entry_mode', 'av_entry_definition', 'role_flip_mode',
                'role_flip_max_changes', 'role_flip_min_displacement_atr', 'qm_extended_mode',
                'qm_extended_swing_window', 'qm_extended_min_head_depth_atr', 'macro_structure_mode',
                'macro_bias_method', 'macro_pivot_radius', 'gap_mode', 'gap_timeframe',
                'gap_min_size_atr', 'gap_min_ticks', 'gap_min_spread_multiple',
                'adaptive_history_enabled', 'history_min_h1', 'history_min_d1', 'history_max_request',
                'm5_confirmation_mode', 'recovery_window_minutes', 'recovery_min_body_ratio', 'h4_neutral_fallback_mode',
                'ai_mode', 'ai_incompatible_policy', 'ai_min_probability', 'ai_min_probability_forex',
                'ai_min_probability_gold', 'ai_min_probability_volatility', 'ai_min_net_expectancy_r', 'enable_candidate_audit',
                'observe_candidate_outcomes', 'candidate_outcome_hours')},
            enable_synthetic_daily_storyline_filter=settings['enable_synthetic_daily_storyline_filter'],
            fractal_min_body_ratio=settings['fractal_min_body_ratio'],
            fractal_max_entry_distance_atr=settings['fractal_max_entry_distance_atr'],
            enable_fakeout_trap=settings.get('enable_fakeout_trap', getattr(self.config, 'enable_fakeout_trap', True)),
            max_fakeout_penetration_atr=settings.get('max_fakeout_penetration_atr', getattr(self.config, 'max_fakeout_penetration_atr', 0.60)),
            fakeout_min_wick_ratio=settings.get('fakeout_min_wick_ratio', getattr(self.config, 'fakeout_min_wick_ratio', 0.50)),
            enable_qmc_pattern=settings.get('enable_qmc_pattern', getattr(self.config, 'enable_qmc_pattern', True)),
            enable_m15_micro_stop=settings.get('enable_m15_micro_stop', getattr(self.config, 'enable_m15_micro_stop', True)),
            enable_runner_trailing_lock=settings.get('enable_runner_trailing_lock', getattr(self.config, 'enable_runner_trailing_lock', True)),
            enable_h1_ema_confluence=settings.get('enable_h1_ema_confluence', getattr(self.config, 'enable_h1_ema_confluence', True)),
            enable_scenario_1_continuation=settings['continuation_mode'] != 'off',
            minimum_body_ratio=settings['continuation_min_body_ratio'],
            continuation_min_adx=settings['continuation_min_adx'],
            continuation_max_entry_distance_atr=settings['continuation_max_entry_distance_atr'],
            maximum_breakout_wick_ratio=settings['continuation_maximum_breakout_wick_ratio'],
            max_entry_distance_atr=settings['qm_max_entry_distance_atr'],
            continuation_fresh_only=settings['continuation_fresh_only'],
            retest_window_minutes=settings['retest_window_minutes'],
            enable_setup_diagnostics=settings['enable_setup_diagnostics'],
            enable_structure_cache=settings['enable_structure_cache'],
            allowed_symbols=tuple(dict.fromkeys((*allowed,*extra))) if allowed else ())
        from strategy.malaysian_snr.experiments import analyze_variants
        result = analyze_variants(context, symbol, now_utc)
        result['analysis_outside_entry_lock'] = settings['analysis_outside_entry_lock']
        result['runtime_controls'] = settings
        result['runtime_settings_version'] = settings['version']
        return result

    def _analyze_symbol_impl(self, symbol: str, now_utc: datetime | None = None) -> dict:
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        base = {"valid": False, "strategy_name": self.config.strategy_name,
                "strategy_version": self.config.strategy_version,
                "action": "WAITING_MALAYSIAN_SNR", "reason": "NO_SETUP_CONFIRMED", "symbol": symbol}
        if not self.config.enabled:
            return {**base, "reason": "STRATEGY_DISABLED"}
        synthetic_d1_filter = getattr(self.config, 'enable_synthetic_daily_storyline_filter', False)
        fractal_min_body_ratio = self.config.fractal_min_body_ratio
        fractal_max_entry_distance_atr = self.config.fractal_max_entry_distance_atr
        settings_version = getattr(self, '_runtime_settings_version', 0)
        loader = getattr(self, 'runtime_settings_loader', None)
        if loader is not None:
            try:
                settings = loader()
                synthetic_d1_filter = settings['enable_synthetic_daily_storyline_filter']
                if type(synthetic_d1_filter) is not bool:
                    raise ValueError('El veto D1 debe ser booleano')
                fractal_min_body_ratio = validate_fractal_min_body_ratio(settings['fractal_min_body_ratio'])
                fractal_max_entry_distance_atr = validate_fractal_max_entry_distance_atr(settings['fractal_max_entry_distance_atr'])
                settings_version = settings.get('version', 0)
            except Exception:
                return {**base, 'reason': 'MSNR_SETTINGS_UNAVAILABLE'}
        daily_bias_enforced = bool(self.config.enable_daily_storyline_filter and
                                  (not is_synthetic_symbol(symbol) or synthetic_d1_filter))
        base.update({'macro_bias_enforced': daily_bias_enforced,
                     'fractal_min_body_ratio': fractal_min_body_ratio,
                     'fractal_max_entry_distance_atr': fractal_max_entry_distance_atr,
                     'runtime_settings_version': settings_version})
        allowed = tuple(self.config.allowed_symbols or ())
        norm = str(symbol).strip().lower().removesuffix("micro")
        if allowed and norm not in {a.strip().lower().removesuffix("micro") for a in allowed}:
            return {**base, "reason": "SYMBOL_NOT_IN_MSNR_ALLOWLIST"}
        if self.config.enable_session_killzones_filter and not is_synthetic_symbol(symbol):
            try:
                in_session = session_allowed(symbol, now, self.config.session_policy)
            except ValueError as exc:
                return {**base, 'reason': str(exc)}
            if not in_session:
                return {**base, "reason": "SESSION_FILTER_OUTSIDE_KILLZONE"}
        try:
            history = {}
            def load(tf, count, minimum):
                cache = getattr(self, '_cycle_history_cache', {})
                key = (tf,count,minimum)
                if key not in cache:
                    cache[key] = useful_history(self.provider, symbol, tf, count, minimum, now,
                        adaptive=self.config.adaptive_history_enabled, limit=self.config.history_max_request)
                frame, diagnostic = cache[key]
                history[tf] = diagnostic
                return frame.copy()
            raw_h1 = load(self.config.structure_timeframe, 80, self.config.history_min_h1)
            raw_m15 = load(self.config.entry_timeframe, 180 if self.config.entry_timeframe=='M5' else 60, 20)
            raw_d1 = (load(self.config.macro_timeframe, 40, self.config.history_min_d1)
                      if (self.config.enable_daily_storyline_filter or getattr(self.config, 'enable_d1_storyline_levels', False)) else None)
            base['history_diagnostics'] = history
        except Exception as exc:
            return {**base, "reason": f"PROVIDER_ERROR: {exc}"}
        try:
            h1 = closed_candles(raw_h1, self.config.structure_timeframe, now)
            m15 = closed_candles(raw_m15, self.config.entry_timeframe, now)
            d1 = closed_candles(raw_d1, self.config.macro_timeframe, now) if raw_d1 is not None else pd.DataFrame()
        except (ValueError, TypeError, KeyError) as exc:
            return {**base, "reason": f"INVALID_CANDLE_DATA: {exc}"}
        if len(h1) < 28 or len(m15) < 20:
            return {**base, "reason": "INSUFFICIENT_CLOSED_CANDLES"}
        for frame, tf in ((h1, self.config.structure_timeframe), (m15, self.config.entry_timeframe)):
            delta = timeframe_delta(tf)
            if now - (frame.iloc[-1].time + delta) >= delta:
                return {**base, "reason": f"STALE_CANDLES_{tf}"}
        # Optional data failures disable only the affected alternative; live macro
        # filtering fails closed below when its required structure is unavailable.
        h4 = pd.DataFrame()
        need_h4 = ((daily_bias_enforced and self.config.macro_structure_mode != 'off'
                    and ('h4' in self.config.macro_bias_method or self.config.h4_neutral_fallback_mode != 'off'))
                   or (self.config.gap_mode != 'off' and self.config.gap_timeframe == 'H4'))
        if need_h4:
            try:
                h4 = load('H4', 80, max(28,2*self.config.macro_pivot_radius+3))
                if h4.empty or now-(h4.iloc[-1].time+timeframe_delta('H4')) >= timeframe_delta('H4'):
                    h4 = pd.DataFrame()
            except Exception:
                h4 = pd.DataFrame()
        gap_data_reason = None
        gap_needs_quote = False
        if self.config.gap_mode != 'off':
            gap_frame = h4 if self.config.gap_timeframe=='H4' else h1
            count = int(self.config.retest_window_minutes/(240 if self.config.gap_timeframe=='H4' else 60))+2
            for index in range(len(gap_frame)-1, max(26,len(gap_frame)-count-1),-1):
                prefix = gap_frame.iloc[:index+1]
                atr_at_creation = float(compute_atr(prefix).iloc[-1])
                if gap_candidate(prefix,atr_at_creation,self.config.gap_min_size_atr,1e-12,1e-12):
                    gap_needs_quote = True
                    break
            if not gap_needs_quote:
                gap_data_reason = 'GAP_H4_UNAVAILABLE' if self.config.gap_timeframe=='H4' and h4.empty else 'GAP_NO_MATERIAL_SEPARATION'
        if gap_needs_quote:
            try:
                info = self.provider.get_symbol_info(symbol)
                tick = self.provider.get_current_tick(symbol)
                size = float(info.get('trade_tick_size') or 0.)
                fallback = getattr(self.provider, 'fallback_provider', None)
                if size<=0 and fallback is not None:
                    size = float(fallback.get_symbol_info(symbol).get('trade_tick_size') or 0.)
                spread = float(tick['ask'])-float(tick['bid'])
                if not (math.isfinite(size) and size>0 and math.isfinite(spread) and spread>0):
                    raise ValueError('invalid market specification')
                self.config = replace(self.config, gap_tick_size=size, gap_spread=spread)
            except Exception:
                self.config = replace(self.config, gap_tick_size=0., gap_spread=0.)
                gap_data_reason = 'GAP_MARKET_SPEC_UNAVAILABLE'
        daily_direction = None
        if self.config.enable_daily_storyline_filter:
            if d1.empty:
                return {**base, "reason": "MISSING_CLOSED_D1"}
            if now - (d1.iloc[-1].time + timeframe_delta(self.config.macro_timeframe)) > pd.Timedelta(days=3):
                return {**base, "reason": "STALE_CANDLES_D1"}
            prev = d1.iloc[-1]
            if prev.close == prev.open and daily_bias_enforced and self.config.macro_structure_mode == 'off':
                return {**base, "reason": "NEUTRAL_D1_BIAS"}
            daily_direction = ("BUY" if prev.close > prev.open else
                               "SELL" if prev.close < prev.open else None)
        candle_direction = daily_direction
        structure_direction = None
        if daily_bias_enforced and self.config.macro_structure_mode != 'off':
            d1_bias = structural_bias(d1, self.config.macro_pivot_radius)
            h4_bias = structural_bias(h4, self.config.macro_pivot_radius)
            structure_direction = (d1_bias if self.config.macro_bias_method == 'd1_structure' else
                h4_bias if self.config.macro_bias_method == 'h4_structure' else
                d1_bias if d1_bias is not None and d1_bias == h4_bias else None)
            fallback_eligible = (self.config.macro_bias_method == 'd1_structure' and d1_bias is None
                and history.get(self.config.macro_timeframe, {}).get('sufficient')
                and h4_bias is not None and history.get('H4', {}).get('sufficient'))
            base['h4_neutral_fallback_eligible'] = bool(fallback_eligible)
            if fallback_eligible and self.config.h4_neutral_fallback_mode == 'live':
                structure_direction = h4_bias
                base['h4_neutral_fallback_used'] = True
            if self.config.macro_structure_mode == 'live':
                if structure_direction is None:
                    return {**base, 'reason':'MACRO_STRUCTURE_UNAVAILABLE_OR_NEUTRAL'}
                daily_direction = structure_direction
        base.update({'macro_structure_bias':structure_direction, 'macro_candle_bias':candle_direction,
                     'gap_data_reason':gap_data_reason})
        if (not 15 <= self.config.retest_window_minutes <= 360
                or self.config.retest_recovery_bars < 1
                or not 0 <= self.config.entry_execution_grace_seconds <= 120
                or not all(math.isfinite(value) and value >= 0 for value in (
                    self.config.retest_tolerance_atr, self.config.max_entry_distance_atr,
                    fractal_max_entry_distance_atr,
                    self.config.max_retest_penetration_atr, self.config.max_tested_wick_penetration_atr,
                    self.config.tested_level_displacement_atr))
                or not 0 < self.config.retest_min_body_ratio <= 1):
            return {**base, 'reason': 'INVALID_RETEST_CONFIG'}
        delta = timeframe_delta(self.config.structure_timeframe)
        entry_delta = timeframe_delta(self.config.entry_timeframe)
        controls = getattr(self, '_runtime_controls', {})
        retest_mins = controls.get('retest_window_minutes', self.config.retest_window_minutes)
        window = pd.Timedelta(minutes=retest_mins)
        grace = pd.Timedelta(seconds=self.config.entry_execution_grace_seconds)
        # Reconstruct original breaks from CLOSED prefixes: restart-safe, causal,
        # and identical for live evaluation and historical replay.
        anchor_count = int(window / delta) + 2
        h1_obstacles = active_av_levels(h1, definition=self.config.obstacle_av_definition)
        d1_obstacles = active_av_levels(d1, definition=self.config.obstacle_av_definition) if self.config.enable_d1_storyline_levels else []
        h4_obstacles = active_av_levels(h4, definition=self.config.obstacle_av_definition) if not h4.empty else []
        h4_obstacle_checked = not h4.empty or self.config.h4_obstacle_mode == 'off'
        observations = []
        shadow_candidates = []
        live_candidate = None
        anchors = [(h1.iloc[:index+1], self.config.structure_timeframe, False)
                   for index in range(len(h1)-1, max(26,len(h1)-anchor_count-1),-1)]
        if self.config.gap_mode != 'off' and self.config.gap_timeframe == 'H4' and len(h4)>=28:
            anchors += [(h4.iloc[:index+1], 'H4', True)
                        for index in range(len(h4)-1, max(26,len(h4)-3),-1)]
        anchors.sort(key=lambda a:a[0].time.iloc[-1]+timeframe_delta(a[1]), reverse=True)
        for prefix, structure_tf, gap_only in anchors:
            break_closed_at = prefix.iloc[-1].time + timeframe_delta(structure_tf)
            age = now - break_closed_at
            candidates = (self._gap_setups(prefix) if gap_only else
                self._setups_at_break(prefix, fractal_min_body_ratio=fractal_min_body_ratio,
                                     fractal_max_entry_distance_atr=fractal_max_entry_distance_atr))
            for setup in candidates:
                direction = setup['direction']
                sign = 1 if direction == 'BUY' else -1
                identity = f"{symbol}|{setup['scenario']}|{break_closed_at.isoformat()}|{direction}|{setup['level']:.12g}"
                setup_id = hashlib.sha256(identity.encode()).hexdigest()[:24]
                details = {**setup, 'setup_id': setup_id, 'macro_bias': daily_direction,
                           'fractal_min_body_ratio': fractal_min_body_ratio,
                           'fractal_max_entry_distance_atr': fractal_max_entry_distance_atr,
                           'macro_bias_enforced': daily_bias_enforced,
                           'macro_candle_bias':candle_direction, 'macro_structure_bias':structure_direction,
                           'structure_timeframe':structure_tf,
                           'entry_timeframe':self.config.entry_timeframe,
                           'runtime_settings_version': settings_version,
                           'structure_closed_at': break_closed_at.isoformat(),
                           'expires_at': (break_closed_at + window).isoformat(),
                           'remaining_minutes': round(max(0., (window - age).total_seconds() / 60), 1)}
                def wait(reason):
                    return {**base, 'reason': reason, 'scenario': setup['scenario'],
                            'direction': direction, 'break_level': setup['level'],
                            'diagnostics': {**details, 'stage': reason}}
                if age > window + grace:
                    observations.append(wait('SETUP_EXPIRED'))
                    continue
                if setup.get('blocked_reason'):
                    observations.append(wait(setup['blocked_reason']))
                    continue
                if not is_direction_allowed(symbol, direction):
                    observations.append(wait('DIRECTION_POLICY_BLOCKED'))
                    continue
                macro_shadow = False
                if daily_bias_enforced and (daily_direction is None or daily_direction != direction):
                    if (self.config.macro_structure_mode == 'shadow' and structure_direction == direction):
                        macro_shadow = True
                    else:
                        observations.append(wait('D1_BIAS_CONFLICT' if daily_direction else 'NEUTRAL_D1_BIAS'))
                        continue
                recent = m15[m15.time >= break_closed_at].reset_index(drop=True)
                if recent.empty:
                    observations.append(wait('WAITING_POST_BREAK_RETEST'))
                    continue
                if recent.iloc[0].time != break_closed_at or (recent.time.diff().dropna() != entry_delta).any():
                    observations.append(wait('RETEST_DATA_GAP'))
                    continue
                extremes = recent.low if sign == 1 else recent.high
                if (sign * (extremes - setup['invalidation_level']) <= 0).any():
                    observations.append(wait('SETUP_STRUCTURE_INVALIDATED'))
                    continue
                evidence = retest_confirmation(
                    recent, setup['level'], direction, setup['atr'],
                    self.config.retest_tolerance_atr, setup['max_entry_distance_atr'],
                    allow_sweep=self.config.enable_crt_sweep_rejection,
                    allow_zone=self.config.enable_zone_rejection_trigger or not self.config.enable_crt_sweep_rejection,
                    max_penetration_atr=self.config.max_retest_penetration_atr,
                    recovery_bars=max(1,int(pd.Timedelta(minutes=controls.get('recovery_window_minutes', self.config.recovery_window_minutes))/entry_delta)),
                    min_body_ratio=self.config.recovery_min_body_ratio,
                    require_displacement=setup['freshness']['state'] == 'TESTED_ONCE',
                    displacement_atr=self.config.tested_level_displacement_atr,
                    timeframe=self.config.entry_timeframe,
                    allow_pinbar=self.config.retest_pinbar_mode == 'live',
                    pinbar_min_wick_ratio=self.config.retest_pinbar_min_wick_ratio,
                    pinbar_min_close_ratio=self.config.retest_pinbar_min_close_ratio,
                    allow_direct_touch=getattr(self.config, 'continuation_direct_trigger', True) if setup['scenario'] == 'ESC_1_CONTINUATION' else False,
                    allow_fakeout_trap=getattr(self.config, 'enable_fakeout_trap', True),
                    max_fakeout_penetration_atr=getattr(self.config, 'max_fakeout_penetration_atr', 0.60),
                    fakeout_min_wick_ratio=getattr(self.config, 'fakeout_min_wick_ratio', 0.50))
                details['retest'] = evidence
                if not evidence['confirmed']:
                    observations.append(wait(evidence['reason']))
                    continue
                conf_idx = evidence['confirmation_index']
                bars_ago = (len(recent) - 1) - conf_idx
                max_lag = getattr(self, '_runtime_controls', {}).get(
                    'confirmation_tolerance_bars',
                    getattr(self.config, 'confirmation_tolerance_bars', 0)
                )
                current_close = float(recent.iloc[-1].close)
                dist_to_level_atr = abs(current_close - setup['level']) / setup['atr']
                max_tol_atr = getattr(self, '_runtime_controls', {}).get(
                    'confirmation_tolerance_max_atr',
                    getattr(self.config, 'confirmation_tolerance_max_atr', 0.35)
                )
                in_retest_zone = dist_to_level_atr <= max_tol_atr
                if bars_ago > 0:
                    if bars_ago > max_lag or not in_retest_zone:
                        observations.append(wait('SETUP_ALREADY_CONFIRMED'))
                        continue
                confirmed_at = recent.iloc[-1].time + entry_delta
                if confirmed_at > break_closed_at + window:
                    observations.append(wait('SETUP_EXPIRED'))
                    continue
                entry = float(recent.iloc[-1].close)
                effective_stop = setup['stop']
                micro_stop_applied = False
                if getattr(self.config, 'enable_m15_micro_stop', True):
                    touch_idx = evidence.get('touch_index', 0)
                    conf_idx = evidence.get('confirmation_index', len(recent) - 1)
                    retest_slice = recent.iloc[touch_idx:conf_idx + 1]
                    buffer_dist = getattr(self.config, 'm15_micro_stop_buffer_atr', 0.10) * setup['atr']
                    min_risk_floor = getattr(self.config, 'm15_micro_stop_min_risk_atr', 0.20) * setup['atr']
                    if sign == 1:
                        m15_extreme = float(retest_slice.low.min())
                        m15_cand_stop = m15_extreme - buffer_dist
                        if m15_cand_stop > setup['stop'] and (entry - m15_cand_stop) >= min_risk_floor:
                            effective_stop = m15_cand_stop
                            micro_stop_applied = True
                    else:
                        m15_extreme = float(retest_slice.high.max())
                        m15_cand_stop = m15_extreme + buffer_dist
                        if m15_cand_stop < setup['stop'] and (m15_cand_stop - entry) >= min_risk_floor:
                            effective_stop = m15_cand_stop
                            micro_stop_applied = True

                risk = sign * (entry - effective_stop)
                # Optional obstacle observation should not add a provider request
                # to every scan with no confirmed setup. Macro/gap requirements
                # still fetch H4 earlier through their original path.
                if not h4_obstacle_checked:
                    h4_obstacle_checked = True
                    try:
                        h4 = load('H4', 80, 28)
                        if h4.empty or now-(h4.iloc[-1].time+timeframe_delta('H4')) >= timeframe_delta('H4'):
                            h4 = pd.DataFrame()
                    except Exception:
                        h4 = pd.DataFrame()
                    h4_obstacles = active_av_levels(h4, definition=self.config.obstacle_av_definition) if not h4.empty else []
                if self.config.h4_obstacle_mode == 'live' and h4.empty:
                    observations.append(wait('H4_OBSTACLES_UNAVAILABLE'))
                    continue
                opposite_type = 'A_RESISTANCE' if sign == 1 else 'V_SUPPORT'
                d1_prices = [item['level'] for item in d1_obstacles if item['type'] == opposite_type
                             and sign * (item['level'] - entry) > 0]
                if d1_prices and min(sign * (price - entry) for price in d1_prices) < self.config.min_obstacle_rr * risk:
                    observations.append(wait('OBSTACLE_D1_BEFORE_2R'))
                    continue
                prices = [item['level'] for item in h1_obstacles if item['type'] == opposite_type
                          and sign * (item['level'] - entry) > 0]
                prices.extend(d1_prices)
                h4_prices = [item['level'] for item in h4_obstacles if item['type'] == opposite_type
                             and sign * (item['level'] - entry) > 0]
                h4_room = min((sign * (price-entry) - self.config.obstacle_buffer_atr*setup['atr']
                               for price in h4_prices), default=None)
                details['h4_obstacle'] = {'mode': self.config.h4_obstacle_mode,
                    'data_available': not h4.empty, 'room_r': h4_room/risk if h4_room is not None and risk>0 else None,
                    'before_tp1': h4_room is not None and h4_room < self.config.tp1_min_rr*risk}
                if self.config.h4_obstacle_mode == 'live':
                    prices.extend(h4_prices)
                obstacle = min(prices, key=lambda price: sign * (price - entry)) if prices else 0.
                result = self._build_confirmed_signal(
                    symbol, direction, setup['scenario'], entry, effective_stop, risk,
                    setup['adx'], setup['body_ratio'], setup['level'], setup['break_level'],
                    setup['atr'], obstacle, confirmed_at.to_pydatetime())
                if not result.get('valid'):
                    observations.append(wait(result['reason']))
                    continue
                signal = result['signal']
                result.update(history_diagnostics=history, macro_bias_enforced=daily_bias_enforced,
                              gap_data_reason=gap_data_reason, macro_candle_bias=candle_direction,
                              macro_structure_bias=structure_direction)
                signal.update({'setup_id': setup_id, 'macro_bias': daily_direction,
                               'entry_timeframe': self.config.entry_timeframe,
                               'h4_neutral_fallback_used':base.get('h4_neutral_fallback_used',False),
                               'fractal_min_body_ratio': fractal_min_body_ratio,
                               'fractal_max_entry_distance_atr': fractal_max_entry_distance_atr,
                               'macro_bias_enforced': daily_bias_enforced,
                               'runtime_settings_version': settings_version,
                               'evaluated_at': now.isoformat(),
                               'macro_bias_method': (self.config.macro_bias_method.upper() if macro_shadow or
                                   self.config.macro_structure_mode == 'live' and daily_bias_enforced
                                   else 'LAST_CLOSED_D1_CANDLE_DIRECTION'),
                               'macro_candle_bias':candle_direction, 'macro_structure_bias':structure_direction,
                               'macro_structure_observation':macro_shadow,
                               'structure_timeframe':structure_tf,
                               'opportunity':setup.get('opportunity', {}),
                               'structure_closed_at': break_closed_at.isoformat(),
                               'confirmation_closed_at': confirmed_at.isoformat(),
                               'entry_confirmation': evidence['trigger'],
                               'freshness': setup['freshness'], 'retest_evidence': evidence,
                               'h4_obstacle_evidence': details['h4_obstacle'],
                               'max_entry_distance_atr': setup['max_entry_distance_atr'],
                               'invalidation_level': setup['invalidation_level'],
                               'setup_execution_deadline_at': (break_closed_at + window + grace).isoformat(),
                               'setup_expires_at': details['expires_at']})
                micro_structure = True
                if setup['scenario'] == 'ESC_1_BREAKER_PAIR':
                    # A same-color pair is displacement, not a structure break.
                    # Only an actual closing cross of the three CLOSED bars
                    # before the first visit may claim a lower-frame break.
                    touched_at = recent.iloc[evidence['touch_index']].time
                    preceding = m15[m15.time < touched_at].tail(3)
                    micro_level = float(preceding.high.max() if sign == 1 else preceding.low.min()) if len(preceding) == 3 else None
                    micro_structure = micro_level is not None and sign * (entry - micro_level) > 0
                    signal['micro_structure_evidence'] = {'confirmed': micro_structure,
                        'timeframe': self.config.entry_timeframe, 'reference_level': micro_level,
                        'method': 'CLOSED_CROSS_OF_THREE_PRE_VISIT_BARS'}
                session_tracking = track_session_liquidity(m15, symbol, now, policy=self.config.session_policy, direction=direction)
                signal['session_tracking'] = session_tracking
                confirmations = {'rejection': True, 'micro_structure': micro_structure,
                                 'displacement': evidence['displacement'] or setup['body_ratio'] >= .50,
                                 'strong_close': True}
                if session_tracking.get('sweep_confirmed'):
                    confirmations['session_sweep'] = True
                    signal['high_confluence_session_sweep'] = True
                if evidence.get('fakeout_trap'):
                    confirmations['fakeout_trap'] = True
                    signal['fakeout_trap_sweep'] = True
                ema_confluence = {'confluence': False}
                if getattr(self.config, 'enable_h1_ema_confluence', True):
                    ema_confluence = h1_ema_dynamic_confluence(
                        h1, setup['level'], direction=direction,
                        period=getattr(self.config, 'h1_ema_period', 50),
                        tolerance_atr=getattr(self.config, 'h1_ema_tolerance_atr', 0.40))
                signal['dynamic_ema_confluence'] = ema_confluence.get('confluence', False)
                signal['dynamic_ema_details'] = ema_confluence
                if ema_confluence.get('confluence'):
                    confirmations['dynamic_ema_50'] = True
                    signal['trade_score'] = min(100.0, signal.get('trade_score', 80.0) + 10.0)
                signal['micro_stop_applied'] = micro_stop_applied
                signal['price_action_confirmations'] = confirmations
                signal['confirmations'] = confirmations.copy()
                result['diagnostics'] = {**details, 'stage': 'RETEST_CONFIRMED'}
                controls = self._runtime_controls
                extra_shadow = (getattr(self, '_asset_mode', None)=='shadow' or
                    (getattr(self, '_asset_mode', None) is None and symbol in controls['additional_symbols']
                     and controls['additional_symbols_mode']=='shadow'))
                continuation_shadow = setup['scenario']=='ESC_1_CONTINUATION' and controls['continuation_mode']=='shadow'
                variant_mode = setup.get('variant_mode', 'live')
                result['shadow_only'] = extra_shadow or continuation_shadow or variant_mode=='shadow' or macro_shadow
                signal['execution_mode'] = 'SHADOW' if result['shadow_only'] else 'LIVE'
                if result['shadow_only']:
                    shadow_candidates.append(result)
                    continue
                if live_candidate is None:
                    live_candidate = result
        if live_candidate is not None:
            live_candidate['shadow_candidates'] = shadow_candidates
            return live_candidate
        if shadow_candidates:
            result = shadow_candidates[0]
            result['shadow_candidates'] = shadow_candidates[1:]
            return result
        if observations:
            # A live setup awaiting recovery is more useful than an older expiry.
            preferred = next((item for item in observations if item['reason'] not in
                              {'SETUP_EXPIRED', 'SETUP_ALREADY_CONFIRMED'}), observations[0])
            preferred['diagnostics']['candidates'] = [
                {'setup_id': item['diagnostics']['setup_id'], 'reason': item['reason']}
                for item in observations]
            return preferred
        diagnostic = self._h1_diagnostics(h1) if self.config.enable_setup_diagnostics else {}
        return {**base, 'diagnostics': {'stage': 'NO_SETUP_CONFIRMED', 'macro_bias': daily_direction,
                                       'h1_snapshot': diagnostic,
                                       'fractal_min_body_ratio': fractal_min_body_ratio,
                                       'fractal_max_entry_distance_atr': fractal_max_entry_distance_atr,
                                       'macro_bias_enforced': daily_bias_enforced,
                                       'runtime_settings_version': settings_version}}

    def _setups_at_break(self, h1: pd.DataFrame, fractal_min_body_ratio: float | None = None,
                        fractal_max_entry_distance_atr: float | None = None) -> list[dict]:
        key = None
        if self.config.enable_structure_cache:
            fingerprint = pd.util.hash_pandas_object(h1[['time','open','high','low','close']], index=False).values.tobytes()
            # Pinbar parameters affect only entry confirmation. Reuse the same
            # immutable H1 formation in its regular and observation branches.
            formation_config = {k:v for k,v in asdict(self.config).items() if not k.startswith('retest_pinbar_')}
            key = (hashlib.blake2b(fingerprint,digest_size=16).digest(),
                   json.dumps(formation_config,sort_keys=True), fractal_min_body_ratio, fractal_max_entry_distance_atr)
            with self._structure_cache_lock:
                if key in self._structure_cache:
                    return deepcopy(self._structure_cache[key])
        setups = self._compute_setups_at_break(h1, fractal_min_body_ratio, fractal_max_entry_distance_atr)
        if key is not None:
            with self._structure_cache_lock:
                if len(self._structure_cache)>=256:
                    self._structure_cache.clear()
                self._structure_cache[key] = deepcopy(setups)
        return setups

    def _h1_diagnostics(self, h1):
        key = None
        if self.config.enable_structure_cache:
            fingerprint = pd.util.hash_pandas_object(h1[['time','open','high','low','close']],index=False).values.tobytes()
            key = ('diagnostics',hashlib.blake2b(fingerprint,digest_size=16).digest(),json.dumps(asdict(self.config),sort_keys=True))
            with self._structure_cache_lock:
                if key in self._structure_cache:
                    return deepcopy(self._structure_cache[key])
        diagnostic = self._compute_h1_diagnostics(h1)
        if key is not None:
            with self._structure_cache_lock:
                if len(self._structure_cache)>=256:
                    self._structure_cache.clear()
                self._structure_cache[key] = deepcopy(diagnostic)
        return diagnostic

    def _compute_h1_diagnostics(self, h1):
        last, previous, prior = h1.iloc[-1], h1.iloc[-2], h1.iloc[-3]
        span = float(last.high-last.low)
        body = float(abs(last.close-last.open)/span) if span>0 else 0.
        buy_sweep, sell_sweep = bool(previous.low<prior.low), bool(previous.high>prior.high)
        buy_break = bool(last.close>last.open and last.close>prior.high)
        sell_break = bool(last.close<last.open and last.close<prior.low)
        reasons = []
        if not (buy_sweep or sell_sweep): reasons.append('FRACTAL_NO_STRUCTURAL_SWEEP')
        if not (buy_break or sell_break): reasons.append('FRACTAL_NO_DIRECTIONAL_BREAK')
        if body<self.config.fractal_min_body_ratio: reasons.append('FRACTAL_BODY_BELOW_MINIMUM')
        if not ((buy_sweep and buy_break) or (sell_sweep and sell_break)):
            reasons.append('FRACTAL_GEOMETRY_NOT_ALIGNED')
        return {'closed_at':(last.time+timeframe_delta(self.config.structure_timeframe)).isoformat(),
            'atr':float(compute_atr(h1).iloc[-1]), 'adx':float(compute_adx(h1).iloc[-1]),
            'body_ratio':round(body,6), 'minimum_body_ratio':self.config.fractal_min_body_ratio,
            'buy_sweep':buy_sweep, 'sell_sweep':sell_sweep, 'buy_break':buy_break, 'sell_break':sell_break,
            'rejections':reasons,
            'qm_confirmed_patterns':len(quasimodo_candidates(h1,self.config.qm_swing_radius))
                if self.config.enable_quasimodo_pattern else None,
            'continuation_enabled':self.config.enable_scenario_1_continuation}

    def _compute_setups_at_break(self, h1, fractal_min_body_ratio=None, fractal_max_entry_distance_atr=None):
        """Freeze structure, volatility and stop at the original closing break."""
        atr = float(compute_atr(h1).iloc[-1])
        adx = float(compute_adx(h1).iloc[-1])
        if not math.isfinite(atr) or atr <= 0 or not math.isfinite(adx):
            return []
        last = h1.iloc[-1]
        span = float(last.high - last.low)
        body_ratio = float(abs(last.close - last.open) / span) if span > 0 else 0.
        setups = []
        fractal_distance = (self.config.fractal_max_entry_distance_atr if fractal_max_entry_distance_atr is None
                            else fractal_max_entry_distance_atr)
        def add(direction, scenario, level, break_level, bound, buffer=.15, freshness=None, blocked_reason=None):
            sign = 1 if direction == 'BUY' else -1
            setups.append({'direction': direction, 'scenario': scenario, 'level': float(level),
                           'break_level': float(break_level), 'invalidation_level': float(bound),
                           'stop': float(bound - sign * buffer * atr), 'atr': atr, 'adx': adx,
                           'body_ratio': body_ratio, 'blocked_reason': blocked_reason,
                           'freshness': freshness or {'state': 'STRUCTURAL_REFERENCE', 'visits': None},
                           'max_entry_distance_atr': fractal_distance
                           if scenario == 'ESC_3_FRACTAL' else self.config.continuation_max_entry_distance_atr
                           if scenario.startswith('ESC_1_') else self.config.max_entry_distance_atr})
        if self.config.enable_scenario_1_continuation and adx >= self.config.continuation_min_adx:
            for level in reversed(av_levels(h1)):
                if not 2 < len(h1) - 1 - level['idx'] <= self.config.level_lookback_candles:
                    continue
                direction = 'BUY' if level['type'] == 'A_RESISTANCE' else 'SELL'
                sign = 1 if direction == 'BUY' else -1
                wick = last.high - last.close if sign == 1 else last.close - last.low
                if (span <= 0 or sign * (last.close - last.open) <= 0
                        or sign * (last.close - level['level']) <= 0
                        or sign * (h1.iloc[-2].close - level['level']) > 0
                        or body_ratio < self.config.minimum_body_ratio
                        or wick / span > self.config.maximum_breakout_wick_ratio):
                    continue
                freshness = level_freshness(h1, level, atr, self.config.max_tested_wick_penetration_atr)
                if self.config.continuation_fresh_only:
                    blocked = ('LEVEL_CONSUMED' if freshness['state'] == 'CONSUMED' else
                               'CONTINUATION_REQUIRES_FRESH' if freshness['state'] != 'FRESH' else None)
                else:
                    blocked = ('LEVEL_INVALIDATED' if freshness['body_invalidated'] else
                               'LEVEL_CONSUMED' if freshness['state'] == 'CONSUMED' else
                               'TESTED_LEVEL_DISABLED' if freshness['state'] == 'TESTED_ONCE' and not getattr(self.config, 'enable_tested_level_entries', True) else None)
                add(direction, 'ESC_1_CONTINUATION', level['level'], level['break_level'],
                    last.low if sign == 1 else last.high, freshness=freshness, blocked_reason=blocked)
        if self.config.enable_quasimodo_pattern:
            for pattern in quasimodo_candidates(h1, self.config.qm_swing_radius):
                add(pattern['direction'], 'ESC_3_QUASIMODO', pattern['shoulder'],
                    pattern['neckline'], pattern['head'], buffer=.10)
        if getattr(self.config, 'enable_qmc_pattern', True):
            for pattern in quasimodo_continuation_candidates(h1, self.config.qm_swing_radius):
                add(pattern['direction'], 'ESC_3_QMC', pattern['shoulder'],
                    pattern['head'], pattern['invalidation_level'], buffer=.10)
        if self.config.enable_scenario_3_fractal:
            prev2, prev1 = h1.iloc[-3], h1.iloc[-2]
            minimum_body = self.config.fractal_min_body_ratio if fractal_min_body_ratio is None else fractal_min_body_ratio
            if body_ratio >= minimum_body:
                if prev1.low < prev2.low and last.close > last.open and last.close > prev2.high:
                    add('BUY', 'ESC_3_FRACTAL', prev2.high, prev1.close, last.low)
                elif prev1.high > prev2.high and last.close < last.open and last.close < prev2.low:
                    add('SELL', 'ESC_3_FRACTAL', prev2.low, prev1.close, last.high)
        # Alternative candidates are appended after existing scenarios. Keep the
        # obstacle map unchanged and never renew an old setup without a new break.
        controls = getattr(self, '_runtime_controls', {})
        def effective_mode(setup):
            return setup.get('variant_mode', controls.get('continuation_mode', 'live')
                if setup['scenario']=='ESC_1_CONTINUATION' else 'live')
        existing = {(s['direction'],s['level']):effective_mode(s)
                    for s in setups if not s['blocked_reason']}
        def reserve(direction, price, mode):
            key = (direction,float(price))
            previous_mode = existing.get(key)
            if previous_mode is not None:
                if previous_mode=='live' or mode!='live':
                    return False
                setups[:] = [s for s in setups if s['blocked_reason'] or (s['direction'],s['level'])!=key]
            existing[key] = mode
            return True
        levels = None
        def extended_add(direction, scenario, price, break_level, bound, mode, opportunity, freshness=None):
            if not reserve(direction,price,mode):
                return
            add(direction, scenario, price, break_level, bound, freshness=freshness)
            setups[-1].update(variant_mode=mode, opportunity=opportunity)
        strong_break = adx>=self.config.continuation_min_adx and body_ratio>=self.config.minimum_body_ratio
        if strong_break and (self.config.av_entry_mode != 'off' or self.config.role_flip_mode != 'off'):
            levels = av_levels(h1, definition=self.config.av_entry_definition)
        if strong_break and self.config.av_entry_mode != 'off':
            legacy_indices = {l['idx'] for l in av_levels(h1)}
            for level in reversed(levels):
                if level['idx'] in legacy_indices or not 2<len(h1)-1-level['idx']<=self.config.level_lookback_candles:
                    continue
                direction = 'BUY' if level['type']=='A_RESISTANCE' else 'SELL'
                sign = 1 if direction=='BUY' else -1
                wick = last.high-last.close if sign==1 else last.close-last.low
                if (sign*(last.close-last.open)<=0 or sign*(last.close-level['level'])<=0
                        or sign*(h1.iloc[-2].close-level['level'])>0 or span<=0
                        or wick/span>self.config.maximum_breakout_wick_ratio):
                    continue
                freshness = level_freshness(h1,level,atr,self.config.max_tested_wick_penetration_atr)
                if freshness['state']=='CONSUMED' or (self.config.continuation_fresh_only and freshness['state']!='FRESH'):
                    continue
                if freshness['state']=='TESTED_ONCE' and self.config.enable_strict_fresh_filter and not self.config.enable_tested_level_entries:
                    continue
                extended_add(direction,'ESC_1_AV_EXTENDED',level['level'],level['break_level'],
                    last.low if sign==1 else last.high,self.config.av_entry_mode,
                    {'kind':'AV_EXTENDED','definition':self.config.av_entry_definition},freshness)
        if strong_break and self.config.role_flip_mode != 'off':
            for level in role_flip_candidates(h1, levels, self.config.role_flip_max_changes,
                                              self.config.role_flip_min_displacement_atr, atr):
                if not 2<len(h1)-1-level['idx']<=self.config.level_lookback_candles:
                    continue
                sign = 1 if level['direction']=='BUY' else -1
                wick = last.high-last.close if sign==1 else last.close-last.low
                if sign*(last.close-last.open)<=0 or span<=0 or wick/span>self.config.maximum_breakout_wick_ratio:
                    continue
                prior = level_freshness(h1,level,atr,self.config.max_tested_wick_penetration_atr)
                # The ordinary first fresh breakout belongs to continuation.
                if level['role_changes']==1 and prior['state']!='CONSUMED':
                    continue
                freshness = {'state':'FRESH','visits':0,'prior_episode':prior,
                             'role_changes':level['role_changes'],'renewed_by_closed_break':True}
                extended_add(level['direction'],'ESC_1_ROLE_FLIP',level['level'],level['level'],
                    last.low if sign==1 else last.high,self.config.role_flip_mode,
                    {'kind':'ROLE_FLIP','role_changes':level['role_changes'],
                     'episode_closed_at':level['episode_closed_at']},freshness)
        if self.config.qm_extended_mode != 'off':
            legacy_qm = {(p['direction'],p['shoulder'],p['head'],p['neckline'])
                         for p in quasimodo_candidates(h1,self.config.qm_swing_radius)}
            for pattern in extended_quasimodo_candidates(h1,self.config.qm_swing_radius,
                    self.config.qm_extended_swing_window,self.config.qm_extended_min_head_depth_atr,atr):
                if (pattern['direction'],pattern['shoulder'],pattern['head'],pattern['neckline']) in legacy_qm:
                    continue
                extended_add(pattern['direction'],'ESC_3_QM_EXTENDED',pattern['shoulder'],
                    pattern['neckline'],pattern['head'],self.config.qm_extended_mode,
                    {'kind':'QM_EXTENDED','head_depth_atr':pattern['head_depth_atr']})
        if self.config.gap_mode != 'off' and self.config.gap_timeframe=='H1':
            for setup in self._gap_setups(h1):
                if reserve(setup['direction'],setup['level'],setup['variant_mode']):
                    setups.append(setup)
        if self.config.breaker_pair_mode != 'off' and adx >= self.config.continuation_min_adx:
            pair = breaker_pair_candidate(h1, atr, self.config.breaker_pair_min_body_ratio,
                                          self.config.breaker_pair_min_displacement_atr)
            if pair is not None:
                extended_add(pair['direction'], 'ESC_1_BREAKER_PAIR', pair['level'], pair['level'],
                    pair['bound'], self.config.breaker_pair_mode,
                    {'kind': 'BREAKER_PAIR', **pair}, {'state': 'FRESH', 'visits': 0})
        return setups

    def _gap_setups(self, frame):
        if len(frame)<28:
            return []
        atr, adx = float(compute_atr(frame).iloc[-1]), float(compute_adx(frame).iloc[-1])
        last = frame.iloc[-1]
        span = float(last.high-last.low)
        body = abs(float(last.close-last.open))/span if span>0 else 0.
        if not math.isfinite(adx) or adx<self.config.continuation_min_adx or body<self.config.minimum_body_ratio:
            return []
        gap = gap_candidate(frame,atr,self.config.gap_min_size_atr,self.config.gap_tick_size,
                            self.config.gap_spread,self.config.gap_min_ticks,self.config.gap_min_spread_multiple)
        if gap is None:
            return []
        sign = 1 if gap['direction']=='BUY' else -1
        if (sign==1 and last.low<gap['band_high']) or (sign==-1 and last.high>gap['band_low']):
            return []
        bound = gap['band_low'] if sign==1 else gap['band_high']
        return [{'direction':gap['direction'], 'scenario':'ESC_4_OPEN_CLOSE', 'level':gap['level'],
                 'break_level':gap['level'],'invalidation_level':bound-.35*sign*atr,
                 'stop':bound-.50*sign*atr, 'atr':atr,'adx':adx,'body_ratio':body,
                 'blocked_reason':None,'freshness':{'state':'FRESH','visits':0},
                 'max_entry_distance_atr':self.config.continuation_max_entry_distance_atr,
                 'variant_mode':self.config.gap_mode,
                 'opportunity':{'kind':'OPEN_CLOSE','timeframe':self.config.gap_timeframe,**gap}}]

    def _build_confirmed_signal(
        self,
        symbol: str,
        direction: str,
        scenario: str,
        entry_price: float,
        stop_loss: float,
        risk_dist: float,
        adx: float,
        body_ratio: float,
        ref_level: float,
        break_level: float,
        current_atr: float = 0.0,
        obstacle_level: float = 0.0,
        now_utc: datetime | None = None,
    ) -> dict:
        """Construye el payload completo de señal dual con targets asimétricos y features para IA."""
        def reject(reason):
            return {"valid": False, "strategy_name": self.config.strategy_name,
                    "strategy_version": self.config.strategy_version, "symbol": symbol,
                    "action": "WAITING_MALAYSIAN_SNR", "reason": reason}

        values = (entry_price, stop_loss, risk_dist, adx, body_ratio, current_atr, obstacle_level)
        if direction not in {"BUY", "SELL"} or not all(math.isfinite(v) for v in values):
            return reject("INVALID_SIGNAL_GEOMETRY")
        sign = 1 if direction == "BUY" else -1
        actual_risk = sign * (entry_price - stop_loss)
        if actual_risk <= 0 or not math.isclose(actual_risk, risk_dist, rel_tol=1e-8, abs_tol=1e-10):
            return reject("INVALID_STOP_OR_RISK_DISTANCE")
        if not is_direction_allowed(symbol, direction):
            return reject("DIRECTION_POLICY_BLOCKED")
        # Variante C2 (walk-forward 180d): ADX(14) H1 >= min_adx en todos los escenarios.
        if getattr(self.config, "enable_c2_fx_metals_atr_cap", False) and adx < float(getattr(self.config, "min_adx", 30.0)) - 1e-9:
            return reject("C2_ADX_BELOW_MIN")
        if getattr(self.config, "enable_c2_fx_metals_atr_cap", False) and current_atr > 0:
            max_sl_atr = (
                float(getattr(self.config, "c2_fx_metals_max_sl_atr", 1.2))
                if is_fx_or_metal_symbol(symbol)
                else float(getattr(self.config, "c2_default_max_sl_atr", 1.5))
            )
            if (risk_dist / current_atr) > max_sl_atr + 1e-9:
                return reject("C2_STOP_ATR_CAP_EXCEEDED")
        # TP1 remains at least 2R; this version has no verified two-year edge.
        tp1_price = entry_price + (self.config.tp1_min_rr * risk_dist) if direction == "BUY" else entry_price - (self.config.tp1_min_rr * risk_dist)

        # 2. Asignación contextual de la corredora
        if scenario in ("ESC_1_CONTINUATION", "ESC_1_FRESH_C_TRADE", "ESC_1_AV_EXTENDED", "ESC_1_ROLE_FLIP", "ESC_3_QMC") and adx >= self.config.adx_tp4_threshold and body_ratio >= self.config.body_ratio_tp4_threshold:
            runner_target_name = "TP4"
            runner_rr = self.config.tp4_runner_rr  # 1:4.0 RR
        elif adx >= self.config.adx_tp3_threshold:
            runner_target_name = "TP3"
            runner_rr = self.config.tp3_runner_rr  # 1:3.0 RR
        else:
            runner_target_name = "TP2"
            runner_rr = self.config.tp2_runner_rr  # 1:2.5 RR

        # Ajuste dinámico de Obstacle Awareness: si hay un obstáculo estructural previo
        if self.config.enable_obstacle_awareness and obstacle_level > 0:
            room = sign * (obstacle_level - entry_price) - self.config.obstacle_buffer_atr * current_atr
            if room < self.config.tp1_min_rr * risk_dist:
                return reject("OBSTACLE_BEFORE_MINIMUM_TP1")
            runner_rr = min(runner_rr, room / risk_dist)
        if not math.isfinite(runner_rr) or runner_rr < self.config.tp1_min_rr or self.config.tp1_min_rr <= 0:
            return reject("INVALID_TARGET_ORDER")

        tp2_price = entry_price + (runner_rr * risk_dist) if direction == "BUY" else entry_price - (runner_rr * risk_dist)

        # Heuristic rule scores, NOT calibrated probabilities of trade success.
        base_score = 75.0
        adx_bonus = min(15.0, max(0.0, (adx - 20.0) * 1.5))
        body_bonus = 10.0 if body_ratio >= 0.60 else 5.0
        trade_score = min(100.0, base_score + adx_bonus + body_bonus)
        conf_pct = 85.0 if "ESC_1" in scenario else 90.0

        # Vector de features para inferencia y meta-etiquetado continuo de IA
        ai_features = {
            "trade_score": round(trade_score, 2),
            "confirmation_percentage": round(conf_pct, 2),
            "adx": round(adx, 2),
            "adx_regime": 1.0 if adx >= 25.0 else 0.0,
            "body_ratio": round(body_ratio, 3),
            "scenario_is_fractal": 1.0 if "ESC_3" in scenario else 0.0,
            "risk_distance": round(risk_dist, 5),
            "is_buy": 1.0 if direction == "BUY" else 0.0,
            "runner_expected_rr": runner_rr,
            "obstacle_level": round(obstacle_level, 5),
        }

        signal = {
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "symbol": symbol,
            "direction": direction,
            "scenario": scenario,
            "entry_time": (now_utc or datetime.now(timezone.utc)).isoformat(),
            "entry_price": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "risk_reward_ratio": runner_rr,
            "risk_reward": runner_rr,
            "risk_reward_ratio_tp1": self.config.tp1_min_rr,
            "risk_reward_ratio_tp2": runner_rr,
            "tp1_price": round(tp1_price, 5),
            "tp1_rr": self.config.tp1_min_rr,
            "tp2_price": round(tp2_price, 5),
            "runner_target_name": runner_target_name,
            "runner_rr": runner_rr,
            "be_trigger_rr": self.config.tp1_min_rr,  # Al tocar TP1, mover SL de corredora a BE
            "timeframe": self.config.entry_timeframe,
            "momentum_adx": round(adx, 1),
            "adx": round(adx, 2),
            "atr": round(current_atr, 5) if current_atr > 0 else round(risk_dist / max(1.0, runner_rr), 5),
            "trade_score": round(trade_score, 2),
            "confirmation_percentage": round(conf_pct, 2),
            "confirmation_percentage_kind": "HEURISTIC_RULE_SCORE_NOT_PROBABILITY",
            "success_probability": None,
            "probability_status": "UNVALIDATED_FOR_CURRENT_STRATEGY_VERSION",
            "structure_break": f"{scenario}_{direction}",
            "body_ratio": round(body_ratio, 2),
            "ref_level": round(ref_level, 5),
            "break_level": round(break_level, 5),
            "obstacle_level": round(obstacle_level, 5),
            "price_action_confirmations": {"rejection": True, "micro_structure": True, "displacement": True, "strong_close": True},
            "confirmations": {"rejection": True, "micro_structure": True, "displacement": True, "strong_close": True},
            "meta_features": ai_features,
            # Configuración para el motor de ejecución de dos piernas (50% / 50%)
            "split_execution": True,
            "leg1_risk_ratio": self.config.leg1_risk_ratio,
            "leg2_risk_ratio": self.config.leg2_risk_ratio,
        }

        return {
            "valid": True,
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "action": "MALAYSIAN_SNR_CONFIRMED",
            "reason": f"{scenario} confirmed ({direction} on {symbol})",
            "symbol": symbol,
            "signal": signal,
        }
