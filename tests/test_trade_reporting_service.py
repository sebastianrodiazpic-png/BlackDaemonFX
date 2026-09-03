from pathlib import Path

import pandas as pd

from database.repository import TradingRepository
from reporting.trade_reporting_service import (
    TradeReportingConfig,
    TradeReportingService,
)
from strategy.execution.paper_trade_executor import PaperTradeExecutor
from trade_lifecycle_manager import (
    STATE_BREAK_EVEN,
    STATE_EXECUTION,
    TradeLifecycleManager,
)


def create_signal():
    return {
        "symbol": "Boom 100 Index",
        "timeframe": "M5",
        "direction": "BUY",
        "entry_time": pd.Timestamp("2026-08-26 15:00:00+00:00"),
        "entry_price": 100.0,
        "stop_loss": 98.0,
        "take_profit": 104.0,
        "risk_reward_ratio": 2.0,
        "action": "MULTI_TIMEFRAME_SIGNAL",
    }


def test_paper_lifecycle_is_persisted_and_exported(tmp_path):
    print()
    print("=" * 80)
    print("TEST: TRADE REPORTING SERVICE + TRADE LIFECYCLE MANAGER")
    print("=" * 80)

    db_path = tmp_path / "paper_trading.db"
    xlsx_path = tmp_path / "paper_trading_report.xlsx"

    repository = TradingRepository(db_path=db_path)
    reporting_service = TradeReportingService(
        repository=repository,
        config=TradeReportingConfig(
            source="PAPER",
            output_path=xlsx_path,
            auto_export=True,
            broker="PAPER",
        ),
    )

    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(
        trade_executor=executor,
        reporting_service=reporting_service,
    )

    lifecycle = manager.process_signal_with_executor(
        signal=create_signal(),
        volume=0.5,
    )

    assert lifecycle.state == STATE_EXECUTION
    assert lifecycle.position_ticket is not None

    open_trades = repository.open_trades(source="PAPER")
    assert len(open_trades) == 1

    trade = open_trades[0]
    assert trade["instrument"] == "Boom 100 Index"
    assert trade["direction"] == "BUY"
    assert trade["status"] == "OPEN"
    assert trade["broker_position_ticket"] == lifecycle.position_ticket
    assert trade["volume"] == 0.5
    assert xlsx_path.exists()

    # 1R alcanzado: SL debe moverse a break-even y el cambio se persiste.
    manager.monitor_execution(
        lifecycle=lifecycle,
        current_price=102.0,
    )

    persisted_open = repository.get_trade_by_position_ticket(
        lifecycle.position_ticket
    )
    assert persisted_open["stop_loss"] == 100.0

    # Regreso al precio de entrada: cierre BREAK_EVEN.
    manager.monitor_execution(
        lifecycle=lifecycle,
        current_price=100.0,
    )

    assert lifecycle.state == STATE_BREAK_EVEN

    persisted = repository.get_trade_by_position_ticket(
        lifecycle.position_ticket
    )
    assert persisted["status"] == "CLOSED"
    assert persisted["result"] == "BREAK_EVEN"
    assert persisted["exit_reason"] == "break_even_stop"
    assert persisted["exit_price"] == 100.0
    assert xlsx_path.exists()

    workbook = pd.ExcelFile(xlsx_path)
    assert "Trades" in workbook.sheet_names
    assert "Open Positions" in workbook.sheet_names
    assert "Summary" in workbook.sheet_names

    trades_df = pd.read_excel(
        xlsx_path,
        sheet_name="Trades",
    )
    assert len(trades_df) == 1
    assert str(trades_df.iloc[0]["status"]).upper() == "CLOSED"

    print("OPERACIÓN PAPER REGISTRADA EN SQLITE: OK")
    print(f"TICKET: {lifecycle.position_ticket}")
    print(f"ESTADO FINAL: {lifecycle.state}")
    print(f"XLSX: {xlsx_path}")
