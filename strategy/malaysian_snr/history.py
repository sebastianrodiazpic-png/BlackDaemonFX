"""Bounded recovery of actual closed bars; never synthesize missing candles."""
import pandas as pd

from .validation import closed_candles, timeframe_delta


def useful_history(provider, symbol, timeframe, count, minimum, now, *, adaptive=True, limit=320):
    requested = min(max(int(count), int(minimum)), int(limit))
    attempts = []
    while True:
        raw = provider.get_candles(symbol, timeframe, count=requested)
        frame = closed_candles(raw, timeframe, now)
        source = str(getattr(raw, 'attrs', {}).get('market_data_source', ''))
        # Deriv may return a partial left-edge candle with an off-grid opening.
        # MT5 daily sessions can have legitimate broker-specific UTC offsets.
        partial = 0
        if source.startswith('DERIV') and not frame.empty:
            aligned = frame.time.dt.floor(timeframe_delta(timeframe)) == frame.time
            partial = int((~aligned).sum())
            frame = frame[aligned].reset_index(drop=True)
        attempts.append({'requested': requested, 'received': len(raw),
                         'closed_aligned': len(frame), 'partial': partial, 'source': source})
        if len(frame) >= minimum or not adaptive or requested >= limit:
            return frame, {'timeframe': timeframe, 'minimum': minimum,
                           'sufficient': len(frame) >= minimum, 'attempts': attempts,
                           'latest_closed_at': ((frame.time.iloc[-1] + timeframe_delta(timeframe)).isoformat()
                                                if not frame.empty else None)}
        requested = min(requested * 2, limit)
