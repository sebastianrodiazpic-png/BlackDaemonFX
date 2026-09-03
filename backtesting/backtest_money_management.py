import pandas as pd


# ==================================================
# CALCULAR RIESGO MONETARIO
# ==================================================

def calculate_risk_amount(
    balance,
    risk_percent
):
    """
    Calcula cuánto dinero se arriesga
    en una operación.

    Ejemplo:

    Balance: 1000
    Riesgo: 1%

    Riesgo monetario:
    1000 * 1% = 10
    """

    balance = float(balance)
    risk_percent = float(risk_percent)

    if balance <= 0:
        return 0.0

    if risk_percent <= 0:
        return 0.0

    risk_amount = (
        balance * risk_percent / 100
    )

    return round(
        float(risk_amount),
        4
    )


# ==================================================
# CALCULAR RESULTADO MONETARIO
# ==================================================

def calculate_trade_pnl(
    risk_amount,
    realized_rr
):
    """
    Calcula la ganancia o pérdida monetaria
    utilizando el R:R realizado.

    Ejemplos:

    Riesgo: $10
    R realizado: +2R

    Resultado:
    +$20


    Riesgo: $10
    R realizado: -1R

    Resultado:
    -$10
    """

    risk_amount = float(risk_amount)
    realized_rr = float(realized_rr)

    pnl = (
        risk_amount * realized_rr
    )

    return round(
        float(pnl),
        4
    )


# ==================================================
# SIMULAR CAPITAL SOBRE OPERACIONES
# ==================================================

