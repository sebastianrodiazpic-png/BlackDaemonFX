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


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 65)
    print("PRUEBA DE CONFIRMACIÓN DE ENTRADAS SMC")
    print("=" * 65)

    # ==================================================
    # 1. CARGAR DATOS
    # ==================================================

    print("\nCargando datos históricos...")

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(
        df["time"]
    )

    print(
        f"Velas cargadas: {len(df)}"
    )

    # ==================================================
    # 2. DETECTAR SWINGS
    # ==================================================

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

    # ==================================================
    # 3. DETECTAR CHOCH / BOS
    # ==================================================

    print(
        "\nProcesando CHOCH / BOS..."
    )

    df = detect_choch_bos(df)

    print(
        "CHOCH / BOS procesados."
    )

    # ==================================================
    # 4. DETECTAR ORDER BLOCKS
    # ==================================================

    print(
        "\nProcesando Order Blocks..."
    )

    order_blocks = detect_order_blocks(df)

    print(
        f"Order Blocks detectados: "
        f"{len(order_blocks)}"
    )

    # ==================================================
    # 5. CALCULAR PREMIUM / DISCOUNT
    # ==================================================

    print(
        "\nCalculando Premium / Discount..."
    )

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    # ==================================================
    # 6. UNIR INFORMACIÓN DE ZONAS
    # ==================================================

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

    # ==================================================
    # 7. DETECTAR SETUPS
    # ==================================================

    print(
        "\nDetectando setups SMC..."
    )

    setups = detect_setups(
        df,
        order_blocks,
        structure_lookback=100
    )

    print(
        f"Setups detectados: {len(setups)}"
    )

    if setups.empty:

        print(
            "\nNo existen setups para confirmar."
        )

        return

    # ==================================================
    # 8. CONFIRMAR ENTRADAS
    # ==================================================

    print(
        "\nBuscando retests y confirmaciones de entrada..."
    )

    confirmations = detect_entry_confirmations(
        df,
        setups,
        max_wait_candles=50
    )

    # ==================================================
    # 9. RESULTADOS GENERALES
    # ==================================================

    print("\n" + "=" * 65)
    print("RESULTADOS GENERALES")
    print("=" * 65)

    print(
        f"\nSetups originales: "
        f"{len(setups)}"
    )

    if confirmations.empty:

        print(
            "\nNo se detectaron confirmaciones de entrada."
        )

        return

    long_confirmations = confirmations[
        confirmations["setup_type"] == "long"
    ].copy()

    short_confirmations = confirmations[
        confirmations["setup_type"] == "short"
    ].copy()

    print(
        f"Confirmaciones LONG: "
        f"{len(long_confirmations)}"
    )

    print(
        f"Confirmaciones SHORT: "
        f"{len(short_confirmations)}"
    )

    print(
        f"Confirmaciones TOTALES: "
        f"{len(confirmations)}"
    )

    # ==================================================
    # 10. MOSTRAR ÚLTIMAS CONFIRMACIONES LONG
    # ==================================================

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 CONFIRMACIONES LONG")
    print("=" * 65)

    if not long_confirmations.empty:

        columns_to_show = [
            "setup_time",
            "entry_time",
            "ob_high",
            "ob_low",
            "entry_price",
            "stop_loss",
            "confirmation_type",
            "zone"
        ]

        print(
            long_confirmations[
                columns_to_show
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print(
            "No se detectaron confirmaciones LONG."
        )

    # ==================================================
    # 11. MOSTRAR ÚLTIMAS CONFIRMACIONES SHORT
    # ==================================================

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 CONFIRMACIONES SHORT")
    print("=" * 65)

    if not short_confirmations.empty:

        columns_to_show = [
            "setup_time",
            "retest_time",
            "entry_time",
            "ob_high",
            "ob_low",
            "entry_price",
            "stop_loss",
            "candles_to_retest",
            "candles_to_confirmation",
            "confirmation_type",
            "zone"
        ]

        print(
            short_confirmations[
                columns_to_show
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print(
            "No se detectaron confirmaciones SHORT."
        )

    # ==================================================
    # 12. RESUMEN
    # ==================================================

    print("\n" + "=" * 65)
    print("RESUMEN FINAL")
    print("=" * 65)

    print(
        f"\nVelas procesadas: {len(df)}"
    )

    print(
        f"Setups SMC: {len(setups)}"
    )

    print(
        f"Entradas confirmadas: "
        f"{len(confirmations)}"
    )

    print(
        f"LONG confirmados: "
        f"{len(long_confirmations)}"
    )

    print(
        f"SHORT confirmados: "
        f"{len(short_confirmations)}"
    )

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    main()