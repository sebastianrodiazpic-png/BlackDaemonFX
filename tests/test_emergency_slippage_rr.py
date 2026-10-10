import pytest
from types import SimpleNamespace
from unittest.mock import Mock
from datetime import datetime, timezone

from brokers.mt5_execution import MT5ExecutionProvider, MT5ExecutionError
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from test_demo_daemon_integration import ExecutionRepo, Provider, Executor, FakeLifecycleManager


def test_pre_send_rr_blocked_universal_for_malaysian_snr_and_smc():
    """Verifica que señales con R:R ejecutable menor a 1.0 son bloqueadas antes de enviarse al broker."""
    p = MT5ExecutionProvider.__new__(MT5ExecutionProvider)
    # Simula la situación del SP500:
    # Ask mercado: 7836.70, SL: 7826.02, TP: 7838.86 -> R:R = 2.16 / 10.68 = 0.202
    req = {'price': 7836.70, 'sl': 7826.02, 'tp': 7838.86}
    
    with pytest.raises(MT5ExecutionError, match='PRE_SEND_RR_BLOCKED'):
        p._validate_executable_rr(req, 'BUY', 1.0)

    # Con precio respetando R:R >= 1.0 (ej. Ask: 7830.0, SL: 7826.0, TP: 7838.0 -> 8.0/4.0 = 2.0)
    req_good = {'price': 7830.0, 'sl': 7826.0, 'tp': 7838.0}
    res = p._validate_executable_rr(req_good, 'BUY', 1.0)
    assert res['executable_rr'] == 2.0


def test_immediate_post_fill_emergency_close_when_rr_unfavorable():
    """Si una orden se llena con R:R < min_acceptable_fill_rr por slippage severo,
    el motor debe forzar el cierre inmediato y disparar rollback."""
    repo = ExecutionRepo()
    close_mock = Mock(return_value={'closed': True, 'ticket': 9999})
    
    class SlippageManager(FakeLifecycleManager):
        def __init__(self):
            super().__init__()
            self.close_execution = close_mock

        def execute_with_executor(self, lifecycle, volume):
            # Simula fill con slippage extremo que reduce el R:R a ~0.15 (entry filled at 116 vs sl 90, tp 120)
            lifecycle.execution_status = 'FILLED'
            lifecycle.position_ticket = '9999'
            lifecycle.entry_price = 116.0
            return lifecycle

    provider = Provider()
    provider.get_current_tick = lambda symbol: {'bid': 100.0, 'ask': 100.0}

    executor = Executor()
    executor.normalize_market_stops = lambda symbol, direction, entry, sl, rr, **kw: {
        'valid': True,
        'entry_price': 100.0,
        'stop_loss': 90.0,
        'take_profit': 120.0,
    }

    manager = SlippageManager()
    config = LiveTradingConfig(
        bot_profile='MALAYSIAN_SNR',
        execution_enabled=True,
        max_entry_drift_r=None,
        min_acceptable_fill_rr=1.0,
        emergency_unfavorable_rr_exit_enabled=True,
        meta_labeling_mode="SHADOW",
    )
    engine = LiveTradingEngine(
        provider=provider,
        repository=repo,
        executor=executor,
        lifecycle_manager=manager,
        config=config,
    )

    now = datetime.now(timezone.utc).isoformat()
    signal = {
        'strategy_name': 'MALAYSIAN_SNR',
        'direction': 'BUY',
        'entry_time': now,
        'entry_price': 100.0,
        'stop_loss': 90.0,
        'take_profit': 120.0,
        'risk_reward_ratio': 2.0,
    }
    engine.malaysian_snr_strategy = SimpleNamespace(
        analyze_symbol=lambda *a, **k: {'valid': True, 'strategy_name': 'MALAYSIAN_SNR', 'signal': signal},
        mark_signal_used=Mock(),
    )
    engine._enrich_learning_indicators = Mock()

    result = engine._process_symbol_guarded('US SP 500')
    assert result['action'] == 'EMERGENCY_SLIPPAGE_EXIT'
    assert 'FILLED_RR_BELOW_MINIMUM' in result['reason']
    assert result['filled_target_rr'] < 1.0
    close_mock.assert_called_once()
    assert close_mock.call_args[1]['reason'] == 'emergency_slippage_unfavorable_rr'


