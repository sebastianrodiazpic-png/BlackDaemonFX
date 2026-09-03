import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.market_structure import (
    classify_market_structure,
    get_current_trend
)


FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 60)
    print("PRUEBA DE ESTRUCTURA DE MERCADO")
    print("=" * 60)

    # --------------------------------------------------------
    # CARGAR DATOS
    # --------------------------------------------------------

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(df["time"])

    print(f"\nVelas cargadas: {len(df)}")

    # --------------------------------------------------------
    # DETECTAR SWINGS
    # --------------------------------------------------------

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    # --------------------------------------------------------
    # CLASIFICAR ESTRUCTURA
    # --------------------------------------------------------

    df = classify_market_structure(df)

    # --------------------------------------------------------
    # CONTAR ESTRUCTURAS
    # --------------------------------------------------------

    hh_count = len(
        df[df["structure"] == "HH"]
    )

    hl_count = len(
        df[df["structure"] == "HL"]
    )

    lh_count = len(
        df[df["structure"] == "LH"]
    )

    ll_count = len(
        df[df["structure"] == "LL"]
    )

    print("\nESTRUCTURA DETECTADA")

    print(f"HH - Higher High: {hh_count}")
    print(f"HL - Higher Low:  {hl_count}")
    print(f"LH - Lower High: {lh_count}")
    print(f"LL - Lower Low:  {ll_count}")

    # --------------------------------------------------------
    # TENDENCIA ACTUAL
    # --------------------------------------------------------

    trend = get_current_trend(df)

    print("\n" + "=" * 60)
    print(f"TENDENCIA ACTUAL: {trend}")
    print("=" * 60)

    # --------------------------------------------------------
    # ÚLTIMOS PUNTOS DE ESTRUCTURA
    # --------------------------------------------------------

    structure_points = df[
        df["structure"].notna()
    ]

    print("\nÚLTIMOS 20 PUNTOS DE ESTRUCTURA")

    print(
        structure_points[
            [
                "time",
                "high",
                "low",
                "structure"
            ]
        ]
        .tail(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()