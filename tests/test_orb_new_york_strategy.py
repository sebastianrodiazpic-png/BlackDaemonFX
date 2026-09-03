from datetime import datetime, timezone

import pandas as pd

from strategy.orb.new_york_orb import (
    ORBConfig,
    NewYorkORBStrategy,
    classify_orb_market,
    is_orb_eligible_symbol,
    is_orb_gold_symbol,
    score_orb_gold_contract_candidate,
)


class FakeProvider:
    def __init__(self, candles, now):
        self._candles = candles
        self._now = now

    def get_candles(self, symbol, timeframe, count=1000):
        assert timeframe == "M5"
        return self._candles.copy()

    def get_current_tick(self, symbol):
        return {"time": pd.Timestamp(self._now), "bid": 1.0, "ask": 1.0}


def _session_candles(direction="BUY", valid_retest=True):
    # Friday 2026-08-28. NY = UTC-4. 09:30..09:40 forma ORB; 09:45 breakout; 09:50 retest.
    times = pd.date_range("2026-08-28 13:30:00+00:00", periods=5, freq="5min")
    rows = []
    opening = [
        (102.0, 103.0, 104.0, 101.5),
        (103.0, 102.5, 105.0, 102.0),
        (102.5, 102.0, 103.5, 100.0),
    ]
    for i, ts in enumerate(times):
        if i < 3:
            o,c,h,l = opening[i]
        elif i == 3:  # breakout M5 09:45
            if direction == "BUY":
                o,c,h,l = 104.8,106.2,106.6,104.7
            else:
                o,c,h,l = 100.2,98.8,100.4,98.4
        else:  # retest M5 09:50
            if direction == "BUY":
                if valid_retest:
                    o,c,h,l = 106.1,105.8,106.4,104.9  # toca OR high=105 y cierra fuera
                else:
                    o,c,h,l = 106.1,106.0,106.4,105.4  # nunca retestea 105
            else:
                if valid_retest:
                    o,c,h,l = 98.9,99.2,100.1,98.6  # toca OR low=100 y cierra debajo
                else:
                    o,c,h,l = 98.9,99.0,99.5,98.6
        rows.append({
            "time": ts, "open": o, "high": h, "low": l, "close": c,
            "tick_volume": 100 + i, "real_volume": 0,
        })
    return pd.DataFrame(rows)


def _strategy(candles, now):
    return NewYorkORBStrategy(FakeProvider(candles, now), ORBConfig())


def test_orb_symbol_scope_is_limited_to_requested_markets():
    assert classify_orb_market("XAUUSDmicro") == "MICRO_XAUUSD"
    assert classify_orb_market("microXAUUSD") == "MICRO_XAUUSD"
    assert classify_orb_market("XAUUSD") == "XAUUSD"
    assert classify_orb_market("Gold BB Pullback Index") is None
    assert classify_orb_market("Wall Street 30") == "WALL_STREET_30"
    assert classify_orb_market("USTEC") == "US_TECH_100"
    assert classify_orb_market("US500") == "US_500"
    assert classify_orb_market("SPX500") == "US_500"
    assert classify_orb_market("S&P 500") == "US_500"
    assert classify_orb_market("SandP500") == "US_500"
    assert classify_orb_market("US SP 500") == "US_500"
    assert not is_orb_eligible_symbol("Volatility 75 Index")


def test_orb_builds_15_minute_range_before_allowing_breakout():
    candles = _session_candles("BUY")
    now = datetime(2026, 8, 28, 13, 42, 30, tzinfo=timezone.utc)
    result = _strategy(candles, now).analyze_symbol("XAUUSD", now)
    assert result["valid"] is False
    assert result["action"] == "BUILDING_OPENING_RANGE"


