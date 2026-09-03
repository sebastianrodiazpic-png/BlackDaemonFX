import pandas as pd

from strategy.smc.harmonic_patterns import HarmonicConfig, detect_harmonic_confirmation


def make_swings(points):
    rows=[]
    for i,(typ,price) in enumerate(points):
        rows.append({
            'time': pd.Timestamp('2026-01-01', tz='UTC') + pd.Timedelta(minutes=i),
            'open': price, 'close': price,
            'high': price if typ == 'H' else price + 0.1,
            'low': price if typ == 'L' else price - 0.1,
            'swing_high': typ == 'H', 'swing_low': typ == 'L'
        })
    return pd.DataFrame(rows)


def test_harmonic_detector_returns_diagnostic_when_no_pattern():
    data = make_swings([('L',100),('H',110),('L',107),('H',115),('L',112)])
    result = detect_harmonic_confirmation(data, 'long', HarmonicConfig())
    assert result['harmonic_confirmed'] is False
    assert result['harmonic_rejection_reason'] in {'NO_VALID_HARMONIC_PATTERN', 'INSUFFICIENT_CONFIRMED_SWINGS'}


def test_harmonic_disabled_is_explicit():
    data = make_swings([('L',100),('H',110),('L',107),('H',115),('L',112)])
    result = detect_harmonic_confirmation(data, 'long', HarmonicConfig(enabled=False))
    assert result['harmonic_enabled'] is False
    assert result['harmonic_rejection_reason'] == 'HARMONIC_DISABLED'
