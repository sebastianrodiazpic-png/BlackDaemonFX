from pathlib import Path

import pandas as pd

from database.repository import TradingRepository
from reporting.trade_report_exporter import TradeReportExporter


def test_export_trade_report(tmp_path):

    print("=" * 80)
    print("TEST 1")
    print("EXPORTAR OPERACIONES A XLSX")
    print("=" * 80)

    db_path = tmp_path / "test_trading.db"

    repository = TradingRepository(
        db_path=db_path
    )

    repository.create_trade(
        {
            "external_ticket": "TEST-ORDER-001",
            "execution_key": "TEST-EXECUTION-001",
            "source": "DEMO",
            "broker": "Deriv-Demo",
            "instrument": "Boom 100 Index",
            "timeframe": "M5",
            "direction": "BUY",
            "status": "OPEN",
            "result": "OPEN",
            "entry_price": 1000.0,
            "stop_loss": 990.0,
            "take_profit": 1020.0,
            "volume": 0.01,
            "planned_rr": 2.0,
            "risk_percent": 1.0,
            "risk_amount": 10.0,
        }
    )

    output_path = (
        tmp_path
        / "deriv_demo_trades.xlsx"
    )

    exporter = TradeReportExporter(
        repository=repository,
        output_path=output_path
    )

    result = exporter.export(
        source="DEMO"
    )

    assert output_path.exists()

    assert result["total_trades"] == 1
    assert result["open_positions"] == 1

    excel_file = pd.ExcelFile(
        output_path
    )

    expected_sheets = {
        "Trades",
        "Open Positions",
        "Summary",
        "Instruments",
        "Account",
        "Metadata",
    }

    assert expected_sheets.issubset(
        set(excel_file.sheet_names)
    )

    trades = pd.read_excel(
        output_path,
        sheet_name="Trades"
    )

    assert len(trades) == 1
    assert trades.iloc[0]["instrument"] == (
        "Boom 100 Index"
    )

    print()
    print("XLSX GENERADO: OK")
    print(
        f"ARCHIVO: {output_path}"
    )
    print(
        f"TRADES: {result['total_trades']}"
    )
    print(
        f"OPEN POSITIONS: "
        f"{result['open_positions']}"
    )