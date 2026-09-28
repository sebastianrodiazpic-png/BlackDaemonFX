import pandas as pd
import pytest
from strategy.smc.structural_validation import (get_h1_structural_range_flexible,
    validate_m15_ob_flexible, validate_m5_fvg_decoupled)
from strategy.smc.m15_setup import build_m15_setups
from strategy.execution.trade_pipeline import PipelineConfig


def test_h1_confirms_with_one_closed_right_bar():
    d=pd.DataFrame({'high':[11.,12,13,20,14,13], 'low':[8.,7,6,5,2,4]})
    assert get_h1_structural_range_flexible(d.iloc[:5]) is None
    r=get_h1_structural_range_flexible(d)
    assert r['high']==20 and r['low']==2 and not r['fallback_used']
    assert r['right']==1


def test_h1_fallback_uses_exactly_24_closed_bars():
    d=pd.DataFrame({'high':[999.]+[20.]*24, 'low':[0.]+[10.]*24})
    r=get_h1_structural_range_flexible(d)
    assert r['fallback_used'] and r['high']==20 and r['low']==10
    assert get_h1_structural_range_flexible(d.tail(23)) is None
    d.loc[24,'high']=float('nan')
    assert get_h1_structural_range_flexible(d) is None


@pytest.mark.parametrize('sell',[False,True])
def test_m15_wick_body_and_eighth_bar_causality(sell):
    d=pd.DataFrame({'open':[9.]*25,'high':[10.]*25,'low':[8.]*25,'close':[9.]*25})
    d.loc[24,'high']=12
    if sell:
        old=d.copy()
        for a,b in [('open','open'),('close','close'),('high','low'),('low','high')]: d[a]=30-old[b]
    side='SELL' if sell else 'BUY'
    assert not validate_m15_ob_flexible(d.iloc[:24],16,side)['has_structure_break']
    r=validate_m15_ob_flexible(d,16,side)
    assert r['break_quality']=='SWEEP' and r['break_index']==24
    assert not validate_m15_ob_flexible(d,15,side)['has_structure_break']
    d.loc[24,'close']=19 if sell else 11
    assert validate_m15_ob_flexible(d,16,side)['break_quality']=='BOS'


def test_live_m15_builder_accepts_wick_only_reference_break():
    from test_m15_responsibilities import candles
    d=candles(); d.loc[10,'high']=105.8
    setups,audit=build_m15_setups(d,PipelineConfig())
    assert len(setups)==1
    assert setups.iloc[0].m15_structure['break_quality']=='SWEEP'
    assert build_m15_setups(d,PipelineConfig(m15_flexible_structure=False))[0].empty


@pytest.mark.parametrize('sell',[False,True])
def test_fvg_extended_window_requires_closed_third_candle(sell):
    d=pd.DataFrame({'high':[10.]*7,'low':[8.]*7})
    d.loc[6,['high','low']]=[14,12]
    if sell:d=pd.DataFrame({'high':30-d.low,'low':30-d.high})
    side='SELL' if sell else 'BUY'
    assert not validate_m5_fvg_decoupled(d,3,side,confirmation_index=5)['has_fvg']
    assert validate_m5_fvg_decoupled(d,3,side,confirmation_index=6)['has_fvg']
    assert not validate_m5_fvg_decoupled(d,2,side,confirmation_index=6)['has_fvg']
    assert not validate_m5_fvg_decoupled(d,7,side,confirmation_index=6)['has_fvg']
