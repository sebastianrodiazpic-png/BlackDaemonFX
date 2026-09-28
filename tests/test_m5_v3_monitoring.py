import json
import pytest
from tools.analyze_smc_telemetry import process_worker_logs
from strategy.smc.candidate_evaluator import evaluate_m5_details_v3


@pytest.mark.parametrize('choch,sweep,tag',[(True,True,'STANDARD_CHOCH_SWEEP'),
 (False,True,'TRUE_MISSING_CHOCH'),(True,False,'MISSING_SWEEP_ONLY'),
 (False,False,'MISSING_BOTH_CHOCH_AND_SWEEP')])
def test_v3_tags(choch,sweep,tag):
 r=evaluate_m5_details_v3(dict(has_choch=choch,has_sweep=sweep,
 choch_timestamp='2026-09-27T12:00Z'),current_time='2026-09-27T12:05Z')
 assert r['diagnostic_tag']==tag
 assert r['score']==(20 if choch and sweep else 0)


def test_latest_snapshots_not_file_count(tmp_path):
 def snapshot(worker,start,total):return dict(bot_name=worker,start_time=start,timestamp=start,
  total_evaluations=total,status_counts={'REJECTED_CRITICAL_VETO':total},
  m5_diagnostic_tags={'TRUE_MISSING_CHOCH':total},telemetry_schema_version=3,
  veto_reason_counts={'M5: falta':total})
 for name,r in [('old',snapshot('BOOM','2026-09-26',100)),('new',snapshot('BOOM','2026-09-27',7)),
                ('other',snapshot('CRASH','2026-09-27',3))]:
  (tmp_path/(name+'.json')).write_text(json.dumps(r))
 (tmp_path/'event.json').write_text(json.dumps({'status':'STRICT_APPROVED'}))
 (tmp_path/'bad.json').write_text('{bad')
 r=process_worker_logs(tmp_path,emit=False)
 assert r['total_evaluations']==10 and r['diagnostic_tags']['TRUE_MISSING_CHOCH']==10
 assert r['top_rejection_reasons']==[('M5: falta',10)] and len(r['errors'])==1
 assert len(r['missing_workers'])==6
 events=process_worker_logs(tmp_path,'events',emit=False)
 assert events['total_evaluations']==1


def test_empty_and_legacy_reports(tmp_path):
 assert process_worker_logs(tmp_path,emit=False)['total_evaluations']==0
 (tmp_path/'old.json').write_text(json.dumps(dict(bot_name='STEP',start_time='2026',
 total_evaluations=5,status_counts={'ADAPTIVE_APPROVED':5},top_3_rejection_reasons=[])))
 r=process_worker_logs(tmp_path,emit=False)
 assert r['total_evaluations']==5 and r['limitations']


def test_first_cycle_empty_is_not_reported():
 from strategy.execution.live_trading_engine import LiveTradingEngine
 engine=LiveTradingEngine.__new__(LiveTradingEngine)
 engine._report_first_m5_cycle([])
 assert not getattr(engine,'_m5_first_cycle_reported',False)


def test_first_nonempty_cycle_generates_report_once(tmp_path,monkeypatch):
 from types import SimpleNamespace
 import strategy.execution.live_trading_engine as live
 import strategy.smc.telemetry_logger as telemetry
 monkeypatch.setattr(live,'__file__',str(tmp_path/'strategy/execution/live_trading_engine.py'))
 tracker=telemetry.SMCTelemetryTracker('BOOM',output_dir=tmp_path/'storage/runtime/smc_telemetry')
 tracker.log_pipeline_result(dict(symbol='A',action='NO_M5_CONFIRMATION',valid=False,reason='TEST'))
 monkeypatch.setattr(telemetry,'get_telemetry_tracker',lambda name:tracker)
 engine=live.LiveTradingEngine.__new__(live.LiveTradingEngine)
 engine.pipeline_config=SimpleNamespace(telemetry_bot_name='BOOM')
 engine._report_first_m5_cycle([{'symbol':'A'}])
 files=list((tmp_path/'storage/analysis/m5_detector').glob('*first_cycle.json'))
 assert len(files)==1 and engine._m5_first_cycle_reported
 report=json.loads(files[0].read_text())
 assert report['trigger']['worker']=='BOOM' and 'BOOM' in report['workers']
 before=files[0].read_bytes()
 engine._report_first_m5_cycle([{'symbol':'A'}])
 assert files[0].read_bytes()==before