def test_orb_buy_requires_m5_breakout_then_retest_and_midpoint_stop():
    candles = _session_candles("BUY", valid_retest=True)
    now = datetime(2026, 8, 28, 13, 55, 30, tzinfo=timezone.utc)  # retest 09:50 ya cerró
    result = _strategy(candles, now).analyze_symbol("XAUUSDmicro", now)
    assert result["valid"] is True
    assert result["action"] == "ORB_SIGNAL_CONFIRMED"
    signal = result["signal"]
    assert signal["timeframe"] == "M5"
    assert signal["direction"] == "BUY"
    assert signal["opening_range_high"] == 105.0
    assert signal["opening_range_low"] == 100.0
    assert signal["opening_range_midpoint"] == 102.5
    assert signal["stop_loss"] == 102.5
    assert signal["entry_price"] == 105.8
    assert signal["risk_reward_ratio"] == 2.0
    assert signal["confirmations"]["m5_fresh_breakout"] is True
    assert signal["confirmations"]["orb_retest_confirmed"] is True
    assert signal["confirmations"]["stop_at_orb_50_percent"] is True


def test_orb_rejects_breakout_without_retest():
    candles = _session_candles("BUY", valid_retest=False)
    now = datetime(2026, 8, 28, 13, 55, 30, tzinfo=timezone.utc)
    result = _strategy(candles, now).analyze_symbol("XAUUSD", now)
    assert result["valid"] is False
    assert result["action"] == "WAITING_M5_BREAKOUT_RETEST"
    assert result["reason"] == "BREAKOUT_M5_SIN_RETEST_CONFIRMADO_AL_ORB"


def test_orb_sell_requires_m5_breakout_then_retest_and_midpoint_stop():
    candles = _session_candles("SELL", valid_retest=True)
    now = datetime(2026, 8, 28, 13, 55, 30, tzinfo=timezone.utc)
    result = _strategy(candles, now).analyze_symbol("US500", now)
    assert result["valid"] is True
    signal=result["signal"]
    assert signal["direction"] == "SELL"
    assert signal["stop_loss"] == 102.5
    assert signal["entry_price"] == 99.2
    assert signal["risk_reward_ratio"] == 2.0


def test_orb_is_disabled_after_new_york_session_close():
    candles = _session_candles("BUY")
    now = datetime(2026, 8, 28, 20, 1, 0, tzinfo=timezone.utc)
    result = _strategy(candles, now).analyze_symbol("Wall Street 30", now)
    assert result["valid"] is False
    assert result["reason"] == "SESION_NEW_YORK_FINALIZADA"


def test_orb_does_not_run_on_weekends():
    candles = _session_candles("BUY")
    now = datetime(2026, 8, 29, 14, 0, 0, tzinfo=timezone.utc)
    result = _strategy(candles, now).analyze_symbol("XAUUSDmicro", now)
    assert result["valid"] is False
    assert result["reason"] == "FIN_DE_SEMANA_NEW_YORK"


def test_orb_gold_scope_accepts_standard_and_micro_gold():
    assert is_orb_gold_symbol("XAUUSD")
    assert is_orb_gold_symbol("XAUUSDmicro")
    assert not is_orb_gold_symbol("US500")


def test_gold_contract_score_prefers_more_precise_half_percent_risk():
    precise = score_orb_gold_contract_candidate(target_leg_risk=50.0, actual_leg_risk=49.9, spread_cost=1.0, margin_required=100.0, free_margin=9000.0)
    coarse = score_orb_gold_contract_candidate(target_leg_risk=50.0, actual_leg_risk=47.0, spread_cost=0.5, margin_required=50.0, free_margin=9000.0)
    assert precise["score"] < coarse["score"]


def test_gold_contract_score_uses_spread_and_margin_as_execution_quality_tiebreakers():
    efficient = score_orb_gold_contract_candidate(target_leg_risk=50.0, actual_leg_risk=49.5, spread_cost=0.5, margin_required=50.0, free_margin=9000.0)
    expensive = score_orb_gold_contract_candidate(target_leg_risk=50.0, actual_leg_risk=49.5, spread_cost=2.0, margin_required=300.0, free_margin=9000.0)
    assert efficient["score"] < expensive["score"]
