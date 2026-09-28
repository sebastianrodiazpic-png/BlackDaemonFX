"""UTC signal-age guard and disaggregated M5 evidence, with an injectable clock."""
from datetime import datetime, timezone
import math
import pandas as pd


def validate_m5_signal_freshness(m5_choch_time, max_allowed_minutes=10, current_time=None):
    if not math.isfinite(float(max_allowed_minutes)) or max_allowed_minutes < 0:
        raise ValueError("Maximum age must be finite and non-negative")
    try:
        stamp = pd.to_datetime(m5_choch_time, utc=True)
        now = pd.to_datetime(current_time if current_time is not None else datetime.now(timezone.utc), utc=True)
        if pd.isna(stamp) or pd.isna(now):
            raise ValueError("Missing timestamp")
        elapsed = (now-stamp).total_seconds()/60
    except (ValueError, TypeError, OverflowError):
        return dict(is_fresh=False, elapsed_minutes=None, reason="M5: Timestamp CHoCH invalido",
                    code="M5_CHOCH_TIMESTAMP_INVALID")
    code = "M5_CHOCH_TIME_IN_FUTURE" if elapsed < 0 else "M5_SIGNAL_EXPIRED" if elapsed > max_allowed_minutes else None
    reason = ("M5: Timestamp CHoCH en el futuro" if elapsed < 0 else
              f"M5: Senal caducada ({elapsed:.1f} min > {max_allowed_minutes} min max)" if code else None)
    return dict(is_fresh=code is None, elapsed_minutes=round(elapsed,1),
                reason=reason, code=code, choch_timestamp=stamp.isoformat(),
                evaluated_at=now.isoformat(), max_allowed_minutes=max_allowed_minutes)


def evaluate_m5_confirmation_detailed(m5_data, current_time_m5=None, max_age_minutes=10,
                                      check_freshness=True):
    native = bool(m5_data.get('has_choch'))
    sweep = bool(m5_data.get('has_sweep'))
    tag = 'STANDARD_CHOCH_SWEEP'
    choch = native
    stamp = m5_data.get('choch_timestamp')
    if sweep and not native:
        if m5_data.get('has_bos_direction_flip'):
            choch, tag = True, 'RECLASSIFIED_BOS_TO_CHOCH'
            stamp = m5_data.get('bos_timestamp', stamp)
        elif m5_data.get('has_wick_break_with_fvg') and m5_data.get('has_fvg'):
            choch, tag = True, 'VALIDATED_WICK_CHOCH_WITH_FVG'
            stamp = m5_data.get('wick_break_timestamp', stamp)
    freshness = None
    if check_freshness and (choch or stamp is not None):
        freshness = validate_m5_signal_freshness(stamp,
                                                max_age_minutes, current_time_m5)
        if not freshness['is_fresh']:
            return dict(approved=False, m5_score=0, veto_reasons=[freshness['reason']],
                        veto_codes=[freshness['code']], latency_rejected=True, freshness=freshness,
                        diagnostic_tag='EXPIRED_SIGNAL' if freshness['code']=='M5_SIGNAL_EXPIRED' else 'INVALID_TIMESTAMP',
                        effective_has_choch=choch, native_has_choch=native)
    code = None
    reason = None
    if not choch and not sweep:
        tag = 'MISSING_BOTH_CHOCH_AND_SWEEP'
        code, reason = 'M5_CHOCH_AND_SWEEP_MISSING', 'M5: Sin CHoCH Y sin Barrido de Liquidez'
    elif not choch:
        code, reason = 'M5_CHOCH_MISSING', 'M5: Falta CHoCH (sin cambio por cuerpo ni mecha con FVG)'
        tag = 'TRUE_MISSING_CHOCH'
    elif not sweep:
        tag = 'MISSING_SWEEP_ONLY'
        code, reason = 'M5_SWEEP_MISSING', 'M5: Falta Barrido de Liquidez'
    score = (20 if tag=='STANDARD_CHOCH_SWEEP' else 15)*bool(choch and sweep) + 10*bool(m5_data.get('has_fvg')) + 5*bool(m5_data.get('clean_retest'))
    return dict(approved=code is None, m5_score=score, veto_reasons=[reason] if reason else [],
                veto_codes=[code] if code else [], latency_rejected=False, freshness=freshness,
                diagnostic_tag=tag, effective_has_choch=choch, native_has_choch=native)
