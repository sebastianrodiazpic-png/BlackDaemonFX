import os
import pandas as pd

from backtesting.backtest_money_management import (
    apply_money_management,
    get_money_management_summary,
    save_money_management_results
)
from backtesting.backtest_storage import persist_money_management_results


# ==================================================
# CONFIGURACIÓN
# ==================================================

INITIAL_BALANCE = 1000.0

RISK_PERCENT = 1.0

COMPOUND = True

INSTRUMENT = "Volatility 90 Index"
TIMEFRAME = "M5"
DB_FILE = "database/trading_bot.sqlite3"
REPORT_FILE = "storage/exports/trading_report.xlsx"


# ==================================================
# RUTAS
# ==================================================

BACKTEST_FILE = (
    "storage/analysis/"
    "Volatility_90_Index_M5_backtest.csv"
)

OUTPUT_FILE = (
    "storage/analysis/"
    "Volatility_90_Index_M5_money_management.csv"
)


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 65)
    print("BACKTEST MONEY MANAGEMENT")
    print("=" * 65)

    print()
    print(
        f"Archivo backtest: {BACKTEST_FILE}"
    )

    print(
        f"Capital inicial: ${INITIAL_BALANCE:.2f}"
    )

    print(
        f"Riesgo por operación: {RISK_PERCENT:.2f}%"
    )

    print(
        f"Interés compuesto: {COMPOUND}"
    )

    # ==============================================
    # VERIFICAR ARCHIVO
    # ==============================================

    if not os.path.exists(BACKTEST_FILE):

        print()
        print(
            "ERROR: No se encontró "
            "el archivo de backtest."
        )

        print(
            BACKTEST_FILE
        )

        return

    # ==============================================
    # CARGAR BACKTEST
    # ==============================================

    print()
    print("Cargando operaciones...")

    trades = pd.read_csv(
        BACKTEST_FILE
    )

    print(
        f"Operaciones cargadas: {len(trades)}"
    )

    # ==============================================
    # VALIDAR COLUMNAS
    # ==============================================

    print()
    print("Columnas disponibles:")

    for column in trades.columns:

        print(
            f" - {column}"
        )

    # ==============================================
    # APLICAR MONEY MANAGEMENT
    # ==============================================

    print()
    print(
        "Aplicando gestión monetaria..."
    )

    managed_trades = apply_money_management(
        trades=trades,
        initial_balance=INITIAL_BALANCE,
        risk_percent=RISK_PERCENT,
        compound=COMPOUND
    )

    # ==============================================
    # RESUMEN
    # ==============================================

    summary = get_money_management_summary(
        trades=managed_trades,
        initial_balance=INITIAL_BALANCE
    )

    # ==============================================
    # MOSTRAR RESUMEN
    # ==============================================

    print()
    print("=" * 65)
    print("RESUMEN FINANCIERO")
    print("=" * 65)

    print(
        f"Capital inicial: "
        f"${summary['initial_balance']:.2f}"
    )

    print(
        f"Capital final: "
        f"${summary['final_balance']:.2f}"
    )

    print(
        f"Ganancia/Pérdida neta: "
        f"${summary['net_profit']:.2f}"
    )

    print(
        f"Rentabilidad: "
        f"{summary['net_profit_percent']:.2f}%"
    )

    print(
        f"Ganancia bruta: "
        f"${summary['gross_profit']:.2f}"
    )

    print(
        f"Pérdida bruta: "
        f"${summary['gross_loss']:.2f}"
    )

    print(
        f"Profit Factor: "
        f"{summary['profit_factor']:.4f}"
    )

    print(
        f"Drawdown máximo: "
        f"${summary['max_drawdown_amount']:.2f}"
    )

    print(
        f"Drawdown máximo %: "
        f"{summary['max_drawdown_percent']:.2f}%"
    )

    print(
        f"Riesgo total operado: "
        f"${summary['total_risk_amount']:.2f}"
    )

    # ==============================================
    # MOSTRAR OPERACIONES
    # ==============================================

    print()
    print("=" * 65)
    print("DETALLE DE OPERACIONES")
    print("=" * 65)

    columns_to_show = [

        "trade_number",

        "entry_time",

        "direction",

        "result",

        "realized_rr",

        "balance_before",

        "risk_amount",

        "pnl",

        "balance_after",

        "drawdown_percent"

    ]

    existing_columns = [

        column
        for column in columns_to_show
        if column in managed_trades.columns

    ]

    print()

    print(
        managed_trades[
            existing_columns
        ].to_string(
            index=False
        )
    )

    # ==============================================
    # GUARDAR
    # ==============================================

    print()
    print("=" * 65)
    print("GUARDANDO RESULTADOS")
    print("=" * 65)

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    saved_file = save_money_management_results(
        trades=managed_trades,
        file_path=OUTPUT_FILE
    )

    print()
    print(
        "Resultados guardados en:"
    )

    print(
        saved_file
    )

    # ==============================================
    # PERSISTIR EN SQLITE Y GENERAR EXCEL
    # ==============================================

    print()
    print("=" * 65)
    print("GUARDANDO EN BASE DE DATOS Y GENERANDO EXCEL")
    print("=" * 65)

    persistence = persist_money_management_results(
        file_path=saved_file,
        instrument=INSTRUMENT,
        timeframe=TIMEFRAME,
        db_path=DB_FILE,
        report_path=REPORT_FILE,
        strategy_version="smc-v1-backtest-aug-2026"
    )

    print(f"Nuevas operaciones SQLite: {persistence['import']['created']}")
    print(f"Operaciones ya existentes: {persistence['import']['existing']}")
    print(f"Excel generado: {persistence['report']}")

    print()
    print("=" * 65)
    print("PROCESO FINALIZADO")
    print("=" * 65)


# ==================================================
# EJECUTAR
# ==================================================

if __name__ == "__main__":

    main()