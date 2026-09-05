"""Gestor de riesgo SMC de alto nivel: límites de cuenta y validaciones.

Reune sobre `position_sizing` y `money_management` las reglas de proteccion
de la cuenta: riesgo maximo por operacion, perdida diaria, drawdown, rachas
de perdidas consecutivas, numero de posiciones abiertas y riesgo agregado.

ESTADO: sin consumidores en produccion. El motor en vivo
(`strategy.execution.live_trading_engine`) implementa su propio dimensionado
y sus propios topes de riesgo, incluida la validacion posterior al fill. Este
paquete se mantiene cubierto por tests y sirve de referencia, pero NO
interviene en la operativa real.

Vinculaciones:
- Importa `strategy.risk.position_sizing` y `strategy.risk.money_management`.
- Solo lo consumen `tests/test_risk_manager.py` y
  `tests/test_risk_integration.py`.
"""

import pandas as pd
import numpy as np

from strategy.risk.position_sizing import (
    calculate_position_size
)

from strategy.risk.money_management import (
    validate_balance,
    validate_risk_percent,
    calculate_risk_amount,
    calculate_drawdown_statistics
)


# ============================================================
# RISK MANAGER SMC
# ============================================================

DEFAULT_MAX_RISK_PERCENT = 1.0
DEFAULT_MAX_DAILY_LOSS_PERCENT = 3.0
DEFAULT_MAX_DRAWDOWN_PERCENT = 10.0
DEFAULT_MAX_CONSECUTIVE_LOSSES = 5
DEFAULT_MAX_OPEN_POSITIONS = 1
DEFAULT_MAX_TOTAL_RISK_PERCENT = 2.0


# ============================================================
# VALIDACIONES GENERALES
# ============================================================

def validate_positive_number(
    value,
    name
):
    """
    Valida que un valor sea numérico, finito y mayor que cero.
    """

    if value is None:

        raise ValueError(
            f"{name} no puede ser None."
        )

    try:

        value = float(value)

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            f"{name} inválido: {value}"
        )

    if not np.isfinite(value):

        raise ValueError(
            f"{name} no es finito: {value}"
        )

    if value <= 0:

        raise ValueError(
            f"{name} debe ser mayor que cero: {value}"
        )

    return float(value)


def validate_non_negative_number(
    value,
    name
):
    """
    Valida que un valor sea numérico, finito y mayor
    o igual a cero.
    """

    if value is None:

        raise ValueError(
            f"{name} no puede ser None."
        )

    try:

        value = float(value)

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            f"{name} inválido: {value}"
        )

    if not np.isfinite(value):

        raise ValueError(
            f"{name} no es finito: {value}"
        )

    if value < 0:

        raise ValueError(
            f"{name} no puede ser negativo: {value}"
        )

    return float(value)


def validate_integer(
    value,
    name,
    minimum=0
):
    """
    Valida un número entero.
    """

    if value is None:

        raise ValueError(
            f"{name} no puede ser None."
        )

    try:

        value = int(value)

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            f"{name} debe ser un entero válido."
        )

    if value < minimum:

        raise ValueError(
            f"{name} debe ser mayor o igual a "
            f"{minimum}: {value}"
        )

    return int(value)


def validate_dataframe(
    trades
):
    """
    Valida que trades sea un pandas DataFrame.
    """

    if trades is None:

        raise ValueError(
            "trades no puede ser None."
        )

    if not isinstance(
        trades,
        pd.DataFrame
    ):

        raise TypeError(
            "trades debe ser un pandas DataFrame."
        )

    return True


# ============================================================
# VALIDAR DIRECCIÓN
# ============================================================

def validate_direction(
    direction
):
    """
    Valida la dirección de una operación.

    Valores permitidos:

        BUY
        SELL
        LONG
        SHORT
    """

    if direction is None:

        raise ValueError(
            "direction no puede ser None."
        )

    direction = str(
        direction
    ).upper().strip()

    valid_directions = {
        "BUY",
        "SELL",
        "LONG",
        "SHORT"
    }

    if direction not in valid_directions:

        raise ValueError(
            "direction inválida: "
            f"{direction}"
        )

    return direction


