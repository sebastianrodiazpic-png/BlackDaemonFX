import pandas as pd
import numpy as np


# ============================================================
# MONEY MANAGEMENT SMC
# ============================================================

DEFAULT_INITIAL_BALANCE = 10000.0
DEFAULT_RISK_PERCENT = 1.0


# ============================================================
# VALIDACIONES
# ============================================================

def validate_balance(balance):
    """
    Valida que el balance sea un número válido y mayor que cero.
    """

    if balance is None:
        raise ValueError(
            "El balance no puede ser None."
        )

    try:
        balance = float(balance)

    except (TypeError, ValueError):

        raise ValueError(
            f"Balance inválido: {balance}"
        )

    if not np.isfinite(balance):

        raise ValueError(
            f"El balance no es finito: {balance}"
        )

    if balance <= 0:

        raise ValueError(
            "El balance debe ser mayor que cero. "
            f"Balance recibido: {balance}"
        )

    return float(balance)


def validate_risk_percent(risk_percent):
    """
    Valida el porcentaje de riesgo.
    """

    if risk_percent is None:

        raise ValueError(
            "El porcentaje de riesgo no puede ser None."
        )

    try:
        risk_percent = float(risk_percent)

    except (TypeError, ValueError):

        raise ValueError(
            f"Porcentaje de riesgo inválido: {risk_percent}"
        )

    if not np.isfinite(risk_percent):

        raise ValueError(
            "El porcentaje de riesgo no es finito: "
            f"{risk_percent}"
        )

    if risk_percent <= 0:

        raise ValueError(
            "El porcentaje de riesgo debe ser mayor que cero: "
            f"{risk_percent}"
        )

    if risk_percent > 100:

        raise ValueError(
            "El porcentaje de riesgo no puede ser mayor a 100: "
            f"{risk_percent}"
        )

    return float(risk_percent)


def validate_pnl(pnl):
    """
    Valida el PnL de una operación.
    """

    if pnl is None:

        return 0.0

    if pd.isna(pnl):

        return 0.0

    try:
        pnl = float(pnl)

    except (TypeError, ValueError):

        raise ValueError(
            f"PnL inválido: {pnl}"
        )

    if not np.isfinite(pnl):

        raise ValueError(
            f"PnL no válido: {pnl}"
        )

    return float(pnl)


def validate_dataframe(trades):
    """
    Valida que trades sea un DataFrame.
    """

    if trades is None:

        raise ValueError(
            "Las operaciones no pueden ser None."
        )

    if not isinstance(trades, pd.DataFrame):

        raise TypeError(
            "trades debe ser un pandas DataFrame."
        )

    return True


# ============================================================
# CÁLCULO DE RIESGO
# ============================================================

def calculate_risk_amount(
    balance,
    risk_percent=DEFAULT_RISK_PERCENT
):
    """
    Calcula cuánto dinero se arriesgará.

    Fórmula:

        risk_amount =
            balance * (risk_percent / 100)

    Ejemplo:

        balance = 10000
        risk_percent = 1

        risk_amount = 100
    """

    balance = validate_balance(
        balance
    )

    risk_percent = validate_risk_percent(
        risk_percent
    )

    risk_amount = (
        balance
        * (
            risk_percent / 100.0
        )
    )

    return float(
        risk_amount
    )


# ============================================================
# ACTUALIZACIÓN DE BALANCE
# ============================================================

def update_balance(
    balance,
    pnl
):
    """
    Actualiza el balance después de una operación.

    Fórmula:

        new_balance = balance + pnl

    Nota:
    Si el resultado es menor o igual a cero,
    se devuelve 0.0.
    """

    balance = validate_balance(
        balance
    )

    pnl = validate_pnl(
        pnl
    )

    new_balance = (
        balance + pnl
    )

    if new_balance <= 0:

        return 0.0

    return float(
        new_balance
    )


# ============================================================
# APLICAR MONEY MANAGEMENT A UNA OPERACIÓN
# ============================================================

