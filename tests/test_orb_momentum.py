
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from test_orb_new_york_strategy import FakeProvider, _session_candles
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


def evaluate(direction="BUY", change=None, enabled=True):
    candles = _session_candles(direction).iloc[:4].copy()
    if change:
        for key, value in change.items():
            candles.loc[3, key] = value
    now = datetime(2026, 8, 28, 13, 50, 1, tzinfo=timezone.utc)
    return NewYorkORBStrategy(FakeProvider(candles, now), ORBConfig(
        momentum_enabled=enabled, require_vwap_alignment=False,
        require_poc_alignment=False)).analyze_symbol("US500", now)


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
def test_momentum_accepts_first_closed_breakout(direction):
    result = evaluate(direction)
    assert result["valid"]
    assert result["signal"]["orb_entry_mode"] == "ORB_BREAKOUT_MOMENTUM"
    assert result["signal"]["direction"] == direction
    assert result["signal"]["retest_candle_time_ny"] is None
    assert "orb_retest_confirmed" not in result["signal"]["confirmations"]


@pytest.mark.parametrize("change,reason", [
    ({"open": 106.1}, "MOMENTUM_BODY_TOO_SMALL"),
    ({"close": 105.1}, "MOMENTUM_DISPLACEMENT_INSUFFICIENT"),
    ({"close": 108., "high": 108.1}, "MOMENTUM_OVEREXTENDED"),
    ({"tick_volume": 0}, "MOMENTUM_VOLUME_UNCONFIRMED"),
])
def test_momentum_filters(change, reason):
    result = evaluate(change=change)
    assert not result["valid"]
    assert reason in result["momentum_rejection_reasons"]


def test_strict_mode_still_requires_another_candle():
    assert not evaluate(enabled=False)["valid"]


def test_no_unclosed_momentum():
    candles = _session_candles().iloc[:4]
    now = datetime(2026, 8, 28, 13, 49, 59, tzinfo=timezone.utc)
    result = NewYorkORBStrategy(FakeProvider(candles, now)).analyze_symbol("US500", now)
    assert not result["valid"]


@pytest.mark.parametrize("h4,h1,blocked", [
    ("BULLISH", "BULLISH", False),
    ("BEARISH", "BULLISH", True),
    ("UNKNOWN", "BULLISH", True),
    ("BULLISH", "BEARISH", True),
])
def test_momentum_is_independent_of_htf(h4, h1, blocked):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(orb_htf_context_enabled=False, orb_use_m15_context=False)
    engine.multi_timeframe = SimpleNamespace(analyze_symbol=lambda _: {
        "h4": {"context": {"trend": h4}}, "h1_trend": h1})
    result = engine._orb_higher_timeframe_context("US500", "BUY", momentum=True)
    assert result["blocked"] is False
    assert result["enabled"] is False


def test_retest_near_edge_and_deep_rejection():
    candles = _session_candles()
    now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
    candles.loc[4, "low"] = 105.1
    strategy = NewYorkORBStrategy(FakeProvider(candles, now))
    result = strategy.analyze_symbol("US500", now)
    assert result["valid"]
    assert result["orb_entry_mode"] == "ORB_BREAKOUT_RETEST"
    candles.loc[4, "low"] = 102.
    assert not NewYorkORBStrategy(FakeProvider(candles, now)).analyze_symbol("US500", now)["valid"]