# ============================================================
# VALIDAR STOP LOSS SEGÚN DIRECCIÓN
# ============================================================

def validate_stop_loss_direction(
    direction,
    entry_price,
    stop_loss
):
    """
    Verifica que el Stop Loss esté correctamente
    ubicado según la dirección.

    BUY / LONG:
        Stop Loss < Entry Price

    SELL / SHORT:
        Stop Loss > Entry Price
    """

    direction = validate_direction(
        direction
    )

    entry_price = validate_positive_number(
        entry_price,
        "entry_price"
    )

    stop_loss = validate_positive_number(
        stop_loss,
        "stop_loss"
    )

    if direction in {
        "BUY",
        "LONG"
    }:

        if stop_loss >= entry_price:

            return {
                "valid": False,
                "reason": (
                    "Para una operación BUY/LONG, "
                    "el Stop Loss debe estar por "
                    "debajo del precio de entrada."
                )
            }

    if direction in {
        "SELL",
        "SHORT"
    }:

        if stop_loss <= entry_price:

            return {
                "valid": False,
                "reason": (
                    "Para una operación SELL/SHORT, "
                    "el Stop Loss debe estar por "
                    "encima del precio de entrada."
                )
            }

    return {
        "valid": True,
        "reason": "Stop Loss válido."
    }


# ============================================================
# VALIDAR TAKE PROFIT SEGÚN DIRECCIÓN
# ============================================================

def validate_take_profit_direction(
    direction,
    entry_price,
    take_profit
):
    """
    Verifica que el Take Profit esté correctamente
    ubicado según la dirección.

    BUY / LONG:
        Take Profit > Entry Price

    SELL / SHORT:
        Take Profit < Entry Price
    """

    direction = validate_direction(
        direction
    )

    entry_price = validate_positive_number(
        entry_price,
        "entry_price"
    )

    take_profit = validate_positive_number(
        take_profit,
        "take_profit"
    )

    if direction in {
        "BUY",
        "LONG"
    }:

        if take_profit <= entry_price:

            return {
                "valid": False,
                "reason": (
                    "Para una operación BUY/LONG, "
                    "el Take Profit debe estar por "
                    "encima del precio de entrada."
                )
            }

    if direction in {
        "SELL",
        "SHORT"
    }:

        if take_profit >= entry_price:

            return {
                "valid": False,
                "reason": (
                    "Para una operación SELL/SHORT, "
                    "el Take Profit debe estar por "
                    "debajo del precio de entrada."
                )
            }

    return {
        "valid": True,
        "reason": "Take Profit válido."
    }


# ============================================================
# CALCULAR RISK / REWARD
# ============================================================

def calculate_risk_reward(
    entry_price,
    stop_loss,
    take_profit
):
    """
    Calcula la relación Risk / Reward.

    Fórmula:

        riesgo = abs(entry - stop_loss)

        recompensa = abs(take_profit - entry)

        RR = recompensa / riesgo
    """

    entry_price = validate_positive_number(
        entry_price,
        "entry_price"
    )

    stop_loss = validate_positive_number(
        stop_loss,
        "stop_loss"
    )

    take_profit = validate_positive_number(
        take_profit,
        "take_profit"
    )

    risk_distance = abs(
        entry_price - stop_loss
    )

    reward_distance = abs(
        take_profit - entry_price
    )

    if risk_distance <= 0:

        raise ValueError(
            "La distancia al Stop Loss debe ser "
            "mayor que cero."
        )

    if reward_distance <= 0:

        raise ValueError(
            "La distancia al Take Profit debe ser "
            "mayor que cero."
        )

    risk_reward_ratio = (
        reward_distance
        / risk_distance
    )

    return {
        "risk_distance": float(
            risk_distance
        ),
        "reward_distance": float(
            reward_distance
        ),
        "risk_reward_ratio": float(
            risk_reward_ratio
        )
    }


