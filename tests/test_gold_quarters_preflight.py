from types import SimpleNamespace
from unittest.mock import Mock
import pandas as pd
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


def setup(direction='BUY', obstacle_tf=None, stale=False):
    now=pd.Timestamp.now(tz='UTC')
    def candles(symbol,tf,count):
        minutes=15 if tf=='M15' else 5
        end=now.floor(f'{minutes}min')-pd.Timedelta(minutes=minutes)
        if stale and tf=='M15':end-=pd.Timedelta(minutes=15)
        data=pd.DataFrame({'time':pd.date_range(end=end,periods=40,freq=f'{minutes}min'),
            'open':100.,'high':101.,'low':99.,'close':100.,'ob_type':None,'ob_low':None,'ob_high':None,'ob_break_time':None,
            'bos_bullish':False,'bos_bearish':False,'choch_bullish':False,'choch_bearish':False})
        # Range extreme outside target, so only the explicit OB is tested.
        data.loc[0,['high','low']]=[140.,60.]
        if obstacle_tf==tf:
            data.loc[10,['ob_type','ob_low','ob_high','ob_break_time']]=['bearish' if direction=='BUY' else 'bullish',104. if direction=='BUY' else 94.,106. if direction=='BUY' else 96.,data.time.iloc[10]]
        return data
    e=LiveTradingEngine.__new__(LiveTradingEngine);e.config=LiveTradingConfig()
    e.provider=SimpleNamespace(get_candles=candles)
    e.multi_timeframe=SimpleNamespace(_run_pipeline=lambda data,symbol:{'data':data})
    e._meta_execution_spread=lambda symbol:{'spread_status':'AVAILABLE','execution_bid':100.,'execution_ask':100.,'spread_source':'MT5_EXECUTION'}
    e._persist_audit_event=Mock()
    signal={'entry_time':(now.floor('5min')-pd.Timedelta(minutes=5)).isoformat(),'stop_loss':90. if direction=='BUY' else 110.,'take_profit':120. if direction=='BUY' else 80.}
    return e,signal

@pytest.mark.parametrize('direction',['BUY','SELL'])
@pytest.mark.parametrize('tf',['M15','M5'])
def test_opposing_ob_before_one_r_blocks(direction,tf):
    e,s=setup(direction,tf)
    result=e._gold_quarters_entry_preflight('XAUUSDmicro',s,direction,s['stop_loss'],[{'name':'FULL','take_profit':s['take_profit']}])
    assert not result['valid']
    assert result['reason']=='SMC_OBSTACLE_BEFORE_MIN_R'
    assert result['path']['nearest_obstacle']['timeframe']==tf
    assert result['path']['nearest_obstacle']['distance_r']==.4


def test_clear_evaluated_path_keeps_original_targets():
    e,s=setup();original=(s['stop_loss'],s['take_profit'])
    result=e._gold_quarters_entry_preflight('XAUUSDmicro',s,'BUY',90,[{'name':'FULL','take_profit':120}])
    assert result['valid'] and result['path']['evaluated']
    assert (s['stop_loss'],s['take_profit'])==original
    assert s['target_path_audit']['paths']['FULL']['clear_path']


def test_stale_history_is_unknown_not_clear():
    e,s=setup(stale=True)
    result=e._gold_quarters_entry_preflight('XAUUSDmicro',s,'BUY',90,[{'name':'FULL','take_profit':120}])
    assert not result['valid'] and result['path']['clear_path'] is None
    assert not result['path']['evaluated']


def test_missing_broker_quote_blocks():
    e,s=setup();e._meta_execution_spread=lambda symbol:{'spread_status':'UNAVAILABLE'}
    assert not e._gold_quarters_entry_preflight('XAUUSDmicro',s,'BUY',90,[{'name':'FULL','take_profit':120}])['valid']


def test_broken_confirmation_extreme_blocks_even_with_clear_path():
    e,s=setup();e._meta_execution_spread=lambda symbol:{'spread_status':'AVAILABLE','execution_ask':98.}
    result=e._gold_quarters_entry_preflight('XAUUSDmicro',s,'BUY',90,[{'name':'FULL','take_profit':120}])
    assert not result['valid'] and result['reason']=='SMC_M5_CONFIRMATION_EXTREME_BROKEN'