def apply_money_management(
    trades,
    initial_balance=1000.0,
    risk_percent=1.0,
    compound=True
):
    """
    Aplica gestión monetaria a los resultados
    de un backtest.

    Parámetros
    ----------

    trades:
        DataFrame generado por trade_simulator.py.

    initial_balance:
        Capital inicial.

    risk_percent:
        Porcentaje de riesgo por operación.

    compound:
        True:
            El riesgo se recalcula según
            el balance actual.

        False:
            El riesgo siempre se calcula
            utilizando el capital inicial.

    Retorna
    -------

    DataFrame con:

    - trade_number
    - balance_before
    - risk_percent
    - risk_amount
    - realized_rr
    - pnl
    - balance_after
    - equity
    - peak_balance
    - drawdown_amount
    - drawdown_percent
    """

    # ==============================================
    # VALIDACIONES
    # ==============================================

    if trades is None:
        raise ValueError(
            "El DataFrame trades no puede ser None."
        )

    if trades.empty:
        return pd.DataFrame()

    if "result" not in trades.columns:
        raise ValueError(
            "Falta la columna 'result' en trades."
        )

    if "realized_rr" not in trades.columns:
        raise ValueError(
            "Falta la columna 'realized_rr' en trades."
        )

    initial_balance = float(initial_balance)
    risk_percent = float(risk_percent)

    if initial_balance <= 0:
        raise ValueError(
            "initial_balance debe ser mayor que 0."
        )

    if risk_percent <= 0:
        raise ValueError(
            "risk_percent debe ser mayor que 0."
        )

    # ==============================================
    # COPIA DE DATOS
    # ==============================================

    df = trades.copy()

    # ==============================================
    # NORMALIZAR RESULTADOS
    # ==============================================

    df["result"] = (
        df["result"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["realized_rr"] = pd.to_numeric(
        df["realized_rr"],
        errors="coerce"
    ).fillna(0.0)

    # ==============================================
    # ORDENAR POR TIEMPO
    # ==============================================

    if "entry_time" in df.columns:

        df["entry_time"] = pd.to_datetime(
            df["entry_time"],
            utc=True,
            errors="coerce"
        )

        df = df.sort_values(
            by="entry_time"
        ).reset_index(
            drop=True
        )

    # ==============================================
    # VARIABLES DEL BACKTEST
    # ==============================================

    balance = initial_balance

    peak_balance = initial_balance

    fixed_risk_amount = calculate_risk_amount(
        balance=initial_balance,
        risk_percent=risk_percent
    )

    records = []

    # ==============================================
    # RECORRER OPERACIONES
    # ==============================================

    for index, trade in df.iterrows():

        result = trade["result"]

        realized_rr = float(
            trade["realized_rr"]
        )

        balance_before = balance

        # ------------------------------------------
        # CALCULAR RIESGO
        # ------------------------------------------

        if result in ["WIN", "LOSS"]:

            if compound:

                risk_amount = calculate_risk_amount(
                    balance=balance_before,
                    risk_percent=risk_percent
                )

            else:

                risk_amount = fixed_risk_amount

        else:

            # OPEN y AMBIGUOUS no modifican
            # el capital por ahora.

            risk_amount = 0.0

        # ------------------------------------------
        # CALCULAR PNL
        # ------------------------------------------

        if result in ["WIN", "LOSS"]:

            pnl = calculate_trade_pnl(
                risk_amount=risk_amount,
                realized_rr=realized_rr
            )

        else:

            pnl = 0.0

        # ------------------------------------------
        # NUEVO BALANCE
        # ------------------------------------------

        balance_after = (
            balance_before + pnl
        )

        # Protección contra balance negativo
        if balance_after < 0:
            balance_after = 0.0

        balance = balance_after

        # ------------------------------------------
        # NUEVO PEAK
        # ------------------------------------------

        if balance_after > peak_balance:

            peak_balance = balance_after

        # ------------------------------------------
        # DRAWDOWN
        # ------------------------------------------

        drawdown_amount = (
            balance_after - peak_balance
        )

        if peak_balance > 0:

            drawdown_percent = (
                drawdown_amount
                / peak_balance
            ) * 100

        else:

            drawdown_percent = 0.0

        # ------------------------------------------
        # CREAR REGISTRO
        # ------------------------------------------

        record = trade.to_dict()

        record.update({

            "trade_number": index + 1,

            "balance_before": round(
                float(balance_before),
                4
            ),

            "risk_percent": round(
                float(risk_percent),
                4
            ),

            "risk_amount": round(
                float(risk_amount),
                4
            ),

            "pnl": round(
                float(pnl),
                4
            ),

            "balance_after": round(
                float(balance_after),
                4
            ),

            "equity": round(
                float(balance_after),
                4
            ),

            "peak_balance": round(
                float(peak_balance),
                4
            ),

            "drawdown_amount": round(
                float(drawdown_amount),
                4
            ),

            "drawdown_percent": round(
                float(drawdown_percent),
                4
            )

        })

        records.append(
            record
        )

    # ==============================================
    # DATAFRAME FINAL
    # ==============================================

    results_df = pd.DataFrame(
        records
    )

    return results_df


# ==================================================
# RESUMEN FINANCIERO
# ==================================================

def get_money_management_summary(
    trades,
    initial_balance=1000.0
):
    """
    Genera estadísticas financieras
    después de aplicar money management.
    """

    # ==============================================
    # VALIDAR
    # ==============================================

    if trades is None or trades.empty:

        return {

            "initial_balance": float(
                initial_balance
            ),

            "final_balance": float(
                initial_balance
            ),

            "net_profit": 0.0,

            "net_profit_percent": 0.0,

            "gross_profit": 0.0,

            "gross_loss": 0.0,

            "profit_factor": 0.0,

            "max_drawdown_amount": 0.0,

            "max_drawdown_percent": 0.0,

            "total_risk_amount": 0.0

        }

    df = trades.copy()

    # ==============================================
    # COLUMNAS
    # ==============================================

    if "pnl" not in df.columns:

        raise ValueError(
            "Falta la columna 'pnl'. "
            "Primero ejecuta apply_money_management()."
        )

    if "balance_after" not in df.columns:

        raise ValueError(
            "Falta la columna 'balance_after'."
        )

    # ==============================================
    # CONVERSIONES
    # ==============================================

    df["pnl"] = pd.to_numeric(
        df["pnl"],
        errors="coerce"
    ).fillna(0.0)

    df["balance_after"] = pd.to_numeric(
        df["balance_after"],
        errors="coerce"
    ).fillna(float(initial_balance))

    if "drawdown_amount" in df.columns:

        df["drawdown_amount"] = pd.to_numeric(
            df["drawdown_amount"],
            errors="coerce"
        ).fillna(0.0)

    else:

        df["drawdown_amount"] = 0.0

    if "drawdown_percent" in df.columns:

        df["drawdown_percent"] = pd.to_numeric(
            df["drawdown_percent"],
            errors="coerce"
        ).fillna(0.0)

    else:

        df["drawdown_percent"] = 0.0

    if "risk_amount" in df.columns:

        df["risk_amount"] = pd.to_numeric(
            df["risk_amount"],
            errors="coerce"
        ).fillna(0.0)

    else:

        df["risk_amount"] = 0.0

    # ==============================================
    # CAPITAL FINAL
    # ==============================================

    final_balance = float(
        df["balance_after"].iloc[-1]
    )

    net_profit = (
        final_balance - float(initial_balance)
    )

    # ==============================================
    # GANANCIA Y PÉRDIDA BRUTA
    # ==============================================

    gross_profit = float(
        df.loc[
            df["pnl"] > 0,
            "pnl"
        ].sum()
    )

    gross_loss = float(
        abs(
            df.loc[
                df["pnl"] < 0,
                "pnl"
            ].sum()
        )
    )

    # ==============================================
    # PROFIT FACTOR
    # ==============================================

    if gross_loss > 0:

        profit_factor = (
            gross_profit / gross_loss
        )

    elif gross_profit > 0:

        profit_factor = float("inf")

    else:

        profit_factor = 0.0

    # ==============================================
    # RENTABILIDAD
    # ==============================================

    if initial_balance > 0:

        net_profit_percent = (
            net_profit / initial_balance
        ) * 100

    else:

        net_profit_percent = 0.0

    # ==============================================
    # DRAWDOWN MÁXIMO
    # ==============================================

    max_drawdown_amount = float(
        df["drawdown_amount"].min()
    )

    max_drawdown_percent = float(
        df["drawdown_percent"].min()
    )

    # ==============================================
    # RIESGO TOTAL OPERADO
    # ==============================================

    total_risk_amount = float(
        df["risk_amount"].sum()
    )

    # ==============================================
    # RETORNAR
    # ==============================================

    return {

        "initial_balance": round(
            float(initial_balance),
            4
        ),

        "final_balance": round(
            float(final_balance),
            4
        ),

        "net_profit": round(
            float(net_profit),
            4
        ),

        "net_profit_percent": round(
            float(net_profit_percent),
            4
        ),

        "gross_profit": round(
            float(gross_profit),
            4
        ),

        "gross_loss": round(
            float(gross_loss),
            4
        ),

        "profit_factor": round(
            float(profit_factor),
            4
        ) if profit_factor != float("inf")
        else float("inf"),

        "max_drawdown_amount": round(
            float(max_drawdown_amount),
            4
        ),

        "max_drawdown_percent": round(
            float(max_drawdown_percent),
            4
        ),

        "total_risk_amount": round(
            float(total_risk_amount),
            4
        )

    }


# ==================================================
# EXPORTAR RESULTADOS
# ==================================================

def save_money_management_results(
    trades,
    file_path
):
    """
    Guarda los resultados financieros
    en un archivo CSV.
    """

    if trades is None:

        raise ValueError(
            "No hay operaciones para guardar."
        )

    trades.to_csv(
        file_path,
        index=False
    )

    return file_path