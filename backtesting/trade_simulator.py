import pandas as pd


# ==================================================
# CALCULAR R:R REALIZADO
# ==================================================

def calculate_realized_rr(
    direction,
    entry_price,
    stop_loss,
    exit_price
):
    """
    Calcula el resultado real de una operación
    expresado en unidades de riesgo (R).

    Ejemplos con un riesgo de 100 puntos:

    BUY
    Entry: 1000
    SL: 900
    Exit: 1200
    Resultado: +2R

    BUY
    Entry: 1000
    SL: 900
    Exit: 900
    Resultado: -1R
    """

    direction = str(direction).upper()

    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    exit_price = float(exit_price)

    # ==============================================
    # BUY
    # ==============================================

    if direction == "BUY":

        risk = entry_price - stop_loss
        profit = exit_price - entry_price

    # ==============================================
    # SELL
    # ==============================================

    elif direction == "SELL":

        risk = stop_loss - entry_price
        profit = entry_price - exit_price

    else:

        raise ValueError(
            f"Dirección inválida: {direction}"
        )

    # ==============================================
    # VALIDAR RIESGO
    # ==============================================

    if risk <= 0:

        return 0.0

    realized_rr = profit / risk

    return round(
        float(realized_rr),
        4
    )


# ==================================================
# CALCULAR R:R PLANIFICADO
# ==================================================

def calculate_planned_rr(
    entry_price,
    stop_loss,
    take_profit
):
    """
    Calcula el Risk:Reward teórico de la operación.

    Ejemplo:

    Riesgo = 100 puntos
    Reward = 200 puntos

    R:R = 2.0
    """

    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    take_profit = float(take_profit)

    risk = abs(
        entry_price - stop_loss
    )

    reward = abs(
        take_profit - entry_price
    )

    if risk <= 0:

        return 0.0

    return round(
        reward / risk,
        4
    )


# ==================================================
# SIMULAR UNA OPERACIÓN
# ==================================================

