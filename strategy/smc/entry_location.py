"""Validate the current entry against closed-candle ranges, not the old OB zone."""
import math
import pandas as pd


def closed_range(data, lookback=100):
    """Range of the last complete lookback; caller supplies closed candles only."""
    if data is None or len(data) < lookback:
        return None
    window = data.tail(lookback)
    if not {"high", "low"}.issubset(window.columns):
        return None
    high = pd.to_numeric(window["high"], errors="coerce")
    low = pd.to_numeric(window["low"], errors="coerce")
    if not all(math.isfinite(float(v)) for v in list(high) + list(low)) or (high < low).any():
        return None
    lo, hi = float(low.min()), float(high.max())
    if hi <= lo:
        return None
    return {"low": lo, "high": hi, "equilibrium": (hi + lo) / 2,
            "lookback": lookback,
            "as_of": str(window["time"].iloc[-1]) if "time" in window else None}


def evaluate_entry_location(direction, price, ranges, policy="ALL_TIMEFRAMES"):
    """Fail closed: BUY in discount / SELL in premium on every required timeframe."""
    if policy not in {"ALL_TIMEFRAMES", "H1_PRIMARY"}:
        raise ValueError("Unknown SMC entry location policy: " + str(policy))
    required = ("H1",) if policy == "H1_PRIMARY" else ("H1", "M15", "M5")
    failures, evidence = [], {}
    try:
        price = float(price)
    except (TypeError, ValueError):
        price = float("nan")
    for timeframe in required:
        bounds = ranges.get(timeframe)
        if not bounds:
            failures.append(timeframe + "_RANGE_UNAVAILABLE")
            continue
        lo, hi = bounds["low"], bounds["high"]
        midpoint = (lo + hi) / 2
        zone = "discount" if price < midpoint else "premium" if price > midpoint else "equilibrium"
        valid = (math.isfinite(price) and lo <= price <= hi and
                 ((direction == "BUY" and zone == "discount") or
                  (direction == "SELL" and zone == "premium")))
        macro = None
        if timeframe == 'H1' and bounds.get('adaptive_context_enabled'):
            from strategy.smc.h1_adaptive_context import evaluate_h1_adaptive_context
            macro = evaluate_h1_adaptive_context(None, price, bounds)
            valid = bool(macro['is_valid_location'] and macro['direction'] == direction)
            zone = macro['context_type']
        evidence[timeframe] = {**bounds, "price": price if math.isfinite(price) else None,
                               "zone": zone, "allowed": valid}
        if not valid:
            failures.append(timeframe + "_ENTRY_LOCATION_INCOMPATIBLE")
    return {"policy": policy, "valid": not failures, "direction": direction, "timeframes": evidence,
            "rejection_reasons": failures, "range_method": (ranges.get("H1") or {}).get("method", "CLOSED_ROLLING_HIGH_LOW")}
