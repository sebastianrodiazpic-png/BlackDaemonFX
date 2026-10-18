"""Closed-prefix structural candidates; no provider, execution or mutable state."""
from itertools import combinations
import math
import numpy as np


def confirmed_swings(frame, radius=2, bodies=False):
    highs = frame.close.to_numpy() if bodies else frame.high.to_numpy()
    lows = frame.close.to_numpy() if bodies else frame.low.to_numpy()
    swings = []
    for i in range(radius, len(frame)-radius):
        high = highs[i] > max(highs[i-radius:i].max(), highs[i+1:i+radius+1].max())
        low = lows[i] < min(lows[i-radius:i].min(), lows[i+1:i+radius+1].min())
        if high == low:
            continue
        point = {'type': 'HIGH' if high else 'LOW', 'idx': i,
                 'price': float(highs[i] if high else lows[i]), 'available_idx': i+radius}
        if swings and swings[-1]['type'] == point['type']:
            if (high and point['price'] > swings[-1]['price']) or (low and point['price'] < swings[-1]['price']):
                swings[-1] = point
        else:
            swings.append(point)
    return swings


def structural_bias(frame, radius=2):
    """Confirmed close pivots and subsequent closed BOS; neutral when ambiguous."""
    if len(frame) < 2*radius+3:
        return None
    swings = confirmed_swings(frame, radius, bodies=True)
    highs = [s for s in swings if s['type']=='HIGH']
    lows = [s for s in swings if s['type']=='LOW']
    if not highs or not lows:
        return None
    events = []
    for side, direction in ((highs, 'BUY'), (lows, 'SELL')):
        pivot = side[-1]
        closes = frame.close.to_numpy()[pivot['available_idx']+1:]
        crossed = np.flatnonzero(closes > pivot['price'] if direction=='BUY' else closes < pivot['price'])
        if len(crossed):
            events.append((pivot['available_idx']+1+int(crossed[0]), direction))
    if events:
        events.sort()
        if len(events)>1 and events[-1][0]==events[-2][0]:
            return None
        return events[-1][1]
    if len(highs)>=2 and len(lows)>=2:
        if highs[-1]['price']>highs[-2]['price'] and lows[-1]['price']>lows[-2]['price']:
            return 'BUY'
        if highs[-1]['price']<highs[-2]['price'] and lows[-1]['price']<lows[-2]['price']:
            return 'SELL'
    return None


def role_flip_candidates(frame, levels, max_changes=1, min_displacement_atr=.20, atr=1.):
    """Emit only a new closing role change, with history and episode identity."""
    found = []
    last_idx = len(frame)-1
    for level in levels:
        price = float(level['level'])
        resistance = level['type']=='A_RESISTANCE'
        changes = 0
        last_event = None
        for idx in range(level['idx']+1, len(frame)):
            close = float(frame.close.iloc[idx])
            crossed = close > price if resistance else close < price
            if crossed:
                changes += 1
                last_event = idx
                resistance = not resistance
        if last_event != last_idx or not 1 <= changes <= max_changes:
            continue
        direction = 'SELL' if resistance else 'BUY'
        sign = 1 if direction=='BUY' else -1
        # A crossing candle must leave sufficient closed displacement.
        if sign*(float(frame.close.iloc[-1])-price) < min_displacement_atr*atr:
            continue
        found.append({**level, 'direction': direction, 'role_changes': changes,
                      'episode_closed_at': frame.time.iloc[-1].isoformat()})
    return found


def extended_quasimodo_candidates(frame, radius=2, swing_window=8, min_head_depth_atr=.20, atr=1.):
    """Search bounded non-adjacent triples without using unconfirmed pivots."""
    swings = confirmed_swings(frame, radius)[-swing_window:]
    closes = frame.close.to_numpy()
    found = []
    for a, b, head in combinations(swings, 3):
        bullish = a['type']=='LOW' and b['type']=='HIGH' and head['type']=='LOW'
        bearish = a['type']=='HIGH' and b['type']=='LOW' and head['type']=='HIGH'
        if not (bullish or bearish):
            continue
        depth = a['price']-head['price'] if bullish else head['price']-a['price']
        if depth < min_head_depth_atr*atr:
            continue
        offset = head['available_idx']+1
        crossed = np.flatnonzero(closes[offset:] > b['price'] if bullish else closes[offset:] < b['price'])
        if not len(crossed) or offset+int(crossed[0]) != len(frame)-1:
            continue
        found.append({'direction':'BUY' if bullish else 'SELL', 'shoulder':a['price'],
                      'head':head['price'], 'neckline':b['price'], 'head_depth_atr':depth/atr})
    return list(reversed(found))


def gap_candidate(frame, atr, min_size_atr=.05, tick_size=0., spread=0., min_ticks=2, spread_multiple=2.):
    """Material directional close/open band formed by two closed same-color bars."""
    if len(frame)<2 or not all(math.isfinite(v) for v in (atr,tick_size,spread)) or atr<=0 or tick_size<=0 or spread<=0:
        return None
    previous, last = frame.iloc[-2], frame.iloc[-1]
    buy = previous.close>previous.open and last.close>last.open and last.open>previous.close
    sell = previous.close<previous.open and last.close<last.open and last.open<previous.close
    if not (buy or sell):
        return None
    size = abs(float(last.open-previous.close))
    if size < max(min_size_atr*atr, min_ticks*tick_size, spread_multiple*spread):
        return None
    return {'direction':'BUY' if buy else 'SELL', 'level':float((last.open+previous.close)/2),
            'band_low':float(min(last.open,previous.close)), 'band_high':float(max(last.open,previous.close)),
            'size_atr':size/atr}
