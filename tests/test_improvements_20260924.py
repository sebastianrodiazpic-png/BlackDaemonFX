import json
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pandas as pd
import numpy as np
import pytest
from dashboard.smc_trial import record, snapshot
from marketdata.deriv import DerivWebSocketTransport, DerivMarketDataProvider, DerivAPIError
from test_pre_send_risk_guard import provider
from brokers.mt5_execution import MT5ExecutionError
from test_complete_learning_audit import candidate
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from test_daemon_risk_target_policy import Provider, Repo, Executor, Analyzer


def test_timestamp_audit_survives_and_keeps_input(tmp_path):
    row={'strategy_name':'SMC','symbol':'TEST','action':'NO_M5_CONFIRMATION',
         'historical_m5_rejection':{'time':pd.Timestamp('2026-09-24T10:00Z'),'n':np.int64(2),'bad':np.float64(float('nan'))}}
    result=record('STEP',row,'H1','STRICT',tmp_path)
    saved=json.loads((tmp_path/'STEP.json').read_text())
    assert saved['latest']['TEST']['historical_m5_rejection']['time'].startswith('2026-09-24T10:00:00')
    assert result['historical_m5_rejection']['bad'] is None
    assert isinstance(row['historical_m5_rejection']['time'],pd.Timestamp)


def test_shadow_incomplete_can_capture_only_while_current(tmp_path):
    now=datetime(2026,9,1,10,5,tzinfo=timezone.utc)
    comparison={'setup_time':'2026-09-01T09:00Z','confirmation_time':'2026-09-01T10:00Z','direction':'long','ob_low':90,'ob_high':95,
                'variants':{'V':{'remaining_critical_failures':[],'ob_respected':True}}}
    row={'strategy_name':'SMC','symbol':'TEST','setup_sequence_shadow':comparison,'shadow_quote':candidate()['execution_quote']}
    record('STEP',row,'H1','STRICT',tmp_path,now)
    setup=next(iter(snapshot(tmp_path)['workers'][0]['unique_setups'].values()))
    assert not setup.get('first_variant_ready')
    assert setup['variant_capture_failures']['V']['reason']=='MISSING_CAUSAL_PLAN'
    row['shadow_plan']=candidate()['plan']
    record('STEP',row,'H1','STRICT',tmp_path,now+timedelta(seconds=10))
    setup=next(iter(snapshot(tmp_path)['workers'][0]['unique_setups'].values()))
    assert setup['first_variant_ready']['V']['observed_at']==(now+timedelta(seconds=10)).isoformat()
    row['symbol']='STALE'
    record('STEP',row,'H1','STRICT',tmp_path,now+timedelta(hours=1))
    setup=[x for x in snapshot(tmp_path)['workers'][0]['unique_setups'].values() if x['symbol']=='STALE'][0]
    assert not setup.get('first_variant_ready')
    assert setup['variant_capture_failures']['V']['reason']=='STALE_OR_UNCLOSED_CONFIRMATION'


def test_rejected_shadow_keeps_live_score_empty_and_checks_setup():
    reject={'setup_time':'2026-09-24T10:00Z','direction':'BUY','entry_price':100,'stop_loss':90,'take_profit':120,
            'setup_sequence_shadow':{'setup_time':'2026-09-24T10:00Z'},'trade_score':30}
    analysis={'direction':'BUY','diagnostics':{'sequence':{'selected_setup_time':'2026-09-24T10:00Z'},'m5':{'latest_rejected_candidate':reject}}}
    out=LiveTradingEngine._compact_symbol_result({'analysis':analysis})
    assert out.get('trade_score') is None and out['shadow_plan']['entry_price']==100
    analysis['diagnostics']['sequence']['selected_setup_time']='2026-09-24T11:00Z'
    out=LiveTradingEngine._compact_symbol_result({'analysis':analysis})
    assert out['shadow_plan']['entry_price'] is None


def test_transport_reconnect_bounded_with_jitter(monkeypatch):
    sleeps=[]; monkeypatch.setattr('marketdata.deriv.time.sleep',sleeps.append)
    sockets=[]
    class Socket:
        def send(self,message): self.request=json.loads(message)
        def recv(self):
            if len(sockets)==1: raise TimeoutError('timeout')
            return json.dumps({'req_id':self.request['req_id'],'ok':True})
        def settimeout(self,value): assert 0 < value <= 12
        def close(self): pass
    t=DerivWebSocketTransport('unused')
    def connect():
        if t._socket is None: t._socket=Socket(); sockets.append(t._socket)
    t.connect=connect
    assert t.request({'ticks_history':'TEST'})['ok']
    assert len(sockets)==2 and len(sleeps)==1 and .5<=sleeps[0]<=1


