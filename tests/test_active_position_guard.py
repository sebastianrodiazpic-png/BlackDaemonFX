from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from strategy.execution.active_position_guard import (
    check_active_position_guard, read_active_position_guard, symbol_cycle_lock)


@pytest.mark.parametrize('record', [dict(symbol='X',ticket=7,sl=100,price_open=100),
    SimpleNamespace(symbol='X',ticket=7,sl=100,price_open=100)])
def test_open_at_break_even_still_blocks(record):
    result=check_active_position_guard('X',[record],[])
    assert not result['can_analyze'] and result['ticket']==7
    assert result['status']=='BLOCKED_ACTIVE_TRADE'


def test_pending_order_partial_close_and_other_symbols():
    assert check_active_position_guard('X',[],[dict(symbol='X',ticket=8)])['status']=='BLOCKED_PENDING_ORDER'
    assert not check_active_position_guard('X',[dict(symbol='X',ticket=2)],[])['can_analyze']
    assert check_active_position_guard('X',[dict(symbol='Y',ticket=3)],[])['can_analyze']
    assert check_active_position_guard('X',[],[])['can_analyze']


@pytest.mark.parametrize('positions,orders',[(None,[]),([],None),([{}],[]),([],42)])
def test_unavailable_or_malformed_snapshot_blocks(positions,orders):
    assert check_active_position_guard('X',positions,orders)['status']=='BLOCKED_POSITION_STATE_UNAVAILABLE'


def test_broker_exception_and_no_snapshot_interface_block():
    broker=SimpleNamespace(get_open_positions=Mock(side_effect=RuntimeError('offline')))
    assert not read_active_position_guard('X',broker)['can_analyze']
    assert not read_active_position_guard('X',object())['can_analyze']


def test_worker_stops_before_analysis_and_releases_after_resolution(tmp_path,monkeypatch):
    from strategy.execution.live_trading_engine import LiveTradingEngine
    import strategy.execution.active_position_guard as module
    original=module.symbol_cycle_lock
    monkeypatch.setattr(module,'symbol_cycle_lock',lambda symbol:original(symbol,tmp_path))
    engine=object.__new__(LiveTradingEngine)
    engine.provider=SimpleNamespace(resolve_symbol=lambda symbol:'X',ensure_symbol=Mock())
    positions=[dict(symbol='X',ticket=9)]
    engine.executor=SimpleNamespace(get_open_positions=lambda:positions,get_pending_orders=lambda:[])
    engine._persist_audit_event=Mock()
    engine._gold_smc_entry_gate=Mock(return_value={'action':'REACHED_NEXT_GATE'})
    result=engine.process_symbol('alias')
    assert result['status']=='BLOCKED_ACTIVE_TRADE'
    engine._gold_smc_entry_gate.assert_not_called()
    positions.clear()
    assert engine.process_symbol('alias')['action']=='REACHED_NEXT_GATE'
    engine._gold_smc_entry_gate.assert_called_once()


def test_lock_blocks_competing_cycle_and_releases(tmp_path):
    with symbol_cycle_lock('X',tmp_path) as first:
        assert first
        with symbol_cycle_lock('X',tmp_path) as second:
            assert not second
        with symbol_cycle_lock('Y',tmp_path) as other:
            assert other
    with symbol_cycle_lock('X',tmp_path) as next_cycle:
        assert next_cycle


def test_mt5_none_is_not_empty_and_magic_is_not_filtered(monkeypatch):
    import brokers.mt5_execution as module
    broker=module.MT5ExecutionProvider(SimpleNamespace(is_connected=lambda:True))
    monkeypatch.setattr(module.mt5,'positions_get',lambda:None)
    monkeypatch.setattr(module.mt5,'last_error',lambda:(-1,'offline'))
    with pytest.raises(module.MT5ExecutionError): broker.get_open_positions()
    row=SimpleNamespace(symbol='X',ticket=1,magic=0)
    monkeypatch.setattr(module.mt5,'positions_get',lambda:(row,))
    monkeypatch.setattr(module.mt5,'orders_get',lambda:())
    assert broker.get_open_positions()==[row]
    assert broker.get_pending_orders()==[]
    monkeypatch.setattr(module.mt5,'orders_get',lambda:None)
    with pytest.raises(module.MT5ExecutionError): broker.get_pending_orders()


def test_guard_telemetry_does_not_count_as_scored_candidate():
    from strategy.smc.telemetry_logger import SMCTelemetryTracker
    tracker=SMCTelemetryTracker()
    tracker.log_pipeline_result(dict(symbol='X',valid=False,action='BLOCKED_PENDING_ORDER',reason='pending'))
    result=tracker.get_summary_report()
    assert result['total_evaluations']==0
    assert result['pipeline_funnel']['stage_counts']['POSITION_GUARD']==1


def test_order_appearing_during_analysis_blocks_final_entry():
    from test_daemon_split_risk_management import Provider,Repo,Executor,Analyzer
    from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig
    executor=Executor()
    executor.get_pending_orders=Mock(side_effect=[[],[dict(symbol='Volatility 90 Index',ticket=99)]])
    engine=LiveTradingEngine(Provider(),Repo(),
        LiveTradingConfig(execution_enabled=False,validate_order_in_dry_run=False,max_entry_drift_r=None),
        executor=executor)
    engine.multi_timeframe=Analyzer()
    engine._smc_entry_preflight=lambda *args: {'valid':True}
    result=engine.process_symbol('Volatility 90 Index')
    assert result['action']=='BLOCKED_PENDING_ORDER'
    assert executor.get_pending_orders.call_count==2


def test_active_trade_dashboard_does_not_restart_entry_analysis():
    from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(bot_profile='STEP')
    engine.repository=SimpleNamespace(open_trades=lambda **kw:[dict(instrument='X',direction='BUY',details={})])
    engine._trade_auditable_by_current_bot=lambda trade:True
    engine.multi_timeframe=SimpleNamespace(analyze_symbol=Mock(side_effect=AssertionError('Entry pipeline must stay paused')))
    engine._persist_audit_event=Mock()
    engine._refresh_current_strategy_views()
    engine.multi_timeframe.analyze_symbol.assert_not_called()
    assert engine._current_strategy_view_cache['X']['entry_analysis_paused']
