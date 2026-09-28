"""Conservative offline replay for shadow candidates; no order side effects."""
import pandas as pd


def replay(candles, *, confirmation_time, direction, entry, stop, target, spread=0.0):
    stamp = pd.to_datetime(confirmation_time, utc=True)
    # Candle times are opens: never use the confirmation candle's own range.
    future = candles[pd.to_datetime(candles.time, utc=True) >= stamp + pd.Timedelta(minutes=5)].copy()
    future = future.sort_values('time')
    base = {'mode':'SHADOW_ONLY','entry_authorized':False,'direction':direction,
            'entry':entry,'stop':stop,'target':target,'spread':spread,
            'confirmation_time':stamp.isoformat()}
    if direction not in {'BUY','SELL'} or spread<0 or not (stop<entry<target if direction=='BUY' else target<entry<stop):
        return {**base,'outcome':'INVALID_PLAN'}
    for _,bar in future.iterrows():
        # Input candles must be broker BID. SELL exits execute at ASK.
        low=float(bar.low)+(spread if direction=='SELL' else 0)
        high=float(bar.high)+(spread if direction=='SELL' else 0)
        sl = low<=stop if direction=='BUY' else high>=stop
        tp = high>=target if direction=='BUY' else low<=target
        if sl or tp:
            outcome='AMBIGUOUS_BOTH_BARRIERS' if sl and tp else 'SL' if sl else 'TP'
            return {**base,'outcome':outcome,'bar_time':str(bar.time),
                    'eligible_for_learning':False}
    return {**base,'outcome':'PENDING_BARRIERS','eligible_for_learning':False}
