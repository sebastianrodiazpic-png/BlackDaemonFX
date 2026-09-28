"""Entry-only SMC guards. Never manages an existing position."""
import math
import pandas as pd
from strategy.smc.target_obstacles import target_path


def obstacle_guard(entry, stop, targets, direction, obstacles, minimum_r=1.0):
    if direction not in {'BUY', 'SELL'} or not targets or not all(
        math.isfinite(float(value)) for value in [entry, stop, minimum_r, *targets.values()]
    ) or entry == stop or minimum_r <= 0:
        raise ValueError('INVALID_PATH_INPUT')
    for zone in obstacles:
        if not all(math.isfinite(float(zone[key])) for key in ('low', 'high')) or zone['low'] > zone['high']:
            raise ValueError('INVALID_OBSTACLE_ZONE')
    paths = {name: target_path(entry, stop, target, direction, obstacles)
             for name, target in targets.items()}
    hits = [zone for path in paths.values() for zone in path['obstacles']]
    nearest = min(hits, key=lambda zone: zone['distance_r']) if hits else None
    valid = nearest is None or nearest['distance_r'] + 1e-9 >= minimum_r
    reason = ('SMC_MINIMUM_CORRIDOR_PASSED_WITH_OBSTACLES' if nearest else 'SMC_PATH_CLEAR') if valid else 'SMC_OBSTACLE_BEFORE_MIN_R'
    return {'valid': valid, 'reason': reason,
            'full_path_clear': not hits,
            'free_r_to_first_obstacle': nearest['distance_r'] if nearest else None,
            'target_r': {name: abs(target-entry)/abs(entry-stop) for name, target in targets.items()},
            'minimum_r': minimum_r, 'nearest_obstacle': nearest, 'paths': paths}


def closed_m5(data, now, timeframe_minutes=5):
    if data is None or data.empty:
        raise ValueError('M5_DATA_UNAVAILABLE')
    data = data.copy()
    data['time'] = pd.to_datetime(data['time'], utc=True, errors='coerce')
    return data[data.time + pd.Timedelta(minutes=timeframe_minutes) <= now].sort_values('time').drop_duplicates('time')


def confirmation_guard(data, signal_time, direction, now, max_later_bars=1, market_price=None, timeframe_minutes=5):
    report = {'valid': False, 'reason': 'SMC_M5_REVALIDATION_DATA_MISSING'}
    if direction not in {'BUY', 'SELL'} or max_later_bars < 0:
        return report
    if timeframe_minutes not in {1, 5}:
        return report
    data = closed_m5(data, now, timeframe_minutes)
    stamp = pd.to_datetime(signal_time, utc=True, errors='coerce')
    if data.empty or pd.isna(stamp):
        return report
    expected = now.floor(f'{timeframe_minutes}min') - pd.Timedelta(minutes=timeframe_minutes)
    if data.iloc[-1].time < expected:
        return {**report, 'reason': 'SMC_M5_FEED_STALE'}
    signal = data[data.time == stamp]
    if signal.empty:
        return report
    later = data[data.time > stamp]
    report.update(confirmation_timeframe=f'M{timeframe_minutes}', signal_time=stamp.isoformat(), latest_closed_time=data.iloc[-1].time.isoformat(),
                  later_bars=len(later), max_later_bars=max_later_bars)
    if len(later) > max_later_bars or data.iloc[-1].time - stamp > pd.Timedelta(minutes=timeframe_minutes*max_later_bars):
        return {**report, 'reason': 'SMC_M5_CONFIRMATION_EXPIRED'}
    contrary = ('bos_bearish', 'choch_bearish') if direction == 'BUY' else ('bos_bullish', 'choch_bullish')
    if not all(key in data for key in contrary):
        return report
    if any(later[key].fillna(False).astype(bool).any() for key in contrary):
        return {**report, 'reason': 'SMC_M5_OPPOSITE_STRUCTURE'}
    boundary = float(signal.iloc[-1]['low' if direction == 'BUY' else 'high'])
    prices = [float(value) for value in later['close']]
    if market_price is not None:
        prices.append(float(market_price))
    if not all(math.isfinite(value) for value in [boundary, *prices]):
        return report
    if any(value < boundary if direction == 'BUY' else value > boundary for value in prices):
        return {**report, 'reason': 'SMC_M5_CONFIRMATION_EXTREME_BROKEN', 'boundary': boundary}
    return {**report, 'valid': True, 'reason': 'SMC_M5_CONFIRMATION_CURRENT', 'boundary': boundary}


def m5_sweep_guard(data, sweep_timestamp, direction, now):
    """Recheck the supporting M5 sweep before executing an early M1 entry."""
    candles = closed_m5(data, now)
    stamp = pd.to_datetime(sweep_timestamp, utc=True, errors='coerce')
    if candles.empty or pd.isna(stamp) or candles.iloc[-1].time < now.floor('5min')-pd.Timedelta(minutes=5):
        return dict(valid=False, reason='M5_SWEEP_CONTEXT_UNAVAILABLE')
    swept = candles[candles.time + pd.Timedelta(minutes=5) == stamp]
    if swept.empty:
        return dict(valid=False, reason='M5_SWEEP_CONTEXT_UNAVAILABLE')
    later = candles[candles.time + pd.Timedelta(minutes=5) > stamp]
    contrary = ('bos_bearish', 'choch_bearish') if direction == 'BUY' else ('bos_bullish', 'choch_bullish')
    if not all(key in later for key in contrary):
        return dict(valid=False, reason='M5_SWEEP_CONTEXT_UNAVAILABLE')
    boundary = float(swept.iloc[-1]['low' if direction == 'BUY' else 'high'])
    broken = (later.close < boundary).any() if direction == 'BUY' else (later.close > boundary).any()
    opposite = any(later[key].fillna(False).astype(bool).any() for key in contrary)
    return dict(valid=not bool(broken or opposite),
                reason='M5_SWEEP_INVALIDATED' if broken or opposite else 'M5_SWEEP_CURRENT')