# ============================================================
# VALIDAR RISK / REWARD MÍNIMO
# ============================================================

def validate_risk_reward(
    entry_price,
    stop_loss,
    take_profit,
    min_risk_reward=1.0
):
    """
    Verifica si la operación cumple con el
    Risk / Reward mínimo.
    """

    min_risk_reward = validate_positive_number(
        min_risk_reward,
        "min_risk_reward"
    )

    result = calculate_risk_reward(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit
    )

    ratio = result[
        "risk_reward_ratio"
    ]

    if ratio < min_risk_reward:

        result["valid"] = False

        result["reason"] = (
            f"Risk/Reward insuficiente: "
            f"{ratio:.2f}. "
            f"Mínimo requerido: "
            f"{min_risk_reward:.2f}."
        )

        return result

    result["valid"] = True

    result["reason"] = (
        f"Risk/Reward válido: "
        f"{ratio:.2f}."
    )

    return result


# ============================================================
# CALCULAR RIESGO ACTUAL
# ============================================================

def calculate_current_risk(
    account_balance,
    entry_price,
    stop_loss,
    risk_percent=DEFAULT_MAX_RISK_PERCENT,
    point_value=1.0,
    min_position_size=0.01,
    max_position_size=None
):
    """
    Calcula el tamaño de posición y riesgo real
    utilizando position_sizing.py.
    """

    account_balance = validate_balance(
        account_balance
    )

    entry_price = validate_positive_number(
        entry_price,
        "entry_price"
    )

    stop_loss = validate_positive_number(
        stop_loss,
        "stop_loss"
    )

    risk_percent = validate_risk_percent(
        risk_percent
    )

    point_value = validate_positive_number(
        point_value,
        "point_value"
    )

    return calculate_position_size(
        entry_price=entry_price,
        stop_loss=stop_loss,
        account_balance=account_balance,
        risk_percent=risk_percent,
        point_value=point_value,
        min_position_size=min_position_size,
        max_position_size=max_position_size
    )


# ============================================================
# CALCULAR PÉRDIDA MÁXIMA
# ============================================================

def calculate_max_loss_amount(
    account_balance,
    max_loss_percent
):
    """
    Calcula un monto máximo de pérdida basado
    en un porcentaje del balance.
    """

    account_balance = validate_balance(
        account_balance
    )

    max_loss_percent = validate_risk_percent(
        max_loss_percent
    )

    return float(
        account_balance
        * (
            max_loss_percent / 100.0
        )
    )


# ============================================================
# CALCULAR PÉRDIDA DIARIA
# ============================================================

def calculate_daily_loss(
    trades,
    current_time=None
):
    """
    Calcula el PnL y la pérdida acumulada
    del día actual.
    """

    validate_dataframe(
        trades
    )

    if trades.empty:

        return {
            "daily_pnl": 0.0,
            "daily_loss": 0.0,
            "date": None,
            "trades_today": 0
        }

    if "pnl" not in trades.columns:

        raise ValueError(
            "No existe la columna pnl."
        )

    result = trades.copy()

    time_column = None

    if "exit_time" in result.columns:

        time_column = "exit_time"

    elif "entry_time" in result.columns:

        time_column = "entry_time"

    if time_column is None:

        pnl = pd.to_numeric(
            result["pnl"],
            errors="coerce"
        ).fillna(0.0)

        daily_pnl = float(
            pnl.sum()
        )

        return {
            "daily_pnl": daily_pnl,
            "daily_loss": abs(
                min(
                    daily_pnl,
                    0.0
                )
            ),
            "date": None,
            "trades_today": int(
                len(result)
            )
        }

    result[time_column] = pd.to_datetime(
        result[time_column],
        errors="coerce"
    )

    result = result.dropna(
        subset=[time_column]
    )

    if result.empty:

        return {
            "daily_pnl": 0.0,
            "daily_loss": 0.0,
            "date": None,
            "trades_today": 0
        }

    if current_time is None:

        current_date = (
            result[time_column]
            .max()
            .date()
        )

    else:

        current_date = pd.to_datetime(
            current_time
        ).date()

    trades_today = result[
        result[time_column].dt.date
        == current_date
    ].copy()

    pnl = pd.to_numeric(
        trades_today["pnl"],
        errors="coerce"
    ).fillna(0.0)

    daily_pnl = float(
        pnl.sum()
    )

    return {
        "daily_pnl": daily_pnl,
        "daily_loss": abs(
            min(
                daily_pnl,
                0.0
            )
        ),
        "date": current_date,
        "trades_today": int(
            len(trades_today)
        )
    }


