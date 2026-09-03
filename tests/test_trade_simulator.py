import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.order_blocks import detect_order_blocks
from strategy.smc.premium_discount import (
    calculate_premium_discount
)
from strategy.smc.setup_detector import (
    detect_setups
)
from strategy.smc.entry_confirmation import (
    detect_entry_confirmations
)
from strategy.smc.risk_reward import (
    calculate_risk_reward
)
from strategy.smc.trade_simulator import (
    simulate_trades
)


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)

MAX_BARS = 500


def main():

    print("=" * 65)
    print("PRUEBA DEL SIMULADOR DE OPERACIONES SMC")
    print("=" * 65)

    # --------------------------------------------------
    # 1. CARGAR DATOS
    # --------------------------------------------------

    print("\nCargando datos históricos...")

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(
        df["time"]
    )

    print(
        f"Velas cargadas: {len(df)}"
    )

    # --------------------------------------------------
    # 2. DETECTAR SWINGS
    # --------------------------------------------------

    print(
        "\nProcesando Swing High / Swing Low..."
    )

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    print(
        "Swing High / Swing Low procesados."
    )

    # --------------------------------------------------
    # 3. DETECTAR CHOCH / BOS
    # --------------------------------------------------

    print(
        "\nProcesando CHOCH / BOS..."
    )

    df = detect_choch_bos(df)

    print(
        "CHOCH / BOS procesados."
    )

    # --------------------------------------------------
    # 4. DETECTAR ORDER BLOCKS
    # --------------------------------------------------

    print(
        "\nProcesando Order Blocks..."
    )

    order_blocks = detect_order_blocks(df)

    print(
        f"Order Blocks detectados: "
        f"{len(order_blocks)}"
    )

    # --------------------------------------------------
    # 5. CALCULAR PREMIUM / DISCOUNT
    # --------------------------------------------------

    print(
        "\nCalculando Premium / Discount..."
    )

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    # --------------------------------------------------
    # 6. UNIR ZONAS CON ORDER BLOCKS
    # --------------------------------------------------

    print(
        "\nUniendo información de zonas..."
    )

    zone_columns = [
        "time",
        "range_high",
        "range_low",
        "equilibrium",
        "price_position",
        "zone"
    ]

    zone_data = df[
        zone_columns
    ].copy()

    order_blocks = order_blocks.merge(
        zone_data,
        on="time",
        how="left"
    )

    print(
        "Información de zonas unida correctamente."
    )

    # --------------------------------------------------
    # 7. DETECTAR SETUPS
    # --------------------------------------------------

    print(
        "\nDetectando setups SMC..."
    )

    setups = detect_setups(
        df,
        order_blocks,
        structure_lookback=100
    )

    print(
        f"Setups detectados: "
        f"{len(setups)}"
    )

    if setups.empty:

        print(
            "\nNo existen setups para simular."
        )

        return

    # --------------------------------------------------
    # 8. CONFIRMAR ENTRADAS
    # --------------------------------------------------

    print(
        "\nBuscando confirmaciones de entrada..."
    )

    confirmations = detect_entry_confirmations(
        df,
        setups
    )

    print(
        f"Confirmaciones detectadas: "
        f"{len(confirmations)}"
    )

    if confirmations.empty:

        print(
            "\nNo existen confirmaciones para calcular "
            "Risk / Reward."
        )

        return

    # --------------------------------------------------
    # 9. CALCULAR RISK / REWARD
    # --------------------------------------------------

    print(
        "\nCalculando Risk / Reward..."
    )

    trades = calculate_risk_reward(
        confirmations,
        risk_reward_ratio=2.0
    )

    print(
        f"Operaciones calculadas: "
        f"{len(trades)}"
    )

    if trades.empty:

        print(
            "\nNo existen operaciones válidas."
        )

        return

    # --------------------------------------------------
    # ASEGURAR TIPO DE OPERACIÓN
    # --------------------------------------------------

    if "trade_type" not in trades.columns:

        if "setup_type" in trades.columns:

            trades["trade_type"] = (
                trades["setup_type"]
            )

        else:

            raise ValueError(
                "No se encontró trade_type "
                "ni setup_type."
            )

    # --------------------------------------------------
    # 10. SIMULAR OPERACIONES
    # --------------------------------------------------

    print(
        "\nSimulando operaciones..."
    )

    simulated_trades = simulate_trades(
        df=df,
        trades=trades,
        max_bars=MAX_BARS
    )

    # --------------------------------------------------
    # 11. RESULTADOS GENERALES
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("RESULTADOS DEL BACKTEST")
    print("=" * 65)

    total_trades = len(
        simulated_trades
    )

    wins = len(
        simulated_trades[
            simulated_trades["result"] == "win"
        ]
    )

    losses = len(
        simulated_trades[
            simulated_trades["result"] == "loss"
        ]
    )

    expired = len(
        simulated_trades[
            simulated_trades["result"] == "expired"
        ]
    )

    ambiguous = len(
        simulated_trades[
            simulated_trades["result"] == "ambiguous"
        ]
    )

    print(
        f"\nOperaciones totales: {total_trades}"
    )

    print(
        f"WIN: {wins}"
    )

    print(
        f"LOSS: {losses}"
    )

    print(
        f"EXPIRED: {expired}"
    )

    print(
        f"AMBIGUOUS: {ambiguous}"
    )

    completed_trades = wins + losses

    if completed_trades > 0:

        win_rate = (
            wins / completed_trades
        ) * 100

        print(
            f"\nWIN RATE: {win_rate:.2f}%"
        )

    # --------------------------------------------------
    # 12. RESULTADOS LONG
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 OPERACIONES LONG")
    print("=" * 65)

    long_trades = simulated_trades[
        simulated_trades["trade_type"] == "long"
    ]

    if not long_trades.empty:

        columns_to_show = [
            "entry_time",
            "exit_time",
            "entry_price",
            "stop_loss",
            "take_profit",
            "result",
            "exit_reason",
            "bars_held"
        ]

        available_columns = [
            column
            for column in columns_to_show
            if column in long_trades.columns
        ]

        print(
            long_trades[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print(
            "No se generaron operaciones LONG."
        )

    # --------------------------------------------------
    # 13. RESULTADOS SHORT
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 OPERACIONES SHORT")
    print("=" * 65)

    short_trades = simulated_trades[
        simulated_trades["trade_type"] == "short"
    ]

    if not short_trades.empty:

        columns_to_show = [
            "entry_time",
            "exit_time",
            "entry_price",
            "stop_loss",
            "take_profit",
            "result",
            "exit_reason",
            "bars_held"
        ]

        available_columns = [
            column
            for column in columns_to_show
            if column in short_trades.columns
        ]

        print(
            short_trades[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print(
            "No se generaron operaciones SHORT."
        )

    # --------------------------------------------------
    # 14. ESTADÍSTICAS DE PNL
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ESTADÍSTICAS FINALES")
    print("=" * 65)

    if "pnl_price" in simulated_trades.columns:

        total_pnl = (
            simulated_trades["pnl_price"]
            .sum()
        )

        print(
            f"\nPnL total en precio: "
            f"{total_pnl:.3f}"
        )

    if completed_trades > 0:

        print(
            f"Win Rate: {win_rate:.2f}%"
        )

    print(
        f"Operaciones cerradas: "
        f"{completed_trades}"
    )

    print(
        f"Operaciones sin resolver: "
        f"{expired + ambiguous}"
    )

    # --------------------------------------------------
    # FINALIZAR
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    main()