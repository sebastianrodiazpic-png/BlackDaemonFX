"""Macro location regimes. Callers provide closed-candle ranges and current price."""
import math


def evaluate_h1_adaptive_context(df_h1, current_price, h1_range):
    """df_h1 is retained for API compatibility; the supplied range is the evidence.

    A captured expansion context may retest within 0.2% of its broken level.
    Initial context is chosen solely by price position, not by inferred trend.
    """
    invalid = dict(is_valid_location=False, context_type='OUTSIDE_RANGE_INVALID',
                   direction=None, reason='H1_RANGE_UNAVAILABLE')
    if not h1_range:
        return invalid
    try:
        hi = float(h1_range.get('swing_high', h1_range.get('high')))
        lo = float(h1_range.get('swing_low', h1_range.get('low')))
        price = float(current_price)
        tolerance = float(h1_range.get('expansion_retest_tolerance', 0.002))
        if not all(math.isfinite(x) for x in (lo, hi, price, tolerance)) or not 0 <= tolerance < 1 or hi <= lo:
            return invalid
    except (ValueError, TypeError):
        return invalid
    eq = (hi+lo)/2
    source = h1_range.get('source') or ('FALLBACK_24H' if h1_range.get('fallback_used') else 'PIVOT')
    active = h1_range.get('active_context_type')
    if active == 'EXPANSION_BUY':
        mode, direction, valid = active, 'BUY', price >= hi-abs(hi)*tolerance
    elif active == 'EXPANSION_SELL':
        mode, direction, valid = active, 'SELL', price <= lo+abs(lo)*tolerance
    elif price > hi:
        mode, direction, valid = 'EXPANSION_BUY', 'BUY', True
    elif price < lo:
        mode, direction, valid = 'EXPANSION_SELL', 'SELL', True
    elif price < eq:
        mode, direction, valid = 'RANGE_DISCOUNT', 'BUY', True
    elif price > eq:
        mode, direction, valid = 'RANGE_PREMIUM', 'SELL', True
    else:
        mode, direction, valid = 'EQUILIBRIUM', None, False
    return dict(is_valid_location=valid, context_type=mode, direction=direction if valid else None,
                source=source, is_discount=lo <= price < eq, is_premium=eq < price <= hi,
                equilibrium=eq, swing_high=hi, swing_low=lo,
                breakout_retest_level=(hi-abs(hi)*tolerance if mode=='EXPANSION_BUY' else
                                       lo+abs(lo)*tolerance if mode=='EXPANSION_SELL' else None),
                reason='H1_'+mode if valid else 'H1_PRICE_AT_EQUILIBRIUM' if mode=='EQUILIBRIUM'
                else 'H1_EXPANSION_RETEST_INVALID')


def h1_ob_location_valid(midpoint, direction, bounds):
    """OB follows the captured macro regime, including the external retest band."""
    context = evaluate_h1_adaptive_context(None, midpoint, bounds)
    if not context['is_valid_location'] or context['direction'] != direction:
        return False
    active = bounds.get('active_context_type')
    return not active or context['context_type'] == active
