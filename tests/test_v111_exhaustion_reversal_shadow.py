from datetime import datetime, timedelta, timezone

import pandas as pd

from strategy.execution.live_trading_engine import LiveTradingEngine
from strategy.smc.exhaustion_reversal import (
    ExhaustionReversalConfig,
    detect_exhaustion_reversal,
)


def _h1_range():
    times = pd.date_range("2026-09-08", periods=60, freq="h", tz="UTC")
    return pd.DataFrame(
        {"time": times, "open": 50.0, "high": 100.0, "low": 0.0, "close": 50.0}
    )


def _m5_base():
    times = pd.date_range("2026-09-11 10:00", periods=22, freq="5min", tz="UTC")
    rows = []
    for index, stamp in enumerate(times):
        center = 80.0 + (index % 2)
        rows.append(
            {
                "time": stamp,
                "open": center,
                "high": center + 2.0,
                "low": center - 2.0,
                "close": center + 0.5,
                "tick_volume": 100.0,
            }
        )
    return pd.DataFrame(rows)


def _sell_sequence():
    data = _m5_base()
    data.loc[data.index[-2], ["open", "high", "low", "close", "tick_volume"]] = [83.0, 90.0, 80.0, 82.0, 200.0]
    data.loc[data.index[-1], ["open", "high", "low", "close", "tick_volume"]] = [82.0, 83.0, 68.0, 69.0, 150.0]
    return data


def _buy_sequence():
    data = _m5_base()
    for index in data.index[:-2]:
        center = 19.0 + (index % 2)
        data.loc[index, ["open", "high", "low", "close"]] = [center, center + 2.0, center - 2.0, center - 0.5]
    data.loc[data.index[-2], ["open", "high", "low", "close", "tick_volume"]] = [17.0, 20.0, 10.0, 18.0, 200.0]
    data.loc[data.index[-1], ["open", "high", "low", "close", "tick_volume"]] = [18.0, 32.0, 17.0, 31.0, 150.0]
    return data


def test_premium_exhaustion_confirms_shadow_sell():
    result = detect_exhaustion_reversal(
        _h1_range(), _sell_sequence(), symbol="EURUSD"
    )
    assert result["valid"] is True
    assert result["direction"] == "SELL"
    assert result["action"] == "EXHAUSTION_REVERSAL_SHADOW_SIGNAL"
    assert result["reason"] == "PREMIUM_EXHAUSTION_SELL_CONFIRMED"
    assert result["checks"]["liquidity_sweep"] is True
    assert result["checks"]["micro_choch"] is True
    assert result["checks"]["displacement"] is True


def test_discount_exhaustion_confirms_shadow_buy():
    result = detect_exhaustion_reversal(
        _h1_range(), _buy_sequence(), symbol="XAUUSD"
    )
    assert result["valid"] is True
    assert result["direction"] == "BUY"
    assert result["reason"] == "DISCOUNT_EXHAUSTION_BUY_CONFIRMED"


def test_boom_policy_blocks_sell_exhaustion():
    result = detect_exhaustion_reversal(
        _h1_range(), _sell_sequence(), symbol="Boom 1000 Index", allowed_direction="BUY"
    )
    assert result["valid"] is False
    assert result["direction"] == "SELL"
    assert result["direction_allowed"] is False
    assert result["reason"] == "DIRECTION_POLICY_REQUIRES_BUY"


def test_missing_volume_does_not_create_false_data_failure():
    data = _sell_sequence().drop(columns=["tick_volume"])
    result = detect_exhaustion_reversal(_h1_range(), data, symbol="EURUSD")
    assert result["valid"] is True
    assert result["volume_applicable"] is False


def test_compact_audit_keeps_exhaustion_shadow_decision():
    shadow = detect_exhaustion_reversal(
        _h1_range(), _sell_sequence(), symbol="EURUSD"
    )
    compact = LiveTradingEngine._compact_symbol_result(
        {
            "symbol": "EURUSD",
            "action": "NO_M15_SETUP",
            "analysis": {
                "valid": False,
                "action": "NO_M15_SETUP",
                "exhaustion_reversal_shadow": shadow,
            },
        }
    )
    assert compact["action"] == "NO_M15_SETUP"
    assert compact["exhaustion_reversal_shadow"]["valid"] is True
    assert compact["exhaustion_reversal_shadow"]["direction"] == "SELL"


def test_attach_shadow_never_changes_primary_execution_decision():
    engine = object.__new__(LiveTradingEngine)
    engine._exhaustion_reversal_shadow = lambda symbol: {
        "strategy_name": "SMC_EXHAUSTION_REVERSAL",
        "mode": "SHADOW",
        "valid": True,
        "action": "EXHAUSTION_REVERSAL_SHADOW_SIGNAL",
        "reason": "DISCOUNT_EXHAUSTION_BUY_CONFIRMED",
        "direction": "BUY",
    }
    events = []
    engine._persist_audit_event = lambda *args, **kwargs: events.append((args, kwargs))
    primary = {"valid": False, "action": "NO_M15_SETUP", "reason": "NO_DIRECTIONAL_M15_SETUP"}

    attached = engine._attach_exhaustion_reversal_shadow("EURUSD", primary)

    assert attached["valid"] is False
    assert attached["action"] == "NO_M15_SETUP"
    assert attached["exhaustion_reversal_shadow"]["valid"] is True
    assert len(events) == 1
