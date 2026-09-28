import pandas as pd
import pytest
from strategy.smc.candidate_evaluator import evaluate_m5_details_v2
from strategy.smc.m5_reclassification import detect_m5_reclassification


def test_native_bos_wick_and_missing():
 base=dict(has_sweep=True,has_choch=False,has_fvg=True,clean_retest=True)
 now='2026-09-27T12:05Z';stamp='2026-09-27T12:00Z'
 cases=[({'has_choch':True,'choch_timestamp':stamp},35,'STANDARD_CHOCH_SWEEP'),
 ({'has_bos_direction_flip':True,'bos_timestamp':stamp},30,'RECLASSIFIED_BOS_TO_CHOCH'),
 ({'has_wick_break_with_fvg':True,'wick_break_timestamp':stamp},30,'VALIDATED_WICK_CHOCH_WITH_FVG'),
 ({},15,'TRUE_MISSING_CHOCH')]
 for extra,score,tag in cases:
  r=evaluate_m5_details_v2(dict(base,**extra),current_time=now)
  assert r['score']==score and r['diagnostic_tag']==tag
  assert r['approved']==(tag!='TRUE_MISSING_CHOCH')


def test_reclassification_cannot_skip_time_sweep_or_fvg():
 base=dict(has_sweep=True,has_bos_direction_flip=True,bos_timestamp='2026-09-27T12:00Z')
 r=evaluate_m5_details_v2(base,current_time='2026-09-27T12:11Z')
 assert r['diagnostic_tag']=='EXPIRED_SIGNAL' and r['score']==0
 assert not evaluate_m5_details_v2(dict(base,bos_timestamp=None),current_time='2026-09-27T12:05Z')['approved']
 assert not evaluate_m5_details_v2(dict(base,has_sweep=False),current_time='2026-09-27T12:05Z')['approved']
 assert not evaluate_m5_details_v2(dict(has_sweep=True,has_wick_break_with_fvg=True,has_fvg=False),current_time='2026-09-27T12:05Z')['approved']


def candles(bos=False,sell=False):
 d=pd.DataFrame({'time':pd.date_range('2026-09-27T12:00Z',periods=10,freq='5min'),
 'open':10.,'high':12.,'low':9.,'close':10.,'bullish_sweep':False,'bos_bullish':False})
 d.loc[2,'high']=15
 d.loc[6,['low','close','bullish_sweep']]=[7,8,True]
 d.loc[8,['high','low','close']]=[17 if bos else 16,11,16 if bos else 14]
 d.loc[9,['high','low','close']]=[15,13,14]
 d['structure_break_level']=float('nan')
 if bos:d.loc[8,['bos_bullish','structure_break_level']]=[True,15]
 if sell:
  old=d.copy()
  for a,b in [('open','open'),('close','close'),('high','low'),('low','high')]:d[a]=40-old[b]
  d['structure_break_level']=40-old.structure_break_level
  d['bearish_sweep']=old.bullish_sweep;d['bos_bearish']=old.bos_bullish
 return d


@pytest.mark.parametrize('bos',[False,True])
@pytest.mark.parametrize('sell',[False,True])
def test_evidence_causal_symmetric(bos,sell):
 d=candles(bos,sell);side='short' if sell else 'long'
 before=detect_m5_reclassification(d,side,d.time.iloc[4],7)
 assert before['bos_index'] is None and before['wick_index'] is None
 r=detect_m5_reclassification(d,side,d.time.iloc[4],9)
 assert r['bos_index' if bos else 'wick_index']==8
 d.loc[6,'bearish_sweep' if sell else 'bullish_sweep']=False
 r=detect_m5_reclassification(d,side,d.time.iloc[4],9)
 assert r['bos_index'] is None and r['wick_index'] is None


@pytest.mark.parametrize('bos',[False,True])
def test_engine_uses_real_reclassification_and_fvg(bos):
 from strategy.smc.confirmation_engine import evaluate_m5_confirmation,M5ConfirmationConfig
 d=candles(bos)
 setup=dict(setup_time=d.time.iloc[4],ob_low=7.,ob_high=12.,h1_range_low=0.,
 h1_range_high=40.,h1_range_source='PIVOT',m15_structure={'break_quality':'BOS'})
 r=evaluate_m5_confirmation(data=d,setup=setup,retest_index=6,confirmation_index=9,
 direction='long',config=M5ConfirmationConfig(adaptive_smc_score_enabled=True))
 assert r['confirmation_valid']
 assert r['m5_detailed_confirmation']['diagnostic_tag']==('RECLASSIFIED_BOS_TO_CHOCH' if bos else 'VALIDATED_WICK_CHOCH_WITH_FVG')
 assert r['m5_detailed_confirmation']['m5_score']<=30
 assert r['m5_detailed_confirmation']['freshness']['elapsed_minutes']==10
