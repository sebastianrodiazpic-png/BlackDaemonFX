"""Measurable interpretations of the supplied SNR lessons, using closed data."""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import math
from .universe import FAMILIES, canonical_symbol


def session_allowed(symbol, now, policy='legacy_utc', synthetic=False):
    if synthetic:
        return True
    if policy == 'legacy_utc':
        hour = now.hour + now.minute / 60 + now.second / 3600
        return 7 <= hour < 11 or 12.5 <= hour < 17
    if policy != 'market_hours':
        raise ValueError('INVALID_MSNR_SESSION_POLICY')
    if canonical_symbol(symbol).upper() in FAMILIES['crypto']:
        return True
    # Local session clocks preserve the windows through each city's DST changes.
    try:
        london = now.tz_convert(ZoneInfo('Europe/London'))
        new_york = now.tz_convert(ZoneInfo('America/New_York'))
    except ZoneInfoNotFoundError as exc:
        raise ValueError('SESSION_TIMEZONE_UNAVAILABLE') from exc
    lh = london.hour + london.minute / 60 + london.second / 3600
    nh = new_york.hour + new_york.minute / 60 + new_york.second / 3600
    return 7 <= lh < 11 or 7 <= nh < 12


def breaker_pair_candidate(frame, atr, min_body_ratio=.50, min_displacement_atr=.50):
    """Close/open junction of two strong same-color candles, including zero gap."""
    if len(frame) < 2 or not math.isfinite(atr) or atr <= 0:
        return None
    previous, last = frame.iloc[-2], frame.iloc[-1]
    sign = 1 if previous.close > previous.open and last.close > last.open else -1 if previous.close < previous.open and last.close < last.open else 0
    if not sign:
        return None
    ratios = []
    for candle in (previous, last):
        span = float(candle.high - candle.low)
        ratios.append(sign * float(candle.close - candle.open) / span if span > 0 else 0.)
    if min(ratios) < min_body_ratio:
        return None
    level = float(previous.close)
    displacement = sign * (float(last.close) - level) / atr
    if displacement < min_displacement_atr:
        return None
    return {'direction': 'BUY' if sign == 1 else 'SELL', 'level': level,
            'bound': float(min(previous.low, last.low) if sign == 1 else max(previous.high, last.high)),
            'minimum_pair_body_ratio': min(ratios), 'displacement_atr': displacement,
            'junction_gap_atr': abs(float(last.open) - level) / atr}


def _to_utc_timestamp(ts):
    if ts is None:
        return None
    import pandas as pd
    if isinstance(ts, str):
        ts = pd.Timestamp(ts)
    if getattr(ts, 'tzinfo', None) is None:
        return ts.tz_localize('UTC')
    return ts.tz_convert('UTC')


def track_session_liquidity(candles, symbol, now, policy='market_hours', direction=None):
    """
    Evaluates session context and detects session liquidity sweeps according to Malaysian SNR & ICT principles:
    1. For Forex / Metals / Traditional Indices:
       - Asian Session: 00:00 to 07:00 UTC (captures asian_high, asian_low, asian_range).
       - London Session: 07:00 to 12:00 UTC (Killzone: 07:00 - 11:00 UTC).
         * Bearish Judas Swing: Price trades above Asian High into an SNR resistance level and rejects.
         * Bullish Judas Swing: Price trades below Asian Low into an SNR support level and rejects.
       - New York Session: 12:00 to 20:00 UTC (Killzone: 12:30 - 17:00 UTC).
         * Bearish: Trades above London High (or Asian High) into SNR resistance and rejects.
         * Bullish: Trades below London Low (or Asian Low) into SNR support and rejects.
    2. For Synthetics / 24-Hour continuous markets:
       - Rolling 4-Hour blocks:
         * Bearish: Trades above prior H4 cycle high into SNR resistance.
         * Bullish: Trades below prior H4 cycle low into SNR support.
    """
    if candles is None or len(candles) < 4:
        return {'session_name': 'UNKNOWN', 'sweep_confirmed': False, 'sweep_type': 'NONE', 'swept_level': None}

    now_utc = _to_utc_timestamp(now)
    hour = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
    today_date = now_utc.date()

    canon = canonical_symbol(symbol).upper()
    is_synth = canon in FAMILIES.get('synthetic', ()) or any(w in symbol.lower() for w in ('boom', 'crash', 'volatility', 'step', 'jump'))
    is_crypto = canon in FAMILIES.get('crypto', ())

    if not is_synth and not is_crypto:
        if 0.0 <= hour < 7.0:
            active_session = 'ASIAN'
        elif 7.0 <= hour < 12.0:
            active_session = 'LONDON'
        elif 12.0 <= hour < 20.0:
            active_session = 'NEW_YORK'
        else:
            active_session = 'OFF_HOURS'

        times = candles['time'].apply(_to_utc_timestamp)

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


