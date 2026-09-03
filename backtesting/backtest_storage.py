from __future__ import annotations

from pathlib import Path
import pandas as pd

from database.repository import TradingRepository
from database.reporting import export_trading_report


def persist_money_management_results(
    file_path: str | Path,
    instrument: str,
    timeframe: str = "M5",
    db_path: str | Path | None = None,
    report_path: str | Path = "storage/exports/trading_report.xlsx",
    strategy_version: str = "smc-v1",
):
    """Importa el CSV financiero a SQLite y genera/actualiza el Excel."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    trades = pd.read_csv(file_path)
    repo = TradingRepository(db_path)
    result = repo.import_backtest_dataframe(
        trades=trades,
        instrument=instrument,
        timeframe=timeframe,
        broker="SIMULATOR",
        strategy_version=strategy_version,
        source="BACKTEST",
    )
    summary = repo.summary(source="BACKTEST")
    report = export_trading_report(
        db_path=db_path,
        output_path=report_path,
        source="BACKTEST",
    )
    return {"import": result, "summary": summary, "report": report}
