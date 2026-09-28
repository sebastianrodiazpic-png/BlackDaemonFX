import json
from types import SimpleNamespace
import pandas as pd
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig, orb_session_asset


def engine(rows):
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig()
    e.repository=SimpleNamespace(trade_history_dataframe=lambda **kw:pd.DataFrame(rows),
                                 open_trades=lambda **kw:[x for x in rows if x.get('status')=='OPEN'])
    return e


def trade(symbol='XAGUSD',strategy='ORB_NEW_YORK',session='2026-09-24',status='CLOSED'):
    return dict(id=123,instrument=symbol,status=status,entry_time=session+'T14:00:00Z',
                details={'metadata':{'strategy_name':strategy,'orb_session_date':session}})


@pytest.mark.parametrize('used,candidate',[('XAGUSD','XAGUSDmicro'),('XAGUSDmicro','XAGUSD'),('microXAGUSD','XAGUSD')])
def test_persisted_session_shared_both_directions(used,candidate):
    row=trade(used);row['details']=json.dumps(row['details'])
    result=engine([row])._orb_session_trade_exists(candidate,'2026-09-24')
    assert result['trade_id']==123 and result['instrument']==used
    assert result['underlying_asset']=='XAGUSD'


def test_prior_session_and_smc_do_not_consume_new_session():
    e=engine([trade(session='2026-09-23'),trade(strategy='SMC')])
    assert e._orb_session_trade_exists('XAGUSDmicro','2026-09-24') is None
    assert e._orb_silver_open_guard('XAGUSDmicro') is None


def test_open_old_orb_blocks_but_open_smc_does_not():
    assert engine([trade(session='2026-09-23',status='OPEN')])._orb_silver_open_guard('XAGUSDmicro')['reason']=='ORB_SILVER_EXPOSURE_ALREADY_OPEN'
    assert engine([trade(strategy='SMC',status='OPEN')])._orb_silver_open_guard('XAGUSDmicro') is None


def test_history_failure_does_not_allow_duplicate():
    e=engine([])
    def fail(**kw):raise OSError('unavailable')
    e.repository.trade_history_dataframe=fail
    assert e._orb_session_trade_exists('XAGUSDmicro','2026-09-24')['guard_error']=='ORB_SILVER_HISTORY_UNAVAILABLE'
    e.repository.open_trades=fail
    assert e._orb_silver_open_guard('XAGUSDmicro')['reason']=='ORB_SILVER_EXPOSURE_UNAVAILABLE'


def test_fill_memory_shared_even_if_general_session_limit_disabled():
    s=NewYorkORBStrategy(data_provider=SimpleNamespace(),config=ORBConfig(one_signal_per_session=False))
    assert not s._session_signal_memory
    s.mark_signal_used('XAGUSDmicro','2026-09-24','2026-09-24T14:00:00Z')
    assert s._session_signal_memory[orb_session_asset('XAGUSD')][0]=='2026-09-24'
    s.mark_signal_used('XAGUSD','2026-09-25','2026-09-25T14:00:00Z')
    assert s._session_signal_memory[orb_session_asset('XAGUSDmicro')][0]=='2026-09-25'


def test_other_instruments_keep_identity():
    assert orb_session_asset('XAUUSDmicro')=='XAUUSDmicro'
    assert engine([trade('XAUUSD')])._orb_session_trade_exists('XAGUSD','2026-09-24') is None


def test_analyzer_blocks_same_breakout_on_other_silver_contract_only_after_fill():
    from datetime import datetime, timezone
    from test_orb_new_york_strategy import _session_candles, _strategy
    now=datetime(2026,8,28,13,55,30,tzinfo=timezone.utc)
    strategy=_strategy(_session_candles("BUY",valid_retest=True),now)
    first=strategy.analyze_symbol("XAGUSD",now)
    assert first['valid']
    assert strategy.analyze_symbol("XAGUSDmicro",now)['valid']
    signal=first['signal']
    strategy.mark_signal_used('XAGUSD',signal['orb_session_date'],signal['breakout_candle_time'])
    blocked=strategy.analyze_symbol('XAGUSDmicro',now)
    assert not blocked['valid']
    assert blocked['reason']=='ORB_SILVER_SESSION_ALREADY_USED'
