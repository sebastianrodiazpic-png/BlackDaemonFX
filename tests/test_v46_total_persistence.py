
import pandas as pd

from database.repository import TradingRepository
from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService
from strategy.execution.paper_trade_executor import PaperTradeExecutor
from trade_lifecycle_manager import TradeLifecycleManager


def signal():
    return {
        "symbol": "EURUSD",
        "timeframe": "M5",
        "direction": "BUY",
        "entry_time": pd.Timestamp("2026-08-31 12:00:00+00:00"),
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
        "risk_reward_ratio": 2.0,
        "action": "SMC_FOREX_CONFIRMED",
    }


def test_audit_event_is_append_only_and_queryable(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "audit.db")
    first = repo.save_audit_event(
        "SYMBOL_PROCESS_RESULT",
        source="DEMO",
        instrument="EURUSD",
        action="NO_SIGNAL",
        reason="WAITING_M5",
        payload={"cycle": 1},
    )
    second = repo.save_audit_event(
        "SYMBOL_PROCESS_RESULT",
        source="DEMO",
        instrument="EURUSD",
        action="ORDER_OPENED",
        payload={"cycle": 2},
    )
    assert second > first
    frame = repo.audit_events_dataframe(source="DEMO")
    assert len(frame) == 2
    assert list(frame["action"]) == ["NO_SIGNAL", "ORDER_OPENED"]


def test_filled_lifecycle_persists_trade_journal_and_audit(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "filled.db")
    service = TradeReportingService(
        repository=repo,
        config=TradeReportingConfig(
            source="DEMO",
            output_path=tmp_path / "report.xlsx",
            auto_export=False,
            broker="PAPER",
        ),
    )
    manager = TradeLifecycleManager(
        trade_executor=PaperTradeExecutor(),
        reporting_service=service,
    )
    lifecycle = manager.process_signal_with_executor(signal(), volume=0.10)

    trades = repo.trades_dataframe(source="DEMO")
    journal = repo.trade_history_dataframe(source="DEMO")
    audit = repo.audit_events_dataframe(source="DEMO")

    assert len(trades) == 1
    assert len(journal) == 1
    assert lifecycle.position_ticket is not None
    assert str(journal.iloc[0]["broker_position_ticket"]) == str(lifecycle.position_ticket)
    assert "LIFECYCLE_EXECUTION_FILLED" in set(audit["event_type"].astype(str))


def test_instrument_selection_also_generates_audit_event(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "selection.db")
    repo.save_instrument_selection(["EURUSD", "GBPUSD"], source="DEMO")
    audit = repo.audit_events_dataframe(source="DEMO")
    assert "INSTRUMENT_SELECTION_CHANGED" in set(audit["event_type"].astype(str))


def test_xlsx_contains_permanent_trades_and_audit_log(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "xlsx.db")
    service = TradeReportingService(
        repository=repo,
        config=TradeReportingConfig(
            source="DEMO",
            output_path=tmp_path / "deriv_demo_trading_report.xlsx",
            auto_export=False,
            broker="PAPER",
        ),
    )
    manager = TradeLifecycleManager(
        trade_executor=PaperTradeExecutor(),
        reporting_service=service,
    )
    manager.process_signal_with_executor(signal(), volume=0.10)
    repo.save_audit_event(
        "TEST_AUDIT",
        source="DEMO",
        instrument="EURUSD",
        action="PERSISTED",
    )

    service.export_now()
    workbook = pd.ExcelFile(tmp_path / "deriv_demo_trading_report.xlsx")
    assert "Trades" in workbook.sheet_names
    assert "Audit Log" in workbook.sheet_names

    trades = pd.read_excel(tmp_path / "deriv_demo_trading_report.xlsx", sheet_name="Trades")
    audit = pd.read_excel(tmp_path / "deriv_demo_trading_report.xlsx", sheet_name="Audit Log")
    assert len(trades) == 1
    assert len(audit) >= 2
