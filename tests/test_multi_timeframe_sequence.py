import pandas as pd

from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig


def _frame(times, column):
    return pd.DataFrame({column: pd.to_datetime(times, utc=True)})


def test_sequence_uses_latest_m15_when_required():
    analyzer = MultiTimeframeAnalyzer(
        None, MultiTimeframeConfig(require_latest_m15_setup=True, require_m5_after_m15=True)
    )
    m15 = _frame(['2026-08-25 10:00:00', '2026-08-25 11:00:00'], 'setup_time')
    m5 = _frame(['2026-08-25 10:30:00'], 'entry_time')

    setup, signal, status, diag = analyzer._select_ordered_pair(m15, m5)

    assert status == 'STALE_M5_CONFIRMATIONS'
    assert setup['setup_time'] == pd.Timestamp('2026-08-25 11:00:00+00:00')
    assert signal is None
    assert diag['selected_setup_time'] == '2026-08-25T11:00:00+00:00'


def test_sequence_can_fall_back_to_previous_m15_when_config_allows_it():
    analyzer = MultiTimeframeAnalyzer(
        None, MultiTimeframeConfig(require_latest_m15_setup=False, require_m5_after_m15=True)
    )
    m15 = _frame(['2026-08-25 10:00:00', '2026-08-25 11:00:00'], 'setup_time')
    m5 = _frame(['2026-08-25 10:30:00'], 'entry_time')

    setup, signal, status, diag = analyzer._select_ordered_pair(m15, m5)

    assert status == 'VALID_SEQUENCE'
    assert setup['setup_time'] == pd.Timestamp('2026-08-25 10:00:00+00:00')
    assert signal['entry_time'] == pd.Timestamp('2026-08-25 10:30:00+00:00')
    assert diag['eligible_confirmations'] == 1


def test_sequence_can_disable_m5_after_m15_requirement():
    analyzer = MultiTimeframeAnalyzer(
        None, MultiTimeframeConfig(require_latest_m15_setup=True, require_m5_after_m15=False)
    )
    m15 = _frame(['2026-08-25 11:00:00'], 'setup_time')
    m5 = _frame(['2026-08-25 10:30:00'], 'entry_time')

    setup, signal, status, diag = analyzer._select_ordered_pair(m15, m5)

    assert status == 'VALID_SEQUENCE'
    assert setup is not None and signal is not None
    assert diag['require_m5_after_m15'] is False
