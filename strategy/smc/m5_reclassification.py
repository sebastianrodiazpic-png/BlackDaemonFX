"""Causal entry-only evidence for BOS reversals and wick breaks after a sweep."""
import pandas as pd
import numpy as np
from strategy.smc.structural_validation import fractal_pivots


def detect_m5_reclassification(data, direction, setup_time, confirmation_index, window=3):
    d=data.iloc[:confirmation_index+1].reset_index(drop=True)
    buy=direction=='long'
    sweep_key='bullish_sweep' if buy else 'bearish_sweep'
    bos_key='bos_bullish' if buy else 'bos_bearish'
    result=dict(bos_index=None, wick_index=None, bos_timestamp=None,
                wick_break_timestamp=None, sweep_index=None, reference_level=None)
    def flag(row,key):
        value=row.get(key)
        return pd.notna(value) and bool(value)
    for i in range(confirmation_index,max(0,confirmation_index-window)-1,-1):
        if pd.to_datetime(d.iloc[i]['time'],utc=True)<setup_time:
            continue
        sweeps=[j for j in range(i) if pd.to_datetime(d.iloc[j]['time'],utc=True)>=setup_time and flag(d.iloc[j],sweep_key)]
        if not sweeps:
            continue
        j=sweeps[-1]
        # Demonstrate an adverse move into the sweep before the directional break.
        if j<1 or not (d.close.iloc[j]<d.close.iloc[j-1] if buy else d.close.iloc[j]>d.close.iloc[j-1]):
            continue
        row=d.iloc[i]
        sweep_level=float(d.iloc[j]['high' if buy else 'low'])
        if flag(row,bos_key) and (row.close>sweep_level if buy else row.close<sweep_level):
            level=row.get('structure_break_level')
            if pd.notna(level) and np.isfinite(float(level)) and (row.close>float(level) if buy else row.close<float(level)):
                result.update(bos_index=i,bos_timestamp=row['time'],sweep_index=j,reference_level=float(level))
                return result
        # Pivot must already be confirmed at the sweep, never by later breakout bars.
        highs,lows=fractal_pivots(d.iloc[:j+1],2)
        pivots=np.flatnonzero(highs if buy else lows)
        if not len(pivots):
            continue
        pivot=int(pivots[-1]);level=float(d.iloc[pivot]['high' if buy else 'low'])
        prior=d.iloc[pivot+2:i]
        consumed=(prior.close>level).any() if buy else (prior.close<level).any()
        wick=(row.high>level and row.close<=level and row.high>sweep_level if buy else
              row.low<level and row.close>=level and row.low<sweep_level)
        if wick and not consumed and result['wick_index'] is None:
            result.update(wick_index=i,wick_break_timestamp=row['time'],sweep_index=j,reference_level=level)
    return result
