from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from strategy.execution.commodity_spread_gate import (
    CommoditySpreadGuard,
    get_commodity_spec,
    is_commodity_rollover,
)

START = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)


def quote(now, spread=0.25, bid=2650.0):
    return {
        'spread_status': 'AVAILABLE',
        'spread_source': 'MT5_EXECUTION',
        'spread': spread,
        'execution_bid': bid,
        'execution_ask': bid + spread,
        'spread_quote_time': now.isoformat(),
        'spread_captured_at': now.isoformat(),
    }


def warm(guard, symbol='XAUUSD', base_spread=0.25):
    for i in range(18):
        now = START + timedelta(seconds=12 * i)
        guard.observe(symbol, quote(now, spread=base_spread), now)
    return now


def test_commodity_spec_resolution():
    gold_spec = get_commodity_spec('XAUUSD')
    assert gold_spec['max_spread'] == 0.45
    assert gold_spec['pip'] == 0.10

    oil_spec = get_commodity_spec('US Oil')
    assert oil_spec['max_spread'] == 0.08

    silver_spec = get_commodity_spec('XAGUSD')
    assert silver_spec['max_spread'] == 0.06


def test_rollover_window_detection():
    # 17:00 NY = 22:00 UTC (in standard/winter time UTC-5)
    # Check directly using datetime in NY
    from zoneinfo import ZoneInfo
    ny_tz = ZoneInfo('America/New_York')
    ny_rollover_time = datetime(2026, 11, 10, 17, 15, tzinfo=ny_tz)
    assert is_commodity_rollover(ny_rollover_time)

    ny_trading_time = datetime(2026, 11, 10, 10, 30, tzinfo=ny_tz)
    assert not is_commodity_rollover(ny_trading_time)


def test_spread_risk_ratio_evaluation(tmp_path):
    guard = CommoditySpreadGuard('TEST_COMMODITIES', tmp_path, max_risk_ratio=0.015)
    now = warm(guard, 'XAUUSD', base_spread=0.25) + timedelta(seconds=15)

    # Entry = 2650.25, Stop = 2620.0 -> Distance = 30.25
    # Spread = 0.25 / 30.25 = 0.0082 (0.82% <= 1.5%) -> Allowed!
    res_good = guard.check('XAUUSD', quote(now, spread=0.25), 'BUY', 2620.0, now=now)
    assert res_good['allowed']
    assert res_good['reason'] == 'SPREAD_ACCEPTED'

    # Stop too tight: Entry = 2650.25, Stop = 2640.0 -> Distance = 10.25
    # Spread = 0.25 / 10.25 = 0.0243 (2.43% > 1.5%) -> Rejected!
    res_tight = guard.check('XAUUSD', quote(now, spread=0.25), 'BUY', 2640.0, now=now)
    assert not res_tight['allowed']
    assert res_tight['reason'] == 'SPREAD_RISK_RATIO_EXCEEDED'


def test_hard_spread_cap_rejection(tmp_path):
    guard = CommoditySpreadGuard('TEST_COMMODITIES', tmp_path)
    now = warm(guard, 'US Oil', base_spread=0.04) + timedelta(seconds=15)

    # US Oil cap is 0.08. If spread jumps to 0.12 (night spread), reject by cap
    res_wide = guard.check('US Oil', quote(now, spread=0.12, bid=72.0), 'BUY', 65.0, now=now)
    assert not res_wide['allowed']
    assert res_wide['reason'] == 'SPREAD_ABOVE_HARD_CAP'


def test_rollover_rejection(tmp_path):
    guard = CommoditySpreadGuard('TEST_COMMODITIES', tmp_path)
    from zoneinfo import ZoneInfo
    ny_tz = ZoneInfo('America/New_York')
    rollover_time = datetime(2026, 11, 10, 17, 0, tzinfo=ny_tz)

    res_rollover = guard.check('XAUUSD', quote(rollover_time, spread=0.25), 'BUY', 2600.0, now=rollover_time)
    assert not res_rollover['allowed']
    assert res_rollover['reason'] == 'COMMODITY_ROLLOVER_MAINTENANCE'


def test_commodities_worker_profile_architecture():
    from app.main import BOT_PROFILES, _selection_profile_for_bot
    assert "COMMODITIES_SNR" in BOT_PROFILES
    profile = BOT_PROFILES["COMMODITIES_SNR"]
    assert profile["mode"] == "commodities-snr-daemon"
    assert profile["magic"] == 26082041
    symbols = profile["symbols"]
    assert "XAUUSD" in symbols
    assert "XAUEUR" in symbols
    assert "XAGUSD" in symbols
    assert "US Oil" in symbols
    assert "UK Brent Oil" in symbols
    assert _selection_profile_for_bot("COMMODITIES_SNR") == "COMMODITIES_SNR"
    assert _selection_profile_for_bot("COMMODITIES") == "COMMODITIES_SNR"


def test_is_commodity_symbol_classification():
    from strategy.execution.commodity_spread_gate import is_commodity_symbol
    assert is_commodity_symbol("XAUUSD")
    assert is_commodity_symbol("XAUUSDmicro")
    assert is_commodity_symbol("XAUEUR")
    assert is_commodity_symbol("XAGUSD")
    assert is_commodity_symbol("US Oil")
    assert is_commodity_symbol("UK Brent Oil")
    assert not is_commodity_symbol("EURUSD")
    assert not is_commodity_symbol("Jump 75 Index")
    assert not is_commodity_symbol("Wall Street 30")
