import os
import pandas as pd

from backtesting.trade_simulator import (
    simulate_all_trades,
    get_backtest_summary
)


# ==================================================
# CONFIGURACIÓN
# ==================================================

HISTORICAL_FILE = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)

ENTRIES_FILE = (
    "storage/analysis/"
    "Volatility_90_Index_M5_confirmations.csv"
)

OUTPUT_FILE = (
    "storage/analysis/"
    "Volatility_90_Index_M5_backtest.csv"
)


# ==================================================
# FORMATEAR NÚMEROS
# ==================================================

def format_number(value, decimals=2):

    if value is None:
        return "-"

    try:
        if pd.isna(value):
            return "-"
    except Exception:
        pass

    return f"{float(value):.{decimals}f}"


# ==================================================
# MOSTRAR RESUMEN
# ==================================================

def print_summary(summary):

    print()
    print("=" * 65)
    print("RESULTADO DEL BACKTEST")
    print("=" * 65)

    print(f"total_trades: {summary['total_trades']}")
    print(f"closed_trades: {summary['closed_trades']}")
    print(f"wins: {summary['wins']}")
    print(f"losses: {summary['losses']}")
    print(f"open: {summary['open']}")
    print(f"ambiguous: {summary['ambiguous']}")
    print(f"win_rate: {summary['win_rate']}%")
    print(
        f"average_planned_rr: "
        f"{summary['average_planned_rr']:.4f}R"
    )
    print(
        f"average_realized_rr: "
        f"{summary['average_realized_rr']:.4f}R"
    )
    print(
        f"total_realized_r: "
        f"{summary['total_realized_r']:.4f}R"
    )


# ==================================================
# MOSTRAR OPERACIONES
# ==================================================

def print_trades(title, trades):

    print()
    print("=" * 65)
    print(title)
    print("=" * 65)

    if trades.empty:

        print("No hay operaciones.")

        return

    columns = [
        "entry_time",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit",
        "planned_rr",
        "result",
        "realized_rr",
        "exit_time",
        "exit_price",
        "bars_held",
        "reason"
    ]

    available_columns = [
        column
        for column in columns
        if column in trades.columns
    ]

    display_df = trades[
        available_columns
    ].copy()

    # ==============================================
    # FORMATEAR PRECIOS
    # ==============================================

    price_columns = [
        "entry_price",
        "stop_loss",
        "take_profit",
        "exit_price"
    ]

    for column in price_columns:

        if column in display_df.columns:

            display_df[column] = (
                display_df[column]
                .apply(
                    lambda x: format_number(
                        x,
                        3
                    )
                )
            )

    # ==============================================
    # FORMATEAR R:R
    # ==============================================

    rr_columns = [
        "planned_rr",
        "realized_rr"
    ]

    for column in rr_columns:

        if column in display_df.columns:

            display_df[column] = (
                display_df[column]
                .apply(
                    lambda x: (
                        "-"
                        if pd.isna(x)
                        else f"{float(x):.4f}R"
                    )
                )
            )

    print(
        display_df.to_string(
            index=False
        )
    )


# ==================================================
# MOSTRAR ESTADÍSTICAS FINANCIERAS EN R
# ==================================================

def print_rr_statistics(trades):

    print()
    print("=" * 65)
    print("ESTADÍSTICAS DE R:R")
    print("=" * 65)

    closed_trades = trades[
        trades["result"].isin(
            ["WIN", "LOSS"]
        )
    ].copy()

    if closed_trades.empty:

        print(
            "No hay operaciones cerradas "
            "para calcular estadísticas."
        )

        return

    # ==============================================
    # GANANCIAS EN R
    # ==============================================

    wins = closed_trades[
        closed_trades["result"] == "WIN"
    ]

    losses = closed_trades[
        closed_trades["result"] == "LOSS"
    ]

    average_win_r = 0.0
    average_loss_r = 0.0

    if not wins.empty:

        average_win_r = (
            wins["realized_rr"].mean()
        )

    if not losses.empty:

        average_loss_r = (
            losses["realized_rr"].mean()
        )

    total_win_r = 0.0
    total_loss_r = 0.0

    if not wins.empty:

        total_win_r = (
            wins["realized_rr"].sum()
        )

    if not losses.empty:

        total_loss_r = (
            losses["realized_rr"].sum()
        )

    # ==============================================
    # PROFIT FACTOR EN R
    # ==============================================

    gross_profit = total_win_r
    gross_loss = abs(total_loss_r)

    if gross_loss > 0:

        profit_factor = (
            gross_profit / gross_loss
        )

    else:

        profit_factor = 0.0

    # ==============================================
    # EXPECTANCY
    # ==============================================

    win_rate = (
        len(wins) / len(closed_trades)
    )

    loss_rate = (
        len(losses) / len(closed_trades)
    )

    expectancy_r = (
        (win_rate * average_win_r)
        +
        (loss_rate * average_loss_r)
    )

    print(
        f"Operaciones cerradas: "
        f"{len(closed_trades)}"
    )

    print(
        f"Operaciones ganadoras: "
        f"{len(wins)}"
    )

    print(
        f"Operaciones perdedoras: "
        f"{len(losses)}"
    )

    print(
        f"R promedio ganador: "
        f"{average_win_r:.4f}R"
    )

    print(
        f"R promedio perdedor: "
        f"{average_loss_r:.4f}R"
    )

    print(
        f"Total ganado: "
        f"{total_win_r:.4f}R"
    )

    print(
        f"Total perdido: "
        f"{total_loss_r:.4f}R"
    )

    print(
        f"Profit Factor: "
        f"{profit_factor:.4f}"
    )

    print(
        f"Expectancy: "
        f"{expectancy_r:.4f}R "
        f"por operación"
    )


