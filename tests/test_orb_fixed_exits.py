from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


@pytest.mark.parametrize('profile,metadata', [
    ('GOLD', {'strategy_name': 'ORB_NEW_YORK'}),
    ('ORB', {}),  # Recovered position without strategy metadata.
    ('GOLD', {'bot_profile': 'ORB'}),
])
@pytest.mark.parametrize('rr', [-0.8, 1.0, 2.0, 4.0])
def test_orb_never_closes_or_moves_stops_from_analysis_or_runner(profile, metadata, rr):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile=profile, runner_extension_enabled=True)
    close = Mock(side_effect=AssertionError('ORB must retain its broker exits'))
    move = Mock(side_effect=AssertionError('ORB must retain its broker stops'))
    metadata = {**metadata, 'trade_leg': 'RUNNER', 'analysis_exit_invalid_streak': 50}
    result = engine._analysis_invalidation_exit(
        trade={}, metadata=metadata, current_rr=rr, close_position=close,
    )
    assert not result['closed']
    assert result['reason'] == 'ORB_FIXED_SL_TP'
    result = engine._manage_runner_extension(
        trade={}, position=None, metadata=metadata, initial_stop_loss=90,
        current_rr=rr, move_stop=move,
    )
    assert not result['closed'] and not result['extended']
    close.assert_not_called()
    move.assert_not_called()


@pytest.mark.parametrize('leg', ['TP1', 'RUNNER', 'SINGLE'])
def test_monitor_leaves_existing_orb_positions_untouched(leg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile='ORB', execution_enabled=True)
    engine.reporting_service = None
    executor = Mock()
    engine.lifecycle_manager = SimpleNamespace(trade_executor=executor)
    engine.executor = SimpleNamespace(get_position=lambda ticket: SimpleNamespace(
        price_open=100., price_current=120., sl=90., tp=130.,
    ))
    engine._trade_owned_by_current_bot = lambda trade: True
    engine._update_excursion_metrics = lambda trade, metadata, rr, price: (metadata, False)
    engine._persist_live_position_market_snapshots = lambda snapshots: {'errors': []}
    engine.repository = SimpleNamespace(open_trades=lambda **kwargs: [{
        'direction': 'BUY', 'instrument': 'XAUUSD', 'stop_loss': 90.,
        'broker_position_ticket': '123', 'details': {'metadata': {
            'strategy_name': 'ORB_NEW_YORK', 'trade_leg': leg,
            'break_even_enabled': True, 'initial_stop_loss': 90.,
        }},
    }])
    result = engine._monitor_break_even_positions()
    assert result['checked'] == 1
    assert len(result['positions']) == 1  # Auditing remains active.
    assert result['errors'] == []
    executor.move_stop_loss.assert_not_called()
    executor.close_position.assert_not_called()


@pytest.mark.parametrize('profile', ['GOLD', 'FOREX_1', 'STEP'])
def test_smc_keeps_its_management_policy(profile):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile=profile)
    assert not engine._orb_fixed_exit_policy({'strategy_name': 'SMC'})
