import copy
from datetime import timedelta
from pathlib import Path
import pytest
from test_forex_spread_execution import START, quote
from strategy.execution.forex_spread_guard import ForexSpreadGuard, snapshot
from dashboard.smc_trial import record, _STATE
from strategy.ai.continuous_audit import refresh
from test_continuous_learning_audit import trade


def test_spread_retries_transient_replace(tmp_path, monkeypatch):
    guard=ForexSpreadGuard('FOREX_1',tmp_path)
    original=Path.replace; calls=[]
    def replace(path,target):
        if target==guard.path:
            calls.append(1)
            if len(calls)<3: raise PermissionError('busy')
        return original(path,target)
    monkeypatch.setattr(Path,'replace',replace)
    guard.observe('GBPCAD',quote(START),START)
    assert len(calls)==3
    assert snapshot(tmp_path)[0]['persistence']['status']=='OK'


def test_failed_persistence_preserves_last_good_file_and_gate(tmp_path,monkeypatch):
    guard=ForexSpreadGuard('FOREX_1',tmp_path)
    guard.observe('GBPCAD',quote(START),START); previous=guard.path.read_bytes()
    original=Path.replace
    def replace(path,target):
        if target==guard.path: raise PermissionError('busy')
        return original(path,target)
    monkeypatch.setattr(Path,'replace',replace)
    with pytest.raises(PermissionError):
        guard.check('GBPCAD',quote(START),'BUY',1.86,now=START)
    assert guard.path.read_bytes()==previous
    assert snapshot(tmp_path)[0]['persistence']['status']=='DEGRADED'


def test_blocks_only_emit_changes_across_restart(tmp_path):
    block=dict(ob_time='2026-09-23T12:00Z',setup_time='2026-09-23T12:30Z',
               direction='BUY',ob_low=1,ob_high=2,zone='discount',accepted=True,reasons=[])
    row=dict(strategy_name='SMC',symbol='TEST',action='NO_M5_CONFIRMATION',m15_block_audit=[block])
    first=record('STEP',row,'H1','ATR',tmp_path,START)
    assert len(first['m15_block_audit'])==1
    _STATE.clear()
    second=record('STEP',row,'H1','ATR',tmp_path,START)
    assert second['m15_block_audit']==[]
    block.update(accepted=False,reasons=['M15_OB_INVALIDATED_BY_CLOSE'])
    third=record('STEP',row,'H1','ATR',tmp_path,START)
    assert len(third['m15_block_audit'])==1
    assert third['m15_block_summary']['unique_blocks_today']==1


def test_signal_first_seen_stale_is_not_repeated_detection(tmp_path):
    row=dict(strategy_name='SMC',symbol='TEST',direction='BUY',action='STALE_M5_SIGNAL',
             signal_age={'signal_time':(START-timedelta(minutes=30)).isoformat(),'is_stale':True})
    a=record('STEP',row,'H1','ATR',tmp_path,START)
    b=record('STEP',row,'H1','ATR',tmp_path,START+timedelta(minutes=5))
    assert a['signal_age']['observation_class']=='FIRST_SEEN_STALE'
    assert b['signal_age']['observation_class']=='REPEATED_HISTORICAL_SIGNAL'
    assert b['signal_age']['first_detection_delay_seconds']==1500
    assert b['signal_age']['is_stale']  # no gate changed


def test_learning_scopes_keep_account_family_and_worker_distinct(tmp_path):
    rows=[trade(i) for i in range(3)]
    for row,worker in zip(rows,['FOREX_1','FOREX_2','GOLD']):
        row['details']['metadata']['bot_profile']=worker
    report=refresh(rows,'FOREX_1','DEMO',root=tmp_path)
    assert [report['scopes'][k]['execution_rows'] for k in ('account','family','worker')]==[3,2,1]
    assert len(report['trade_eligibility'])==2
    assert report['training_funnel']['promotion_allowed'] is False
