import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.liquidity import detect_liquidity_levels
from strategy.smc.liquidity_sweeps import detect_liquidity_sweeps


FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 60)
    print("PRUEBA DE DETECCIÓN DE LIQUIDITY SWEEPS")
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
    # DETECTAR LIQUIDEZ
    # --------------------------------------------------------

    df = detect_liquidity_levels(
        df,
        tolerance=0.0015
    )

    # --------------------------------------------------------
    # DETECTAR SWEEPS
    # --------------------------------------------------------

    df = detect_liquidity_sweeps(df)

    bullish_sweeps = df[df["bullish_sweep"]]
    bearish_sweeps = df[df["bearish_sweep"]]

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    print(
        f"\nBullish Sweeps detectados: "
        f"{len(bullish_sweeps)}"
    )

    print(
        f"Bearish Sweeps detectados: "
        f"{len(bearish_sweeps)}"
    )

    # --------------------------------------------------------
    # ÚLTIMOS BULLISH SWEEPS
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BULLISH SWEEPS")
    print("=" * 60)

    print(
        bullish_sweeps[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "sweep_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # ÚLTIMOS BEARISH SWEEPS
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BEARISH SWEEPS")
    print("=" * 60)

    print(
        bearish_sweeps[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "sweep_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()