import pandas as pd
from strategy.smc.target_obstacles import collect_obstacles,target_path


def test_target_audit_is_informational_and_symmetric():
    for direction,target,zone in [("BUY",120,{"low":108,"high":110}),("SELL",80,{"low":90,"high":92})]:
        result=target_path(100,95,target,direction,[zone])
        assert result["mode"]=="INFORMATION_ONLY"
        assert result["target"]==target and result["stop_loss"]==95
        assert result["obstacles"][0]["distance_r"]==1.6


def test_invalidated_ob_is_not_reported():
    data=pd.DataFrame({"time":pd.date_range("2026-09-21",periods=3,freq="15min",tz="UTC"),"high":[110,111,113],"low":[108,109,110],"close":[109,110,112],"ob_type":["bearish",None,None],"ob_low":[108,None,None],"ob_high":[110,None,None],"ob_break_time":[pd.Timestamp("2026-09-21T00:15Z"),pd.NaT,pd.NaT]})
    assert all(o["type"]!="OPPOSING_OB" for o in collect_obstacles(data,"BUY"))


def test_similar_forces_with_zero_delta_blocks(monkeypatch):
    from strategy.smc.confirmation_engine import evaluate_m5_confirmation,M5ConfirmationConfig
    from test_confirmation_engine import _data,_setup
    import strategy.smc.confirmation_engine as module
    original=module.detect_chart_pattern_confirmation
    def pattern(*args,**kwargs):
        result=original(*args,**kwargs)
        result.update(chart_pattern_confirmed=True,chart_pattern_conflict=True,chart_pattern_conflict_level="FUERZAS_SIMILARES",chart_pattern_conflict_strength_delta=0.,chart_pattern_supporting_strength=.78,chart_pattern_conflicting_strength=.78)
        return result
    monkeypatch.setattr(module,"detect_chart_pattern_confirmation",pattern)
    data=_data()
    result=evaluate_m5_confirmation(data=data,setup=_setup(data),retest_index=2,confirmation_index=3,direction="long",config=M5ConfirmationConfig(require_fvg=False,require_chart_pattern=False))
    assert result["chart_pattern_conflict_blocked"]
    assert not result["confirmation_valid"]
