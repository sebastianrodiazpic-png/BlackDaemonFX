from datetime import datetime, timezone
from types import SimpleNamespace
import copy
import pandas as pd
import pytest
from strategy.gold_quarters import GoldQuarterStrategy
from strategy.ai.trade_observation import learning_rows, eligibility
from strategy.ai.feature_extraction import FEATURE_NAMES
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

NOW=pd.Timestamp('2026-09-22T12:00:00Z')

class QuarterProvider:
    def __init__(self,buy=True): self.buy=buy
    def get_candles(self,symbol,tf,count):
        if tf=='H1':
            return pd.DataFrame({'time':pd.date_range(end=NOW-pd.Timedelta(hours=1),periods=100,freq='h'),
                'open':100.,'close':100.,'high':180. if self.buy else 110.,'low':90. if self.buy else 20.})
        data=pd.DataFrame({'time':pd.date_range(end=NOW-pd.Timedelta(minutes=5),periods=40,freq='5min'),
                          'open':101.,'close':101.,'high':102.,'low':98.})
        data.loc[38,['open','close','high','low']]=[102,102,103,99.8] if self.buy else [98,98,100.2,97]
        data.loc[39,['open','close','high','low']]=[102,104,104.5,102] if self.buy else [98,96,98,95.5]
        return data

@pytest.mark.parametrize('buy',[True,False])
def test_quarters_closed_confirmation_and_fixed_target(buy):
    r=GoldQuarterStrategy(QuarterProvider(buy)).analyze_symbol('XAUUSD',NOW)
    assert r['valid']
    assert r['signal']['quarter_target']==(125 if buy else 75)
    assert r['signal']['direction']==('BUY' if buy else 'SELL')
    assert r['signal']['risk_reward_ratio']>=2
    assert not GoldQuarterStrategy(QuarterProvider(buy)).analyze_symbol('EURUSD',NOW)['valid']
    # Confirmation candle still forming: cannot use its eventual close.
    assert not GoldQuarterStrategy(QuarterProvider(buy)).analyze_symbol('XAUUSD',NOW-pd.Timedelta(minutes=1))['valid']


def test_external_audit_does_not_grant_management():
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='BOOM',magic=26082101)
    trade={'details':{'metadata':{'managed_by_daemon':False,'mt5_magic':26082101}}}
    assert engine._trade_auditable_by_current_bot(trade)
    assert not engine._trade_owned_by_current_bot(trade)
    engine.config.bot_profile='GOLD'
    assert not engine._trade_auditable_by_current_bot(trade)


def test_late_observation_learns_only_subsequent_price_change():
    row={'id':1,'status':'CLOSED','entry_time':'2026-09-21T00:00Z','exit_time':'2026-09-22T15:00Z',
         'entry_price':50.,'exit_price':101.,'realized_rr':20.,'net_pnl':500.,'details':{'metadata':{
         'managed_by_daemon':False,'observation_worker':'BOOM','mt5_observation':{
             'evaluated_at':'2026-09-22T12:00Z','observed_price':102.,'risk_distance':2.,'direction':'BUY',
             'feature_names':list(FEATURE_NAMES),'features':{n:0. for n in FEATURE_NAMES}}}}}
    original=copy.deepcopy(row)
    r=learning_rows([row])[0]
    assert r['realized_rr']==-.5  # original entry won; observed interval lost
    assert r['details']['metadata']['strategy_name']=='MT5_OBSERVATION'
    assert r['entry_time']=='2026-09-22T12:00Z'
    assert eligibility(row)['reason']=='ELEGIBLE_OBSERVACION'
    assert row==original
    row['status']='OPEN'
    assert eligibility(row)['reason']=='ESPERANDO_CIERRE'


