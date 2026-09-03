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


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 65)
    print("PRUEBA DEL DETECTOR DE SETUPS SMC")
    print("=" * 65)

    # --------------------------------------------------
    # 1. CARGAR DATOS
    # --------------------------------------------------

    print("\nCargando datos históricos...")

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(df["time"])

    print(f"Velas cargadas: {len(df)}")

    # --------------------------------------------------
    # 2. DETECTAR SWINGS
    # --------------------------------------------------

    print("\nProcesando Swing High / Swing Low...")

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    print("Swing High / Swing Low procesados.")

    # --------------------------------------------------
    # 3. DETECTAR CHOCH / BOS
    # --------------------------------------------------

    print("\nProcesando CHOCH / BOS...")

    df = detect_choch_bos(df)

    # --------------------------------------------------
    # VALIDAR COLUMNAS DE ESTRUCTURA
    # --------------------------------------------------

    print("\nVerificando columnas de CHOCH / BOS...")

    required_structure_columns = [
        "choch_bullish",
        "choch_bearish",
        "bos_bullish",
        "bos_bearish"
    ]

    missing_columns = [
        column
        for column in required_structure_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Faltan columnas necesarias:")

        for column in missing_columns:
            print(f" - {column}")

        print("\nColumnas actualmente disponibles:")
        print(df.columns.tolist())

        print("\nLa función detect_choch_bos() debe corregirse.")
        print("No se puede continuar con setup_detector.py.")

        return

    print("Columnas CHOCH / BOS verificadas correctamente.")

    # --------------------------------------------------
    # 4. DETECTAR ORDER BLOCKS
    # --------------------------------------------------

    print("\nProcesando Order Blocks...")

    order_blocks = detect_order_blocks(df)

    print(f"Order Blocks detectados: {len(order_blocks)}")

    # --------------------------------------------------
    # 5. CALCULAR PREMIUM / DISCOUNT
    # --------------------------------------------------

    print("\nCalculando Premium / Discount...")

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    # --------------------------------------------------
    # 6. UNIR ZONAS CON ORDER BLOCKS
    # --------------------------------------------------

    print("\nUniendo información de zonas...")

    zone_columns = [
        "time",
        "range_high",
        "range_low",
        "equilibrium",
        "price_position",
        "zone"
    ]

    missing_zone_columns = [
        column
        for column in zone_columns
        if column not in df.columns
    ]

    if missing_zone_columns:

        print("\nERROR: Faltan columnas de Premium / Discount:")

        for column in missing_zone_columns:
            print(f" - {column}")

        return

    zone_data = df[
        zone_columns
    ].copy()

    order_blocks = order_blocks.merge(
        zone_data,
        on="time",
        how="left"
    )

    print("Información de zonas unida correctamente.")

    # --------------------------------------------------
    # 7. DETECTAR SETUPS
    # --------------------------------------------------

    print("\nDetectando setups SMC...")

    setups = detect_setups(
        df,
        order_blocks,
        structure_lookback=100
    )

    # --------------------------------------------------
    # 8. RESULTADOS GENERALES
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("RESULTADOS")
    print("=" * 65)

    if setups.empty:

        print("\nNo se detectaron setups completos.")

        return

    long_setups = setups[
        setups["setup_type"] == "long"
    ]

    short_setups = setups[
        setups["setup_type"] == "short"
    ]

    print(f"\nSetups LONG detectados: {len(long_setups)}")
    print(f"Setups SHORT detectados: {len(short_setups)}")
    print(f"Setups TOTALES: {len(setups)}")

    # --------------------------------------------------
    # 9. MOSTRAR ÚLTIMOS LONG
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ÚLTIMOS 10 SETUPS LONG")
    print("=" * 65)

    if not long_setups.empty:

        columns_to_show = [
            "time",
            "ob_high",
            "ob_low",
            "equilibrium",
            "zone",
            "choch_bullish",
            "bos_bullish"
        ]

        available_columns = [
            column
            for column in columns_to_show
            if column in long_setups.columns
        ]

        print(
            long_setups[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:
        print("No se detectaron setups LONG.")

    # --------------------------------------------------
    # 10. MOSTRAR ÚLTIMOS SHORT
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ÚLTIMOS 10 SETUPS SHORT")
    print("=" * 65)

    if not short_setups.empty:

        columns_to_show = [
            "time",
            "ob_high",
            "ob_low",
            "equilibrium",
            "zone",
            "choch_bearish",
            "bos_bearish"
        ]

        available_columns = [
            column
            for column in columns_to_show
            if column in short_setups.columns
        ]

        print(
            short_setups[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:
        print("No se detectaron setups SHORT.")

    # --------------------------------------------------
    # 11. FINALIZAR
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    main()