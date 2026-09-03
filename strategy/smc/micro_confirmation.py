import pandas as pd


def detect_micro_confirmation(
    df,
    setup_type,
    start_time
):

    if df.empty:

        return None

    data = df.copy()

    data["time"] = pd.to_datetime(
        data["time"],
        utc=True
    )

    data = (
        data
        .sort_values("time")
        .reset_index(drop=True)
    )

    start_time = pd.to_datetime(
        start_time,
        utc=True
    )

    future = data[
        data["time"] >= start_time
    ].copy()

    if len(future) < 3:

        return None

    for i in range(1, len(future)):

        current = future.iloc[i]

        previous = future.iloc[i - 1]

        current_open = float(
            current["open"]
        )

        current_close = float(
            current["close"]
        )

        previous_high = float(
            previous["high"]
        )

        previous_low = float(
            previous["low"]
        )

        if setup_type == "long":

            bullish = (
                current_close > current_open
            )

            breaks_structure = (
                current_close > previous_high
            )

            if bullish and breaks_structure:

                return {
                    "confirmed": True,
                    "direction": "long",
                    "time": current["time"],
                    "price": current_close,
                    "confirmation": "micro_bullish_break"
                }

        elif setup_type == "short":

            bearish = (
                current_close < current_open
            )

            breaks_structure = (
                current_close < previous_low
            )

            if bearish and breaks_structure:

                return {
                    "confirmed": True,
                    "direction": "short",
                    "time": current["time"],
                    "price": current_close,
                    "confirmation": "micro_bearish_break"
                }

    return None