def test_external_refresh_persists_first_observation_and_history():
    from strategy.ai.trade_observation import observe
    current=pd.Timestamp.now(tz='UTC').floor('5min')
    class P:
        price=101.
        def get_current_tick(self,s):return {'bid':self.price,'ask':self.price+.1}
        def get_candles(self,*args,**kwargs):
            return pd.DataFrame({'time':pd.date_range(end=current-pd.Timedelta(minutes=5),periods=20,freq='5min'),
                                 'open':100.,'close':100.,'low':99.,'high':102.})
    class R:
        def __init__(self):
            self.trade={'id':1,'instrument':'XAUUSD','direction':'BUY','status':'OPEN','source':'MT5_EXTERNAL',
                'entry_time':'2026-09-21T00:00Z','entry_price':99.,'stop_loss':98.,'take_profit':125.,
                'details':{'metadata':{'managed_by_daemon':False}}}
            self.snapshots=[];self.visuals=[]
        def open_trades(self,source):return [self.trade] if source=='MT5_EXTERNAL' else []
        def sync_closed_mt5_trades(self,*args,**kwargs):return 0
        def update_trade(self,i,data):self.trade.update(data)
        def trade_visual_audits(self,source):return self.visuals if source=='MT5_EXTERNAL' else []
        def upsert_trade_visual_audit(self,i,**data):self.visuals=[{'trade_id':i,**data}]
        def save_trade_audit_snapshot(self,i,**data):self.snapshots.append(data)
    e=object.__new__(LiveTradingEngine);e.config=LiveTradingConfig(bot_profile='BOOM',execution_enabled=False)
    e.provider=P();e.repository=R();e.executor=SimpleNamespace()
    e._persist_audit_event=lambda *args,**kwargs:None
    assert e._refresh_current_strategy_views()['updated']==1
    first=copy.deepcopy(e.repository.trade['details']['metadata']['mt5_observation'])
    e.provider.price=102.;e._last_current_strategy_refresh_monotonic=0
    assert e._refresh_current_strategy_views()['updated']==1
    assert e.repository.trade['details']['metadata']['mt5_observation']==first
    assert len(e.repository.snapshots)==2
    assert e.repository.snapshots[-1]['source']=='MT5_EXTERNAL'
    assert e.repository.snapshots[-1]['current_view']['observed_price']==102.
    assert e.repository.snapshots[-1]['entry_view']['observed_price']==101.
    assert e.repository.trade['details']['metadata']['managed_by_daemon'] is False


def test_gold_quarters_execution_keeps_one_leg_and_fixed_target():
    from test_demo_daemon_integration import Provider, ExecutionRepo, Executor, FakeLifecycleManager
    e=LiveTradingEngine(provider=Provider(), repository=ExecutionRepo(), executor=Executor(),
        lifecycle_manager=FakeLifecycleManager(),config=LiveTradingConfig(bot_profile='GOLD',orb_enabled=False,
            execution_enabled=True, max_entry_drift_r=None))
    e.multi_timeframe=SimpleNamespace(analyze_symbol=lambda s:{'valid':False,'reason':'NO_SMC_SETUP'})
    e._attach_exhaustion_reversal_shadow=lambda s,a:a
    e._gold_quarters_analysis=lambda s:{'valid':True,'strategy_name':'GOLD_QUARTERS','signal':{
        'strategy_name':'GOLD_QUARTERS','direction':'BUY','entry_time':pd.Timestamp.now(tz='UTC').isoformat(),
        'entry_price':100.,'stop_loss':95.,'quarter_target':125.,'take_profit':125.,'risk_reward_ratio':5.,
        'entry_location_ranges':{'H1':{'low':90.,'high':140.}}}}
    # The sizing/target contract is independent of the separately tested preflight.
    from unittest.mock import Mock
    guard = Mock(return_value={'valid':False,'reason':'GOLD_QUARTERS_DATA_UNAVAILABLE'})
    e._gold_quarters_entry_preflight = guard
    blocked=e.process_symbol('XAUUSD')
    assert blocked['action']=='GOLD_QUARTERS_ENTRY_BLOCKED'
    assert not e.repository.rows
    guard.return_value={'valid':True,'reason':'GOLD_QUARTERS_PREFLIGHT_PASSED'}
    result=e.process_symbol('XAUUSD')
    assert guard.call_count==2
    assert result['action']=='ORDER_OPENED',result
    assert len(e.repository.rows)==1
    row=next(iter(e.repository.rows.values()))
    assert row['take_profit']==125.
    assert row['details']['metadata']['strategy_name']=='GOLD_QUARTERS'

