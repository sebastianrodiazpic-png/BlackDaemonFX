import pandas as pd


def calculate_ob_displacement(
    df,
    ob_time,
    ob_type,
    lookforward=10
):

    if df.empty:

        return 0.0

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

    positions = data.index[
        data["time"] == pd.to_datetime(
            ob_time,
            utc=True
        )
    ]

    if len(positions) == 0:

        return 0.0

    index = positions[0]

    future = data.iloc[
        index + 1:
        index + 1 + lookforward
    ]

    if future.empty:

        return 0.0

    ob_close = float(
        data.iloc[index]["close"]
    )

    if ob_type == "bullish":

        max_price = float(
            future["high"].max()
        )

        return max(
            0.0,
            max_price - ob_close
        )

    elif ob_type == "bearish":

        min_price = float(
            future["low"].min()
        )

        return max(
            0.0,
            ob_close - min_price
        )

    return 0.0


def calculate_average_range(
    df,
    period=20
):

    if df.empty:

        return 0.0

    data = df.copy()

    ranges = (
        data["high"].astype(float)
        -
        data["low"].astype(float)
    )

    recent_ranges = ranges.tail(period)

    if recent_ranges.empty:

        return 0.0

    return float(
        recent_ranges.mean()
    )


def calculate_ob_score(
    trend_aligned=False,
    correct_zone=False,
    liquidity_sweep=False,
    choch=False,
    bos=False,
    strong_displacement=False,
    fresh=True,
    retest_clean=False,
    micro_confirmation=False
):

    score = 0

    if trend_aligned:
        score += 20

    if correct_zone:
        score += 15

    if liquidity_sweep:
        score += 15

    if choch:
        score += 10

    if bos:
        score += 10

    if strong_displacement:
        score += 10

    if fresh:
        score += 10

    if retest_clean:
        score += 5

    if micro_confirmation:
        score += 5

    return min(score, 100)


def get_ob_grade(score):

    score = float(score)

    if score >= 85:
        return "A+"

    if score >= 70:
        return "A"

    if score >= 60:
        return "B"

    if score >= 40:
        return "C"

    return "REJECT"


def evaluate_order_block(
    trend_aligned=False,
    correct_zone=False,
    liquidity_sweep=False,
    choch=False,
    bos=False,
    strong_displacement=False,
    ob_touches=0,
    retest_clean=False,
    micro_confirmation=False,
    max_touches=1
):

    fresh = (
        ob_touches <= max_touches
    )

    score = calculate_ob_score(
        trend_aligned=trend_aligned,
        correct_zone=correct_zone,
        liquidity_sweep=liquidity_sweep,
        choch=choch,
        bos=bos,
        strong_displacement=strong_displacement,
        fresh=fresh,
        retest_clean=retest_clean,
        micro_confirmation=micro_confirmation
    )

    grade = get_ob_grade(score)

    return {
        "ob_score": score,
        "ob_grade": grade,
        "ob_fresh": fresh,
        "ob_touches": int(ob_touches),
        "ob_valid": (
            fresh
            and grade != "REJECT"
        )
    }