import pytest

from position_manager import POSITION_CLOSED, POSITION_OPEN, PositionManager
from strategy.execution.paper_trade_executor import PaperTradeExecutor
from strategy.execution.trade_executor import EXECUTION_STATUS_CLOSED, TradeExecutionRequest


SYMBOL = "Boom 100 Index"
ENTRY_TIME = "2026-08-25 15:00:00+00:00"


def buy_request():
    return TradeExecutionRequest(
        symbol=SYMBOL,
        timeframe="M5",
        direction="BUY",
        entry_time=ENTRY_TIME,
        entry_price=111.0,
        stop_loss=109.0,
        take_profit=115.0,
        volume=0.01,
    )


def sell_request():
    return TradeExecutionRequest(
        symbol=SYMBOL,
        timeframe="M5",
        direction="SELL",
        entry_time=ENTRY_TIME,
        entry_price=111.0,
        stop_loss=113.0,
        take_profit=107.0,
        volume=0.01,
    )


def test_execute_registers_position_in_position_manager():
    print("\nINTEGRACION 1: PAPER EXECUTOR -> POSITION MANAGER")
    manager = PositionManager()
    executor = PaperTradeExecutor(position_manager=manager)
    result = executor.execute_trade(buy_request())

    managed = manager.get_position(result.position_ticket)
    assert managed is not None
    assert managed["status"] == POSITION_OPEN
    assert managed["filled_price"] == 111.0
    assert manager.open_positions_count() == 1
    print("POSICION REGISTRADA AUTOMATICAMENTE: OK")


def test_monitoring_break_even_syncs_stop_loss_to_paper_executor():
    print("\nINTEGRACION 2: BREAK EVEN SINCRONIZADO")
    executor = PaperTradeExecutor()
    result = executor.execute_trade(buy_request())

    monitor = executor.monitor_position(result.position_ticket, 113.0)
    paper = executor.get_position(result.position_ticket)
    managed = executor.position_manager.get_position(result.position_ticket)

    assert monitor["closed"] is False
    assert monitor["action"] == "break_even_activated"
    assert paper["stop_loss"] == 111.0
    assert paper["break_even_activated"] is True
    assert managed["stop_loss"] == 111.0
    assert managed["break_even_activated"] is True
    print("SL PAPER Y MANAGER EN ENTRY: OK")


def test_monitoring_take_profit_closes_paper_and_managed_position():
    print("\nINTEGRACION 3: TAKE PROFIT CIERRA AMBAS CAPAS")
    executor = PaperTradeExecutor()
    result = executor.execute_trade(buy_request())

    monitor = executor.monitor_position(result.position_ticket, 115.0)
    paper = executor.get_position(result.position_ticket)
    managed = executor.position_manager.get_position(result.position_ticket)

    assert monitor["closed"] is True
    assert monitor["action"] == "take_profit"
    assert paper["status"] == EXECUTION_STATUS_CLOSED
    assert paper["exit_price"] == 115.0
    assert paper["exit_reason"] == "take_profit"
    assert managed["status"] == POSITION_CLOSED
    assert managed["exit_price"] == 115.0
    assert managed["realized_pnl_price"] == 4.0
    assert executor.get_open_positions() == []
    print("TAKE PROFIT SINCRONIZADO: OK")


def test_monitoring_break_even_stop_closes_paper_and_managed_position():
    print("\nINTEGRACION 4: BREAK EVEN STOP CIERRA AMBAS CAPAS")
    executor = PaperTradeExecutor()
    result = executor.execute_trade(sell_request())

    executor.monitor_position(result.position_ticket, 109.0)
    monitor = executor.monitor_position(result.position_ticket, 111.0)

    paper = executor.get_position(result.position_ticket)
    managed = executor.position_manager.get_position(result.position_ticket)

    assert monitor["closed"] is True
    assert monitor["action"] == "break_even_stop"
    assert paper["status"] == EXECUTION_STATUS_CLOSED
    assert paper["exit_reason"] == "break_even_stop"
    assert managed["status"] == POSITION_CLOSED
    assert managed["realized_pnl_price"] == 0.0
    print("BREAK EVEN STOP SINCRONIZADO: OK")


def test_manual_close_syncs_position_manager():
    print("\nINTEGRACION 5: CIERRE MANUAL SINCRONIZADO")
    executor = PaperTradeExecutor()
    result = executor.execute_trade(buy_request())

    paper = executor.close_position(
        result.position_ticket,
        exit_price=112.0,
        reason="manual_close",
    )
    managed = executor.position_manager.get_position(result.position_ticket)

    assert paper["status"] == EXECUTION_STATUS_CLOSED
    assert paper["exit_price"] == 112.0
    assert managed["status"] == POSITION_CLOSED
    assert managed["exit_price"] == 112.0
    assert managed["realized_pnl_price"] == 1.0
    print("CIERRE MANUAL SINCRONIZADO: OK")


def test_monitor_multiple_open_positions_through_executor():
    print("\nINTEGRACION 6: MONITOREO MULTIPLE DESDE EXECUTOR")
    executor = PaperTradeExecutor()
    buy = executor.execute_trade(buy_request())
    sell = executor.execute_trade(sell_request())

    results = executor.monitor_open_positions({
        buy.position_ticket: 113.0,
        sell.position_ticket: 109.0,
    })

    assert len(results) == 2
    assert all(item["action"] == "break_even_activated" for item in results)
    assert executor.get_position(buy.position_ticket)["stop_loss"] == 111.0
    assert executor.get_position(sell.position_ticket)["stop_loss"] == 111.0
    print("MONITOREO MULTIPLE Y BREAK EVEN: OK")
