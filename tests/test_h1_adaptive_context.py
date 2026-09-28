import pytest
from strategy.smc.h1_adaptive_context import evaluate_h1_adaptive_context, h1_ob_location_valid
from strategy.smc.entry_location import evaluate_entry_location


@pytest.mark.parametrize('price,mode,direction,valid',[
 (90,'EXPANSION_SELL','SELL',True),(110,'RANGE_DISCOUNT','BUY',True),
 (150,'EQUILIBRIUM',None,False),(190,'RANGE_PREMIUM','SELL',True),
 (210,'EXPANSION_BUY','BUY',True)])
def test_regimes(price,mode,direction,valid):
 r=evaluate_h1_adaptive_context(None,price,{'swing_high':200,'swing_low':100,'equilibrium':150})
 assert (r['context_type'],r['direction'],r['is_valid_location'])==(mode,direction,valid)


@pytest.mark.parametrize('side,mode,price,failed',[('BUY','EXPANSION_BUY',199.6,199.59),('SELL','EXPANSION_SELL',100.2,100.21)])
def test_retest_band_shared_by_ob_and_presend(side,mode,price,failed):
 bounds=dict(high=200,low=100,adaptive_context_enabled=True,active_context_type=mode)
 assert h1_ob_location_valid(price,side,bounds)
 assert evaluate_entry_location(side,price,{'H1':bounds},'H1_PRIMARY')['valid']
 assert not evaluate_entry_location(side,failed,{'H1':bounds},'H1_PRIMARY')['valid']
 assert not h1_ob_location_valid(failed,side,bounds)
 opposite='SELL' if side=='BUY' else 'BUY'
 assert not evaluate_entry_location(opposite,price,{'H1':bounds},'H1_PRIMARY')['valid']


def test_invalid_and_fallback():
 assert not evaluate_h1_adaptive_context(None,120,None)['is_valid_location']
 assert not evaluate_h1_adaptive_context(None,float('nan'),dict(high=200,low=100))['is_valid_location']
 assert evaluate_h1_adaptive_context(None,210,dict(high=200,low=100,fallback_used=True))['source']=='FALLBACK_24H'
 assert not evaluate_entry_location('BUY',210,{'H1':dict(high=200,low=100)},'H1_PRIMARY')['valid']


def test_score_accepts_expansion_and_rejects_failed_retest():
 from test_confirmation_engine import _data,_setup
 from strategy.smc.confirmation_engine import M5ConfirmationConfig,evaluate_m5_confirmation
 d=_data();s=_setup(d).to_dict()
 s.update(h1_range_low=90.,h1_range_high=102.,h1_range_source='PIVOT',
  h1_context_type='EXPANSION_BUY',h1_adaptive_bounds=dict(low=90.,high=102.,adaptive_context_enabled=True,active_context_type='EXPANSION_BUY'),
  m15_structure={'break_quality':'BOS'})
 d['choch_bullish']=False;d.loc[3,'choch_bullish']=True
 d['bullish_sweep']=False;d.loc[2,'bullish_sweep']=True
 def evaluate():return evaluate_m5_confirmation(data=d,setup=s,retest_index=2,confirmation_index=3,
    direction='long',config=M5ConfirmationConfig(adaptive_smc_score_enabled=True))
 assert evaluate()['confirmation_valid']
 s['h1_adaptive_bounds']['high']=110.
 assert 'H1_LOCATION_REQUIRED' in evaluate()['critical_confirmation_failures']
