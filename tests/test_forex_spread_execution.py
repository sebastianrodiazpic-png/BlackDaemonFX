from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from strategy.execution.forex_spread_guard import ForexSpreadGuard
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

START=datetime(2026,9,23,14,tzinfo=timezone.utc)
def quote(now, spread=.0002):
    return {'spread_status':'AVAILABLE','spread_source':'MT5_EXECUTION','spread':spread,
            'execution_bid':1.87,'execution_ask':1.87+spread,'spread_quote_time':now.isoformat(),
            'spread_captured_at':now.isoformat()}

def warm(guard):
    for i in range(25):
        now=START+timedelta(seconds=15*i)
        guard.observe('GBPCAD',quote(now),now)
    return now

def test_bootstrap_risk_cap_and_relative_spike(tmp_path):
    guard=ForexSpreadGuard('FOREX_1',tmp_path)
    assert guard.check('GBPCAD',quote(START),'SELL',1.873,now=START)['reason']=='BASELINE_WARMUP'
    now=warm(guard)+timedelta(seconds=15)
    assert guard.check('GBPCAD',quote(now),'SELL',1.873,now=now)['allowed']
    assert not guard.check('GBPCAD',quote(now),'SELL',1.871,now=now)['allowed']
    assert guard.check('GBPCAD',quote(now,.00045),'SELL',1.88,now=now)['reason']=='SPREAD_ABOVE_LIMIT'


def test_reopen_requires_new_stability_and_persisted_baseline(tmp_path):
    guard=ForexSpreadGuard('FOREX_1',tmp_path);warm(guard)
    guard=ForexSpreadGuard('FOREX_1',tmp_path)
    reopen=datetime(2026,9,23,21,tzinfo=timezone.utc)
    for i in range(5):
        now=reopen+timedelta(seconds=15*i)
        report=guard.check('GBPCAD',quote(now),'SELL',1.873,now=now)
        assert report['allowed']==(i==4)
    assert guard.state['symbols']['GBPCAD']['samples_count']==25


def test_rapid_checks_do_not_fake_stability(tmp_path):
    guard=ForexSpreadGuard('FOREX_1',tmp_path);warm(guard)
    now=datetime(2026,9,23,21,tzinfo=timezone.utc)
    for _ in range(20):
        report=guard.check('GBPCAD',quote(now),'SELL',1.873,now=now)
        assert not report['allowed']
    assert report['stable_count']==1


def test_stale_and_missing_quotes_fail_closed(tmp_path):
    guard=ForexSpreadGuard('FOREX_1',tmp_path);now=warm(guard)
    assert guard.check('GBPCAD',quote(now-timedelta(seconds=31)),'SELL',1.88,now=now)['reason']=='QUOTE_UNAVAILABLE'
    assert guard.check('GBPCAD',{},'SELL',1.88,now=now)['reason']=='QUOTE_UNAVAILABLE'


def test_sample_gap_resets_stability(tmp_path):
    guard=ForexSpreadGuard('FOREX_1',tmp_path);now=warm(guard)+timedelta(minutes=2)
    assert not guard.check('GBPCAD',quote(now),'SELL',1.873,now=now)['allowed']


def test_jpy_pips_and_absolute_cap(tmp_path):
    guard=ForexSpreadGuard('FOREX_1',tmp_path)
    report=guard.observe('USDJPY',quote(START,.06),START)
    assert report['spread_pips']==6
    assert report['samples_count']==0


def test_engine_keeps_calendar_and_excludes_other_workers(tmp_path):
    engine=LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='FOREX_1')
    engine._forex_spread_tracker=ForexSpreadGuard('FOREX_1',tmp_path)
    engine._forex_rollover_entry_gate=lambda symbol:{'action':'FOREX_ROLLOVER_ENTRY_BLOCKED'}
    assert engine._forex_execution_gate('GBPCAD','SELL',1.88)['action']=='FOREX_ROLLOVER_ENTRY_BLOCKED'
    engine._forex_rollover_entry_gate=lambda symbol:None
    engine.config.bot_profile='GOLD'
    assert engine._forex_execution_gate('XAUUSD','BUY',100) is None
    engine.config.bot_profile='FOREX_1';engine._meta_execution_spread=lambda symbol:{}
    engine._persist_audit_event=Mock()
    assert engine._forex_execution_gate('GBPCAD','SELL',1.88)['reason']=='QUOTE_UNAVAILABLE'
    assert engine._persist_audit_event.called

def test_monitor_persists_quotes_without_altering_barriers(tmp_path):
    import threading
    from database.repository import TradingRepository
    repo=TradingRepository(tmp_path/'quotes.sqlite')
    tid=repo.create_trade({'source':'DEMO','instrument':'GBPCAD','direction':'SELL','timeframe':'M5',
        'status':'OPEN','entry_price':1.87,'stop_loss':1.88,'take_profit':1.86,
        'details':{'metadata':{'other_evidence':'keep'}}})
    engine=LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='FOREX_1')
    engine.repository=repo;engine._execution_persistence_lock=threading.RLock()
    engine._forex_spread_tracker=ForexSpreadGuard('FOREX_1',tmp_path/'spread')
    engine._trade_owned_by_current_bot=lambda row:True
    engine._meta_execution_spread=lambda symbol:quote(datetime.now(timezone.utc))
    engine._persist_audit_event=Mock()
    engine._sample_forex_execution_quotes(['GBPCAD'])
    row=repo.get_trade(tid)
    assert row['stop_loss']==1.88 and row['take_profit']==1.86
    assert row['details']['metadata']['other_evidence']=='keep'
    assert len(row['details']['metadata']['forex_execution_quotes'])==1
    assert engine._persist_audit_event.call_args.args[0]=='FOREX_POSITION_QUOTE'
