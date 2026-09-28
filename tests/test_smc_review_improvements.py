import pandas as pd
import pytest
from strategy.smc.entry_location import evaluate_entry_location
from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation
from strategy.execution.live_trading_engine import LiveTradingEngine


def test_h1_primary_keeps_h1_location_guard():
    ranges = {"H1": {"low": 100., "high": 200.}, "M15": {"low": 90., "high": 130.}, "M5": {"low": 100., "high": 130.}}
    assert not evaluate_entry_location("BUY", 125, ranges)["valid"]
    assert evaluate_entry_location("BUY", 125, ranges, "H1_PRIMARY")["valid"]
    assert not evaluate_entry_location("BUY", 175, ranges, "H1_PRIMARY")["valid"]
    assert not evaluate_entry_location("BUY", 125, {}, "H1_PRIMARY")["valid"]
    with pytest.raises(ValueError):
        evaluate_entry_location("BUY", 125, ranges, "typo")


def test_compact_audit_keeps_rejected_candidate_and_sequence():
    result = {"analysis": {"h1": {"context": {"trend": "NEUTRAL", "recent_swings": [{"structure": "LH"}]}}, "diagnostics": {
        "m5": {"latest_rejected_candidate": {"critical_confirmation_failures": ["clean_retest"], "missing_confirmations": ["rejection"]}},
        "sequence": {"selected_setup_time": "2026-09-16"},
        "signal_age": {"latest_closed_candle_time": "2026-09-16", "age_candles": 3}}}}
    compact = LiveTradingEngine._compact_symbol_result(result)
    assert compact["critical_confirmation_failures"] == ["clean_retest"]
    assert compact["missing_confirmations"] == ["rejection"]
    assert compact["h1_context"]["recent_swings"][0]["structure"] == "LH"
    assert compact["signal_age"]["age_candles"] == 3
    assert compact["sequence"]["selected_setup_time"] == "2026-09-16"


@pytest.mark.parametrize("direction", ["long", "short"])
def test_atr_retest_is_bounded_and_does_not_use_future_data(direction):
    df = pd.DataFrame({"time": pd.date_range("2026-01-01", periods=17, freq="5min", tz="UTC"), "open": [100.]*17, "high": [110.]*17, "low": [90.]*17, "close": [101.]*17})
    df.loc[15, ["open", "high", "low", "close"]] = [100,101,99.4,100.9]
    setup = pd.Series({"setup_time":df.iloc[14].time,"ob_low":100.,"ob_high":101.,"trend_ok":True,"sweep_ok":True,"structure_break_ok":True,"premium_discount_ok":True})
    if direction == "short":
        df.loc[15, ["open", "high", "low", "close"]] = [101,101.6,100,100.1]
    def run(mode):
        return evaluate_m5_confirmation(data=df, setup=setup, retest_index=15, confirmation_index=16, direction=direction, config=M5ConfirmationConfig(retest_tolerance_mode=mode))
    strict=run("STRICT"); variant=run("ATR_BOUNDED")
    assert not strict["clean_retest"]
    assert variant["clean_retest"]
    assert variant["retest_comparison"]["atr_bounded_limit"] == .75
    df.loc[16,"high"] = 10000.
    assert run("ATR_BOUNDED")["retest_comparison"] == variant["retest_comparison"]
    df.loc[15,"low" if direction == "long" else "high"] = 98 if direction == "long" else 103
    assert not run("ATR_BOUNDED")["clean_retest"]
