"""Dimensionado de posición: convierte riesgo permitido en tamaño de lote.

Idea central: el tamano NO se elige, se deduce. Fijados el precio de entrada
y el stop loss, la distancia entre ambos es el riesgo por unidad; el volumen
es entonces el que hace que ese riesgo coincida con el porcentaje del capital
que se esta dispuesto a arriesgar.

Vinculaciones:
- Lo consume `strategy.risk.risk_manager`.
- `strategy.smc.risk_reward` lo referencia como el calculo de lote asociado
  a sus niveles.
- El motor en vivo NO lo usa: implementa su propio dimensionado con
  restricciones adicionales de broker (granularidad de lote, margen y
  verificacion del riesgo real tras el fill).
"""

import pandas as pd


def calculate_position_size(
    entry_price: float,
    stop_loss: float,
    account_balance: float,
    risk_percent: float = 1.0,
    point_value: float = 1.0,
    min_position_size: float = 0.01,
    max_position_size: float | None = None
) -> dict:
    """
    Calcula el tamaño de posición basándose en el riesgo
    permitido sobre el capital de la cuenta.

    Parámetros
    ----------
    entry_price : float
        Precio de entrada.

    stop_loss : float
        Precio del Stop Loss.

    account_balance : float
        Capital disponible antes de abrir la operación.

    risk_percent : float
        Porcentaje del capital que se desea arriesgar.

        Ejemplo:
        1.0 = arriesgar el 1% del capital.

    point_value : float
        Valor monetario de un punto por cada unidad
        de tamaño de posición.

    min_position_size : float
        Tamaño mínimo permitido.

    max_position_size : float | None
        Tamaño máximo permitido.
    """

    # ==================================================
    # VALIDACIONES
    # ==================================================

    if account_balance <= 0:
        raise ValueError(
            "account_balance debe ser mayor que cero."
        )

    if risk_percent <= 0:
        raise ValueError(
            "risk_percent debe ser mayor que cero."
        )

    if point_value <= 0:
        raise ValueError(
            "point_value debe ser mayor que cero."
        )

    if entry_price <= 0:
        raise ValueError(
            "entry_price debe ser mayor que cero."
        )

    if stop_loss <= 0:
        raise ValueError(
            "stop_loss debe ser mayor que cero."
        )

    # ==================================================
    # CALCULAR DISTANCIA AL STOP LOSS
    # ==================================================

    stop_distance = abs(
        entry_price - stop_loss
    )

    if stop_distance <= 0:
        raise ValueError(
            "La distancia del Stop Loss debe ser mayor que cero."
        )

    # ==================================================
    # CAPITAL ARRIESGADO
    # ==================================================

    risk_amount = (
        account_balance
        * risk_percent
        / 100
    )

    # ==================================================
    # RIESGO POR UNA UNIDAD DE POSICIÓN
    # ==================================================

    risk_per_unit = (
        stop_distance
        * point_value
    )

    if risk_per_unit <= 0:
        raise ValueError(
            "El riesgo por unidad debe ser mayor que cero."
        )

    # ==================================================
    # TAMAÑO DE POSICIÓN
    # ==================================================

    position_size = (
        risk_amount
        / risk_per_unit
    )

    # ==================================================
    # RESPETAR TAMAÑO MÍNIMO
    # ==================================================

    if position_size < min_position_size:
        position_size = min_position_size

    # ==================================================
    # RESPETAR TAMAÑO MÁXIMO
    # ==================================================

    if (
        max_position_size is not None
        and position_size > max_position_size
    ):
        position_size = max_position_size

    # ==================================================
    # RIESGO REAL
    # ==================================================

    actual_risk_amount = (
        position_size
        * risk_per_unit
    )

    actual_risk_percent = (
        actual_risk_amount
        / account_balance
        * 100
    )

    # ==================================================
    # RESULTADO
    # ==================================================

    return {
        "account_balance": float(account_balance),
        "risk_percent": float(risk_percent),
        "risk_amount": float(risk_amount),
        "stop_distance": float(stop_distance),
        "point_value": float(point_value),
        "risk_per_unit": float(risk_per_unit),
        "position_size": float(position_size),
        "actual_risk_amount": float(
            actual_risk_amount
        ),
        "actual_risk_percent": float(
            actual_risk_percent
        )
    }


def add_position_sizing(
    trades: pd.DataFrame,
    initial_balance: float,
    risk_percent: float = 1.0,
    point_value: float = 1.0,
    min_position_size: float = 0.01,
    max_position_size: float | None = None
) -> pd.DataFrame:
    """
    Agrega información de gestión de tamaño de posición
    a un DataFrame de operaciones.

    El cálculo se realiza operación por operación,
    utilizando el balance disponible antes de cada trade.
    """

    # ==================================================
    # VALIDAR DATAFRAME
    # ==================================================

    if trades.empty:
        return trades.copy()

    required_columns = [
        "entry_price",
        "stop_loss"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in trades.columns
    ]

    if missing_columns:
        raise ValueError(
            "Faltan columnas en trades: "
            f"{missing_columns}"
        )

    # ==================================================
    # COPIA DE SEGURIDAD
    # ==================================================

    result = trades.copy()

    # ==================================================
    # ORDENAR POR TIEMPO
    # ==================================================

    if "entry_time" in result.columns:

        result["entry_time"] = pd.to_datetime(
            result["entry_time"]
        )

        result = result.sort_values(
            "entry_time"
        ).reset_index(drop=True)

    # ==================================================
    # COLUMNAS DE RESULTADO
    # ==================================================

    result["balance_before"] = 0.0

    result["risk_amount"] = 0.0

    result["stop_distance"] = 0.0

    result["risk_per_unit"] = 0.0

    result["position_size"] = 0.0

    result["actual_risk_amount"] = 0.0

    result["actual_risk_percent"] = 0.0

    # ==================================================
    # BALANCE ACTUAL
    # ==================================================

    current_balance = float(
        initial_balance
    )

    # ==================================================
    # CALCULAR OPERACIÓN POR OPERACIÓN
    # ==================================================

    for i in range(len(result)):

        row = result.iloc[i]

        entry_price = float(
            row["entry_price"]
        )

        stop_loss = float(
            row["stop_loss"]
        )

        sizing = calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            account_balance=current_balance,
            risk_percent=risk_percent,
            point_value=point_value,
            min_position_size=min_position_size,
            max_position_size=max_position_size
        )

        result.loc[
            result.index[i],
            "balance_before"
        ] = sizing["account_balance"]

        result.loc[
            result.index[i],
            "risk_amount"
        ] = sizing["risk_amount"]

        result.loc[
            result.index[i],
            "stop_distance"
        ] = sizing["stop_distance"]

        result.loc[
            result.index[i],
            "risk_per_unit"
        ] = sizing["risk_per_unit"]

        result.loc[
            result.index[i],
            "position_size"
        ] = sizing["position_size"]

        result.loc[
            result.index[i],
            "actual_risk_amount"
        ] = sizing[
            "actual_risk_amount"
        ]

        result.loc[
            result.index[i],
            "actual_risk_percent"
        ] = sizing[
            "actual_risk_percent"
        ]

        # ------------------------------------------------
        # ACTUALIZAR BALANCE SI EXISTE PNL
        # ------------------------------------------------

        if (
            "pnl"
            in result.columns
        ):

            pnl = row["pnl"]

            if pd.notna(pnl):

                current_balance += (
                    float(pnl)
                    * sizing["position_size"]
                    * point_value
                )

    return result