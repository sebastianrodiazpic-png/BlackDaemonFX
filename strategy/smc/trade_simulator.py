import pandas as pd


def simulate_trade(
    df: pd.DataFrame,
    trade: pd.Series,
    max_bars: int = 500
) -> dict:
    """
    Simula una operación utilizando las velas posteriores
    al momento de entrada.

    Estados posibles:

    win
        El Take Profit fue alcanzado.

    loss
        El Stop Loss fue alcanzado.

    expired
        No se alcanzó TP ni SL dentro del máximo de velas.

    ambiguous
        La misma vela tocó TP y SL. Con datos OHLC no es posible
        saber cuál ocurrió primero.
    """

    required_trade_columns = [
        "entry_time",
        "entry_price",
        "stop_loss",
        "take_profit"
    ]

    missing_columns = [
        column
        for column in required_trade_columns
        if column not in trade.index
    ]

    if missing_columns:
        raise ValueError(
            f"Faltan columnas en la operación: {missing_columns}"
        )

    required_price_columns = [
        "time",
        "high",
        "low"
    ]

    missing_price_columns = [
        column
        for column in required_price_columns
        if column not in df.columns
    ]

    if missing_price_columns:
        raise ValueError(
            f"Faltan columnas en el histórico: {missing_price_columns}"
        )

    data = df.copy()

    data["time"] = pd.to_datetime(
        data["time"],
        utc=True
    )

    entry_time = pd.to_datetime(
        trade["entry_time"],
        utc=True
    )

    entry_price = float(
        trade["entry_price"]
    )

    stop_loss = float(
        trade["stop_loss"]
    )

    take_profit = float(
        trade["take_profit"]
    )

    # --------------------------------------------------
    # DETERMINAR DIRECCIÓN
    # --------------------------------------------------

    if "trade_type" in trade.index:

        trade_type = str(
            trade["trade_type"]
        ).lower()

    elif "setup_type" in trade.index:

        trade_type = str(
            trade["setup_type"]
        ).lower()

    else:

        raise ValueError(
            "No se encontró 'trade_type' ni 'setup_type' "
            "para determinar la dirección de la operación."
        )

    if trade_type not in ["long", "short"]:

        raise ValueError(
            f"Tipo de operación no válido: {trade_type}"
        )

    # --------------------------------------------------
    # OBTENER VELAS POSTERIORES A LA ENTRADA
    # --------------------------------------------------

    future_bars = data[
        data["time"] > entry_time
    ].copy()

    future_bars = future_bars.head(
        max_bars
    )

    # --------------------------------------------------
    # SIN VELAS POSTERIORES
    # --------------------------------------------------

    if future_bars.empty:

        return {
            "exit_time": pd.NaT,
            "exit_price": None,
            "result": "expired",
            "exit_reason": "no_future_data",
            "bars_held": 0,
            "pnl_price": 0.0
        }

    # --------------------------------------------------
    # SIMULAR LONG
    # --------------------------------------------------

    if trade_type == "long":

        for bar_number, (_, candle) in enumerate(
            future_bars.iterrows(),
            start=1
        ):

            high = float(
                candle["high"]
            )

            low = float(
                candle["low"]
            )

            hit_sl = (
                low <= stop_loss
            )

            hit_tp = (
                high >= take_profit
            )

            # Ambos niveles fueron tocados
            if hit_sl and hit_tp:

                return {
                    "exit_time": candle["time"],
                    "exit_price": None,
                    "result": "ambiguous",
                    "exit_reason": "sl_and_tp_same_bar",
                    "bars_held": bar_number,
                    "pnl_price": 0.0
                }

            # Stop Loss
            if hit_sl:

                return {
                    "exit_time": candle["time"],
                    "exit_price": stop_loss,
                    "result": "loss",
                    "exit_reason": "stop_loss",
                    "bars_held": bar_number,
                    "pnl_price": (
                        stop_loss - entry_price
                    )
                }

            # Take Profit
            if hit_tp:

                return {
                    "exit_time": candle["time"],
                    "exit_price": take_profit,
                    "result": "win",
                    "exit_reason": "take_profit",
                    "bars_held": bar_number,
                    "pnl_price": (
                        take_profit - entry_price
                    )
                }

    # --------------------------------------------------
    # SIMULAR SHORT
    # --------------------------------------------------

    elif trade_type == "short":

        for bar_number, (_, candle) in enumerate(
            future_bars.iterrows(),
            start=1
        ):

            high = float(
                candle["high"]
            )

            low = float(
                candle["low"]
            )

            hit_sl = (
                high >= stop_loss
            )

            hit_tp = (
                low <= take_profit
            )

            # Ambos niveles fueron tocados
            if hit_sl and hit_tp:

                return {
                    "exit_time": candle["time"],
                    "exit_price": None,
                    "result": "ambiguous",
                    "exit_reason": "sl_and_tp_same_bar",
                    "bars_held": bar_number,
                    "pnl_price": 0.0
                }

            # Stop Loss
            if hit_sl:

                return {
                    "exit_time": candle["time"],
                    "exit_price": stop_loss,
                    "result": "loss",
                    "exit_reason": "stop_loss",
                    "bars_held": bar_number,
                    "pnl_price": (
                        entry_price - stop_loss
                    )
                }

            # Take Profit
            if hit_tp:

                return {
                    "exit_time": candle["time"],
                    "exit_price": take_profit,
                    "result": "win",
                    "exit_reason": "take_profit",
                    "bars_held": bar_number,
                    "pnl_price": (
                        entry_price - take_profit
                    )
                }

    # --------------------------------------------------
    # EXPIRÓ
    # --------------------------------------------------

    last_candle = future_bars.iloc[-1]

    return {
        "exit_time": last_candle["time"],
        "exit_price": float(
            last_candle["close"]
        ) if "close" in last_candle.index else None,
        "result": "expired",
        "exit_reason": "max_bars_reached",
        "bars_held": len(future_bars),
        "pnl_price": 0.0
    }


def simulate_trades(
    df: pd.DataFrame,
    trades: pd.DataFrame,
    max_bars: int = 500
) -> pd.DataFrame:
    """
    Simula múltiples operaciones y agrega el resultado
    de cada una al DataFrame original.
    """

    if trades.empty:

        return trades.copy()

    results = []

    for _, trade in trades.iterrows():

        simulation = simulate_trade(
            df=df,
            trade=trade,
            max_bars=max_bars
        )

        result_row = trade.to_dict()

        result_row.update(
            simulation
        )

        results.append(
            result_row
        )

    simulated_trades = pd.DataFrame(
        results
    )

    if not simulated_trades.empty:

        simulated_trades = (
            simulated_trades
            .sort_values("entry_time")
            .reset_index(drop=True)
        )

    return simulated_trades