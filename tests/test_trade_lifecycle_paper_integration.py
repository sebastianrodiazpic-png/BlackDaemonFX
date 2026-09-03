import pandas as pd
import pytest

from strategy.execution.paper_trade_executor import PaperTradeExecutor
from trade_lifecycle_manager import (
    STATE_BREAK_EVEN,
    STATE_EXECUTION,
    STATE_LOSS,
    STATE_WIN,
    TradeLifecycleManager,
)


def signal(direction="BUY"):
    if direction == "BUY":
        return {
            "action": "MULTI_TIMEFRAME_SIGNAL",
            "symbol": "TEST_SYMBOL",
            "m5_timeframe": "M5",
            "direction": "BUY",
            "entry_time": pd.Timestamp("2026-08-25 15:00:00+00:00"),
            "entry_price": 111.0,
            "stop_loss": 109.0,
            "take_profit": 115.0,
            "risk_reward_ratio": 2.0,
        }
    return {
        "action": "MULTI_TIMEFRAME_SIGNAL",
        "symbol": "TEST_SYMBOL",
        "m5_timeframe": "M5",
        "direction": "SELL",
        "entry_time": pd.Timestamp("2026-08-25 15:00:00+00:00"),
        "entry_price": 111.0,
        "stop_loss": 113.0,
        "take_profit": 107.0,
        "risk_reward_ratio": 2.0,
    }


def test_full_paper_lifecycle_open_and_break_even():
    print("\nTEST 1 - READY_TO_ENTER -> PAPER EXECUTION -> BREAK EVEN")
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)

    lifecycle = manager.process_signal_with_executor(signal(), volume=1.0)

    assert lifecycle.state == STATE_EXECUTION
    assert lifecycle.position_ticket == "PAPER-000001"
    assert manager.get_active_lifecycle(lifecycle.position_ticket) is lifecycle
    assert executor.get_position(lifecycle.position_ticket)["status"] == "FILLED"

    monitor = manager.monitor_execution(lifecycle, 113.0)
    assert monitor["closed"] is False
    assert monitor["action"] == "break_even_activated"
    assert lifecycle.stop_loss == 111.0
    assert lifecycle.metadata["break_even_activated"] is True
    assert lifecycle.state == STATE_EXECUTION
    print("BREAK EVEN SINCRONIZADO: OK")


def test_full_paper_lifecycle_take_profit_to_win_and_history():
    print("\nTEST 2 - PAPER EXECUTION -> TAKE PROFIT -> WIN")
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)
    lifecycle = manager.process_signal_with_executor(signal())

    monitor = manager.monitor_execution(lifecycle, 115.0)

    assert monitor["closed"] is True
    assert lifecycle.state == STATE_WIN
    assert lifecycle.result == "win"
    assert lifecycle.exit_reason == "take_profit"
    assert lifecycle.exit_price == 115.0
    assert lifecycle.pnl_price == 4.0
    assert manager.get_active_lifecycles() == []
    assert manager.get_completed_trades() == [lifecycle]
    print("WIN E HISTORIAL: OK")


def test_full_paper_lifecycle_stop_loss_to_loss():
    print("\nTEST 3 - PAPER EXECUTION -> STOP LOSS -> LOSS")
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)
    lifecycle = manager.process_signal_with_executor(signal())

    monitor = manager.monitor_execution(lifecycle, 109.0)

    assert monitor["closed"] is True
    assert lifecycle.state == STATE_LOSS
    assert lifecycle.result == "loss"
    assert lifecycle.exit_reason == "stop_loss"
    assert lifecycle.exit_price == 109.0
    assert lifecycle.pnl_price == -2.0
    print("LOSS SINCRONIZADO: OK")


def test_full_paper_lifecycle_break_even_stop_is_final():
    print("\nTEST 4 - PAPER EXECUTION -> BREAK EVEN -> BREAK EVEN STOP")
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)
    lifecycle = manager.process_signal_with_executor(signal())

    manager.monitor_execution(lifecycle, 113.0)
    monitor = manager.monitor_execution(lifecycle, 111.0)

    assert monitor["closed"] is True
    assert lifecycle.state == STATE_BREAK_EVEN
    assert lifecycle.result == "break_even"
    assert lifecycle.exit_reason == "break_even_stop"
    assert lifecycle.exit_price == 111.0
    assert lifecycle.pnl_price == 0.0
    assert lifecycle in manager.get_completed_trades()
    print("BREAK EVEN STOP FINAL: OK")


def test_monitor_multiple_active_lifecycles():
    print("\nTEST 5 - MONITOREAR MULTIPLES LIFECYCLES ACTIVOS")
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)

    buy = manager.process_signal_with_executor(signal("BUY"))
    sell = manager.process_signal_with_executor(signal("SELL"))

    results = manager.monitor_open_executions({
        buy.position_ticket: 113.0,
        sell.position_ticket: 109.0,
    })

    assert len(results) == 2
    assert all(item["action"] == "break_even_activated" for item in results)
    assert buy.stop_loss == 111.0
    assert sell.stop_loss == 111.0
    assert len(manager.get_active_lifecycles()) == 2
    print("MULTI POSITION MONITORING: OK")


def test_rejected_executor_result_does_not_create_active_lifecycle():
    print("\nTEST 6 - EJECUCION RECHAZADA NO CREA POSICION ACTIVA")
    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(trade_executor=executor)
    lifecycle = manager.create_from_signal(signal())

    with pytest.raises(ValueError):
        manager.execute_with_executor(lifecycle, volume=0.0)

    assert lifecycle.position_ticket is None
    assert manager.get_active_lifecycles() == []
    print("EJECUCION INVALIDA BLOQUEADA: OK")
