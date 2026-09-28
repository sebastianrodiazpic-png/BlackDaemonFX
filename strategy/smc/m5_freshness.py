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
    freshness = None
    if check_freshness and (m5_data.get('has_choch') or m5_data.get('choch_timestamp') is not None):
        freshness = validate_m5_signal_freshness(m5_data.get('choch_timestamp'),
                                                max_age_minutes, current_time_m5)
        if not freshness['is_fresh']:
            return dict(approved=False, m5_score=0, veto_reasons=[freshness['reason']],
                        veto_codes=[freshness['code']], latency_rejected=True, freshness=freshness)
    choch, sweep = bool(m5_data.get('has_choch')), bool(m5_data.get('has_sweep'))
    code = None
    reason = None
    if not choch and not sweep:
        code, reason = 'M5_CHOCH_AND_SWEEP_MISSING', 'M5: Sin CHoCH Y sin Barrido de Liquidez'
    elif not choch:
        code, reason = 'M5_CHOCH_MISSING', 'M5: Falta CHoCH (Estructura interna no confirmada)'
    elif not sweep:
        code, reason = 'M5_SWEEP_MISSING', 'M5: Falta Barrido de Liquidez'
    score = 20*bool(choch and sweep) + 10*bool(m5_data.get('has_fvg')) + 5*bool(m5_data.get('clean_retest'))
    return dict(approved=code is None, m5_score=score, veto_reasons=[reason] if reason else [],
                veto_codes=[code] if code else [], latency_rejected=False, freshness=freshness)
