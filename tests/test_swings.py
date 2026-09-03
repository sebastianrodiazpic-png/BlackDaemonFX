import pandas as pd

from strategy.smc.swings import detect_swings


FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 60)
    print("PRUEBA DE DETECCIÓN DE SWING HIGH Y SWING LOW")
    print("=" * 60)

    # Cargar datos históricos
    df = pd.read_csv(FILE_PATH)

    # Convertir la columna time
    df["time"] = pd.to_datetime(df["time"])

    print(f"\nVelas cargadas: {len(df)}")

    # Detectar swings
    df = detect_swings(
        df,
        left=3,
        right=3
    )

    swing_highs = df[df["swing_high"]]
    swing_lows = df[df["swing_low"]]

    print(f"\nSwing Highs detectados: {len(swing_highs)}")
    print(f"Swing Lows detectados: {len(swing_lows)}")

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 SWING HIGHS")
    print("=" * 60)

    print(
        swing_highs[
            ["time", "high"]
        ].tail(10).to_string(index=False)
    )

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 SWING LOWS")
    print("=" * 60)

    print(
        swing_lows[
            ["time", "low"]
        ].tail(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()