# ============================================================
# CONTAR PÉRDIDAS CONSECUTIVAS
# ============================================================

def count_consecutive_losses(
    trades
):
    """
    Cuenta las operaciones perdedoras consecutivas
    al final del historial.

    Una pérdida se define como:

        pnl < 0
    """

    validate_dataframe(
        trades
    )

    if trades.empty:

        return 0

    if "pnl" not in trades.columns:

        raise ValueError(
            "No existe la columna pnl."
        )

    result = trades.copy()

    if "exit_time" in result.columns:

        result["exit_time"] = pd.to_datetime(
            result["exit_time"],
            errors="coerce"
        )

        result = result.sort_values(
            "exit_time",
            na_position="last"
        )

    elif "entry_time" in result.columns:

        result["entry_time"] = pd.to_datetime(
            result["entry_time"],
            errors="coerce"
        )

        result = result.sort_values(
            "entry_time",
            na_position="last"
        )

    pnl_values = pd.to_numeric(
        result["pnl"],
        errors="coerce"
    ).fillna(0.0).tolist()

    consecutive_losses = 0

    for pnl in reversed(pnl_values):

        if pnl < 0:

            consecutive_losses += 1

        else:

            break

    return int(
        consecutive_losses
    )


# ============================================================
# CALCULAR DRAWDOWN ACTUAL
# ============================================================

def calculate_current_drawdown(
    trades,
    initial_balance
):
    """
    Calcula el drawdown actual y máximo.

    Si existe balance_after se utiliza directamente.
    En caso contrario, se reconstruye el balance
    utilizando initial_balance + pnl acumulado.
    """

    validate_dataframe(
        trades
    )

    initial_balance = validate_balance(
        initial_balance
    )

    balances = [
        float(initial_balance)
    ]

    if trades.empty:

        return {
            "current_balance": float(
                initial_balance
            ),
            "peak_balance": float(
                initial_balance
            ),
            "current_drawdown_amount": 0.0,
            "current_drawdown_percent": 0.0,
            "max_drawdown_amount": 0.0,
            "max_drawdown_percent": 0.0
        }

    result = trades.copy()

    # ========================================================
    # USAR BALANCE_AFTER
    # ========================================================

    if "balance_after" in result.columns:

        balance_values = pd.to_numeric(
            result["balance_after"],
            errors="coerce"
        ).replace(
            [np.inf, -np.inf],
            np.nan
        ).dropna().tolist()

        balances.extend(
            [
                float(value)
                for value in balance_values
            ]
        )

    # ========================================================
    # RECONSTRUIR CON PNL
    # ========================================================

    elif "pnl" in result.columns:

        current_balance = float(
            initial_balance
        )

        pnl_values = pd.to_numeric(
            result["pnl"],
            errors="coerce"
        ).fillna(0.0)

        for pnl in pnl_values:

            current_balance += float(
                pnl
            )

            balances.append(
                max(
                    current_balance,
                    0.0
                )
            )

    else:

        raise ValueError(
            "Se requiere balance_after o pnl "
            "para calcular el drawdown."
        )

    balances_series = pd.Series(
        balances,
        dtype=float
    )

    peak_balance = float(
        balances_series.max()
    )

    current_balance = float(
        balances_series.iloc[-1]
    )

    current_drawdown_amount = max(
        peak_balance - current_balance,
        0.0
    )

    current_drawdown_percent = (
        current_drawdown_amount
        / peak_balance
        * 100.0
        if peak_balance > 0
        else 0.0
    )

    drawdown_statistics = (
        calculate_drawdown_statistics(
            balances_series
        )
    )

    return {
        "current_balance": float(
            current_balance
        ),
        "peak_balance": float(
            peak_balance
        ),
        "current_drawdown_amount": float(
            current_drawdown_amount
        ),
        "current_drawdown_percent": float(
            current_drawdown_percent
        ),
        "max_drawdown_amount": float(
            drawdown_statistics[
                "max_drawdown_amount"
            ]
        ),
        "max_drawdown_percent": float(
            drawdown_statistics[
                "max_drawdown_percent"
            ]
        )
    }


