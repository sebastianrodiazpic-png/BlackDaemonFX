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

from strategy.risk.position_sizing import (
    calculate_position_size,
    add_position_sizing
)


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)

INITIAL_BALANCE = 10000.0

RISK_PERCENT = 1.0

POINT_VALUE = 1.0

MIN_POSITION_SIZE = 0.01

MAX_POSITION_SIZE = None


def main():

    print("=" * 65)
    print("PRUEBA DE POSITION SIZING SMC")
    print("=" * 65)

    # ==================================================
    # 1. CARGAR DATOS
    # ==================================================

    print("\nCargando datos históricos...")

    df = pd.read_csv(
        FILE_PATH
    )

    df["time"] = pd.to_datetime(
        df["time"]
    )

    print(
        f"Velas cargadas: {len(df)}"
    )

    # ==================================================
    # 2. DETECTAR SWINGS
    # ==================================================

    print("\nProcesando Swing High / Swing Low...")

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    print(
        "Swing High / Swing Low procesados."
    )

    # ==================================================
    # 3. DETECTAR CHOCH / BOS
    # ==================================================

    print("\nProcesando CHOCH / BOS...")

    df = detect_choch_bos(
        df
    )

    print(
        "CHOCH / BOS procesados."
    )

    # ==================================================
    # 4. DETECTAR ORDER BLOCKS
    # ==================================================

    print("\nProcesando Order Blocks...")

    order_blocks = detect_order_blocks(
        df
    )

    print(
        f"Order Blocks detectados: "
        f"{len(order_blocks)}"
    )

    # ==================================================
    # 5. CALCULAR PREMIUM / DISCOUNT
    # ==================================================

    print("\nCalculando Premium / Discount...")

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    print(
        "Premium / Discount calculado."
    )

    # ==================================================
    # 6. UNIR INFORMACIÓN DE ZONAS
    # ==================================================

    print("\nUniendo información de zonas...")

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

    # ==================================================
    # 7. DETECTAR SETUPS SMC
    # ==================================================

    print("\nDetectando setups SMC...")

    setups = detect_setups(
        df,
        order_blocks,
        structure_lookback=100
    )

    print(
        f"Setups detectados: "
        f"{len(setups)}"
    )

    # ==================================================
    # 8. CONFIRMAR ENTRADAS
    # ==================================================

    print("\nBuscando confirmaciones de entrada...")

    confirmations = detect_entry_confirmations(
        df,
        setups
    )

    print(
        f"Confirmaciones detectadas: "
        f"{len(confirmations)}"
    )

    # ==================================================
    # 9. CALCULAR RISK / REWARD
    # ==================================================

    print("\nCalculando Risk / Reward...")

    trades = calculate_risk_reward(
        confirmations,
        risk_reward_ratio=2.0
    )

    print(
        f"Operaciones con R:R calculado: "
        f"{len(trades)}"
    )

    # ==================================================
    # 10. SIMULAR OPERACIONES
    # ==================================================

    print("\nSimulando operaciones...")

    simulated_trades = simulate_trades(
        df,
        trades
    )

    print(
        f"Operaciones simuladas: "
        f"{len(simulated_trades)}"
    )

    # ==================================================
    # VALIDAR OPERACIONES
    # ==================================================

    if simulated_trades.empty:

        print(
            "\nNo existen operaciones para "
            "calcular Position Sizing."
        )

        print("\n" + "=" * 65)
        print("PRUEBA FINALIZADA")
        print("=" * 65)

        return

    # ==================================================
    # 11. PRUEBA INDIVIDUAL DE POSITION SIZE
    # ==================================================

    print("\nProbando cálculo individual...")

    first_trade = simulated_trades.iloc[0]

    example_sizing = calculate_position_size(
        entry_price=float(
            first_trade["entry_price"]
        ),
        stop_loss=float(
            first_trade["stop_loss"]
        ),
        account_balance=INITIAL_BALANCE,
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        min_position_size=MIN_POSITION_SIZE,
        max_position_size=MAX_POSITION_SIZE
    )

    print(
        "\nEJEMPLO PRIMERA OPERACIÓN"
    )

    print(
        f"Balance: "
        f"{example_sizing['account_balance']:.3f}"
    )

    print(
        f"Riesgo objetivo: "
        f"{example_sizing['risk_percent']:.3f}%"
    )

    print(
        f"Monto arriesgado: "
        f"{example_sizing['risk_amount']:.3f}"
    )

    print(
        f"Distancia Stop Loss: "
        f"{example_sizing['stop_distance']:.3f}"
    )

    print(
        f"Riesgo por unidad: "
        f"{example_sizing['risk_per_unit']:.3f}"
    )

    print(
        f"Tamaño de posición: "
        f"{example_sizing['position_size']:.6f}"
    )

    print(
        f"Riesgo real: "
        f"{example_sizing['actual_risk_amount']:.3f}"
    )

    print(
        f"Riesgo real %: "
        f"{example_sizing['actual_risk_percent']:.6f}%"
    )

    # ==================================================
    # 12. AGREGAR POSITION SIZING
    # ==================================================

    print(
        "\nCalculando tamaño de posición "
        "para todas las operaciones..."
    )

    sized_trades = add_position_sizing(
        trades=simulated_trades,
        initial_balance=INITIAL_BALANCE,
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        min_position_size=MIN_POSITION_SIZE,
        max_position_size=MAX_POSITION_SIZE
    )

    print(
        f"Operaciones procesadas: "
        f"{len(sized_trades)}"
    )

    # ==================================================
    # VALIDAR COLUMNAS GENERADAS
    # ==================================================

    print(
        "\nVerificando columnas generadas..."
    )

    required_columns = [
        "balance_before",
        "risk_amount",
        "stop_distance",
        "risk_per_unit",
        "position_size",
        "actual_risk_amount",
        "actual_risk_percent"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in sized_trades.columns
    ]

    if missing_columns:

        raise ValueError(
            "Faltan columnas de Position Sizing: "
            f"{missing_columns}"
        )

    print(
        "Columnas verificadas correctamente."
    )

    # ==================================================
    # ESTADÍSTICAS GENERALES
    # ==================================================

    print("\n" + "=" * 65)
    print("ESTADÍSTICAS DE POSITION SIZING")
    print("=" * 65)

    print(
        f"\nBalance inicial: "
        f"{INITIAL_BALANCE:.3f}"
    )

    print(
        f"Riesgo configurado: "
        f"{RISK_PERCENT:.3f}%"
    )

    print(
        f"Valor por punto: "
        f"{POINT_VALUE:.3f}"
    )

    print(
        f"Tamaño mínimo: "
        f"{MIN_POSITION_SIZE:.6f}"
    )

    if MAX_POSITION_SIZE is not None:

        print(
            f"Tamaño máximo: "
            f"{MAX_POSITION_SIZE:.6f}"
        )

    print(
        f"\nTamaño promedio: "
        f"{sized_trades['position_size'].mean():.6f}"
    )

    print(
        f"Tamaño mínimo utilizado: "
        f"{sized_trades['position_size'].min():.6f}"
    )

    print(
        f"Tamaño máximo utilizado: "
        f"{sized_trades['position_size'].max():.6f}"
    )

    print(
        f"\nRiesgo objetivo promedio: "
        f"{sized_trades['risk_amount'].mean():.3f}"
    )

    print(
        f"Riesgo real promedio: "
        f"{sized_trades['actual_risk_amount'].mean():.3f}"
    )

    print(
        f"Riesgo real promedio %: "
        f"{sized_trades['actual_risk_percent'].mean():.6f}%"
    )

    print(
        f"\nBalance mínimo antes de operar: "
        f"{sized_trades['balance_before'].min():.3f}"
    )

    print(
        f"Balance máximo antes de operar: "
        f"{sized_trades['balance_before'].max():.3f}"
    )

    # ==================================================
    # RESULTADOS LONG / SHORT
    # ==================================================

    print("\n" + "-" * 65)
    print("POSITION SIZING LONG / SHORT")
    print("-" * 65)

    if "side" in sized_trades.columns:

        long_trades = sized_trades[
            sized_trades["side"]
            == "long"
        ]

        short_trades = sized_trades[
            sized_trades["side"]
            == "short"
        ]

    elif "direction" in sized_trades.columns:

        long_trades = sized_trades[
            sized_trades["direction"]
            == "long"
        ]

        short_trades = sized_trades[
            sized_trades["direction"]
            == "short"
        ]

    else:

        long_trades = pd.DataFrame()

        short_trades = pd.DataFrame()

    if not long_trades.empty:

        print(
            f"\nOperaciones LONG: "
            f"{len(long_trades)}"
        )

        print(
            f"Tamaño promedio LONG: "
            f"{long_trades['position_size'].mean():.6f}"
        )

        print(
            f"Riesgo promedio LONG: "
            f"{long_trades['actual_risk_amount'].mean():.3f}"
        )

    if not short_trades.empty:

        print(
            f"\nOperaciones SHORT: "
            f"{len(short_trades)}"
        )

        print(
            f"Tamaño promedio SHORT: "
            f"{short_trades['position_size'].mean():.6f}"
        )

        print(
            f"Riesgo promedio SHORT: "
            f"{short_trades['actual_risk_amount'].mean():.3f}"
        )

    # ==================================================
    # ÚLTIMAS OPERACIONES
    # ==================================================

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 OPERACIONES CON POSITION SIZING")
    print("=" * 65)

    columns_to_show = [
        "entry_time",
        "exit_time",
        "entry_price",
        "stop_loss",
        "take_profit",
        "result",
        "pnl",
        "balance_before",
        "risk_amount",
        "stop_distance",
        "position_size",
        "actual_risk_amount",
        "actual_risk_percent"
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in sized_trades.columns
    ]

    print(
        sized_trades[
            available_columns
        ]
        .tail(10)
        .to_string(index=False)
    )

    # ==================================================
    # VALIDACIONES FINALES
    # ==================================================

    print("\n" + "-" * 65)
    print("VALIDACIONES FINALES")
    print("-" * 65)

    invalid_position_sizes = sized_trades[
        sized_trades["position_size"] <= 0
    ]

    invalid_stop_distances = sized_trades[
        sized_trades["stop_distance"] <= 0
    ]

    print(
        f"\nOperaciones con tamaño inválido: "
        f"{len(invalid_position_sizes)}"
    )

    print(
        f"Operaciones con Stop Distance inválido: "
        f"{len(invalid_stop_distances)}"
    )

    if len(invalid_position_sizes) > 0:

        raise ValueError(
            "Existen tamaños de posición inválidos."
        )

    if len(invalid_stop_distances) > 0:

        raise ValueError(
            "Existen distancias de Stop Loss inválidas."
        )

    # ==================================================
    # FINALIZAR
    # ==================================================

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    main()