import pandas as pd

from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


def _analyzer(max_age=3, max_minutes=None):
    return MultiTimeframeAnalyzer(
        data_provider=None,
        config=MultiTimeframeConfig(
            max_m5_signal_age_candles=max_age,
            max_m5_signal_age_minutes=max_minutes,
        ),
    )


def test_m5_signal_age_exact_index_is_fresh_at_limit():
    times = pd.date_range('2026-08-25 14:00:00+00:00', periods=5, freq='5min')
    data = pd.DataFrame({'time': times})
    signal = {'entry_time': times[1]}

    diag = _analyzer(max_age=3)._signal_age_diagnostics(data, signal)

    assert diag['signal_found_in_m5'] is True
    assert diag['signal_bar_index'] == 1
    assert diag['latest_bar_index'] == 4
    assert diag['age_candles'] == 3
    assert diag['is_stale'] is False
    assert diag['valid'] is True


def test_m5_signal_age_becomes_stale_after_limit():
    times = pd.date_range('2026-08-25 14:00:00+00:00', periods=6, freq='5min')
    data = pd.DataFrame({'time': times})
    signal = {'entry_time': times[1]}

    diag = _analyzer(max_age=3)._signal_age_diagnostics(data, signal)

    assert diag['age_candles'] == 4
    assert diag['stale_by_candles'] is True
    assert diag['is_stale'] is True
    assert diag['reason'] == 'M5_SIGNAL_TOO_OLD'


def test_m5_signal_age_minutes_can_block_even_when_candle_limit_allows():
    times = pd.to_datetime([
        '2026-08-25 14:00:00+00:00',
        '2026-08-25 14:05:00+00:00',
        '2026-08-25 14:10:00+00:00',
        '2026-08-25 14:15:00+00:00',
    ])
    data = pd.DataFrame({'time': times})
    signal = {'entry_time': times[0]}

    diag = _analyzer(max_age=10, max_minutes=10)._signal_age_diagnostics(data, signal)

    assert diag['age_candles'] == 3
    assert diag['age_minutes'] == 15.0
    assert diag['stale_by_minutes'] is True
    assert diag['is_stale'] is True


def _engine(max_drift=0.5):
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(max_entry_drift_r=max_drift)
    return engine


def test_market_signal_buy_is_invalidated_at_structural_stop():
    signal = {'entry_price': 100.0}
    diag = _engine()._market_signal_diagnostics(
        'Boom 100 Index', 'BUY', signal,
        {'bid': 89.0, 'ask': 90.0}, 90.0, 90.0
    )
    assert diag['market_invalidated_signal'] is True
    assert diag['reason'] == 'BUY_MARKET_AT_OR_BELOW_STRUCTURAL_SL'


def test_market_signal_sell_is_invalidated_at_structural_stop():
    signal = {'entry_price': 100.0}
    diag = _engine()._market_signal_diagnostics(
        'Crash 100 Index', 'SELL', signal,
        {'bid': 110.0, 'ask': 111.0}, 110.0, 110.0
    )
    assert diag['market_invalidated_signal'] is True
    assert diag['reason'] == 'SELL_MARKET_AT_OR_ABOVE_STRUCTURAL_SL'


def test_market_signal_blocks_large_entry_drift_in_r_units():
    signal = {'entry_price': 100.0}
    diag = _engine(max_drift=0.5)._market_signal_diagnostics(
        'Boom 100 Index', 'BUY', signal,
        {'bid': 106.0, 'ask': 106.0}, 106.0, 90.0
    )
    assert diag['market_invalidated_signal'] is False
    assert diag['entry_drift_r'] == 0.6
    assert diag['entry_drift_exceeded'] is True
    assert diag['reason'] == 'ENTRY_PRICE_DRIFT_TOO_LARGE'


def test_signal_age_uses_temporal_fallback_when_timestamp_is_not_exact_candle():
    times = pd.date_range('2026-08-25 14:00:00+00:00', periods=5, freq='5min')
    data = pd.DataFrame({'time': times})
    signal = {'entry_time': pd.Timestamp('2026-08-25 14:07:00+00:00')}

    diag = _analyzer(max_age=3)._signal_age_diagnostics(data, signal)

    assert diag['signal_found_in_m5'] is False
    assert diag['age_candles'] == 3
    assert diag['is_stale'] is False
    assert diag['valid'] is True
