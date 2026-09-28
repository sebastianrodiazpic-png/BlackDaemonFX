
import pandas as pd
import pytest
from strategy.smc.entry_location import closed_range, evaluate_entry_location
from strategy.smc.market_structure import get_current_trend
from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig


@pytest.mark.parametrize("points,expected", [
    (["HH","HL","LH","LL"], "BEARISH"),
    (["LH","LL","HH","HL"], "BULLISH"),
    (["HL","LH","HH","LL"], "NEUTRAL"),
    (["HH","HL","LH","HL"], "NEUTRAL"),
])
def test_latest_high_low_pair_has_no_buy_precedence(points, expected):
    assert get_current_trend(pd.DataFrame({"structure": points})) == expected


def test_mixed_htf_not_overridden_by_internal_bullish_event():
    data = pd.DataFrame({"time": pd.date_range("2026-09-14", periods=4, freq="h", tz="UTC"),
                         "structure": ["HL","LH","HH","LL"], "bos_bullish": [False]*3+[True]})
    result = MultiTimeframeAnalyzer(None)._get_h1_context({"data":data,"summary":{"trend":"BULLISH"}})
    assert result["trend"] == "NEUTRAL"
    assert not result["valid"]


@pytest.mark.parametrize("direction,price,allowed", [
    ("BUY", 125., True), ("BUY", 175., False),
    ("SELL", 175., True), ("SELL", 125., False),
    ("BUY", 150., False), ("SELL", 150., False),
    ("BUY", 99., False), ("SELL", 201., False),
    ("BUY", float("nan"), False),
])
def test_current_price_controls_location(direction, price, allowed):
    ranges = {tf: {"low":100., "high":200.} for tf in ("H1","M15","M5")}
    assert evaluate_entry_location(direction, price, ranges)["valid"] is allowed


def test_missing_history_fails_closed():
    data = pd.DataFrame({"high":[200.]*99,"low":[100.]*99})
    assert closed_range(data) is None
    assert not evaluate_entry_location("BUY",125.,{})["valid"]


def test_spread_can_move_buy_from_discount_into_premium():
    ranges = {tf: {"low":100., "high":200.} for tf in ("H1","M15","M5")}
    assert evaluate_entry_location("BUY",149.9,ranges)["valid"]
    assert not evaluate_entry_location("BUY",150.1,ranges)["valid"]


class LocationAnalyzer(MultiTimeframeAnalyzer):
    def __init__(self, direction, price):
        super().__init__(None, MultiTimeframeConfig(
            require_h4_h1_convergence=False, smc_entry_location_enabled=True))
        self.direction, self.price = direction, price

    def _get_stage_result(self, symbol, timeframe, count):
        assert timeframe != "H4", "SMC must not fetch H4"
        times = pd.date_range("2026-09-14",periods=100,freq="5min",tz="UTC")
        data = pd.DataFrame({"time":times,"open":self.price,"high":200.,
                             "low":100.,"close":self.price,"structure":None})
        data["high"] = 190.; data["low"] = 110.
        data.loc[20,"high"] = 200.; data.loc[40,"low"] = 100.
        data.loc[96:99,"structure"] = (["HH","HL","HH","HL"] if self.direction=="BUY" else ["LH","LL","LH","LL"])
        setup = {"setup_time":times[-2],"setup_type":"long" if self.direction=="BUY" else "short",
                 "zone":"discount" if self.direction=="BUY" else "premium"}
        signal = {"entry_time":times[-1],"direction":self.direction,
                  "entry_price":self.price,"stop_loss":110. if self.direction=="BUY" else 190.,
                  "take_profit":190. if self.direction=="BUY" else 110.,
                  "risk_reward_ratio":2., "valid":True, "confirmations":{}}
        return data, {"data":data, "summary":{}, "diagnostics":{},
                      "setups":pd.DataFrame([setup]),"confirmations":pd.DataFrame([signal])}, {}


@pytest.mark.parametrize("direction,price,valid",[
    ("BUY",175.,False),("BUY",125.,True),("SELL",125.,False),("SELL",175.,True)])
@pytest.mark.parametrize("symbol", ["XAUUSD", "EURUSD", "Volatility 15 (1s) Index", "Step Index", "Jump 25 Index"])
def test_full_analyzer_requires_current_zone_despite_valid_old_ob(direction, price, valid, symbol):
    result = LocationAnalyzer(direction,price).analyze_symbol(symbol)
    assert result["valid"] is valid, result
    if not valid:
        assert result["action"] == "ENTRY_LOCATION_BLOCKED"
    else:
        assert "entry_location_ranges" in result["signal"]


@pytest.mark.parametrize("symbol,direction,price,valid", [
    ("Boom 500 Index", "BUY", 125., True),
    ("Boom 500 Index", "BUY", 175., False),
    ("Boom 500 Index", "SELL", 175., False),
    ("Crash 500 Index", "SELL", 175., True),
    ("Crash 500 Index", "SELL", 125., False),
    ("Crash 500 Index", "BUY", 125., False),
])
def test_location_does_not_override_boom_crash_direction_policy(symbol, direction, price, valid):
    assert LocationAnalyzer(direction, price).analyze_symbol(symbol)["valid"] is valid


@pytest.mark.parametrize("symbol", ["XAUUSD", "EURUSD", "Step Index"])
def test_correct_location_without_m5_confirmation_still_waits(symbol):
    analyzer = LocationAnalyzer("BUY", 125.)
    original = analyzer._get_stage_result
    def without_confirmation(*args):
        data, result, timing = original(*args)
        result["confirmations"] = pd.DataFrame()
        return data, result, timing
    analyzer._get_stage_result = without_confirmation
    result = analyzer.analyze_symbol(symbol)
    assert not result["valid"]
    assert result["action"] != "ENTRY_LOCATION_BLOCKED"


def test_h1_location_is_required_even_if_h4_would_allow_buy():
    ranges = {"H4":{"low":90.,"high":210.}, "H1":{"low":100.,"high":140.},
              "M15":{"low":100.,"high":200.},"M5":{"low":100.,"high":200.}}
    result = evaluate_entry_location("BUY",125.,ranges)
    assert not result["valid"]
    assert result["rejection_reasons"] == ["H1_ENTRY_LOCATION_INCOMPATIBLE"]
    assert "H4" not in result["timeframes"]


def test_legacy_h4_ranges_do_not_replace_missing_h1():
    result = evaluate_entry_location("BUY",125.,{
        tf:{"low":100.,"high":200.} for tf in ("H4","M15","M5")})
    assert "H1_RANGE_UNAVAILABLE" in result["rejection_reasons"]