def fakeout_trap_candidate(candle, level: float, direction: str, atr: float,
                           max_penetration_atr: float = 0.60,
                           min_wick_ratio: float = 0.50) -> dict | None:
    """
    Evaluates whether a candle represents a Fakeout Trap / Liquidity Sweep:
    - Pierces the SNR level with a wick (retail stop run).
    - Penetration depth is bounded (<= max_penetration_atr).
    - Closes back inside or within tolerance of the level.
    - Exhibits strong rejection absorption (wick_ratio >= min_wick_ratio).
    """
    if atr <= 0 or not math.isfinite(atr):
        return None
    span = float(candle.high - candle.low)
    if span <= 0:
        return None
    sign = 1 if direction == 'BUY' else -1 if direction == 'SELL' else 0
    if sign == 0:
        return None

    extreme = float(candle.low if sign == 1 else candle.high)
    depth = max(0.0, -sign * (extreme - level) / atr)

    # Must have pierced the level by wick
    if depth <= 0.0 or depth > max_penetration_atr:
        return None

    # Candle body must have reclaimed/closed on the valid side of the level (or within tiny tolerance 0.10 ATR)
    close_dist = sign * (float(candle.close) - level) / atr
    if close_dist < -0.10:
        return None

    rejection_wick = (float(min(candle.open, candle.close) - candle.low) if sign == 1
                      else float(candle.high - max(candle.open, candle.close)))
    wick_ratio = rejection_wick / span if span > 0 else 0.0

    if wick_ratio < min_wick_ratio:
        return None

    return {
        'is_fakeout': True,
        'direction': direction,
        'penetration_atr': round(depth, 4),
        'wick_ratio': round(wick_ratio, 4),
        'close_distance_atr': round(close_dist, 4),
        'reclaimed': True,
    }


def h1_ema_dynamic_confluence(h1_candles, level: float, direction: str | None = None,
                              period: int = 50, tolerance_atr: float = 0.40) -> dict:
    """
    Evaluates dynamic support/resistance confluence on H1 with EMA (typically EMA 50):
    - Computes EMA of `period` on H1 closed candle closes.
    - Tests distance from `level` to the current EMA value.
    - If within tolerance_atr * atr, confirms dynamic confluence.
    """
    if h1_candles is None or len(h1_candles) < period or tolerance_atr < 0:
        return {'confluence': False, 'ema_value': None, 'distance_atr': None}

    import pandas as pd
    closes = h1_candles['close']
    ema_series = closes.ewm(span=period, adjust=False).mean()
    ema_val = float(ema_series.iloc[-1])

    prev_close = closes.shift(1)
    tr = pd.concat([
        h1_candles['high'] - h1_candles['low'],
        (h1_candles['high'] - prev_close).abs(),
        (h1_candles['low'] - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr_val = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else float(tr.mean())

    if atr_val <= 0 or not math.isfinite(atr_val):
        return {'confluence': False, 'ema_value': ema_val, 'distance_atr': None}

    dist_atr = abs(level - ema_val) / atr_val
    confluent = dist_atr <= tolerance_atr

    return {
        'confluence': bool(confluent),
        'ema_value': round(ema_val, 5),
        'distance_atr': round(dist_atr, 4),
        'period': period,
    }
