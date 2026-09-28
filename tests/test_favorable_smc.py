import pandas as pd
import pytest
from strategy.smc.confirmation_engine import same_setup_exhaustion, evaluate_m5_confirmation, M5ConfirmationConfig
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from types import SimpleNamespace

@pytest.mark.parametrize("direction", ["long", "short"])
def test_exhaustion_requires_ob_and_later_directional_break(direction):
    df = pd.DataFrame({"time":pd.date_range("2026-09-19", periods=3, freq="5min",tz="UTC"),"open":[100,100,100],"high":[101,101,103],"low":[99,98,100],"close":[100,100.5,102]})
    if direction == "short":
        df[["open","high","low","close"]] = pd.DataFrame({"open":200-df.open,"high":200-df.low,"low":200-df.high,"close":200-df.close})
    assert same_setup_exhaustion(df,df.time.iloc[0],1,2,direction,99,101)
    assert not same_setup_exhaustion(df,df.time.iloc[0],1,1,direction,99,101)
    assert not same_setup_exhaustion(df,df.time.iloc[2],1,2,direction,99,101)
    assert not same_setup_exhaustion(df,df.time.iloc[0],1,2,direction,110,111)
    df.loc[2,"close"] = 100
    assert not same_setup_exhaustion(df,df.time.iloc[0],1,2,direction,99,101)

@pytest.mark.parametrize("profile", ["GOLD","FOREX_1","BOOM","CRASH","VOLATILITY_1","STEP","JUMP"])
def test_all_live_smc_profiles_enable_gate(profile):
    engine = LiveTradingEngine(provider=SimpleNamespace(),repository=SimpleNamespace(),executor=SimpleNamespace(),config=LiveTradingConfig(bot_profile=profile))
    assert engine.pipeline_config.require_favorable_confirmation


def test_no_pattern_or_exhaustion_cannot_be_compensated_by_score(monkeypatch):
    from test_confirmation_engine import _data, _setup
    df = _data()
    # Existing high quality fixture has too large a body for exhaustion.
    monkeypatch.setattr("strategy.smc.confirmation_engine.same_setup_exhaustion",lambda *a:False)
    result=evaluate_m5_confirmation(data=df,setup=_setup(df),retest_index=2,confirmation_index=3,direction="long",config=M5ConfirmationConfig(require_favorable_confirmation=True,chart_patterns_enabled=False,require_chart_pattern=False,require_fvg=False,minimum_trade_score=0,minimum_viable_trade_score=0,minimum_confirmation_ratio=0))
    assert not result["confirmation_valid"]
    assert "favorable_confirmation" in result["critical_confirmation_failures"]


def test_exhaustion_alternative_is_audited(monkeypatch):
    from test_confirmation_engine import _data, _setup
    df=_data()
    monkeypatch.setattr("strategy.smc.confirmation_engine.same_setup_exhaustion",lambda *a:True)
    result=evaluate_m5_confirmation(data=df,setup=_setup(df),retest_index=2,confirmation_index=3,direction="long",config=M5ConfirmationConfig(require_favorable_confirmation=True,chart_patterns_enabled=False,require_chart_pattern=False,require_fvg=False,minimum_trade_score=70))
    assert result["confirmation_valid"]
    assert result["favorable_confirmation"]["exhaustion"]