# ============================================================
# CALCULAR RIESGO DE POSICIONES ABIERTAS
# ============================================================

def calculate_open_positions_risk(
    open_positions
):
    """
    Calcula el riesgo total de las posiciones
    actualmente abiertas.

    Cada posición puede contener:

        actual_risk_amount
        risk_amount

    o, como alternativa:

        entry_price
        stop_loss
        position_size
        point_value
    """

    if open_positions is None:

        return {
            "open_positions_count": 0,
            "total_open_risk_amount": 0.0
        }

    if not isinstance(
        open_positions,
        (list, tuple)
    ):

        raise TypeError(
            "open_positions debe ser una lista o tupla."
        )

    total_open_risk_amount = 0.0

    for position in open_positions:

        if not isinstance(
            position,
            dict
        ):

            raise TypeError(
                "Cada posición debe ser un diccionario."
            )

        # ====================================================
        # RIESGO YA CALCULADO
        # ====================================================

        if (
            "actual_risk_amount"
            in position
        ):

            risk = float(
                position[
                    "actual_risk_amount"
                ]
            )

        elif (
            "risk_amount"
            in position
        ):

            risk = float(
                position[
                    "risk_amount"
                ]
            )

        # ====================================================
        # CALCULAR DESDE LOS DATOS
        # ====================================================

        else:

            required = [
                "entry_price",
                "stop_loss",
                "position_size",
                "point_value"
            ]

            missing = [
                column
                for column in required
                if column not in position
            ]

            if missing:

                raise ValueError(
                    "No se puede calcular el riesgo "
                    "de la posición. Faltan: "
                    f"{missing}"
                )

            risk = (
                abs(
                    float(
                        position[
                            "entry_price"
                        ]
                    )
                    -
                    float(
                        position[
                            "stop_loss"
                        ]
                    )
                )
                *
                float(
                    position[
                        "position_size"
                    ]
                )
                *
                float(
                    position[
                        "point_value"
                    ]
                )
            )

        if risk < 0:

            raise ValueError(
                "El riesgo de una posición no "
                "puede ser negativo."
            )

        total_open_risk_amount += risk

    return {
        "open_positions_count": int(
            len(open_positions)
        ),
        "total_open_risk_amount": float(
            total_open_risk_amount
        )
    }


# ============================================================
# VALIDAR PÉRDIDA DIARIA
# ============================================================

def check_daily_loss_limit(
    trades,
    account_balance,
    max_daily_loss_percent=DEFAULT_MAX_DAILY_LOSS_PERCENT,
    current_time=None
):
    """
    Verifica si se alcanzó el límite máximo
    de pérdida diaria.
    """

    account_balance = validate_balance(
        account_balance
    )

    max_daily_loss_percent = validate_risk_percent(
        max_daily_loss_percent
    )

    daily = calculate_daily_loss(
        trades=trades,
        current_time=current_time
    )

    max_daily_loss_amount = (
        calculate_max_loss_amount(
            account_balance=account_balance,
            max_loss_percent=max_daily_loss_percent
        )
    )

    allowed = (
        daily["daily_loss"]
        < max_daily_loss_amount
    )

    return {
        "allowed": bool(allowed),
        "daily_pnl": float(
            daily["daily_pnl"]
        ),
        "daily_loss": float(
            daily["daily_loss"]
        ),
        "max_daily_loss_percent": float(
            max_daily_loss_percent
        ),
        "max_daily_loss_amount": float(
            max_daily_loss_amount
        ),
        "trades_today": int(
            daily["trades_today"]
        ),
        "reason": (
            "Límite de pérdida diaria alcanzado."
            if not allowed
            else
            "Pérdida diaria dentro del límite."
        )
    }