def apply_money_management_to_trade(
    trade,
    current_balance,
    risk_percent=DEFAULT_RISK_PERCENT
):
    """
    Aplica Money Management a una sola operación.

    Agrega:

        balance_before
        risk_percent
        risk_amount
        balance_after

    Retorna:

        trade
        new_balance
    """

    if trade is None:

        raise ValueError(
            "La operación no puede ser None."
        )

    current_balance = validate_balance(
        current_balance
    )

    risk_percent = validate_risk_percent(
        risk_percent
    )

    trade = trade.copy()

    # ========================================================
    # BALANCE ANTES
    # ========================================================

    balance_before = float(
        current_balance
    )

    # ========================================================
    # RIESGO
    # ========================================================

    risk_amount = calculate_risk_amount(
        balance=balance_before,
        risk_percent=risk_percent
    )

    # ========================================================
    # PNL
    # ========================================================

    pnl = trade.get(
        "pnl",
        0.0
    )

    pnl = validate_pnl(
        pnl
    )

    # ========================================================
    # BALANCE DESPUÉS
    # ========================================================

    balance_after = update_balance(
        balance=balance_before,
        pnl=pnl
    )

    # ========================================================
    # GUARDAR INFORMACIÓN
    # ========================================================

    trade[
        "balance_before"
    ] = balance_before

    trade[
        "risk_percent"
    ] = risk_percent

    trade[
        "risk_amount"
    ] = risk_amount

    trade[
        "balance_after"
    ] = balance_after

    return (
        trade,
        balance_after
    )


# ============================================================
# APLICAR MONEY MANAGEMENT A TODAS LAS OPERACIONES
# ============================================================

def apply_money_management(
    trades,
    initial_balance=DEFAULT_INITIAL_BALANCE,
    risk_percent=DEFAULT_RISK_PERCENT
):
    """
    Aplica Money Management secuencialmente
    a todas las operaciones.

    El balance se actualiza después
    de cada operación.

    Se generan las columnas:

        balance_before
        risk_percent
        risk_amount
        balance_after
    """

    # ========================================================
    # VALIDACIONES
    # ========================================================

    validate_dataframe(
        trades
    )

    initial_balance = validate_balance(
        initial_balance
    )

    risk_percent = validate_risk_percent(
        risk_percent
    )

    # ========================================================
    # DATAFRAME VACÍO
    # ========================================================

    if trades.empty:

        result = trades.copy()

        result[
            "balance_before"
        ] = pd.Series(
            dtype=float
        )

        result[
            "risk_percent"
        ] = pd.Series(
            dtype=float
        )

        result[
            "risk_amount"
        ] = pd.Series(
            dtype=float
        )

        result[
            "balance_after"
        ] = pd.Series(
            dtype=float
        )

        return result

    # ========================================================
    # VALIDAR COLUMNAS
    # ========================================================

    required_columns = [
        "pnl"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in trades.columns
    ]

    if missing_columns:

        raise ValueError(
            "Faltan columnas requeridas: "
            f"{missing_columns}"
        )

    # ========================================================
    # COPIA DEL DATAFRAME
    # ========================================================

    result = trades.copy()

    # ========================================================
    # ORDENAR CRONOLÓGICAMENTE
    # ========================================================

    if "entry_time" in result.columns:

        result[
            "entry_time"
        ] = pd.to_datetime(
            result[
                "entry_time"
            ],
            errors="coerce"
        )

        result = result.sort_values(
            by="entry_time",
            na_position="last"
        )

        result = result.reset_index(
            drop=True
        )

    else:

        result = result.reset_index(
            drop=True
        )

    # ========================================================
    # LISTAS PARA RESULTADOS
    # ========================================================

    balance_before_values = []

    risk_percent_values = []

    risk_amount_values = []

    balance_after_values = []

    # ========================================================
    # BALANCE ACTUAL
    # ========================================================

    current_balance = float(
        initial_balance
    )

    # ========================================================
    # PROCESAR CADA OPERACIÓN
    # ========================================================

    for _, trade in result.iterrows():

        processed_trade, new_balance = (
            apply_money_management_to_trade(
                trade=trade,
                current_balance=current_balance,
                risk_percent=risk_percent
            )
        )

        balance_before_values.append(
            processed_trade[
                "balance_before"
            ]
        )

        risk_percent_values.append(
            processed_trade[
                "risk_percent"
            ]
        )

        risk_amount_values.append(
            processed_trade[
                "risk_amount"
            ]
        )

        balance_after_values.append(
            processed_trade[
                "balance_after"
            ]
        )

        current_balance = float(
            new_balance
        )

        # ====================================================
        # SI LA CUENTA QUEDA EN CERO
        # ====================================================

        if current_balance <= 0:

            current_balance = 0.0

    # ========================================================
    # GUARDAR RESULTADOS
    # ========================================================

    result[
        "balance_before"
    ] = balance_before_values

    result[
        "risk_percent"
    ] = risk_percent_values

    result[
        "risk_amount"
    ] = risk_amount_values

    result[
        "balance_after"
    ] = balance_after_values

    return result


