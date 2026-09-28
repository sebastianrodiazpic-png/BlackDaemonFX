"""Closed-bar dual trigger: mandatory M5 liquidity, M5 or M1 confirmation."""
import pandas as pd
from strategy.smc.m5_freshness import validate_m5_signal_freshness


def validate_signal_latency(timestamp, max_allowed_minutes=10, current_time=None):
    value = validate_m5_signal_freshness(timestamp, max_allowed_minutes, current_time)
    return dict(value, fresh=value['is_fresh'], elapsed=value['elapsed_minutes'])


def evaluate_dual_m5_m1_trigger(m5_data, m1_data=None, max_age_minutes=10, current_time=None):
    m1 = m1_data or {}
    sweep = bool(m5_data.get('has_sweep'))
    native = bool(m5_data.get('has_choch'))
    early = bool(m1.get('has_choch'))
    tag, frame, stamp, base = 'TRUE_MISSING_CHOCH', None, None, 0
    if native:
        tag, frame, stamp, base = 'M5_SWEEP_M5_CHOCH_STANDARD', 'M5', m5_data.get('choch_timestamp'), 20
    elif early:
        tag, frame, stamp, base = 'M5_SWEEP_M1_CHOCH_EARLY_TRIGGER', 'M1', m1.get('choch_timestamp'), 20
    elif sweep and m5_data.get('has_bos_direction_flip'):
        tag, frame, stamp, base = 'RECLASSIFIED_BOS_TO_CHOCH', 'M5', m5_data.get('bos_timestamp'), 15
    elif sweep and m5_data.get('has_wick_break_with_fvg') and m5_data.get('has_fvg'):
        tag, frame, stamp, base = 'VALIDATED_WICK_CHOCH_WITH_FVG', 'M5', m5_data.get('wick_break_timestamp'), 15
    reasons, codes, freshness = [], [], None
    if not sweep:
        tag = 'MISSING_SWEEP_ONLY' if frame else 'MISSING_BOTH_CHOCH_AND_SWEEP'
        codes.append('M5_SWEEP_MISSING' if frame else 'M5_CHOCH_AND_SWEEP_MISSING')
        reasons.append('Trigger: Falta barrido M5' if frame else 'Trigger: Sin Sweep M5 ni CHoCH M5/M1')
    elif not frame:
        codes.append('M5_CHOCH_MISSING')
        reasons.append('Trigger: Existe Sweep M5 pero falta CHoCH en M5/M1')
    if frame:
        freshness = validate_signal_latency(stamp, max_age_minutes, current_time)
        if not freshness['fresh']:
            tag = 'EXPIRED_SIGNAL' if freshness['code'] == 'M5_SIGNAL_EXPIRED' else 'INVALID_TIMESTAMP'
            reasons.append(freshness['reason'])
            codes.append(freshness['code'])
        if frame == 'M1' and sweep:
            # Timestamp is the close at which evidence became available.
            sweep_time = pd.to_datetime(m5_data.get('sweep_timestamp'), utc=True, errors='coerce')
            event_time = pd.to_datetime(stamp, utc=True, errors='coerce')
            if pd.isna(sweep_time) or pd.isna(event_time) or event_time <= sweep_time:
                tag = 'M1_CHOCH_NOT_AFTER_M5_SWEEP'
                codes.append('M1_CHOCH_NOT_AFTER_M5_SWEEP')
                reasons.append('Trigger: CHoCH M1 debe ser posterior al Sweep M5 confirmado')
    fvg = bool(m5_data.get('has_fvg') or (frame == 'M1' and m1.get('has_fvg')))
    clean = bool(m5_data.get('clean_retest') or (frame == 'M1' and m1.get('clean_retest')))
    score = 0 if reasons else base + 10 * fvg + 5 * clean
    return dict(approved=not reasons, score=score, m5_score=score, vetos=reasons,
                veto_reasons=reasons, veto_codes=codes, diagnostic_tag=tag, tag=tag,
                confirmation_timeframe=frame, confirmation_timestamp=stamp,
                sweep_timestamp=m5_data.get('sweep_timestamp'), has_fvg=fvg,
                freshness=freshness, latency_rejected=bool(freshness and not freshness['fresh']),
                effective_has_choch=bool(frame), native_has_choch=native)


evaluate_m5_m1_trigger = evaluate_dual_m5_m1_trigger


def m5_evidence_before_m1(data, setup_time, event_close, direction):
    """Only directional M5 sweeps closed BEFORE the M1 structural event."""
    empty = dict(has_sweep=False, has_choch=False)
    if data is None or data.empty or event_close is None:
        return empty
    times = pd.to_datetime(data['time'], utc=True)
    event = pd.to_datetime(event_close, utc=True)
    prefix = data[(times >= pd.to_datetime(setup_time, utc=True)) &
                  (times + pd.Timedelta(minutes=5) < event)]
    key = 'bullish_sweep' if direction == 'long' else 'bearish_sweep'
    if key not in prefix:
        return empty
    sweeps = prefix[prefix[key].fillna(False).astype(bool)]
    if sweeps.empty:
        return empty
    sweep = sweeps.iloc[-1]
    # An opposite structural break after liquidity invalidates that sequence.
    contrary = 'choch_bearish' if direction == 'long' else 'choch_bullish'
    later = prefix[pd.to_datetime(prefix['time'], utc=True) > pd.to_datetime(sweep['time'], utc=True)]
    if contrary in later and later[contrary].fillna(False).astype(bool).any():
        return empty
    has_fvg = False
    if {'high', 'low', 'close'}.issubset(prefix.columns) and len(prefix) >= 3:
        from strategy.smc.fair_value_gap import detect_fvg_confirmation, FVGConfig
        window = prefix.reset_index(drop=True)
        has_fvg = detect_fvg_confirmation(window, direction, len(window)-1,
            FVGConfig(enabled=True, lookback=3, max_age_candles=3, require_alignment_with_zone=False))['fvg_confirmed']
    return dict(has_sweep=True, has_choch=False, has_fvg=has_fvg,
                sweep_timestamp=pd.to_datetime(sweep['time'], utc=True)+pd.Timedelta(minutes=5))