def simulate_trade(
    candles,
    entry_time,
    direction,
    entry_price,
    stop_loss,
    take_profit,
    max_bars=None
):
    """
    Simula una operación utilizando las velas
    posteriores a la entrada.

    Resultados posibles:

    WIN
    LOSS
    OPEN
    AMBIGUOUS

    También calcula:

    - planned_rr
    - realized_rr
    - exit_price
    - exit_time
    - bars_held
    """

    candles = candles.copy()

    # ==============================================
    # VALIDAR TIEMPO
    # ==============================================

    candles["time"] = pd.to_datetime(
        candles["time"],
        utc=True
    )

    entry_time = pd.to_datetime(
        entry_time,
        utc=True
    )

    # ==============================================
    # NORMALIZAR DIRECCIÓN
    # ==============================================

    direction = str(direction).upper()

    if direction not in ["BUY", "SELL"]:

        raise ValueError(
            f"Dirección inválida: {direction}"
        )

    # ==============================================
    # CONVERTIR PRECIOS
    # ==============================================

    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    take_profit = float(take_profit)

    # ==============================================
    # CALCULAR R:R PLANIFICADO
    # ==============================================

    planned_rr = calculate_planned_rr(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit
    )

    # ==============================================
    # OBTENER VELAS FUTURAS
    # ==============================================

    future_candles = candles[
        candles["time"] > entry_time
    ].copy()

    # ==============================================
    # LIMITAR NÚMERO DE VELAS
    # ==============================================

    if max_bars is not None:

        future_candles = future_candles.head(
            max_bars
        )

    # ==============================================
    # RECORRER VELAS
    # ==============================================

    for bars_held, (_, candle) in enumerate(
        future_candles.iterrows(),
        start=1
    ):

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        candle_time = candle["time"]

        # ==========================================
        # BUY
        # ==========================================

        if direction == "BUY":

            hit_stop = (
                low <= stop_loss
            )

            hit_target = (
                high >= take_profit
            )

            # --------------------------------------
            # AMBIGUOUS
            # --------------------------------------

            if hit_stop and hit_target:

                return {
                    "result": "AMBIGUOUS",
                    "exit_time": candle_time,
                    "exit_price": None,
                    "bars_held": bars_held,
                    "planned_rr": planned_rr,
                    "realized_rr": 0.0,
                    "reason": (
                        "Stop Loss y Take Profit "
                        "fueron alcanzados en la "
                        "misma vela."
                    )
                }

            # --------------------------------------
            # LOSS
            # --------------------------------------

            if hit_stop:

                exit_price = stop_loss

                realized_rr = (
                    calculate_realized_rr(
                        direction=direction,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        exit_price=exit_price
                    )
                )

                return {
                    "result": "LOSS",
                    "exit_time": candle_time,
                    "exit_price": float(exit_price),
                    "bars_held": bars_held,
                    "planned_rr": planned_rr,
                    "realized_rr": realized_rr,
                    "reason": "Stop Loss alcanzado."
                }

            # --------------------------------------
            # WIN
            # --------------------------------------

            if hit_target:

                exit_price = take_profit

                realized_rr = (
                    calculate_realized_rr(
                        direction=direction,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        exit_price=exit_price
                    )
                )

                return {
                    "result": "WIN",
                    "exit_time": candle_time,
                    "exit_price": float(exit_price),
                    "bars_held": bars_held,
                    "planned_rr": planned_rr,
                    "realized_rr": realized_rr,
                    "reason": "Take Profit alcanzado."
                }

        # ==========================================
        # SELL
        # ==========================================

        elif direction == "SELL":

            hit_stop = (
                high >= stop_loss
            )

            hit_target = (
                low <= take_profit
            )

            # --------------------------------------
            # AMBIGUOUS
            # --------------------------------------

            if hit_stop and hit_target:

                return {
                    "result": "AMBIGUOUS",
                    "exit_time": candle_time,
                    "exit_price": None,
                    "bars_held": bars_held,
                    "planned_rr": planned_rr,
                    "realized_rr": 0.0,
                    "reason": (
                        "Stop Loss y Take Profit "
                        "fueron alcanzados en la "
                        "misma vela."
                    )
                }

            # --------------------------------------
            # LOSS
            # --------------------------------------

            if hit_stop:

                exit_price = stop_loss

                realized_rr = (
                    calculate_realized_rr(
                        direction=direction,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        exit_price=exit_price
                    )
                )

                return {
                    "result": "LOSS",
                    "exit_time": candle_time,
                    "exit_price": float(exit_price),
                    "bars_held": bars_held,
                    "planned_rr": planned_rr,
                    "realized_rr": realized_rr,
                    "reason": "Stop Loss alcanzado."
                }

            # --------------------------------------
            # WIN
            # --------------------------------------

            if hit_target:

                exit_price = take_profit

                realized_rr = (
                    calculate_realized_rr(
                        direction=direction,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        exit_price=exit_price
                    )
                )

                return {
                    "result": "WIN",
                    "exit_time": candle_time,
                    "exit_price": float(exit_price),
                    "bars_held": bars_held,
                    "planned_rr": planned_rr,
                    "realized_rr": realized_rr,
                    "reason": "Take Profit alcanzado."
                }

    # ==============================================
    # OPERACIÓN ABIERTA
    # ==============================================

    return {
        "result": "OPEN",
        "exit_time": None,
        "exit_price": None,
        "bars_held": len(future_candles),
        "planned_rr": planned_rr,
        "realized_rr": 0.0,
        "reason": (
            "La operación no alcanzó "
            "Stop Loss ni Take Profit "
            "dentro del histórico analizado."
        )
    }


# ==================================================
# SIMULAR TODAS LAS OPERACIONES
# ==================================================