# ============================================================
# OBTENER BALANCE FINAL
# ============================================================

def get_final_balance(
    trades,
    initial_balance=DEFAULT_INITIAL_BALANCE
):
    """
    Obtiene el balance final.

    Utiliza balance_after de la última operación.

    Si no existen operaciones,
    devuelve initial_balance.
    """

    validate_dataframe(
        trades
    )

    initial_balance = validate_balance(
        initial_balance
    )

    if trades.empty:

        return float(
            initial_balance
        )

    if "balance_after" not in trades.columns:

        raise ValueError(
            "No existe la columna balance_after."
        )

    final_balance = trades[
        "balance_after"
    ].iloc[-1]

    if pd.isna(final_balance):

        return float(
            initial_balance
        )

    try:

        final_balance = float(
            final_balance
        )

    except (TypeError, ValueError):

        raise ValueError(
            "El balance final es inválido: "
            f"{final_balance}"
        )

    if not np.isfinite(final_balance):

        raise ValueError(
            "El balance final no es finito: "
            f"{final_balance}"
        )

    return float(
        final_balance
    )


# ============================================================
# CALCULAR DRAWDOWN
# ============================================================

def calculate_drawdown_statistics(
    balances
):
    """
    Calcula estadísticas de drawdown
    a partir de una serie de balances.
    """

    if balances is None:

        raise ValueError(
            "balances no puede ser None."
        )

    balances = pd.Series(
        balances,
        dtype=float
    )

    if balances.empty:

        return {
            "max_drawdown_amount": 0.0,
            "max_drawdown_percent": 0.0
        }

    running_max = balances.cummax()

    drawdown_amount = (
        balances
        - running_max
    )

    safe_running_max = running_max.replace(
        0,
        np.nan
    )

    drawdown_percent = (
        drawdown_amount
        / safe_running_max
        * 100.0
    )

    drawdown_percent = drawdown_percent.fillna(
        0.0
    )

    max_drawdown_amount = abs(
        float(
            drawdown_amount.min()
        )
    )

    max_drawdown_percent = abs(
        float(
            drawdown_percent.min()
        )
    )

    return {
        "max_drawdown_amount":
            max_drawdown_amount,

        "max_drawdown_percent":
            max_drawdown_percent
    }


# ============================================================
# ESTADÍSTICAS DE MONEY MANAGEMENT
# ============================================================