def test_daemon_monitoring_invalidation_closes_unfavorable_rr_position():
    """El bucle de monitoreo continuo detecta posiciones con R:R desfavorable y las cierra."""
    repo = ExecutionRepo()
    close_mock = Mock(return_value={'closed': True})

    config = LiveTradingConfig(
        bot_profile='MALAYSIAN_SNR',
        execution_enabled=True,
        emergency_unfavorable_rr_exit_enabled=True,
        min_acceptable_fill_rr=1.0,
    )
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        executor=Executor(),
        lifecycle_manager=SimpleNamespace(),
        config=config,
    )

    trade = {'instrument': 'US SP 500', 'direction': 'BUY'}
    metadata = {
        'strategy_name': 'MALAYSIAN_SNR',
        'execution_rr_audit': {
            'filled_target_rr': 0.202,
            'planned_target_rr': 2.0,
        }
    }

    result = engine._analysis_invalidation_exit(
        trade=trade,
        metadata=metadata,
        current_rr=-0.1,
        close_position=close_mock,
    )
    assert result['managed'] is True
    assert result['closed'] is True
    assert 'EMERGENCY_SLIPPAGE_EXIT' in result['reason']
    close_mock.assert_called_once_with('emergency_slippage_unfavorable_rr')


def test_direct_executor_fallback_pathway_closes_unfavorable_fill():
    """En la ruta sin lifecycle_manager, si la orden se llena con R:R desfavorable, se fuerza el cierre."""
    repo = ExecutionRepo()
    close_position_mock = Mock(return_value={'closed': True})

    provider = Provider()
    provider.get_current_tick = lambda symbol: {'bid': 100.0, 'ask': 100.0}

    executor = Executor()
    executor.normalize_market_stops = lambda symbol, direction, entry, sl, rr, **kw: {
        'valid': True,
        'entry_price': 100.0,
        'stop_loss': 90.0,
        'take_profit': 120.0,
    }
    executor.place_market_order = Mock(return_value={
        'order_ticket': 111,
        'deal_ticket': 222,
        'entry_price': 116.0,
        'filled_volume': 0.1,
    })
    executor.find_position_ticket = Mock(return_value='333')
    executor.close_position = close_position_mock

    config = LiveTradingConfig(
        bot_profile='MALAYSIAN_SNR',
        execution_enabled=True,
        max_entry_drift_r=None,
        min_acceptable_fill_rr=1.0,
        emergency_unfavorable_rr_exit_enabled=True,
        meta_labeling_mode="SHADOW",
    )
    engine = LiveTradingEngine(
        provider=provider,
        repository=repo,
        executor=executor,
        lifecycle_manager=None,
        config=config,
    )

    now = datetime.now(timezone.utc).isoformat()
    signal = {
        'strategy_name': 'MALAYSIAN_SNR',
        'direction': 'BUY',
        'entry_time': now,
        'entry_price': 100.0,
        'stop_loss': 90.0,
        'take_profit': 120.0,
        'risk_reward_ratio': 2.0,
    }
    engine.malaysian_snr_strategy = SimpleNamespace(
        analyze_symbol=lambda *a, **k: {'valid': True, 'strategy_name': 'MALAYSIAN_SNR', 'signal': signal},
        mark_signal_used=Mock(),
    )
    engine._enrich_learning_indicators = Mock()

    result = engine._process_symbol_guarded('US SP 500')
    assert result['action'] == 'EMERGENCY_SLIPPAGE_EXIT'
    assert 'FILLED_RR_BELOW_MINIMUM' in result['reason']
    assert result['filled_target_rr'] < 1.0
    close_position_mock.assert_called_once_with('333')
