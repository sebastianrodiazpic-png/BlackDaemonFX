from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pytest

from strategy.execution.index_spread_gate import (
    IndexSpreadGuard,
    get_index_spec,
    is_index_cash_session,
    is_index_symbol,
)

START = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)


def quote(now, spread=1.5, bid=43500.0):
    return {
        'spread_status': 'AVAILABLE',
        'spread_source': 'MT5_EXECUTION',
        'spread': spread,
        'execution_bid': bid,
        'execution_ask': bid + spread,
        'spread_quote_time': now.isoformat(),
        'spread_captured_at': now.isoformat(),
    }


def test_index_spec_resolution():
    dow_spec = get_index_spec('Wall Street 30')
    assert dow_spec['max_spread'] == 4.0
    assert dow_spec['tz'] == 'America/New_York'

    nas_spec = get_index_spec('US Tech 100')
    assert nas_spec['max_spread'] == 2.5

    dax_spec = get_index_spec('Germany 40')
    assert dax_spec['max_spread'] == 3.0
    assert dax_spec['tz'] == 'Europe/Berlin'


def test_index_symbol_classification():
    assert is_index_symbol("Wall Street 30")
    assert is_index_symbol("US Tech 100")
    assert is_index_symbol("US SP 500")
    assert is_index_symbol("Germany 40")
    assert not is_index_symbol("XAUUSD")
    assert not is_index_symbol("EURUSD")
    assert not is_index_symbol("Jump 75 Index")


def test_cash_session_detection():
    ny_tz = ZoneInfo('America/New_York')
    # Martes 10:30 NY -> Dentro de sesión de contado (08:00 - 16:00)
    in_session_ny = datetime(2026, 11, 10, 10, 30, tzinfo=ny_tz)
    assert is_index_cash_session('Wall Street 30', in_session_ny)

    # Martes 08:30 NY -> Dentro de sesión extendida / pre-market institucional (>= 08:00 NY)
    pre_market_ny = datetime(2026, 11, 10, 8, 30, tzinfo=ny_tz)
    assert is_index_cash_session('Wall Street 30', pre_market_ny)

    # Martes 07:30 NY -> Fuera de sesión (< 08:00 NY)
    early_ny = datetime(2026, 11, 10, 7, 30, tzinfo=ny_tz)
    assert not is_index_cash_session('Wall Street 30', early_ny)

    # Sábado 12:00 NY -> Fin de semana
    weekend_ny = datetime(2026, 11, 14, 12, 0, tzinfo=ny_tz)
    assert not is_index_cash_session('Wall Street 30', weekend_ny)

    # Germany 40: 10:00 Frankfurt -> Dentro de sesión (08:00 - 16:30 CET)
    berlin_tz = ZoneInfo('Europe/Berlin')
    in_session_dax = datetime(2026, 11, 10, 10, 0, tzinfo=berlin_tz)
    assert is_index_cash_session('Germany 40', in_session_dax)


def test_index_spread_guard_evaluation(tmp_path):
    guard = IndexSpreadGuard('TEST_INDICES', tmp_path, max_risk_ratio=0.015)
    ny_tz = ZoneInfo('America/New_York')
    now = datetime(2026, 11, 10, 11, 0, tzinfo=ny_tz)

    # Warmup
    for i in range(16):
        t = now + timedelta(seconds=12 * i)
        guard.observe('Wall Street 30', quote(t, spread=1.8), t)

    check_time = now + timedelta(seconds=12 * 17)

    # Entry = 43501.8, Stop = 43300.0 -> Distance = 201.8 pts
    # Spread = 1.8 / 201.8 = 0.0089 (0.89% <= 1.5%) -> Allowed!
    res_good = guard.check('Wall Street 30', quote(check_time, spread=1.8), 'BUY', 43300.0, now=check_time)
    assert res_good['allowed']
    assert res_good['reason'] == 'SPREAD_ACCEPTED'

    # Spread spike above cap (5.5 pts > 4.0 pts) -> Rejected!
    res_spike = guard.check('Wall Street 30', quote(check_time, spread=5.5), 'BUY', 43300.0, now=check_time)
    assert not res_spike['allowed']
    assert res_spike['reason'] == 'SPREAD_ABOVE_HARD_CAP'

    # Outside cash session
    off_hours = datetime(2026, 11, 10, 20, 0, tzinfo=ny_tz)
    res_off = guard.check('Wall Street 30', quote(off_hours, spread=1.8), 'BUY', 43300.0, now=off_hours)
    assert not res_off['allowed']
    assert res_off['reason'] == 'INDEX_OFF_MARKET_HOURS'