def calculate_money_management_statistics(
    trades,
    initial_balance=DEFAULT_INITIAL_BALANCE
):
    """
    Calcula estadísticas completas
    de la evolución del capital.

    Retorna:

        initial_balance
        final_balance
        net_profit
        return_percent
        max_balance
        min_balance
        max_drawdown_amount
        max_drawdown_percent
    """

    # ========================================================
    # VALIDACIONES
    # ========================================================

    validate_dataframe(
        trades
    )

    initial_balance = validate_balance(
        initial_balance
    )

    # ========================================================
    # SIN OPERACIONES
    # ========================================================

    if trades.empty:

        return {
            "initial_balance":
                float(initial_balance),

            "final_balance":
                float(initial_balance),

            "net_profit":
                0.0,

            "return_percent":
                0.0,

            "max_balance":
                float(initial_balance),

            "min_balance":
                float(initial_balance),

            "max_drawdown_amount":
                0.0,

            "max_drawdown_percent":
                0.0
        }

    # ========================================================
    # VALIDAR COLUMNAS
    # ========================================================

    required_columns = [
        "balance_before",
        "balance_after"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in trades.columns
    ]

    if missing_columns:

        raise ValueError(
            "Faltan columnas para estadísticas: "
            f"{missing_columns}"
        )

    # ========================================================
    # OBTENER BALANCES
    # ========================================================

    balance_after_series = pd.to_numeric(
        trades[
            "balance_after"
        ],
        errors="coerce"
    )

    balance_after_series = (
        balance_after_series
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .dropna()
    )

    # ========================================================
    # SI NO HAY BALANCES VÁLIDOS
    # ========================================================

    if balance_after_series.empty:

        final_balance = float(
            initial_balance
        )

        balances = pd.Series(
            [initial_balance],
            dtype=float
        )

    else:

        balances = pd.concat(
            [
                pd.Series(
                    [initial_balance],
                    dtype=float
                ),

                balance_after_series.astype(
                    float
                )
            ],
            ignore_index=True
        )

        final_balance = float(
            balances.iloc[-1]
        )

    # ========================================================
    # GANANCIA NETA
    # ========================================================

    net_profit = (
        final_balance
        - initial_balance
    )

    # ========================================================
    # RETORNO PORCENTUAL
    # ========================================================

    return_percent = (
        (
            net_profit
            / initial_balance
        )
        * 100.0
    )

    # ========================================================
    # BALANCE MÁXIMO Y MÍNIMO
    # ========================================================

    max_balance = float(
        balances.max()
    )

    min_balance = float(
        balances.min()
    )

    # ========================================================
    # DRAWDOWN
    # ========================================================

    drawdown_statistics = (
        calculate_drawdown_statistics(
            balances=balances
        )
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "initial_balance":
            float(initial_balance),

        "final_balance":
            float(final_balance),

        "net_profit":
            float(net_profit),

        "return_percent":
            float(return_percent),

        "max_balance":
            float(max_balance),

        "min_balance":
            float(min_balance),

        "max_drawdown_amount":
            float(
                drawdown_statistics[
                    "max_drawdown_amount"
                ]
            ),

        "max_drawdown_percent":
            float(
                drawdown_statistics[
                    "max_drawdown_percent"
                ]
            )
    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_money_management(
    trades,
    initial_balance=DEFAULT_INITIAL_BALANCE,
    risk_percent=DEFAULT_RISK_PERCENT
):
    """
    Ejecuta todo el proceso de Money Management.

    Proceso:

        1. Valida las operaciones.
        2. Aplica gestión monetaria.
        3. Calcula balances.
        4. Calcula riesgo monetario.
        5. Calcula estadísticas.
        6. Calcula drawdown.

    Retorna:

        trades_with_management,
        statistics
    """

    # ========================================================
    # APLICAR MONEY MANAGEMENT
    # ========================================================

    trades_with_management = (
        apply_money_management(
            trades=trades,
            initial_balance=initial_balance,
            risk_percent=risk_percent
        )
    )

    # ========================================================
    # CALCULAR ESTADÍSTICAS
    # ========================================================

    statistics = (
        calculate_money_management_statistics(
            trades=trades_with_management,
            initial_balance=initial_balance
        )
    )

    return (
        trades_with_management,
        statistics
    )