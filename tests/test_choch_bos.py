import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos


FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 60)
    print("PRUEBA DE DETECCIÓN DE CHOCH Y BOS")
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

    # Filtrar resultados
    choch_bullish = df[df["choch_bullish"]]
    choch_bearish = df[df["choch_bearish"]]

    bos_bullish = df[df["bos_bullish"]]
    bos_bearish = df[df["bos_bearish"]]

    # --------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    print(f"\nBullish CHOCH detectados: {len(choch_bullish)}")
    print(f"Bearish CHOCH detectados: {len(choch_bearish)}")

    print(f"\nBullish BOS detectados: {len(bos_bullish)}")
    print(f"Bearish BOS detectados: {len(bos_bearish)}")

    # --------------------------------------------------
    # ÚLTIMOS CHOCH ALCISTAS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BULLISH CHOCH")
    print("=" * 60)

    print(
        choch_bullish[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "structure_break_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    # --------------------------------------------------
    # ÚLTIMOS CHOCH BAJISTAS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BEARISH CHOCH")
    print("=" * 60)

    print(
        choch_bearish[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "structure_break_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    # --------------------------------------------------
    # ÚLTIMOS BOS ALCISTAS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BULLISH BOS")
    print("=" * 60)

    print(
        bos_bullish[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "structure_break_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )

    # --------------------------------------------------
    # ÚLTIMOS BOS BAJISTAS
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ÚLTIMOS 10 BEARISH BOS")
    print("=" * 60)

    print(
        bos_bearish[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "structure_break_level"
            ]
        ]
        .tail(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()