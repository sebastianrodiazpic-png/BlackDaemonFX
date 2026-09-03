import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.order_blocks import detect_order_blocks


FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 60)
    print("PRUEBA DE DETECCIÓN DE ORDER BLOCKS")
    print("=" * 60)

    # --------------------------------------------------
    # CARGAR DATOS
    # --------------------------------------------------

    df = pd.read_csv(FILE_PATH)

    df["time"] = pd.to_datetime(df["time"])

    print(f"\nVelas cargadas: {len(df)}")

    # --------------------------------------------------
    # DETECTAR SWINGS
    # --------------------------------------------------

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    # --------------------------------------------------
    # DETECTAR CHOCH Y BOS
    # --------------------------------------------------

    df = detect_choch_bos(df)

    # --------------------------------------------------
    # DETECTAR ORDER BLOCKS
    # --------------------------------------------------

    df = detect_order_blocks(
        df,
        lookback=20
    )

    # --------------------------------------------------
    # FILTRAR RESULTADOS
    # --------------------------------------------------

    bullish_obs = df[df["bullish_order_block"]]

    bearish_obs = df[df["bearish_order_block"]]

    # --------------------------------------------------
    # RESULTADOS GENERALES
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    print(
        f"\nBullish Order Blocks detectados: "
        f"{len(bullish_obs)}"
    )

    print(
        f"Bearish Order Blocks detectados: "
        f"{len(bearish_obs)}"
    )

    # --------------------------------------------------
    # ÚLTIMOS BULLISH ORDER BLOCKS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BULLISH ORDER BLOCKS")
    print("=" * 60)

    if len(bullish_obs) > 0:

        print(
            bullish_obs[
                [
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "ob_high",
                    "ob_low",
                    "ob_type"
                ]
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print("No se detectaron Bullish Order Blocks.")

    # --------------------------------------------------
    # ÚLTIMOS BEARISH ORDER BLOCKS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BEARISH ORDER BLOCKS")
    print("=" * 60)

    if len(bearish_obs) > 0:

        print(
            bearish_obs[
                [
                    "time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "ob_high",
                    "ob_low",
                    "ob_type"
                ]
            ]
            .tail(10)
            .to_string(index=False)
        )

    else:

        print("No se detectaron Bearish Order Blocks.")


if __name__ == "__main__":
    main()