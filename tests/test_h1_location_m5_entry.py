import pandas as pd
import pytest
from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig
from strategy.smc.confirmation_engine import M5ConfirmationConfig,evaluate_m5_confirmation

@pytest.mark.parametrize("trend,price,direction",[("NEUTRAL",125,"BUY"),("BEARISH",125,"BUY"),("BULLISH",175,"SELL")])
def test_h1_trend_does_not_block_zone_direction(monkeypatch,trend,price,direction):
    analyzer=MultiTimeframeAnalyzer(None,MultiTimeframeConfig(h1_location_only=True))
    frame=pd.DataFrame({"time":pd.date_range("2026-09-10",periods=100,freq="h",tz="UTC"),"open":125.,"high":200.,"low":100.,"close":price})
    frame["high"]=190.; frame["low"]=110.
    frame.loc[20,"high"]=200.; frame.loc[40,"low"]=100.
    monkeypatch.setattr(analyzer,"_get_stage_result",lambda *args:(frame,{"data":frame,"setups":pd.DataFrame(),"confirmations":pd.DataFrame(),"summary":{}},{}))
    monkeypatch.setattr(analyzer,"_get_h1_context",lambda *a:{"trend":trend,"valid":trend!="NEUTRAL","reason":"TEST","context_time":None})
    result=analyzer.analyze_symbol("EURUSD")
    assert result["action"]=="NO_M15_SETUP"
    assert result["direction"]==direction
    assert result["h1"]["context"]["role"]=="LOCATION_ONLY"


def test_explicit_m5_bos_required_even_if_micro_structure_passes():
    from test_confirmation_engine import _data,_setup
    df=_data();cfg=M5ConfirmationConfig(require_m5_structure_event=True,require_chart_pattern=False,require_fvg=False,minimum_trade_score=70)
    args=dict(data=df,setup=_setup(df),retest_index=2,confirmation_index=3,direction="long",config=cfg)
    result=evaluate_m5_confirmation(**args)
    assert "M5_BOS_CHOCH_REQUIRED" in result["critical_confirmation_failures"]
    df["bos_bullish"]=False;df.loc[3,"bos_bullish"]=True
    assert evaluate_m5_confirmation(**args)["confirmation_valid"]


def test_close_recovery_is_optional_and_keeps_penetration_cap():
    from test_confirmation_engine import _data,_setup
    df=_data();df.loc[2,["open","high","low","close"]]=[100.,100.4,99.7,99.8]
    args=dict(data=df,setup=_setup(df),retest_index=2,confirmation_index=3,direction="long")
    cfg=dict(require_chart_pattern=False,require_fvg=False,minimum_trade_score=70)
    assert not evaluate_m5_confirmation(**args,config=M5ConfirmationConfig(**cfg))["clean_retest"]
    result=evaluate_m5_confirmation(**args,config=M5ConfirmationConfig(**cfg,allow_ob_close_recovery=True))
    assert result["ob_close_recovery"] and result["clean_retest"]
    df.loc[2,"low"]=95.
    assert not evaluate_m5_confirmation(**args,config=M5ConfirmationConfig(**cfg,allow_ob_close_recovery=True))["clean_retest"]
