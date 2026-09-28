import pytest
from dataclasses import replace
from strategy.smc.m5_freshness import validate_m5_signal_freshness, evaluate_m5_confirmation_detailed
from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation


@pytest.mark.parametrize('stamp,fresh,code',[
 ('2026-09-26T12:00:00Z',True,None),
 ('2026-09-26 12:00:00',True,None),
 ('2026-09-26T09:00:00-03:00',True,None),
 ('2026-09-26T11:59:59Z',False,'M5_SIGNAL_EXPIRED'),
 ('2026-09-26T12:11:00Z',False,'M5_CHOCH_TIME_IN_FUTURE'),
 ('invalid',False,'M5_CHOCH_TIMESTAMP_INVALID'),
 (None,False,'M5_CHOCH_TIMESTAMP_INVALID'),
])
def test_time_boundaries(stamp,fresh,code):
 r=validate_m5_signal_freshness(stamp,current_time='2026-09-26T12:10Z')
 assert r['is_fresh']==fresh and r['code']==code


@pytest.mark.parametrize('choch,sweep,code',[
 (False,False,'M5_CHOCH_AND_SWEEP_MISSING'),
 (False,True,'M5_CHOCH_MISSING'),
 (True,False,'M5_SWEEP_MISSING'),
 (True,True,None)])
def test_disaggregated_evidence(choch,sweep,code):
 r=evaluate_m5_confirmation_detailed(dict(has_choch=choch,has_sweep=sweep,
  choch_timestamp='2026-09-26T12:00Z',has_fvg=True,clean_retest=True),'2026-09-26T12:05Z')
 assert r['veto_codes']==([code] if code else [])
 assert r['m5_score']==(15 if code else 35)


def test_expiry_short_circuits_bonus_and_evidence():
 r=evaluate_m5_confirmation_detailed(dict(has_choch=True,has_sweep=True,
  choch_timestamp='2026-09-26T12:00Z',has_fvg=True,clean_retest=True),'2026-09-26T12:11Z')
 assert r['latency_rejected'] and r['m5_score']==0
 assert r['veto_codes']==['M5_SIGNAL_EXPIRED']


def test_engine_live_clock_and_historical_clock(monkeypatch):
 from test_confirmation_engine import _data,_setup
 import strategy.smc.telemetry_logger as telemetry
 d=_data();s=_setup(d).to_dict()
 s.update(h1_range_low=90.,h1_range_high=130.,h1_range_source='PIVOT',m15_structure={'break_quality':'BOS'})
 d['choch_bullish']=False;d.loc[3,'choch_bullish']=True
 d['bullish_sweep']=False;d.loc[2,'bullish_sweep']=True
 tracker=telemetry.SMCTelemetryTracker('CLOCK')
 monkeypatch.setattr(telemetry,'get_telemetry_tracker',lambda name:tracker)
 cfg=M5ConfirmationConfig(adaptive_smc_score_enabled=True,telemetry_bot_name='CLOCK')
 args=dict(data=d,setup=s,retest_index=2,confirmation_index=3,direction='long')
 historical=evaluate_m5_confirmation(**args,config=cfg)
 assert historical['confirmation_valid']
 at_limit=evaluate_m5_confirmation(**args,config=replace(cfg,m5_evaluation_time='2026-01-01T00:25:00Z'))
 assert at_limit['confirmation_valid']
 expired=evaluate_m5_confirmation(**args,config=replace(cfg,m5_evaluation_time='2026-01-01T00:25:01Z'))
 assert not expired['confirmation_valid']
 assert expired['adaptive_score']['score_breakdown']['m5']==0
 assert expired['m5_detailed_confirmation']['latency_rejected']
 assert tracker.get_summary_report()['m5_rejection_codes']=={'M5_SIGNAL_EXPIRED':1}
