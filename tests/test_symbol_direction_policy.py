from config.symbol_policy import (
    classify_synthetic_symbol,
    get_symbol_direction_policy,
    is_direction_allowed,
)


def test_boom_is_buy_only():
    assert classify_synthetic_symbol('Boom 150 Index') == 'boom'
    assert get_symbol_direction_policy('Boom 150 Index').allowed_direction == 'BUY'
    assert is_direction_allowed('Boom 150 Index', 'BUY')
    assert not is_direction_allowed('Boom 150 Index', 'SELL')


def test_crash_is_sell_only():
    assert classify_synthetic_symbol('Crash 500 Index') == 'crash'
    assert get_symbol_direction_policy('Crash 500 Index').allowed_direction == 'SELL'
    assert is_direction_allowed('Crash 500 Index', 'SELL')
    assert not is_direction_allowed('Crash 500 Index', 'BUY')


def test_other_symbols_keep_neutral_policy():
    assert get_symbol_direction_policy('Volatility 75 Index').allowed_direction is None
    assert is_direction_allowed('Volatility 75 Index', 'BUY')
    assert is_direction_allowed('Volatility 75 Index', 'SELL')

def test_pipeline_policy_filter_accepts_long_short_and_buy_sell_representations():
    import pandas as pd

    from strategy.execution.trade_pipeline import _filter_by_policy

    setups = pd.DataFrame({'setup_type': ['long', 'short', 'LONG', 'SHORT']})
    confirmations = pd.DataFrame({'direction': ['BUY', 'SELL', 'buy', 'sell']})

    boom_setups = _filter_by_policy(setups, 'setup_type', 'BUY')
    crash_setups = _filter_by_policy(setups, 'setup_type', 'SELL')
    boom_confirmations = _filter_by_policy(confirmations, 'direction', 'BUY')
    crash_confirmations = _filter_by_policy(confirmations, 'direction', 'SELL')

    assert boom_setups['setup_type'].tolist() == ['long', 'LONG']
    assert crash_setups['setup_type'].tolist() == ['short', 'SHORT']
    assert boom_confirmations['direction'].tolist() == ['BUY', 'buy']
    assert crash_confirmations['direction'].tolist() == ['SELL', 'sell']


def test_boom_confirmation_policy_does_not_drop_buy_confirmation_after_direction_conversion():
    import pandas as pd

    from strategy.execution.trade_pipeline import _filter_by_policy

    confirmations = pd.DataFrame({
        'setup_type': ['long', 'short'],
        'direction': ['BUY', 'SELL'],
        'valid': [True, True],
    })

    result = _filter_by_policy(confirmations, 'direction', 'BUY')

    assert len(result) == 1
    assert result.iloc[0]['direction'] == 'BUY'
    assert result.iloc[0]['setup_type'] == 'long'