def simulate_all_trades(
    candles,
    entries,
    max_bars=None
):
    """
    Simula todas las entradas confirmadas.
    """

    results = []

    entries = entries.copy()

    if entries.empty:

        return pd.DataFrame()

    # ==============================================
    # VALIDAR COLUMNAS
    # ==============================================

    required_columns = [
        "entry_time",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit"
    ]

    missing = [
        column
        for column in required_columns
        if column not in entries.columns
    ]

    if missing:

        raise ValueError(
            "Faltan columnas en entries: "
            f"{missing}"
        )

    # ==============================================
    # SIMULAR CADA TRADE
    # ==============================================

    for _, entry in entries.iterrows():

        simulation = simulate_trade(
            candles=candles,
            entry_time=entry["entry_time"],
            direction=entry["direction"],
            entry_price=entry["entry_price"],
            stop_loss=entry["stop_loss"],
            take_profit=entry["take_profit"],
            max_bars=max_bars
        )

        trade = entry.to_dict()

        trade.update(
            simulation
        )

        results.append(
            trade
        )

    results_df = pd.DataFrame(
        results
    )

    return results_df


# ==================================================
# ALIAS PARA COMPATIBILIDAD
# ==================================================

def simulate_trades(
    candles,
    entries,
    max_bars=None
):
    """
    Alias de compatibilidad.

    Permite utilizar:

        simulate_trades(...)

    en los tests existentes.
    """

    return simulate_all_trades(
        candles=candles,
        entries=entries,
        max_bars=max_bars
    )


# ==================================================
# RESUMEN DEL BACKTEST
# ==================================================

def get_backtest_summary(
    trades
):
    """
    Genera un resumen estadístico
    de las operaciones simuladas.
    """

    if trades is None or trades.empty:

        return {
            "total_trades": 0,
            "closed_trades": 0,
            "wins": 0,
            "losses": 0,
            "open": 0,
            "ambiguous": 0,
            "win_rate": 0.0,
            "average_planned_rr": 0.0,
            "average_realized_rr": 0.0,
            "total_realized_r": 0.0
        }

    df = trades.copy()

    # ==============================================
    # NORMALIZAR RESULTADO
    # ==============================================

    df["result"] = (
        df["result"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    total_trades = len(df)

    wins = int(
        (df["result"] == "WIN").sum()
    )

    losses = int(
        (df["result"] == "LOSS").sum()
    )

    open_trades = int(
        (df["result"] == "OPEN").sum()
    )

    ambiguous = int(
        (df["result"] == "AMBIGUOUS").sum()
    )

    closed_trades = (
        wins + losses
    )

    # ==============================================
    # WIN RATE
    # ==============================================

    if closed_trades > 0:

        win_rate = (
            wins / closed_trades
        ) * 100

    else:

        win_rate = 0.0

    # ==============================================
    # R:R PROMEDIO
    # ==============================================

    if (
        "planned_rr" in df.columns
        and len(df) > 0
    ):

        average_planned_rr = (
            df["planned_rr"]
            .mean()
        )

    else:

        average_planned_rr = 0.0

    closed_df = df[
        df["result"].isin(
            ["WIN", "LOSS"]
        )
    ].copy()

    if (
        "realized_rr" in closed_df.columns
        and not closed_df.empty
    ):

        average_realized_rr = (
            closed_df["realized_rr"]
            .mean()
        )

        total_realized_r = (
            closed_df["realized_rr"]
            .sum()
        )

    else:

        average_realized_rr = 0.0
        total_realized_r = 0.0

    return {

        "total_trades": total_trades,

        "closed_trades": closed_trades,

        "wins": wins,

        "losses": losses,

        "open": open_trades,

        "ambiguous": ambiguous,

        "win_rate": round(
            float(win_rate),
            2
        ),

        "average_planned_rr": round(
            float(average_planned_rr),
            4
        ),

        "average_realized_rr": round(
            float(average_realized_rr),
            4
        ),

        "total_realized_r": round(
            float(total_realized_r),
            4
        )
    }