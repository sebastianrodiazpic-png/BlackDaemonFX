import pandas as pd
from strategy.smc.sequence_shadow import compare
from dashboard.smc_trial import record,snapshot,_STATE
from test_pre_send_risk_guard import provider


def test_sizing_and_send_use_identical_adverse_price():
    p=provider()
    for side,entry,sl in [('BUY',100.,99.),('SELL',99.,100.)]:
        price=p.risk_buffered_entry_price('TEST',side,entry)
        risk_per_lot=p.calculate_risk_amount(symbol='TEST',direction=side,volume=1,entry_price=price,stop_loss=sl)['actual_risk_amount']
        volume=30/risk_per_lot
        p._validate_pre_send_risk({'symbol':'TEST','price':entry,'sl':sl,'volume':volume,'deviation':20},side,30.01)
        assert price>entry if side=='BUY' else price<entry


def test_shadow_sequence_is_bounded_and_does_not_authorize_orders():
    data=pd.DataFrame({'time':pd.date_range('2026-09-22T10:00Z',periods=4,freq='5min'),
                       'close':[101]*4,'bos_bullish':[False,True,False,False]})
    setup={'setup_time':'2026-09-22T10:00Z','ob_low':100,'ob_high':102}
    failures=['M5_BOS_CHOCH_REQUIRED','clean_retest']
    r=compare(data,setup,'long',3,failures)
    v=r['variants']['STRUCTURE_WITHIN_3_BARS']
    assert v['resolved_failures']==['M5_BOS_CHOCH_REQUIRED']
    assert v['remaining_critical_failures']==['clean_retest']
    assert not v['entry_authorized']
    setup['setup_time']='2026-09-22T10:10Z'
    assert not compare(data,setup,'long',3,failures)['variants']['STRUCTURE_WITHIN_3_BARS']['resolved_failures']
    setup['setup_time']='2026-09-22T10:00Z';data.loc[2,'close']=99
    assert not compare(data,setup,'long',3,failures)['variants']['STRUCTURE_WITHIN_3_BARS']['resolved_failures']


def test_unique_setup_survives_refresh_and_restart(tmp_path):
    row={'strategy_name':'SMC','symbol':'EURUSD','action':'NO_M5_CONFIRMATION',
         'setup_sequence_shadow':{'setup_time':'2026-09-22T10:00Z','direction':'long','ob_low':1,'ob_high':2}}
    for _ in range(3):record('FOREX_3',row,'H1_PRIMARY','ATR_BOUNDED',tmp_path)
    _STATE.clear()
    record('FOREX_3',row,'H1_PRIMARY','ATR_BOUNDED',tmp_path)
    worker=snapshot(tmp_path)['workers'][0]
    assert len(worker['unique_setups'])==1
    assert next(iter(worker['unique_setups'].values()))['evaluations']==4


def test_risk_rejection_cools_down_instead_of_repeating(monkeypatch,tmp_path):
    from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig
    from test_demo_daemon_integration import Provider,ExecutionRepo,Executor
    from brokers.mt5_execution import MT5ExecutionError
    import dashboard.smc_trial as trial
    monkeypatch.setattr(trial,'ROOT',tmp_path)
    engine=LiveTradingEngine(provider=Provider(),repository=ExecutionRepo(),executor=Executor(),
                             config=LiveTradingConfig(orb_enabled=False))
    engine._refresh_learning_audit=lambda:None
    calls=[]
    def fail(*args,**kwargs):
        calls.append(1)
        raise MT5ExecutionError('PRE_SEND_RISK_CAP_BREACH: simulated')
    engine.process_symbol=fail
    first=engine.process_symbols(['GBPJPY'],sync_before_execution=False)
    second=engine.process_symbols(['GBPJPY'],sync_before_execution=False)
    assert first[0]['action']=='ERROR'
    assert second[0]['action']=='RISK_RETRY_COOLDOWN'
    assert len(calls)==1