def test_transport_failure_defers_other_workers():
    delays=[]
    def fail(payload): raise DerivAPIError('timeout')
    p=DerivMarketDataProvider(transport=SimpleNamespace(request=fail),
        rate_limiter=SimpleNamespace(wait=lambda:None,defer=delays.append))
    with pytest.raises(DerivAPIError): p._request({'ticks_history':'TEST'})
    assert len(delays)==1 and delays[0]>=3


@pytest.mark.parametrize('second_price,send_expected',[(63.064,True),(64.,False)])
def test_resize_rechecks_and_never_sends_over_cap(second_price,send_expected):
    p=provider(); events=[]
    request={'symbol':'XAGUSDmicro','price':63.054,'sl':62.949,'tp':63.5,'volume':6.07,'deviation':20,'type_filling':0}
    p._ensure=lambda:None
    p._build_market_request_base=lambda **k:dict(request)
    p._run_order_check_with_fallback=lambda *a:{'valid':True,'request':dict(request)}
    prices=iter([63.064,second_price]);p._current_market_price=lambda *a:next(prices)
    p.calculate_volume=lambda *a:{'volume':4.,'actual_risk_amount':27.}
    def check(r):
        events.append(('check',r['volume']));return SimpleNamespace(retcode=0),r,{}
    p._order_check_safe=check;p._is_order_check_success=lambda r:True
    p._is_order_send_success=lambda r:True;p._filling_name=lambda x:'FOK'
    def send(r):
        assert r['volume']==4. and r['sl']==request['sl'] and r['tp']==request['tp']
        events.append(('send',r['volume']))
        return SimpleNamespace(retcode=0,price=r['price'],volume=4.,order=1,deal=2),r,{}
    p._order_send_safe=send
    if send_expected:
        result=p.place_market_order('XAGUSDmicro','BUY',6.07,62.949,63.5,1,'test',max_risk_amount=33.34992525)
        assert result['filled_volume']==4. and result['risk_resize']['original_volume']==6.07
        assert events==[('check',4.),('send',4.)]
    else:
        with pytest.raises(MT5ExecutionError,match='PRE_SEND_RISK_CAP_BREACH'):
            p.place_market_order('XAGUSDmicro','BUY',6.07,62.949,63.5,1,'test',max_risk_amount=33.34992525)
        assert events==[('check',4.)]


def test_lower_risk_reaches_existing_smc_preflight():
    engine=LiveTradingEngine(provider=Provider(),repository=Repo(),executor=Executor(),
        config=LiveTradingConfig(execution_enabled=False,max_entry_drift_r=None,validate_order_in_dry_run=False))
    engine.multi_timeframe=Analyzer()
    # Existing preflight still rejects this intentionally incomplete setup.
    out=engine.process_symbol('Volatility 75 Index')
    assert out['action']=='SMC_ENTRY_PREFLIGHT_BLOCKED'
    assert out['actual_risk_amount']>0



def test_reduced_fill_volume_reaches_reporting(monkeypatch):
    from brokers.mt5_trade_executor import MT5TradeExecutor
    from trade_lifecycle_manager import TradeLifecycleManager
    from test_trade_lifecycle_paper_integration import signal
    import brokers.mt5_trade_executor as adapter
    monkeypatch.setattr(adapter, 'mt5', object())
    resize={'original_volume':6.,'volume':4.}
    fake=SimpleNamespace(assert_demo_account=lambda:None,
        place_market_order=lambda **kwargs:{'filled_volume':4.,'entry_price':111.,'deal_ticket':2,'risk_resize':resize},
        find_position_ticket=lambda *args:1)
    manager=TradeLifecycleManager(trade_executor=MT5TradeExecutor(fake, magic=1))
    events=[]
    manager._notify_reporting=lambda **kwargs:events.append(kwargs)
    lifecycle=manager.process_signal_with_executor(signal(),volume=6.)
    assert lifecycle.metadata['volume']==4.
    assert lifecycle.metadata['requested_volume']==6.
    assert lifecycle.metadata['risk_resize']==resize
    assert events[-1]['volume']==4.


def test_unmatched_responses_cannot_extend_deadline(monkeypatch):
    monkeypatch.setattr('marketdata.deriv.time.sleep',lambda delay:None)
    clock=[0.]
    monkeypatch.setattr('marketdata.deriv.time.monotonic',lambda:clock[0])
    reads=[]
    class Socket:
        def send(self,msg): pass
        def settimeout(self,value): pass
        def recv(self):
            clock[0]+=1;reads.append(1)
            return '{"req_id":999}'
        def close(self): pass
    t=DerivWebSocketTransport('unused',timeout_seconds=2.)
    t.connect=lambda:setattr(t,'_socket',Socket())
    with pytest.raises(DerivAPIError,match='deadline'):
        t.request({'ticks_history':'TEST'})
    assert len(reads)==4
