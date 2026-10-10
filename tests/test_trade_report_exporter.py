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


def test_export_trade_report_with_huge_cell_contents_sanitized(tmp_path, recwarn):
    """Verifica que celdas con más de 32.767 caracteres (límite Excel) no emitan UserWarning ni fallen."""
    db_path = tmp_path / "test_huge.db"
    repository = TradingRepository(db_path=db_path)

    # Creamos un payload JSON masivo de 50.000 caracteres
    huge_json = '{"analysis": "' + ("A" * 50000) + '"}'

    repository.create_trade(
        {
            "external_ticket": "TEST-HUGE-001",
            "execution_key": "TEST-HUGE-001",
            "source": "DEMO",
            "broker": "Deriv-Demo",
            "instrument": "Boom 1000 Index",
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
            "details_json": huge_json,
        }
    )

    output_path = tmp_path / "huge_test_trades.xlsx"
    exporter = TradeReportExporter(repository=repository, output_path=output_path)

    result = exporter.export(source="DEMO")
    assert output_path.exists()
    assert result["total_trades"] == 1

    # Verificar que no se emitió ninguna advertencia de UserWarning de openpyxl
    cell_warnings = [
        w for w in recwarn if issubclass(w.category, UserWarning) and "Cell contents too long" in str(w.message)
    ]
    assert len(cell_warnings) == 0, f"Se emitieron warnings de openpyxl: {cell_warnings}"

    # Verificar que el contenido en Excel se lee limpiamente y no excede el límite
    trades = pd.read_excel(output_path, sheet_name="Trades")
    assert len(trades) == 1
    if "details_json" in trades.columns:
        cell_val = str(trades.iloc[0]["details_json"])
        assert len(cell_val) <= 32767
        assert "TRUNCADO_EXCEL" in cell_val