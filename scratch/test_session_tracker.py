import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import numpy as np

def _to_utc(ts):
    if ts is None:
        return None
    if isinstance(ts, str):
        ts = pd.Timestamp(ts)
    if getattr(ts, 'tzinfo', None) is None:
        return ts.tz_localize('UTC')
    return ts.tz_convert('UTC')

def track_session_liquidity(candles, symbol, now, policy='market_hours', direction=None):
    if candles is None or len(candles) < 4:
        return {'session_name': 'UNKNOWN', 'sweep_confirmed': False, 'sweep_type': 'NONE', 'swept_level': None}
    
    now_utc = _to_utc(now)
    hour = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
    today_date = now_utc.date()
    
    from strategy.malaysian_snr.universe import FAMILIES, canonical_symbol
    canon = canonical_symbol(symbol).upper()
    is_synth = canon in FAMILIES.get('synthetic', ()) or any(w in symbol.lower() for w in ('boom', 'crash', 'volatility', 'step', 'jump'))
    is_crypto = canon in FAMILIES.get('crypto', ())
    
    if not is_synth and not is_crypto:
        # Forex, Metals, Traditional Indices
        if 0.0 <= hour < 7.0:
            active_session = 'ASIAN'
        elif 7.0 <= hour < 12.0:
            active_session = 'LONDON'
        elif 12.0 <= hour < 20.0:
            active_session = 'NEW_YORK'
        else:
            active_session = 'OFF_HOURS'
            
        times = candles['time'].apply(_to_utc)
        
        # Asian session candles for today: 00:00 to 07:00 UTC
        asia_mask = (times.dt.date == today_date) & (times.dt.hour >= 0) & (times.dt.hour < 7)
        asia_bars = candles[asia_mask]
        
        asian_high = float(asia_bars['high'].max()) if len(asia_bars) > 0 else None
        asian_low = float(asia_bars['low'].min()) if len(asia_bars) > 0 else None
        asian_range = (asian_high - asian_low) if (asian_high is not None and asian_low is not None) else None
        
        # London session candles: 07:00 to 12:00 UTC
        london_mask = (times.dt.date == today_date) & (times.dt.hour >= 7) & (times.dt.hour < 12)
        london_bars = candles[london_mask]
        london_high = float(london_bars['high'].max()) if len(london_bars) > 0 else None
        london_low = float(london_bars['low'].min()) if len(london_bars) > 0 else None
        
        # Current session candles up to now
        curr_mask = (times.dt.date == today_date) & (times <= now_utc)
        if active_session == 'LONDON':
            curr_mask = curr_mask & (times.dt.hour >= 7)
        elif active_session == 'NEW_YORK':
            curr_mask = curr_mask & (times.dt.hour >= 12)
        curr_bars = candles[curr_mask]
        curr_high = float(curr_bars['high'].max()) if len(curr_bars) > 0 else None
        curr_low = float(curr_bars['low'].min()) if len(curr_bars) > 0 else None
        
        sweep_confirmed = False
        sweep_type = 'NONE'
        swept_level = None
        
        if direction == 'SELL':
            if active_session == 'LONDON' and asian_high is not None and curr_high is not None and curr_high > asian_high:
                sweep_confirmed = True
                sweep_type = 'ASIAN_HIGH_SWEPT'
                swept_level = asian_high
            elif active_session == 'NEW_YORK':
                if london_high is not None and curr_high is not None and curr_high > london_high:
                    sweep_confirmed = True
                    sweep_type = 'LONDON_HIGH_SWEPT'
                    swept_level = london_high
                elif asian_high is not None and curr_high is not None and curr_high > asian_high:
                    sweep_confirmed = True
                    sweep_type = 'ASIAN_HIGH_SWEPT'
                    swept_level = asian_high
        elif direction == 'BUY':
            if active_session == 'LONDON' and asian_low is not None and curr_low is not None and curr_low < asian_low:
                sweep_confirmed = True
                sweep_type = 'ASIAN_LOW_SWEPT'
                swept_level = asian_low
            elif active_session == 'NEW_YORK':
                if london_low is not None and curr_low is not None and curr_low < london_low:
                    sweep_confirmed = True
                    sweep_type = 'LONDON_LOW_SWEPT'
                    swept_level = london_low
                elif asian_low is not None and curr_low is not None and curr_low < asian_low:
                    sweep_confirmed = True
                    sweep_type = 'ASIAN_LOW_SWEPT'
                    swept_level = asian_low
                    
        return {
            'session_name': active_session,
            'is_synthetic': False,
            'asian_high': asian_high,
            'asian_low': asian_low,
            'asian_range': asian_range,
            'london_high': london_high,
            'london_low': london_low,
            'current_session_high': curr_high,
            'current_session_low': curr_low,
            'sweep_confirmed': sweep_confirmed,
            'sweep_type': sweep_type,
            'swept_level': swept_level,
        }
    else:
        # Synthetic / Crypto 24/7: H4 cycle tracking
        active_session = 'SYNTHETIC_24_7'
        # Prior 16 bars vs current 4 bars
        prior_bars = candles.iloc[-20:-4] if len(candles) >= 20 else candles.iloc[:-4] if len(candles) > 6 else candles.iloc[:len(candles)//2]
        curr_bars = candles.iloc[-4:]
        prior_h4_high = float(prior_bars['high'].max())
        prior_h4_low = float(prior_bars['low'].min())
        curr_high = float(curr_bars['high'].max())
        curr_low = float(curr_bars['low'].min())
        
        sweep_confirmed = False
        sweep_type = 'NONE'
        swept_level = None
        
        if direction == 'SELL' and curr_high > prior_h4_high:
            sweep_confirmed = True
            sweep_type = 'PRIOR_H4_HIGH_SWEPT'
            swept_level = prior_h4_high
        elif direction == 'BUY' and curr_low < prior_h4_low:
            sweep_confirmed = True
            sweep_type = 'PRIOR_H4_LOW_SWEPT'
            swept_level = prior_h4_low
            
        return {
            'session_name': active_session,
            'is_synthetic': True,
            'prior_h4_high': prior_h4_high,
            'prior_h4_low': prior_h4_low,
            'current_high': curr_high,
            'current_low': curr_low,
            'sweep_confirmed': sweep_confirmed,
            'sweep_type': sweep_type,
            'swept_level': swept_level,
        }

# Test with mock data
print("Testing track_session_liquidity...")
# Asian candles: 00:00 to 06:45 (range 1.0800 - 1.0830)
t0 = pd.Timestamp('2026-10-13 00:00:00Z')
bars = []
for i in range(28):
    bars.append({'time': t0 + pd.Timedelta(minutes=15*i), 'open': 1.0810, 'high': 1.0830, 'low': 1.0800, 'close': 1.0820})
# London candle at 07:30 sweeping asian high: high 1.0845, close 1.0815
bars.append({'time': pd.Timestamp('2026-10-13 07:15:00Z'), 'open': 1.0820, 'high': 1.0845, 'low': 1.0815, 'close': 1.0825})
bars.append({'time': pd.Timestamp('2026-10-13 07:30:00Z'), 'open': 1.0825, 'high': 1.0850, 'low': 1.0810, 'close': 1.0815})
df = pd.DataFrame(bars)

res_sell = track_session_liquidity(df, 'EURUSD', pd.Timestamp('2026-10-13 07:45:00Z'), direction='SELL')
print("EURUSD Sell result:", res_sell)
assert res_sell['sweep_confirmed'] is True
assert res_sell['sweep_type'] == 'ASIAN_HIGH_SWEPT'
assert res_sell['swept_level'] == 1.0830

res_buy = track_session_liquidity(df, 'EURUSD', pd.Timestamp('2026-10-13 07:45:00Z'), direction='BUY')
print("EURUSD Buy result:", res_buy)
assert res_buy['sweep_confirmed'] is False

print("ALL TESTS PASSED SUCCESSFULLY!")
