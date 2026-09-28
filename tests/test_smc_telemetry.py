import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import pytest
from strategy.smc.telemetry_logger import SMCTelemetryTracker
from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation


def result(status='STRICT_APPROVED', score=90):
    return dict(status=status, final_score=score, approved=status.endswith('APPROVED'), reasons=[])


def test_states_stage_dedup_and_scores(tmp_path):
    t=SMCTelemetryTracker('TEST',output_dir=tmp_path,history_capacity=2)
    t.log_evaluation(result(), 'A','1')
    t.log_evaluation(result('ADAPTIVE_APPROVED',75),'A','2')
    veto=result('REJECTED',30)
    veto.update(reasons=['H1: fuera','H1: fuente','M5: falta'],veto_codes=['H1_LOCATION_REQUIRED','M5_CHOCH_SWEEP_REQUIRED'])
    t.log_evaluation(veto,'B','3')
    t.log_evaluation(result('REJECTED_LOW_SCORE',65),'B','4')
    assert not t.log_evaluation(veto,'B','3')
    r=t.get_summary_report()
    assert r['total_evaluations']==4 and r['approval_rate_pct']==50
    assert r['status_counts']['REJECTED_CRITICAL_VETO']==1
    assert r['stage_rejection_pct']['H1_location']==25
    assert r['average_score']==65 and len(t.scores_history)==2
    t.flush()
    assert json.loads(next(tmp_path.glob('*.json')).read_text())['total_evaluations']==4
    t.reset_counters()
    assert t.get_summary_report()['total_evaluations']==0


def test_workers_threads_and_every_100(monkeypatch):
    t=SMCTelemetryTracker('ONE'); other=SMCTelemetryTracker('TWO')
    reports=[]
    monkeypatch.setattr(t,'print_telemetry_dashboard',lambda: reports.append(t.total_evaluations))
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda i:t.log_evaluation(result(),'A',str(i%100)),range(200)))
    assert t.total_evaluations==100 and reports==[100]
    assert other.total_evaluations==0


def test_storage_error_does_not_stop_evaluation(tmp_path):
    blocked=tmp_path/'file';blocked.write_text('x')
    t=SMCTelemetryTracker(output_dir=blocked)
    assert t.log_evaluation(result(),'A')
    assert t.total_evaluations==1


def test_confirmation_integration_records_once_without_changing_decision(monkeypatch):
    from test_confirmation_engine import _data,_setup
    import strategy.smc.telemetry_logger as telemetry
    d=_data();s=_setup(d).to_dict()
    s.update(h1_range_low=90.,h1_range_high=130.,h1_range_source='PIVOT',m15_structure={'break_quality':'BOS'})
    d['choch_bullish']=False;d.loc[3,'choch_bullish']=True
    d['bullish_sweep']=False;d.loc[2,'bullish_sweep']=True
    tracker=SMCTelemetryTracker('WORKER')
    names=[]
    def get(name):names.append(name);return tracker
    monkeypatch.setattr(telemetry,'get_telemetry_tracker',get)
    cfg=M5ConfirmationConfig(adaptive_smc_score_enabled=True)
    args=dict(data=d,setup=s,retest_index=2,confirmation_index=3,direction='long')
    baseline=evaluate_m5_confirmation(**args,config=cfg)
    enabled=replace(cfg,telemetry_bot_name='WORKER',telemetry_symbol='TEST_INDEX')
    for _ in range(2):
        got=evaluate_m5_confirmation(**args,config=enabled)
        assert got['adaptive_score']==baseline['adaptive_score']
    assert tracker.total_evaluations==1 and names==['WORKER','WORKER']
    assert tracker.get_summary_report()['symbol_counts']=={'TEST_INDEX':1}
    def fail(*a,**k):raise OSError('disk')
    monkeypatch.setattr(tracker,'log_evaluation',fail)
    assert evaluate_m5_confirmation(**args,config=enabled)['confirmation_valid']==baseline['confirmation_valid']


def test_pipeline_passes_worker_and_symbol(monkeypatch):
    import pandas as pd
    import strategy.execution.trade_pipeline as pipeline
    from test_m15_responsibilities import candles
    captured={}
    def confirm(data,setups,**kwargs):
        captured['cfg']=kwargs['confirmation_config']
        return pd.DataFrame()
    monkeypatch.setattr(pipeline,'detect_entry_confirmations',confirm)
    pipeline.run_trade_pipeline(candles(),pipeline.PipelineConfig(
        telemetry_bot_name='VOLATILITY_2',adaptive_smc_score_enabled=True),symbol='Step Index')
    assert captured['cfg'].telemetry_bot_name=='VOLATILITY_2'
    assert captured['cfg'].telemetry_symbol=='Step Index'


def test_funnel_counts_early_exits_separately_and_deduplicates():
    t=SMCTelemetryTracker('FUNNEL')
    for action in ['NO_H1_CONTEXT','NO_M15_SETUP','NO_M5_CONFIRMATION','MULTI_TIMEFRAME_SIGNAL']:
        r=dict(symbol='A',action=action,reason=action,valid=action=='MULTI_TIMEFRAME_SIGNAL')
        assert t.log_pipeline_result(r,evaluation_id=action)
        assert not t.log_pipeline_result(r,evaluation_id=action)
    t.log_evaluation(result(),'A','score')
    rep=t.get_summary_report()
    assert rep['total_evaluations']==1
    assert rep['pipeline_funnel']['total']==4
    assert rep['pipeline_funnel']['stage_counts']=={'H1':1,'M15':1,'M5':1,'SIGNAL_READY':1}
    assert rep['pipeline_funnel']['stage_pct']['H1']==25
    assert rep['approval_breakdown']['strict_approved']==1
    assert sum(rep['pipeline_funnel']['stage_counts'].values())==4


def test_analyzer_terminal_hook_and_h1_detail(monkeypatch):
    import strategy.smc.telemetry_logger as telemetry
    from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer
    from strategy.execution.trade_pipeline import PipelineConfig
    t=SMCTelemetryTracker('WORKER')
    monkeypatch.setattr(telemetry,'get_telemetry_tracker',lambda name:t)
    a=MultiTimeframeAnalyzer(None,pipeline_config=PipelineConfig(telemetry_bot_name='WORKER'))
    kwargs=dict(symbol='A',valid=False,action='NO_H1_CONTEXT',state='NO_H1_CONTEXT',
        direction=None,reason='H1_LOCATION_UNAVAILABLE_OR_EQUILIBRIUM',transitions=[],policy_diag={},
        h1={'context':{'location_detail':'H1_PRICE_OUTSIDE_RANGE'}})
    r=a._build_result(**kwargs)
    assert t.get_summary_report()['pipeline_funnel']['top_3_rejection_reasons']==[('H1_PRICE_OUTSIDE_RANGE',1)]
    def fail(*args,**kwargs):raise OSError('disk')
    monkeypatch.setattr(t,'log_pipeline_result',fail)
    assert a._build_result(**kwargs)==r


def test_funnel_report_every_100_and_reset(monkeypatch):
    t=SMCTelemetryTracker('FUNNEL')
    reports=[]
    monkeypatch.setattr(t,'print_telemetry_dashboard',lambda:reports.append(t.funnel_total))
    for i in range(100):
        t.log_pipeline_result(dict(symbol='A',valid=False,action='NO_M15_SETUP',reason='NO_DIRECTIONAL_M15_SETUP'),str(i))
    assert reports==[100]
    t.reset_counters()
    assert t.get_summary_report()['pipeline_funnel']['total']==0
