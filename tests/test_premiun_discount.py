import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.order_blocks import detect_order_blocks
from strategy.smc.premium_discount import (
    calculate_premium_discount,
    is_bullish_ob_in_discount,
    is_bearish_ob_in_premium
)


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


# ==================================================
# FUNCIÓN PRINCIPAL
# ==================================================

def main():

    print("=" * 65)
    print("PRUEBA DE DETECCIÓN DE PREMIUM Y DISCOUNT")
    print("=" * 65)

    # --------------------------------------------------
    # 1. CARGAR DATOS HISTÓRICOS
    # --------------------------------------------------

    print("\nCargando datos históricos...")

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(df["time"])

    print(f"Velas cargadas: {len(df)}")

    # --------------------------------------------------
    # 2. DETECTAR SWING HIGH Y SWING LOW
    # --------------------------------------------------

    print("\nProcesando Swing High / Swing Low...")

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    swing_highs = df["swing_high"].sum()
    swing_lows = df["swing_low"].sum()

    print(f"Swing Highs detectados: {int(swing_highs)}")
    print(f"Swing Lows detectados: {int(swing_lows)}")

    # --------------------------------------------------
    # 3. DETECTAR CHOCH / BOS
    # --------------------------------------------------

    print("\nProcesando CHOCH / BOS...")

    df = detect_choch_bos(df)

    # Mostrar resultados solo si existen las columnas
    if "choch_bullish" in df.columns:
        print(
            f"Bullish CHOCH detectados: "
            f"{int(df['choch_bullish'].sum())}"
        )

    if "choch_bearish" in df.columns:
        print(
            f"Bearish CHOCH detectados: "
            f"{int(df['choch_bearish'].sum())}"
        )

    if "bos_bullish" in df.columns:
        print(
            f"Bullish BOS detectados: "
            f"{int(df['bos_bullish'].sum())}"
        )

    if "bos_bearish" in df.columns:
        print(
            f"Bearish BOS detectados: "
            f"{int(df['bos_bearish'].sum())}"
        )

    # --------------------------------------------------
    # 4. DETECTAR ORDER BLOCKS
    # --------------------------------------------------

    print("\nProcesando Order Blocks...")

    order_blocks = detect_order_blocks(df)

    print(
        f"Bullish Order Blocks detectados: "
        f"{len(order_blocks[order_blocks['ob_type'] == 'bullish'])}"
    )

    print(
        f"Bearish Order Blocks detectados: "
        f"{len(order_blocks[order_blocks['ob_type'] == 'bearish'])}"
    )

    # --------------------------------------------------
    # 5. CALCULAR PREMIUM / DISCOUNT
    # --------------------------------------------------

    print("\nCalculando Premium / Discount...")

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    # --------------------------------------------------
    # 6. VALIDAR COLUMNAS NECESARIAS
    # --------------------------------------------------

    required_columns = [
        "time",
        "range_high",
        "range_low",
        "equilibrium",
        "price_position",
        "zone"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Faltan columnas necesarias:")
        print(missing_columns)

        print("\nColumnas disponibles en el DataFrame:")
        print(df.columns.tolist())

        return

    # --------------------------------------------------
    # 7. UNIR PREMIUM / DISCOUNT CON ORDER BLOCKS
    # --------------------------------------------------

    print("\nUniendo información de zonas...")

    columns_to_merge = [
        "time",
        "range_high",
        "range_low",
        "equilibrium",
        "price_position",
        "zone"
    ]

    zone_data = df[columns_to_merge].copy()

    order_blocks = order_blocks.merge(
        zone_data,
        on="time",
        how="left"
    )

    # --------------------------------------------------
    # 8. FILTRAR BULLISH ORDER BLOCKS EN DISCOUNT
    # --------------------------------------------------

    print("\nBuscando Bullish Order Blocks en Discount...")

    bullish_discount = is_bullish_ob_in_discount(
        order_blocks
    )

    # --------------------------------------------------
    # 9. FILTRAR BEARISH ORDER BLOCKS EN PREMIUM
    # --------------------------------------------------

    print("Buscando Bearish Order Blocks en Premium...")

    bearish_premium = is_bearish_ob_in_premium(
        order_blocks
    )

    # --------------------------------------------------
    # 10. RESULTADOS GENERALES
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("RESULTADOS GENERALES")
    print("=" * 65)

    bullish_total = len(
        order_blocks[
            order_blocks["ob_type"] == "bullish"
        ]
    )

    bearish_total = len(
        order_blocks[
            order_blocks["ob_type"] == "bearish"
        ]
    )

    print(f"\nBullish Order Blocks totales: {bullish_total}")

    print(f"Bearish Order Blocks totales: {bearish_total}")

    print("\n" + "-" * 65)

    print(
        f"\nBullish Order Blocks en Discount: "
        f"{len(bullish_discount)}"
    )

    print(
        f"Bearish Order Blocks en Premium: "
        f"{len(bearish_premium)}"
    )

    # --------------------------------------------------
    # 11. MOSTRAR ÚLTIMOS BULLISH OB EN DISCOUNT
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ÚLTIMOS 10 BULLISH ORDER BLOCKS EN DISCOUNT")
    print("=" * 65)

    if not bullish_discount.empty:

        columns_to_show = [
            "time",
            "ob_high",
            "ob_low",
            "equilibrium",
            "zone"
        ]

        available_columns = [
            column
            for column in columns_to_show
            if column in bullish_discount.columns
        ]

        print(
            bullish_discount[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print(
            "No se detectaron Bullish Order Blocks "
            "en Discount."
        )

    # --------------------------------------------------
    # 12. MOSTRAR ÚLTIMOS BEARISH OB EN PREMIUM
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("ÚLTIMOS 10 BEARISH ORDER BLOCKS EN PREMIUM")
    print("=" * 65)

    if not bearish_premium.empty:

        columns_to_show = [
            "time",
            "ob_high",
            "ob_low",
            "equilibrium",
            "zone"
        ]

        available_columns = [
            column
            for column in columns_to_show
            if column in bearish_premium.columns
        ]

        print(
            bearish_premium[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print(
            "No se detectaron Bearish Order Blocks "
            "en Premium."
        )

    # --------------------------------------------------
    # 13. RESUMEN FINAL
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)

    print("\nResumen:")

    print(f"- Velas procesadas: {len(df)}")
    print(f"- Order Blocks totales: {len(order_blocks)}")
    print(f"- Bullish OB en Discount: {len(bullish_discount)}")
    print(f"- Bearish OB en Premium: {len(bearish_premium)}")

    print()


# ==================================================
# EJECUCIÓN
# ==================================================

if __name__ == "__main__":
    main()