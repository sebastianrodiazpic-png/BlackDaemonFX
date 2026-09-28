import copy
from types import SimpleNamespace
from unittest.mock import Mock
import pandas as pd
import pytest
from brokers.mt5_execution import MT5ExecutionProvider, MT5ExecutionError
from reporting.target_audit import target_changes, exit_target_evidence
from strategy.orb.new_york_orb import NewYorkORBStrategy
from strategy.ai.feature_extraction import extract_meta_features, FEATURE_NAMES
from strategy.ai.training import build_training_dataset
from strategy.ai.continuous_audit import refresh
from test_continuous_learning_audit import trade


@pytest.mark.parametrize('side,price,stop,target,minimum,allowed', [
    ('BUY', 100, 90, 110, 1, True),
    ('BUY', 105, 90, 110, 1, False),
    ('SELL', 100, 110, 80, 2, True),
    ('SELL', 95, 110, 80, 2, False),
    ('BUY', 90, 90, 110, 1, False),
    ('BUY', 100, 90, 110, float('nan'), False),
])
def test_executable_rr_preserves_fixed_targets(side, price, stop, target, minimum, allowed):
    request={'price':price, 'sl':stop, 'tp':target}
    original=dict(request)
    if allowed:
        assert MT5ExecutionProvider._validate_executable_rr(request,side,minimum)['executable_rr']>=minimum
    else:
        with pytest.raises(MT5ExecutionError,match='PRE_SEND_RR_BLOCKED'):
            MT5ExecutionProvider._validate_executable_rr(request,side,minimum)
    assert request==original


def test_volume_absence_and_future_data_are_not_confirmation():
    times=pd.date_range('2026-09-24',periods=4,freq='5min',tz='UTC')
    df=pd.DataFrame({'time':times})
    assert NewYorkORBStrategy._breakout_volume_confirmed(df,times[2])==(None,None,None)
    df['tick_volume']=[0,0,0,200]
    assert NewYorkORBStrategy._breakout_volume_confirmed(df,times[2])==(None,None,None)
    df['tick_volume']=[100,100,150,20000]
    assert NewYorkORBStrategy._breakout_volume_confirmed(df,times[2])==(True,150.,100.)
    absent=extract_meta_features(signal={})
    zero=extract_meta_features(signal={'breakout_volume_ratio':0.0})
    assert absent['breakout_volume_available']==0
    assert zero['breakout_volume_available']==1


def test_target_evidence_does_not_invent_change_author():
    row={'stop_loss':90.,'take_profit':110.}
    assert target_changes(row,dict(row))=={}
    e=exit_target_evidence(row,'TP','[tp 115.00]')
    assert e['requires_review'] and e['actor']=='UNKNOWN'
    assert e['changed_at'] is None
    assert exit_target_evidence(row,'TP','[tp 110.00]')['status']=='MATCH'
    assert exit_target_evidence(row,'SL','manual')['status']=='UNAVAILABLE'


def test_mismatch_in_second_leg_excludes_whole_setup():
    rows=[trade(0),trade(1)]
    for row in rows: row['details']['metadata']['parent_execution_key']='one'
    rows[1]['details']['metadata']['target_reconciliation']={'requires_review':True}
    assert build_training_dataset(rows)['rows']==0


def test_external_observation_has_own_report_scope(tmp_path):
    row=trade(0)
    row.update(source='MT5_EXTERNAL',exit_price=112.)
    row['details']['metadata']={'observation_worker':'BOOM', 'mt5_observation':{
        'risk_distance':10., 'observed_price':100.,'direction':'BUY',
        'evaluated_at':'2026-09-01T00:05:00Z',
        'features':{n:0.25 for n in FEATURE_NAMES},'feature_names':list(FEATURE_NAMES)}}
    report=refresh([row],'BOOM','MT5_EXTERNAL',root=tmp_path)
    assert report['worker']=='EXTERNAL'
    assert report['scopes']['worker']['execution_rows']==1
    assert report['strategies']['MT5_OBSERVATION']['eligible_closed_setups']==1
    assert not report['training_funnel']['promotion_allowed']
    assert (tmp_path/'MT5_EXTERNAL_EXTERNAL.json').exists()


def test_repository_records_target_changes_atomically(tmp_path):
    from database.repository import TradingRepository
    repo=TradingRepository(tmp_path/'audit.sqlite3')
    ident,_=repo.create_trade_once({'source':'DEMO','instrument':'TEST','direction':'BUY',
        'status':'OPEN','execution_key':'quality-target','entry_price':100.,'stop_loss':90.,'take_profit':110.})
    repo.update_trade(ident,{'take_profit':115.,'target_change_source':'MT5_POSITION_SNAPSHOT'})
    repo.update_trade(ident,{'take_profit':115.})
    events=repo.audit_events_dataframe(source='DEMO')
    changes=events[events.event_type=='TRADE_TARGET_CHANGE']
    assert len(changes)==1
    assert repo.get_trade(ident)['take_profit']==115.


