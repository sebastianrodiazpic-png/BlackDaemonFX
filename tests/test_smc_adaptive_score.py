import pytest
from strategy.smc.adaptive_score import calculate_adaptive_score
from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation
from strategy.execution.trade_pipeline import PipelineConfig
from strategy.smc.m15_setup import build_m15_setups


def score(source='PIVOT', quality='BOS', fvg=True, clean=True, volume=True, div=True):
    return calculate_adaptive_score({'is_valid_location':True,'source':source},
        {'break_quality':quality,'has_displacement':True},
        {'has_choch':True,'has_sweep':True,'has_fvg':fvg,'clean_retest':clean},
        {'volume_ok':volume,'exhaustion_or_div':div})


@pytest.mark.parametrize('kwargs,expected,status',[
    ({},100,'STRICT_APPROVED'),
    ({'fvg':False,'clean':False},85,'STRICT_APPROVED'),
    ({'source':'FALLBACK_24H','fvg':False,'clean':False,'div':False},70,'ADAPTIVE_APPROVED'),
    ({'source':'FALLBACK_24H','fvg':False,'clean':False,'div':False,'volume':False},65,'REJECTED_LOW_SCORE'),
    ({'source':'FALLBACK_24H','quality':'SWEEP'},80,'ADAPTIVE_APPROVED'),
    ({'quality':None},80,'ADAPTIVE_APPROVED'),
])
def test_boundaries_and_weights(kwargs,expected,status):
    r=score(**kwargs)
    assert r['final_score']==expected and r['status']==status
    assert sum(r['score_breakdown'].values())==expected


@pytest.mark.parametrize('missing',['location','invalidated','choch','sweep','m15','source'])
def test_vetos_cannot_be_compensated(missing):
    h={'is_valid_location':True,'source':'PIVOT'}
    m={'break_quality':'BOS'}
    five={'has_choch':True,'has_sweep':True,'has_fvg':True,'clean_retest':True}
    if missing=='location':h['is_valid_location']=False
    if missing=='source':h['source']=None
    if missing=='invalidated':m['is_invalidated']=True
    if missing=='m15':m={}
    if missing=='choch':five['has_choch']=False
    if missing=='sweep':five['has_sweep']=False
    r=calculate_adaptive_score(h,m,five,{'volume_ok':True,'exhaustion_or_div':True})
    assert not r['approved'] and r['status']=='REJECTED' and r['reasons']


def test_live_engine_approves_without_fvg_and_legacy_gates():
    from test_confirmation_engine import _data,_setup
    d=_data(); setup=_setup(d).to_dict()
    setup.update(h1_range_low=90.,h1_range_high=130.,h1_range_source='PIVOT',
                 m15_structure={'break_quality':'BOS'},m15_is_invalidated=False)
    d['choch_bullish']=False;d.loc[3,'choch_bullish']=True
    d['bullish_sweep']=False;d.loc[2,'bullish_sweep']=True
    cfg=M5ConfirmationConfig(adaptive_smc_score_enabled=True,require_fvg=True,
        require_chart_pattern=True,require_harmonic=True,minimum_trade_score=100,
        minimum_viable_trade_score=100,minimum_confirmation_ratio=1.)
    def evaluate():return evaluate_m5_confirmation(data=d,setup=setup,retest_index=2,
        confirmation_index=3,direction='long',config=cfg)
    r=evaluate()
    assert r['confirmation_valid'] and r['fvg_missing_but_allowed']
    assert r['trade_score']==r['adaptive_score']['final_score']
    assert not r['critical_confirmation_failures'] and not r['rejection_reasons']
    d.loc[2,'low']=97.
    r=evaluate()
    assert not r['clean_retest'] and r['confirmation_valid']
    assert r['trade_score'] >= 70
    d.loc[3,'choch_bullish']=False
    assert not evaluate()['confirmation_valid']
    d.loc[3,'choch_bullish']=True;setup['m15_is_invalidated']=True
    assert 'M15_OB_INVALIDATED' in evaluate()['critical_confirmation_failures']
    setup['m15_is_invalidated']=False;setup['h1_range_high']=105.
    assert 'H1_LOCATION_REQUIRED' in evaluate()['critical_confirmation_failures']


def test_displacement_only_ob_reaches_scoring():
    from test_m15_responsibilities import candles
    d=candles();d.loc[10,'high']=110.
    assert build_m15_setups(d,PipelineConfig())[0].empty
    setups,_=build_m15_setups(d,PipelineConfig(adaptive_smc_score_enabled=True))
    assert len(setups)==1 and setups.iloc[0].m15_has_displacement
    assert not setups.iloc[0].structure_break_ok