# ============================================================
# VALIDAR DRAWDOWN
# ============================================================

def check_drawdown_limit(
    trades,
    initial_balance,
    max_drawdown_percent=DEFAULT_MAX_DRAWDOWN_PERCENT
):
    """
    Verifica si el drawdown actual supera
    el límite permitido.
    """

    max_drawdown_percent = validate_risk_percent(
        max_drawdown_percent
    )

    drawdown = calculate_current_drawdown(
        trades=trades,
        initial_balance=initial_balance
    )

    allowed = (
        drawdown[
            "current_drawdown_percent"
        ]
        < max_drawdown_percent
    )

    result = drawdown.copy()

    result[
        "allowed"
    ] = bool(
        allowed
    )

    result[
        "max_allowed_drawdown_percent"
    ] = float(
        max_drawdown_percent
    )

    result[
        "reason"
    ] = (
        "Límite de drawdown alcanzado."
        if not allowed
        else
        "Drawdown dentro del límite."
    )

    return result


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def evaluate_trade_risk(
    direction,
    entry_price,
    stop_loss,
    take_profit,
    account_balance,
    trades=None,
    initial_balance=None,
    risk_percent=DEFAULT_MAX_RISK_PERCENT,
    point_value=1.0,
    min_position_size=0.01,
    max_position_size=None,
    min_risk_reward=1.0,
    max_daily_loss_percent=DEFAULT_MAX_DAILY_LOSS_PERCENT,
    max_drawdown_percent=DEFAULT_MAX_DRAWDOWN_PERCENT,
    max_consecutive_losses=DEFAULT_MAX_CONSECUTIVE_LOSSES,
    open_positions=None,
    max_open_positions=DEFAULT_MAX_OPEN_POSITIONS,
    max_total_risk_percent=DEFAULT_MAX_TOTAL_RISK_PERCENT,
    current_time=None
):
    """
    Evalúa completamente el riesgo de una operación.

    Devuelve:

        approved
        reason
        direction
        entry_price
        stop_loss
        take_profit
        account_balance
        risk_amount
        position_size
        actual_risk_amount
        actual_risk_percent
        risk_reward_ratio
        daily_loss
        drawdown
        consecutive_losses
        open_positions_count
    """

    # ========================================================
    # RESULTADO BASE
    # ========================================================

    result = {
        "approved": False,
        "reason": "",
        "direction": None,
        "entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "account_balance": None,
        "risk_percent": None,
        "risk_amount": None,
        "position_size": None,
        "actual_risk_amount": None,
        "actual_risk_percent": None,
        "risk_reward_ratio": None,
        "daily_loss": 0.0,
        "max_daily_loss_amount": 0.0,
        "current_drawdown_percent": 0.0,
        "max_allowed_drawdown_percent": 0.0,
        "consecutive_losses": 0,
        "open_positions_count": 0,
        "total_open_risk_amount": 0.0,
        "total_risk_amount": 0.0,
        "total_risk_percent": 0.0
    }

    # ========================================================
    # VALIDAR DATOS BÁSICOS
    # ========================================================

    direction = validate_direction(
        direction
    )

    entry_price = validate_positive_number(
        entry_price,
        "entry_price"
    )

    stop_loss = validate_positive_number(
        stop_loss,
        "stop_loss"
    )

    take_profit = validate_positive_number(
        take_profit,
        "take_profit"
    )

    account_balance = validate_balance(
        account_balance
    )

    risk_percent = validate_risk_percent(
        risk_percent
    )

    point_value = validate_positive_number(
        point_value,
        "point_value"
    )

    min_position_size = validate_positive_number(
        min_position_size,
        "min_position_size"
    )

    max_consecutive_losses = validate_integer(
        max_consecutive_losses,
        "max_consecutive_losses",
        minimum=0
    )

    max_open_positions = validate_integer(
        max_open_positions,
        "max_open_positions",
        minimum=1
    )

    max_total_risk_percent = validate_risk_percent(
        max_total_risk_percent
    )

    if max_position_size is not None:

        max_position_size = validate_positive_number(
            max_position_size,
            "max_position_size"
        )

        if (
            max_position_size
            < min_position_size
        ):

            raise ValueError(
                "max_position_size no puede ser "
                "menor que min_position_size."
            )

    if initial_balance is None:

        initial_balance = account_balance

    initial_balance = validate_balance(
        initial_balance
    )

    result["direction"] = direction
    result["entry_price"] = entry_price
    result["stop_loss"] = stop_loss
    result["take_profit"] = take_profit
    result["account_balance"] = account_balance
    result["risk_percent"] = risk_percent

    # ========================================================
    # HISTORIAL VACÍO
    # ========================================================

    if trades is None:

        trades = pd.DataFrame()

    validate_dataframe(
        trades
    )

    # ========================================================
    # VALIDAR STOP LOSS
    # ========================================================

    stop_validation = (
        validate_stop_loss_direction(
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
    )

    if not stop_validation["valid"]:

        result["reason"] = (
            stop_validation["reason"]
        )

        return result

    # ========================================================
    # VALIDAR TAKE PROFIT
    # ========================================================

    take_profit_validation = (
        validate_take_profit_direction(
            direction=direction,
            entry_price=entry_price,
            take_profit=take_profit
        )
    )

    if not take_profit_validation["valid"]:

        result["reason"] = (
            take_profit_validation["reason"]
        )

        return result

    # ========================================================
    # VALIDAR RISK / REWARD
    # ========================================================

    rr = validate_risk_reward(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        min_risk_reward=min_risk_reward
    )

    result[
        "risk_reward_ratio"
    ] = rr[
        "risk_reward_ratio"
    ]

    if not rr["valid"]:

        result["reason"] = (
            rr["reason"]
        )

        return result

    # ========================================================
    # VALIDAR PÉRDIDA DIARIA
    # ========================================================

    if not trades.empty:

        daily_check = (
            check_daily_loss_limit(
                trades=trades,
                account_balance=account_balance,
                max_daily_loss_percent=max_daily_loss_percent,
                current_time=current_time
            )
        )

        result[
            "daily_loss"
        ] = daily_check[
            "daily_loss"
        ]

        result[
            "max_daily_loss_amount"
        ] = daily_check[
            "max_daily_loss_amount"
        ]

        if not daily_check["allowed"]:

            result["reason"] = (
                daily_check["reason"]
            )

            return result

    # ========================================================
    # VALIDAR DRAWDOWN
    # ========================================================

    if not trades.empty:

        drawdown_check = (
            check_drawdown_limit(
                trades=trades,
                initial_balance=initial_balance,
                max_drawdown_percent=max_drawdown_percent
            )
        )

        result[
            "current_drawdown_percent"
        ] = drawdown_check[
            "current_drawdown_percent"
        ]

        result[
            "max_allowed_drawdown_percent"
        ] = drawdown_check[
            "max_allowed_drawdown_percent"
        ]

        if not drawdown_check["allowed"]:

            result["reason"] = (
                drawdown_check["reason"]
            )

            return result

    # ========================================================
    # VALIDAR PÉRDIDAS CONSECUTIVAS
    # ========================================================

    consecutive_losses = 0

    if not trades.empty:

        consecutive_losses = (
            count_consecutive_losses(
                trades
            )
        )

    result[
        "consecutive_losses"
    ] = consecutive_losses

    if (
        consecutive_losses
        >= max_consecutive_losses
    ):

        result["reason"] = (
            "Máximo de pérdidas consecutivas "
            "alcanzado."
        )

        return result

    # ========================================================
    # VALIDAR POSICIONES ABIERTAS
    # ========================================================

    open_risk = (
        calculate_open_positions_risk(
            open_positions
        )
    )

    result[
        "open_positions_count"
    ] = open_risk[
        "open_positions_count"
    ]

    result[
        "total_open_risk_amount"
    ] = open_risk[
        "total_open_risk_amount"
    ]

    if (
        open_risk[
            "open_positions_count"
        ]
        >= max_open_positions
    ):

        result["reason"] = (
            "Máximo de posiciones abiertas "
            "alcanzado."
        )

        return result

    # ========================================================
    # CALCULAR TAMAÑO DE POSICIÓN
    # ========================================================

    sizing = calculate_current_risk(
        account_balance=account_balance,
        entry_price=entry_price,
        stop_loss=stop_loss,
        risk_percent=risk_percent,
        point_value=point_value,
        min_position_size=min_position_size,
        max_position_size=max_position_size
    )

    result[
        "risk_amount"
    ] = sizing[
        "risk_amount"
    ]

    result[
        "position_size"
    ] = sizing[
        "position_size"
    ]

    result[
        "actual_risk_amount"
    ] = sizing[
        "actual_risk_amount"
    ]

    result[
        "actual_risk_percent"
    ] = sizing[
        "actual_risk_percent"
    ]

    # ========================================================
    # VALIDAR RIESGO TOTAL
    # ========================================================

    total_risk_amount = (
        open_risk[
            "total_open_risk_amount"
        ]
        +
        sizing[
            "actual_risk_amount"
        ]
    )

    total_risk_percent = (
        total_risk_amount
        / account_balance
        * 100.0
    )

    result[
        "total_risk_amount"
    ] = float(
        total_risk_amount
    )

    result[
        "total_risk_percent"
    ] = float(
        total_risk_percent
    )

    if (
        total_risk_percent
        > max_total_risk_percent
    ):

        result["reason"] = (
            "El riesgo total de posiciones "
            "supera el límite permitido."
        )

        return result

    # ========================================================
    # OPERACIÓN APROBADA
    # ========================================================

    result["approved"] = True

    result["reason"] = (
        "Operación aprobada por el Risk Manager."
    )

    return result


# ============================================================
# FUNCIÓN ALIAS PRINCIPAL
# ============================================================

def evaluate_risk(
    **kwargs
):
    """
    Alias simplificado de evaluate_trade_risk().
    """

    return evaluate_trade_risk(
        **kwargs
    )


# ============================================================
# GENERAR RESUMEN
# ============================================================

def get_risk_summary(
    evaluation
):
    """
    Genera un resumen simplificado del resultado
    de una evaluación de riesgo.
    """

    if evaluation is None:

        raise ValueError(
            "evaluation no puede ser None."
        )

    if not isinstance(
        evaluation,
        dict
    ):

        raise TypeError(
            "evaluation debe ser un diccionario."
        )

    return {
        "approved": bool(
            evaluation.get(
                "approved",
                False
            )
        ),

        "reason": evaluation.get(
            "reason",
            ""
        ),

        "position_size": evaluation.get(
            "position_size"
        ),

        "risk_amount": evaluation.get(
            "actual_risk_amount"
        ),

        "risk_percent": evaluation.get(
            "actual_risk_percent"
        ),

        "risk_reward_ratio": evaluation.get(
            "risk_reward_ratio"
        ),

        "total_risk_percent": evaluation.get(
            "total_risk_percent"
        ),

        "consecutive_losses": evaluation.get(
            "consecutive_losses",
            0
        )
    }


# ============================================================
# EJECUCIÓN DIRECTA DE PRUEBA
# ============================================================

if __name__ == "__main__":

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0,
        risk_percent=1.0,
        point_value=1.0,
        min_position_size=0.01,
        max_position_size=None,
        min_risk_reward=1.5
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "RISK MANAGER"
    )

    print(
        "=" * 60
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print(
        "=" * 60
        + "\n"
    )