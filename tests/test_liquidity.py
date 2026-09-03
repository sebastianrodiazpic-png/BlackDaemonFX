import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.liquidity import detect_liquidity_levels


FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 60)
    print("PRUEBA DE DETECCIÓN DE LIQUIDEZ")
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
    # BUY-SIDE LIQUIDITY
    # --------------------------------------------------------

    buy_side = df[
        df["buy_side_liquidity"]
    ]

    # --------------------------------------------------------
    # SELL-SIDE LIQUIDITY
    # --------------------------------------------------------

    sell_side = df[
        df["sell_side_liquidity"]
    ]

    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    print(
        f"\nBuy-Side Liquidity detectada: "
        f"{len(buy_side)}"
    )

    print(
        f"Sell-Side Liquidity detectada: "
        f"{len(sell_side)}"
    )

    # --------------------------------------------------------
    # ÚLTIMOS NIVELES BUY SIDE
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 NIVELES DE BUY-SIDE LIQUIDITY")
    print("=" * 60)

    print(
        buy_side[
            [
                "time",
                "high",
                "liquidity_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # ÚLTIMOS NIVELES SELL SIDE
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 NIVELES DE SELL-SIDE LIQUIDITY")
    print("=" * 60)

    print(
        sell_side[
            [
                "time",
                "low",
                "liquidity_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()