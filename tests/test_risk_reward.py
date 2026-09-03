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


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)

RISK_REWARD_RATIO = 2.0


def main():

    print("=" * 70)
    print("PRUEBA DE RISK / REWARD SMC")
    print("=" * 70)

    # ==================================================
    # 1. CARGAR DATOS
    # ==================================================

    print("\nCargando datos históricos...")

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(df["time"])

    print(f"Velas cargadas: {len(df)}")

    # ==================================================
    # 2. DETECTAR SWINGS
    # ==================================================

    print("\nProcesando Swing High / Swing Low...")

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    print("Swing High / Swing Low procesados.")

    # ==================================================
    # 3. DETECTAR CHOCH / BOS
    # ==================================================

    print("\nProcesando CHOCH / BOS...")

    df = detect_choch_bos(df)

    print("CHOCH / BOS procesados.")

    # ==================================================
    # 4. DETECTAR ORDER BLOCKS
    # ==================================================

    print("\nProcesando Order Blocks...")

    order_blocks = detect_order_blocks(df)

    print(
        f"Order Blocks detectados: "
        f"{len(order_blocks)}"
    )

    # ==================================================
    # 5. PREMIUM / DISCOUNT
    # ==================================================

    print("\nCalculando Premium / Discount...")

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    print("Premium / Discount calculado.")

    # ==================================================
    # 6. UNIR ZONAS
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

    order_blocks["time"] = pd.to_datetime(
        order_blocks["time"]
    )

    zone_data["time"] = pd.to_datetime(
        zone_data["time"]
    )

    order_blocks = order_blocks.merge(
        zone_data,
        on="time",
        how="left"
    )

    print("Información de zonas unida correctamente.")

    # ==================================================
    # 7. DETECTAR SETUPS
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
        f"Entradas confirmadas: "
        f"{len(confirmations)}"
    )

    # ==================================================
    # 9. CALCULAR RISK / REWARD
    # ==================================================

    print(
        f"\nCalculando Risk / Reward "
        f"1:{RISK_REWARD_RATIO}..."
    )

    trades = calculate_risk_reward(
        confirmations,
        risk_reward_ratio=RISK_REWARD_RATIO
    )

    # ==================================================
    # RESULTADOS GENERALES
    # ==================================================

    print("\n" + "=" * 70)
    print("RESULTADOS GENERALES")
    print("=" * 70)

    print(f"\nVelas procesadas: {len(df)}")
    print(f"Setups originales: {len(setups)}")
    print(f"Entradas confirmadas: {len(confirmations)}")
    print(f"Operaciones válidas: {len(trades)}")

    if trades.empty:

        print(
            "\nNo se generaron operaciones válidas "
            "con Risk / Reward."
        )

        return

    long_trades = trades[
        trades["setup_type"] == "long"
    ]

    short_trades = trades[
        trades["setup_type"] == "short"
    ]

    print(f"\nOperaciones LONG: {len(long_trades)}")
    print(f"Operaciones SHORT: {len(short_trades)}")

    print(
        f"Risk / Reward objetivo: "
        f"1:{RISK_REWARD_RATIO}"
    )

    # ==================================================
    # ÚLTIMAS OPERACIONES LONG
    # ==================================================

    print("\n" + "=" * 70)
    print("ÚLTIMAS 10 OPERACIONES LONG")
    print("=" * 70)

    if not long_trades.empty:

        columns_to_show = [
            "setup_time",
            "entry_time",
            "entry_price",
            "stop_loss",
            "take_profit",
            "risk",
            "reward",
            "risk_reward_ratio",
            "confirmation_type"
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
            "No se detectaron operaciones LONG."
        )

    # ==================================================
    # ÚLTIMAS OPERACIONES SHORT
    # ==================================================

    print("\n" + "=" * 70)
    print("ÚLTIMAS 10 OPERACIONES SHORT")
    print("=" * 70)

    if not short_trades.empty:

        columns_to_show = [
            "setup_time",
            "entry_time",
            "entry_price",
            "stop_loss",
            "take_profit",
            "risk",
            "reward",
            "risk_reward_ratio",
            "confirmation_type"
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
            "No se detectaron operaciones SHORT."
        )

    # ==================================================
    # ESTADÍSTICAS
    # ==================================================

    print("\n" + "=" * 70)
    print("ESTADÍSTICAS DE RIESGO")
    print("=" * 70)

    print(
        f"\nRiesgo promedio: "
        f"{trades['risk'].mean():.3f}"
    )

    print(
        f"Reward promedio: "
        f"{trades['reward'].mean():.3f}"
    )

    print(
        f"Stop Loss mínimo: "
        f"{trades['risk'].min():.3f}"
    )

    print(
        f"Stop Loss máximo: "
        f"{trades['risk'].max():.3f}"
    )

    # ==================================================
    # FINALIZAR
    # ==================================================

    print("\n" + "=" * 70)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()