def test_final_quote_rr_prevents_order_send():
    from test_pre_send_risk_guard import provider
    p=provider()
    req={'symbol':'US500','price':100.,'sl':90.,'tp':110.,'volume':1.,'deviation':20,'type_filling':0}
    p._ensure=lambda:None
    p._build_market_request_base=lambda **kw:dict(req)
    p._run_order_check_with_fallback=lambda *a:{'valid':True,'request':dict(req)}
    prices=iter([100.,105.]);p._current_market_price=lambda *a:next(prices)
    p._order_check_safe=lambda r:(SimpleNamespace(retcode=0),r,{})
    p._is_order_check_success=lambda r:True
    p._order_send_safe=Mock(side_effect=AssertionError('Must not send poor RR'))
    with pytest.raises(MT5ExecutionError,match='PRE_SEND_RR_BLOCKED'):
        p.place_market_order('US500','BUY',1.,90.,110.,1,'test',minimum_executable_rr=1.)
    p._order_send_safe.assert_not_called()


def test_snapshot_cannot_capture_after_execution():
    row=trade(0)
    snapshot=row['details']['metadata']['entry_learning_snapshot']
    snapshot.update(schema='entry-learning-v4',captured_at='2026-09-01T00:01:00Z')
    assert build_training_dataset([row])['rows']==0
    snapshot['captured_at']='2026-09-01T00:00:00Z'
    assert build_training_dataset([row])['rows']==1


def test_open_position_reconciliation_is_idempotent(tmp_path):
    from database.repository import TradingRepository
    repo=TradingRepository(tmp_path/'sync.sqlite3')
    ident,_=repo.create_trade_once({'source':'DEMO','instrument':'TEST','direction':'BUY',
        'status':'OPEN','execution_key':'quality-sync','broker_position_ticket':'123',
        'entry_price':100.,'stop_loss':90.,'take_profit':110.})
    executor=SimpleNamespace(get_position=lambda ticket:SimpleNamespace(sl=92.,tp=115.))
    assert repo.sync_closed_mt5_trades(executor,source='DEMO')==0
    assert repo.sync_closed_mt5_trades(executor,source='DEMO')==0
    row=repo.get_trade(ident)
    assert row['stop_loss']==92. and row['take_profit']==115. and row['status']=='OPEN'
    events=repo.audit_events_dataframe(source='DEMO')
    assert len(events[events.event_type=='TRADE_TARGET_CHANGE'])==1


@pytest.mark.parametrize('rejection', ['exception','result'])
def test_orb_second_leg_rejection_preserves_first(rejection):
    from test_demo_daemon_integration import ExecutionRepo, Provider, Executor, FakeLifecycleManager
    from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
    from datetime import datetime,timezone
    class Manager(FakeLifecycleManager):
        def __init__(self): self.calls=0; self.close_execution=Mock(side_effect=AssertionError('No early close'))
        def execute_with_executor(self,lifecycle,volume):
            self.calls+=1
            assert lifecycle.metadata['minimum_executable_rr'] > 0
            if self.calls==2:
                if rejection=='exception': raise MT5ExecutionError('PRE_SEND_RR_BLOCKED: test')
                lifecycle.execution_status='REJECTED'
                lifecycle.metadata['execution_reason']='BROKER_REJECTED'
                return lifecycle
            return super().execute_with_executor(lifecycle,volume)
    repo=ExecutionRepo(); manager=Manager()
    engine=LiveTradingEngine(provider=Provider(),repository=repo,executor=Executor(),
        lifecycle_manager=manager,config=LiveTradingConfig(bot_profile='ORB',execution_enabled=True,max_entry_drift_r=None))
    now=datetime.now(timezone.utc).isoformat()
    signal={'strategy_name':'ORB_NEW_YORK','direction':'BUY','entry_time':now,
        'entry_price':101.,'stop_loss':95.,'risk_reward_ratio':2.,
        'orb_session_date':now[:10],'breakout_candle_time':now}
    mark=Mock()
    engine.orb_strategy=SimpleNamespace(config=SimpleNamespace(one_signal_per_session=False),analyze_symbol=lambda *a,**k:{'valid':True,'strategy_name':'ORB_NEW_YORK','signal':signal},mark_signal_used=mark)
    engine._enrich_learning_indicators=Mock()
    result=engine.process_symbol('US500')
    assert result['action'] in ('EXECUTABLE_RR_BLOCKED','EXECUTION_REJECTED'),result
    assert result['partial_execution'] is True
    assert len(result['opened_legs'])==1
    assert len(repo.rows)==1 and mark.called
    manager.close_execution.assert_not_called()


def test_idle_audit_sampling_keeps_heartbeat_and_state_changes(monkeypatch):
    from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='STEP')
    engine.repository=SimpleNamespace(upsert_worker_runtime_state=Mock(),save_audit_event=Mock(return_value=1))
    clock=[1.]
    monkeypatch.setattr('strategy.execution.live_trading_engine.time.monotonic',lambda:clock[0])
    payload={'symbols_count':0,'selected_symbols_count':3,'runtime_state':'WAITING_NEW_M5_BAR'}
    engine._persist_audit_event('DAEMON_CYCLE_START',payload=payload)
    clock[0]=20
    engine._persist_audit_event('DAEMON_CYCLE_START',payload=payload)
    assert engine.repository.save_audit_event.call_count==1
    assert engine.repository.upsert_worker_runtime_state.call_count==2
    clock[0]=21
    engine._persist_audit_event('DAEMON_CYCLE_START',payload={**payload,'runtime_state':'OUTSIDE_SESSION'})
    assert engine.repository.save_audit_event.call_count==2
    clock[0]=85
    engine._persist_audit_event('DAEMON_CYCLE_START',payload={**payload,'runtime_state':'OUTSIDE_SESSION'})
    assert engine.repository.save_audit_event.call_count==3
