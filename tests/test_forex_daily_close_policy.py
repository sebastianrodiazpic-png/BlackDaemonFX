from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

def engine():
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile='FOREX_1', execution_enabled=True)
    return e

@pytest.mark.parametrize('stamp,blocked,flat', [
    ('2026-09-22T17:59:59+00:00', False, False),
    ('2026-09-22T18:00:00+00:00', True, False),
    ('2026-09-22T20:45:00+00:00', True, True),
    ('2026-09-22T21:00:00+00:00', False, False),
    ('2026-09-25T21:00:00+00:00', True, False),
    ('2026-09-27T20:59:59+00:00', True, False),
    ('2026-09-27T21:00:00+00:00', False, False),
    ('2026-12-01T19:00:00+00:00', True, False),
    ('2026-12-01T21:45:00+00:00', True, True),
    ('2026-12-01T22:00:00+00:00', False, False),
])
def test_boundaries_dst_and_weekend(stamp, blocked, flat):
    s = engine()._forex_rollover_status(datetime.fromisoformat(stamp))
    assert s['block_new_entries'] == blocked
    assert s['force_flat_now'] == flat

def test_closes_winners_and_losers_only_owned_forex_and_retries_errors():
    e = engine()
    e._forex_rollover_status = lambda: {'force_flat_now': True}
    close = Mock(side_effect=[RuntimeError('temporary'), {'closed': True}, {'closed': True}, {'closed': True}])
    e.lifecycle_manager = SimpleNamespace(trade_executor=SimpleNamespace(close_position=close))
    e.repository = SimpleNamespace(open_trades=lambda **kw: [
        {'id': i, 'instrument': symbol, 'broker_position_ticket': str(i), 'net_pnl': pnl}
        for i, symbol, pnl in [(1, 'GBPCAD', -30), (2, 'EURUSD', 20), (3, 'XAUUSD', 0), (4, 'GBPUSD', 0)]])
    e._trade_owned_by_current_bot = lambda trade: trade['id'] != 4
    e._persist_audit_event = Mock()
    assert e._close_forex_positions_for_rollover()['closed'] == 1
    assert e._close_forex_positions_for_rollover()['closed'] == 2
    assert close.call_count == 4

def test_no_close_outside_window():
    e = engine()
    e._forex_rollover_status = lambda: {'force_flat_now': False}
    assert e._close_forex_positions_for_rollover()['closed'] == 0
