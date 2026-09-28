"""M15 supplies causal OB zones; M5 owns entry structure and confirmation."""
import math
import pandas as pd
from strategy.smc.structural_validation import validate_m15_ob_structure, validate_m15_ob_flexible


def build_m15_setups(data, config):
    rows, audit = [], []
    if data is None or data.empty:
        return pd.DataFrame(), audit
    d = data.reset_index(drop=True)
    # Prior candles only: the impulse cannot inflate its own reference range.
    reference = (d.high - d.low).rolling(config.confirmation_range_lookback).mean().shift(1)
    seen = set()
    for i in range(1, len(d)):
        c = d.iloc[i]
        for direction in ('long', 'short'):
            bullish = direction == 'long'
            if not (c.close > c.open if bullish else c.close < c.open):
                continue
            origin = next((j for j in range(i-1, max(-1, i-config.order_block_lookback-1), -1)
                           if (d.iloc[j].close < d.iloc[j].open if bullish else d.iloc[j].close > d.iloc[j].open)), None)
            if origin is None:
                continue
            if config.m15_flexible_structure and i-origin > config.m15_impulse_bars:
                continue
            ob = d.iloc[origin]
            if not (c.close > ob.high if bullish else c.close < ob.low):
                continue
            key = (origin, direction)
            if key in seen:
                continue
            width = float(c.high-c.low)
            displacement = (math.isfinite(float(reference.iloc[i])) and width > 0
                            and width >= float(reference.iloc[i])*config.displacement_range_multiplier
                            and abs(float(c.close-c.open))/width >= config.minimum_body_ratio)
            reasons = []
            if not displacement and not config.adaptive_smc_score_enabled:
                reasons.append('M15_OB_DISPLACEMENT_REQUIRED')
            if config.m15_flexible_structure:
                structure = validate_m15_ob_flexible(d.iloc[:i+1], origin, direction,
                                                    impulse_bars=config.m15_impulse_bars)
            else:
                structure = validate_m15_ob_structure(d.iloc[:i+1], origin, direction,
                    n=getattr(config, 'm15_fractal_window', 3))
            if (not structure['has_structure_break']
                    and not (config.adaptive_smc_score_enabled and displacement)):
                reasons.append('M15_OB_STRUCTURE_BREAK_REQUIRED')
            low, high = float(ob.low), float(ob.high)
            if not (math.isfinite(low) and math.isfinite(high) and high > low):
                reasons.append('M15_OB_INVALID_BOUNDS')
            zone = str(ob.get('zone', 'unknown'))
            # Location is validated against H1 by the coordinator.
            following = d.iloc[i+1:]
            if ((following.close < low) if bullish else (following.close > high)).any():
                reasons.append('M15_OB_INVALIDATED_BY_CLOSE')
            if len(d)-1-i > config.max_retest_candles:
                reasons.append('M15_OB_EXPIRED')
            ready = pd.to_datetime(c.time, utc=True)+pd.Timedelta(minutes=15)
            item = dict(ob_time=pd.to_datetime(ob.time, utc=True).isoformat(),
                        setup_time=ready.isoformat(), direction='BUY' if bullish else 'SELL',
                        ob_low=low, ob_high=high, zone=zone, accepted=not reasons, reasons=reasons, m15_structure=structure)
            audit.append(item)
            if reasons:
                continue
            seen.add(key)
            rows.append(dict(time=ready, setup_time=ready, break_time=ready,
                             setup_type=direction, ob_low=low, ob_high=high,
                             ob_type='bullish' if bullish else 'bearish', zone=zone,
                             equilibrium=ob.get('equilibrium'),
                             premium_discount_ok=(zone == ('discount' if bullish else 'premium')),
                             setup_origin='M15_DISPLACEMENT_OB', structure_break_type=None,
                             structure_break_ok=structure['has_structure_break'],
                             m15_has_displacement=bool(displacement), m15_is_invalidated=False,
                             m15_structure=structure))
    return pd.DataFrame(rows), audit