# ==================================================
# VALIDAR ARCHIVOS
# ==================================================

def validate_files():

    if not os.path.exists(
        HISTORICAL_FILE
    ):

        raise FileNotFoundError(
            "No se encontró el histórico:\n"
            f"{HISTORICAL_FILE}"
        )

    if not os.path.exists(
        ENTRIES_FILE
    ):

        raise FileNotFoundError(
            "No se encontró el archivo "
            "de entradas:\n"
            f"{ENTRIES_FILE}"
        )


# ==================================================
# CARGAR DATOS
# ==================================================

def load_data():

    print()
    print("Cargando histórico...")

    candles = pd.read_csv(
        HISTORICAL_FILE
    )

    print(
        f"Histórico cargado: "
        f"{len(candles)} velas"
    )

    print()
    print("Cargando entradas confirmadas...")

    entries = pd.read_csv(
        ENTRIES_FILE
    )

    print(
        f"Entradas cargadas: "
        f"{len(entries)}"
    )

    return candles, entries


# ==================================================
# PREPARAR DATOS
# ==================================================

def prepare_data(candles, entries):

    # ==============================================
    # TIEMPO DE VELAS
    # ==============================================

    if "time" not in candles.columns:

        raise ValueError(
            "El histórico no contiene "
            "la columna 'time'."
        )

    candles["time"] = pd.to_datetime(
        candles["time"],
        utc=True
    )

    candles = (
        candles
        .sort_values("time")
        .reset_index(drop=True)
    )

    # ==============================================
    # TIEMPO DE ENTRADAS
    # ==============================================

    if "entry_time" not in entries.columns:

        raise ValueError(
            "El archivo de entradas no contiene "
            "la columna 'entry_time'."
        )

    entries["entry_time"] = pd.to_datetime(
        entries["entry_time"],
        utc=True
    )

    entries = (
        entries
        .sort_values("entry_time")
        .reset_index(drop=True)
    )

    return candles, entries


# ==================================================
# BACKTEST PRINCIPAL
# ==================================================

def run_backtest():

    print("=" * 65)
    print("BACKTEST DE ENTRADAS SMC")
    print("=" * 65)

    print()
    print(f"Histórico: {HISTORICAL_FILE}")
    print(f"Entradas: {ENTRIES_FILE}")

    # ==============================================
    # VALIDAR
    # ==============================================

    validate_files()

    # ==============================================
    # CARGAR
    # ==============================================

    candles, entries = load_data()

    # ==============================================
    # PREPARAR
    # ==============================================

    candles, entries = prepare_data(
        candles,
        entries
    )

    print()
    print(
        f"Velas cargadas: "
        f"{len(candles)}"
    )

    print(
        f"Entradas cargadas: "
        f"{len(entries)}"
    )

    # ==============================================
    # EJECUTAR SIMULACIÓN
    # ==============================================

    print()
    print("Ejecutando simulación...")

    trades = simulate_all_trades(
        candles=candles,
        entries=entries,
        max_bars=None
    )

    if trades.empty:

        print()
        print(
            "No se generaron resultados "
            "en el backtest."
        )

        return

    # ==============================================
    # GUARDAR RESULTADOS
    # ==============================================

    output_directory = os.path.dirname(
        OUTPUT_FILE
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    trades.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ==============================================
    # RESUMEN
    # ==============================================

    summary = get_backtest_summary(
        trades
    )

    print_summary(
        summary
    )

    # ==============================================
    # ESTADÍSTICAS R:R
    # ==============================================

    print_rr_statistics(
        trades
    )

    # ==============================================
    # OPERACIONES GANADORAS
    # ==============================================

    winning_trades = trades[
        trades["result"] == "WIN"
    ].copy()

    print_trades(
        "OPERACIONES GANADORAS",
        winning_trades
    )

    # ==============================================
    # OPERACIONES PERDEDORAS
    # ==============================================

    losing_trades = trades[
        trades["result"] == "LOSS"
    ].copy()

    print_trades(
        "OPERACIONES PERDEDORAS",
        losing_trades
    )

    # ==============================================
    # OPERACIONES AMBIGUAS
    # ==============================================

    ambiguous_trades = trades[
        trades["result"] == "AMBIGUOUS"
    ].copy()

    print_trades(
        "OPERACIONES AMBIGUAS",
        ambiguous_trades
    )

    # ==============================================
    # OPERACIONES ABIERTAS
    # ==============================================

    open_trades = trades[
        trades["result"] == "OPEN"
    ].copy()

    print_trades(
        "OPERACIONES ABIERTAS",
        open_trades
    )

    # ==============================================
    # MOSTRAR ARCHIVO
    # ==============================================

    print()
    print("=" * 65)
    print("BACKTEST GUARDADO EN:")
    print(OUTPUT_FILE)
    print("=" * 65)

    return trades, summary


# ==================================================
# EJECUCIÓN
# ==================================================

if __name__ == "__main__":

    try:

        run_backtest()

    except Exception as error:

        print()
        print("=" * 65)
        print("ERROR EN EL BACKTEST")
        print("=" * 65)

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )