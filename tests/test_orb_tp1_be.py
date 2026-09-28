from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

@pytest.mark.parametrize('direction', ['BUY', 'SELL'])
@pytest.mark.parametrize('reached', [False, True])
def test_orb_tp1_gate_spread_confirmation_and_retry(direction, reached):
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile='ORB')
    buy = direction == 'BUY'
    target = 110 if buy else 90
    bid = (111 if reached else 109) if buy else (88 if reached else 90)
    pos = SimpleNamespace(price_open=100, sl=90 if buy else 110, tp=120 if buy else 80)
    e.provider = SimpleNamespace(get_current_tick=lambda _: {'bid':bid, 'ask':bid+1})
    e.executor = SimpleNamespace(get_position=lambda _:pos, get_symbol_constraints=lambda _: {
        'point':.01, 'tick_size':.01, 'digits':2})
    e.repository = SimpleNamespace(update_trade=Mock(), get_trade_by_execution_key=lambda _:None)
    meta = {'trade_leg':'RUNNER', 'orb_tp1_target_price':target, 'initial_stop_loss':pos.sl}
    trade = {'id':1, 'instrument':'US30', 'direction':direction, 'broker_position_ticket':123, 'details':{}}
    failed = Mock(return_value={'modified':False})
    result = e.process_orb_break_even_management(trade,pos,meta,failed)
    assert not result['activated']
    if not reached:
        failed.assert_not_called()
        return
    assert not meta['break_even_confirmed']
    def move(**kw):
        pos.sl = kw['stop_loss']
        assert kw['take_profit'] == pos.tp
        return {'modified':True}
    mover = Mock(side_effect=move)
    result = e.process_orb_break_even_management(trade,pos,meta,mover)
    assert result['activated'] and meta['break_even_confirmed']
    assert pos.sl >= 101 if buy else pos.sl <= 99
    e.process_orb_break_even_management(trade,pos,meta,mover)
    assert mover.call_count == 1


def test_requested_asset_profiles():
    from strategy.orb.asset_rules import default_asset_profiles
    p = default_asset_profiles()
    assert p['XAUUSD']['allowed_modes'] == ['MOMENTUM','RETEST']
    assert p['XAGUSD']['allowed_modes'] == ['RETEST']
    assert p['US500']['allowed_modes'] == ['MOMENTUM']
    assert p['USOIL']['max_range_atr_ratio'] == 2


def test_monitor_dispatches_orb_to_tp1_management():
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile='ORB', execution_enabled=True)
    e.reporting_service = None
    e.lifecycle_manager = SimpleNamespace(trade_executor=Mock())
    e.executor = SimpleNamespace(get_position=lambda _:SimpleNamespace(price_open=100, price_current=109, sl=90, tp=120))
    e.repository = SimpleNamespace(open_trades=lambda **kw:[dict(id=1, direction='BUY', instrument='US30',
        stop_loss=90, broker_position_ticket='1', details={'metadata':{'strategy_name':'ORB_NEW_YORK'}})])
    e._trade_owned_by_current_bot = lambda _:True
    e._update_excursion_metrics = lambda trade,meta,rr,price:(meta,False)
    e._persist_live_position_market_snapshots = lambda _: {'errors':[]}
    e.process_orb_break_even_management = Mock(return_value={'activated':False,'action':'ORB_WAITING_TP1'})
    result=e._monitor_break_even_positions()
    e.process_orb_break_even_management.assert_called_once()
    assert not result['errors']


@pytest.mark.parametrize('symbol,key', [('GOLD','XAUUSD'),('SILVER','XAGUSD'),('microXAGUSD','XAGUSD'),('CL','USOIL'),('USA500','US500')])
def test_alias_profiles(symbol,key):
    from strategy.orb.asset_rules import get_asset_rules, ASSET_CONFIG
    assert get_asset_rules(symbol) == ASSET_CONFIG[key]
