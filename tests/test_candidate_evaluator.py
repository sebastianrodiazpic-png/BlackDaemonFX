import pytest
from strategy.smc.candidate_evaluator import evaluate_candidate_signal, evaluate_h1_context


def evaluate(side='BUY',price=210,source='PIVOT',age='2026-09-26T12:05Z',**m5):
    return evaluate_candidate_signal(side,price,dict(high=200,low=100,source=source),
      dict(break_quality='BOS'),dict(has_choch=True,has_sweep=True,has_fvg=True,
      clean_retest=True,choch_timestamp='2026-09-26T12:00Z',**m5),
      current_time=age)


@pytest.mark.parametrize('side,price,mode',[('BUY',210,'EXPANSION_BUY'),('SELL',90,'EXPANSION_SELL'),
 ('BUY',120,'RANGE_DISCOUNT'),('SELL',180,'RANGE_PREMIUM')])
def test_unified_context_and_score(side,price,mode):
    r=evaluate(side,price)
    assert r['status']=='STRICT_APPROVED' and r['final_score']==90
    assert r['h1_context']['context_type']==mode
    assert r['m5_detail']['freshness']['elapsed_minutes']==5


def test_fallback_preserves_adaptive_mode_and_countertrend_veto():
    r=evaluate(source='FALLBACK_24H')
    assert r['status']=='ADAPTIVE_APPROVED' and r['final_score']==80
    r=evaluate('SELL',210)
    assert not r['approved'] and 'H1_LOCATION_REQUIRED' in r['veto_codes']
    assert not evaluate_h1_context(dict(high=200,low=100),150,'BUY')['valid']


def test_expired_cannot_be_saved_by_expansion():
    r=evaluate(age='2026-09-26T12:11Z')
    assert r['veto_codes']==['M5_SIGNAL_EXPIRED']
    assert r['score_breakdown']['m5']==0 and not r['approved']


def test_telemetry_has_regime_and_freshness():
    from strategy.smc.telemetry_logger import SMCTelemetryTracker
    t=SMCTelemetryTracker('UNIFIED')
    t.log_evaluation(evaluate(),'A')
    report=t.get_summary_report()
    assert report['h1_context_counts']=={'EXPANSION_BUY':1}
    assert report['last_evaluation']['m5_detail']['freshness']['is_fresh']
