from types import SimpleNamespace
import pytest
from test_daemon_break_even_live import Repo,Provider,BrokerExecutor,TradeExecutor,LifecycleManager
from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig


def setup_engine(direction='BUY',price=105.,sibling=None):
    repo=Repo();repo.trade.update(instrument='XAUUSD',direction=direction)
    initial=90. if direction=='BUY' else 110.
    repo.trade['stop_loss']=initial
    meta=repo.trade['details']['metadata']
    meta.update(initial_stop_loss=initial,trade_leg='RUNNER',parent_execution_key='op',gold_tp1_target_price=110. if direction=='BUY' else 90.)
    repo.get_trade_by_execution_key=lambda key:sibling
    broker=BrokerExecutor();broker.sl=initial
    broker.get_position=lambda ticket:SimpleNamespace(ticket=ticket,price_open=100.,price_current=price,sl=broker.sl,tp=120. if direction=='BUY' else 80.)
    provider=Provider()
    provider.get_current_tick=lambda symbol:dict(bid=price if direction=='BUY' else price-.1,ask=price+.1 if direction=='BUY' else price)
    mover=TradeExecutor(broker)
    engine=LiveTradingEngine(provider,repo,LiveTradingConfig(bot_profile='GOLD',execution_enabled=True,
        gold_break_even_positive_at_new_york=True,break_even_confirmation_delay_seconds=0),
        executor=broker,lifecycle_manager=LifecycleManager(mover))
    engine._trade_owned_by_current_bot=lambda trade:True
    engine._gold_smc_session_state=lambda:{'active':False}
    engine._analysis_invalidation_exit=lambda **kw:{'managed':False,'closed':False}
    return engine,repo,broker,mover


@pytest.mark.parametrize('direction,price',[('BUY',100.2),('BUY',109.99),('SELL',99.8),('SELL',90.01)])
def test_gold_keeps_initial_sl_before_tp1_even_at_new_york(direction,price):
    engine,repo,broker,mover=setup_engine(direction,price)
    repo.trade['details']['metadata']['break_even_trigger_rr']=.1
    result=engine._monitor_break_even_positions()
    assert not result['errors'],result
    assert result['activated']==0 and not mover.calls
    assert broker.sl==repo.trade['details']['metadata']['initial_stop_loss']


@pytest.mark.parametrize('direction,price',[('BUY',110.),('SELL',90.)])
def test_tp1_touch_enables_spread_protected_be(direction,price):
    engine,repo,broker,mover=setup_engine(direction,price)
    result=engine._monitor_break_even_positions()
    assert result['activated']==1,result
    stop=mover.calls[0][1]
    assert stop>100.1 if direction=='BUY' else stop<99.9
    assert repo.trade['details']['metadata']['gold_tp1_evidence']['reached']
    assert repo.trade['details']['metadata']['break_even_activation_reason']=='GOLD_TP1_REACHED_SPREAD_PROTECTED'


def test_small_profitable_tp1_close_does_not_unlock_runner():
    sibling=dict(instrument='XAUUSD',direction='BUY',take_profit=110.,status='CLOSED',result='WIN',exit_price=103.)
    engine,repo,broker,mover=setup_engine(price=105.,sibling=sibling)
    assert engine._monitor_break_even_positions()['activated']==0
    assert not mover.calls


def test_actual_tp1_close_unlocks_after_retracement():
    sibling=dict(instrument='XAUUSD',direction='BUY',take_profit=110.,status='CLOSED',result='WIN',exit_price=110.)
    engine,repo,broker,mover=setup_engine(price=108.,sibling=sibling)
    assert engine._monitor_break_even_positions()['activated']==1


def test_missing_quote_blocks_and_tp1_leg_never_moves():
    engine,repo,broker,mover=setup_engine(price=110.)
    engine.provider.get_current_tick=lambda symbol:None
    assert engine._monitor_break_even_positions()['activated']==0
    engine.provider.get_current_tick=lambda symbol:dict(bid=110.,ask=110.1)
    repo.trade['details']['metadata']['trade_leg']='TP1'
    assert engine._monitor_break_even_positions()['activated']==0
    assert not mover.calls


def test_invalid_stop_distance_defers_and_touch_survives_restart():
    engine,repo,broker,mover=setup_engine(price=110.)
    broker.get_symbol_constraints=lambda symbol:dict(point=.01,digits=2,min_stop_distance=20.)
    assert engine._monitor_break_even_positions()['activated']==0
    assert repo.trade['details']['metadata']['gold_tp1_evidence']['reached']
    broker.get_symbol_constraints=lambda symbol:dict(point=.01,digits=2)
    engine.provider.get_current_tick=lambda symbol:dict(bid=108.,ask=108.1)
    assert engine._monitor_break_even_positions()['activated']==1


def test_previously_tightened_stop_is_not_widened():
    engine,repo,broker,mover=setup_engine(price=110.)
    broker.sl=106.
    assert engine._monitor_break_even_positions()['activated']==0
    assert broker.sl==106. and not mover.calls


def test_runner_management_remains_available_after_tp1_and_be():
    from unittest.mock import Mock
    engine,repo,broker,mover=setup_engine(price=110.)
    assert engine._monitor_break_even_positions()['activated']==1
    engine._manage_runner_extension=Mock(return_value={'managed':False})
    engine._monitor_break_even_positions()
    engine._manage_runner_extension.assert_called_once()
    assert len(mover.calls)==1


def test_single_legacy_trade_requires_at_least_virtual_tp1():
    engine,repo,broker,mover=setup_engine(price=105.)
    meta=repo.trade['details']['metadata']
    meta.update(trade_leg='SINGLE',break_even_trigger_rr=.2)
    meta.pop('gold_tp1_target_price')
    assert engine._monitor_break_even_positions()['activated']==0
    assert not mover.calls
