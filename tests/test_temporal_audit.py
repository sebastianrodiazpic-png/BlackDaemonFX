import pandas as pd
from strategy.smc.structural_validation import get_h1_structural_range_flexible
from strategy.smc.candidate_evaluator import evaluate_h1_context
from strategy.smc.dual_trigger import evaluate_dual_m5_m1_trigger

def test_pivot_confirmation_age_is_causal():
    df=pd.DataFrame(dict(time=pd.date_range('2026-09-01',periods=9,freq='h',tz='UTC'),
        high=[10,11,12,15,12,11,12,11,10],low=[8,7,6,7,5,7,8,7,6],close=[9]*9))
    r=get_h1_structural_range_flexible(df,left=1,right=1)
    t=r['temporal_audit']
    assert t['high_confirmed_at']=='2026-09-01T08:00:00+00:00'
    assert t['high_age_hours']==1
    assert evaluate_h1_context(r,9,'BUY')['temporal_audit']==t

def test_gap_is_diagnostic_not_new_veto():
    result=evaluate_dual_m5_m1_trigger({'has_sweep':True,'sweep_timestamp':'2026-09-01T10:00Z'},
        {'has_choch':True,'choch_timestamp':'2026-09-01T11:26Z'},current_time=pd.Timestamp('2026-09-01T11:27Z'))
    assert result['approved']
    assert result['sweep_to_choch_minutes']==86
