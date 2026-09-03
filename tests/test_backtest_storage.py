from pathlib import Path

from backtesting.backtest_storage import persist_money_management_results


MONEY_MANAGEMENT_FILE = Path(
    "storage/analysis/Volatility_90_Index_M5_money_management.csv"
)
INSTRUMENT = "Volatility 90 Index"
TIMEFRAME = "M5"
DB_FILE = Path("database/test_backtest_storage.sqlite3")
REPORT_FILE = Path("storage/exports/test_backtest_storage_report.xlsx")


def main():
    print("=" * 65)
    print("PRUEBA DE PERSISTENCIA BACKTEST -> SQLITE -> EXCEL")
    print("=" * 65)

    if not MONEY_MANAGEMENT_FILE.exists():
        raise FileNotFoundError(
            "Primero ejecuta python -m tests.test_backtest_money_management"
        )

    if DB_FILE.exists():
        DB_FILE.unlink()
    if REPORT_FILE.exists():
        REPORT_FILE.unlink()

    result = persist_money_management_results(
        file_path=MONEY_MANAGEMENT_FILE,
        instrument=INSTRUMENT,
        timeframe=TIMEFRAME,
        db_path=DB_FILE,
        report_path=REPORT_FILE,
        strategy_version="smc-v1-backtest-aug-2026",
    )

    print()
    print("IMPORTACIÓN")
    print(f"Nuevas operaciones: {result['import']['created']}")
    print(f"Operaciones existentes: {result['import']['existing']}")

    print()
    print("RESUMEN SQLITE")
    for key, value in result["summary"].items():
        print(f"{key}: {value}")

    print()
    print(f"Base de datos: {DB_FILE}")
    print(f"Reporte Excel: {result['report']}")

    # Ejecutar una segunda vez no debe duplicar operaciones.
    second = persist_money_management_results(
        file_path=MONEY_MANAGEMENT_FILE,
        instrument=INSTRUMENT,
        timeframe=TIMEFRAME,
        db_path=DB_FILE,
        report_path=REPORT_FILE,
        strategy_version="smc-v1-backtest-aug-2026",
    )
    print()
    print("VALIDACIÓN IDEMPOTENTE")
    print(f"Segunda ejecución - nuevas: {second['import']['created']}")
    print(f"Segunda ejecución - existentes: {second['import']['existing']}")


if __name__ == "__main__":
    main()
