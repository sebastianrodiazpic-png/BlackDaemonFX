import pandas as pd
import numpy as np


# ==================================================
# FUNCIÓN PRINCIPAL
# ==================================================

def calculate_backtest_metrics(
    trades: pd.DataFrame,
    initial_capital: float = 10000.0,
    risk_per_trade_percent: float = 1.0,
    point_value: float = 1.0,
    commission_per_trade: float = 0.0,
    compound: bool = True
) -> tuple[pd.DataFrame, dict]:
    """
    Calcula métricas completas de un backtest con
    gestión de capital y riesgo.

    Parámetros
    ----------
    trades:
        DataFrame de operaciones proveniente de
        trade_simulator.py.

    initial_capital:
        Capital inicial de la cuenta.

    risk_per_trade_percent:
        Porcentaje del capital que se arriesga
        en cada operación.

        Ejemplo:
        1.0 = 1%

    point_value:
        Valor monetario de un punto de movimiento
        para una posición de tamaño 1.0.

        Por defecto:
        1.0

    commission_per_trade:
        Comisión monetaria aplicada a cada operación.

    compound:
        Si es True, el riesgo se calcula utilizando
        el equity actual.

        Si es False, siempre se utiliza el capital
        inicial para calcular el riesgo.

    Retorna
    -------
    1. DataFrame con información detallada:

        - risk
        - reward
        - risk_amount
        - position_size
        - gross_pnl
        - commission
        - pnl
        - r_multiple
        - equity_before
        - equity
        - equity_peak
        - drawdown
        - drawdown_percent

    2. Diccionario con métricas generales.
    """

    # ==================================================
    # VALIDAR PARÁMETROS
    # ==================================================

    if initial_capital <= 0:

        raise ValueError(
            "initial_capital debe ser mayor que 0."
        )

    if risk_per_trade_percent <= 0:

        raise ValueError(
            "risk_per_trade_percent debe ser mayor que 0."
        )

    if point_value <= 0:

        raise ValueError(
            "point_value debe ser mayor que 0."
        )

    if commission_per_trade < 0:

        raise ValueError(
            "commission_per_trade no puede ser negativo."
        )

    # ==================================================
    # MÉTRICAS VACÍAS
    # ==================================================

    empty_metrics = {

        # Configuración
        "initial_capital": round(
            float(initial_capital),
            3
        ),

        "final_capital": round(
            float(initial_capital),
            3
        ),

        "return_percent": 0.0,

        "risk_per_trade_percent": round(
            float(risk_per_trade_percent),
            3
        ),

        # Operaciones
        "total_trades": 0,
        "closed_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "unresolved_trades": 0,

        # Porcentajes
        "win_rate": 0.0,
        "loss_rate": 0.0,

        # PnL
        "total_pnl": 0.0,
        "average_pnl": 0.0,
        "average_win": 0.0,
        "average_loss": 0.0,

        # Rentabilidad
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,

        # Riesgo
        "average_risk_amount": 0.0,
        "average_position_size": 0.0,

        # R Multiple
        "average_r_multiple": 0.0,

        # Drawdown
        "max_drawdown": 0.0,
        "max_drawdown_percent": 0.0,

        # Rachas
        "max_consecutive_wins": 0,
        "max_consecutive_losses": 0,

        # Long / Short
        "long_trades": 0,
        "short_trades": 0,

        "long_pnl": 0.0,
        "short_pnl": 0.0,

        "long_win_rate": 0.0,
        "short_win_rate": 0.0,

        # Costos
        "total_commissions": 0.0
    }

    # ==================================================
    # VALIDAR DATAFRAME
    # ==================================================

    if trades is None or trades.empty:

        return (
            pd.DataFrame(),
            empty_metrics
        )

    # ==================================================
    # COPIA DE SEGURIDAD
    # ==================================================

    df = trades.copy()

    # ==================================================
    # VALIDAR COLUMNAS
    # ==================================================

    required_columns = [
        "entry_price",
        "stop_loss",
        "take_profit",
        "result"
    ]

    missing_columns = [

        column
        for column in required_columns
        if column not in df.columns

    ]

    if missing_columns:

        raise ValueError(
            "Faltan columnas necesarias para calcular "
            f"métricas: {missing_columns}"
        )

    # ==================================================
    # ORDENAR OPERACIONES CRONOLÓGICAMENTE
    # ==================================================

    if "entry_time" in df.columns:

        df["entry_time"] = pd.to_datetime(
            df["entry_time"],
            errors="coerce"
        )

        df = df.sort_values(
            "entry_time"
        ).reset_index(drop=True)

    # ==================================================
    # CONVERTIR COLUMNAS NUMÉRICAS
    # ==================================================

    numeric_columns = [
        "entry_price",
        "stop_loss",
        "take_profit"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # ==================================================
    # NORMALIZAR RESULTADOS
    # ==================================================

    df["result"] = (
        df["result"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # ==================================================
    # CALCULAR RIESGO EN PRECIO
    # ==================================================

    df["risk"] = (
        df["entry_price"] -
        df["stop_loss"]
    ).abs()

    # ==================================================
    # CALCULAR REWARD EN PRECIO
    # ==================================================

    df["reward"] = (
        df["take_profit"] -
        df["entry_price"]
    ).abs()

    # ==================================================
    # INICIALIZAR COLUMNAS
    # ==================================================

    df["equity_before"] = 0.0

    df["risk_amount"] = 0.0

    df["position_size"] = 0.0

    df["gross_pnl"] = 0.0

    df["commission"] = 0.0

    df["pnl"] = 0.0

    df["r_multiple"] = 0.0

    df["equity"] = 0.0

    # ==================================================
    # CALCULAR OPERACIÓN POR OPERACIÓN
    # ==================================================

    current_equity = float(
        initial_capital
    )

    risk_fraction = (
        risk_per_trade_percent / 100.0
    )

    for i in range(len(df)):

        # ----------------------------------------------
        # EQUITY ANTES DE LA OPERACIÓN
        # ----------------------------------------------

        equity_before = current_equity

        df.loc[
            df.index[i],
            "equity_before"
        ] = equity_before

        # ----------------------------------------------
        # CALCULAR CAPITAL BASE PARA EL RIESGO
        # ----------------------------------------------

        if compound:

            risk_capital = equity_before

        else:

            risk_capital = initial_capital

        # ----------------------------------------------
        # PROTEGER CUENTA SIN CAPITAL
        # ----------------------------------------------

        if risk_capital <= 0:

            risk_amount = 0.0

        else:

            risk_amount = (
                risk_capital *
                risk_fraction
            )

        df.loc[
            df.index[i],
            "risk_amount"
        ] = risk_amount

        # ----------------------------------------------
        # OBTENER RIESGO EN PRECIO
        # ----------------------------------------------

        price_risk = df.loc[
            df.index[i],
            "risk"
        ]

        # ----------------------------------------------
        # CALCULAR TAMAÑO DE POSICIÓN
        # ----------------------------------------------

        if (
            pd.isna(price_risk)
            or price_risk <= 0
            or risk_amount <= 0
        ):

            position_size = 0.0

        else:

            position_size = (
                risk_amount /
                (
                    price_risk *
                    point_value
                )
            )

        df.loc[
            df.index[i],
            "position_size"
        ] = position_size

        # ----------------------------------------------
        # RESULTADO DE LA OPERACIÓN
        # ----------------------------------------------

        result = df.loc[
            df.index[i],
            "result"
        ]

        reward = df.loc[
            df.index[i],
            "reward"
        ]

        # ----------------------------------------------
        # GANANCIA
        # ----------------------------------------------

        if result == "win":

            gross_pnl = (
                reward *
                position_size *
                point_value
            )

            commission = commission_per_trade

            r_multiple = (
                gross_pnl /
                risk_amount
                if risk_amount > 0
                else 0.0
            )

        # ----------------------------------------------
        # PÉRDIDA
        # ----------------------------------------------

        elif result == "loss":

            gross_pnl = (
                -risk_amount
            )

            commission = commission_per_trade

            r_multiple = -1.0

        # ----------------------------------------------
        # OPERACIÓN SIN RESOLVER
        # ----------------------------------------------

        else:

            gross_pnl = 0.0

            commission = 0.0

            r_multiple = 0.0

        # ----------------------------------------------
        # PNL NETO
        # ----------------------------------------------

        net_pnl = (
            gross_pnl -
            commission
        )

        # ----------------------------------------------
        # GUARDAR RESULTADOS
        # ----------------------------------------------

        df.loc[
            df.index[i],
            "gross_pnl"
        ] = gross_pnl

        df.loc[
            df.index[i],
            "commission"
        ] = commission

        df.loc[
            df.index[i],
            "pnl"
        ] = net_pnl

        df.loc[
            df.index[i],
            "r_multiple"
        ] = r_multiple

        # ----------------------------------------------
        # ACTUALIZAR EQUITY
        # ----------------------------------------------

        current_equity = (
            current_equity +
            net_pnl
        )

        df.loc[
            df.index[i],
            "equity"
        ] = current_equity

    # ==================================================
    # EQUITY PEAK
    # ==================================================

    df["equity_peak"] = df[
        "equity"
    ].cummax()

    # El capital inicial también debe considerarse
    # como posible máximo histórico.

    df["equity_peak"] = df[
        "equity_peak"
    ].clip(
        lower=initial_capital
    )

    # ==================================================
    # DRAWDOWN MONETARIO
    # ==================================================

    df["drawdown"] = (
        df["equity"] -
        df["equity_peak"]
    )

    # ==================================================
    # DRAWDOWN PORCENTUAL
    # ==================================================

    df["drawdown_percent"] = 0.0

    valid_peak_mask = (
        df["equity_peak"] > 0
    )

    df.loc[
        valid_peak_mask,
        "drawdown_percent"
    ] = (
        df.loc[
            valid_peak_mask,
            "drawdown"
        ]
        /
        df.loc[
            valid_peak_mask,
            "equity_peak"
        ]
        * 100
    )

    # ==================================================
    # IDENTIFICAR OPERACIONES CERRADAS
    # ==================================================

    closed_mask = (
        df["result"]
        .isin([
            "win",
            "loss"
        ])
    )

    closed_trades = df[
        closed_mask
    ].copy()

    winning_trades = df[
        df["result"] == "win"
    ].copy()

    losing_trades = df[
        df["result"] == "loss"
    ].copy()

    unresolved_trades = df[
        ~closed_mask
    ].copy()

    # ==================================================
    # MÉTRICAS BÁSICAS
    # ==================================================

    total_trades = len(df)

    total_closed = len(
        closed_trades
    )

    total_wins = len(
        winning_trades
    )

    total_losses = len(
        losing_trades
    )

    total_unresolved = len(
        unresolved_trades
    )

    # ==================================================
    # WIN RATE
    # ==================================================

    if total_closed > 0:

        win_rate = (
            total_wins /
            total_closed
        ) * 100

        loss_rate = (
            total_losses /
            total_closed
        ) * 100

    else:

        win_rate = 0.0

        loss_rate = 0.0

    # ==================================================
    # PNL
    # ==================================================

    total_pnl = df[
        "pnl"
    ].sum()

    if total_closed > 0:

        average_pnl = (
            closed_trades[
                "pnl"
            ]
            .mean()
        )

    else:

        average_pnl = 0.0

    # ==================================================
    # GANANCIA PROMEDIO
    # ==================================================

    if not winning_trades.empty:

        average_win = (
            winning_trades[
                "pnl"
            ]
            .mean()
        )

    else:

        average_win = 0.0

    # ==================================================
    # PÉRDIDA PROMEDIO
    # ==================================================

    if not losing_trades.empty:

        average_loss = abs(
            losing_trades[
                "pnl"
            ]
            .mean()
        )

    else:

        average_loss = 0.0

    # ==================================================
    # GANANCIA Y PÉRDIDA BRUTA
    # ==================================================

    gross_profit = (
        winning_trades[
            "pnl"
        ]
        .sum()
        if not winning_trades.empty
        else 0.0
    )

    gross_loss = abs(
        losing_trades[
            "pnl"
        ]
        .sum()
    ) if not losing_trades.empty else 0.0

    # ==================================================
    # PROFIT FACTOR
    # ==================================================

    if gross_loss > 0:

        profit_factor = (
            gross_profit /
            gross_loss
        )

    elif gross_profit > 0:

        profit_factor = np.inf

    else:

        profit_factor = 0.0

    # ==================================================
    # EXPECTANCY
    # ==================================================

    if total_closed > 0:

        win_probability = (
            total_wins /
            total_closed
        )

        loss_probability = (
            total_losses /
            total_closed
        )

        expectancy = (
            (
                win_probability *
                average_win
            )
            -
            (
                loss_probability *
                average_loss
            )
        )

    else:

        expectancy = 0.0

    # ==================================================
    # CAPITAL FINAL
    # ==================================================

    final_capital = current_equity

    # ==================================================
    # RENTABILIDAD PORCENTUAL
    # ==================================================

    return_percent = (
        (
            final_capital -
            initial_capital
        )
        /
        initial_capital
        * 100
    )

    # ==================================================
    # MAXIMUM DRAWDOWN
    # ==================================================

    if not df.empty:

        max_drawdown = abs(
            df[
                "drawdown"
            ]
            .min()
        )

        max_drawdown_percent = abs(
            df[
                "drawdown_percent"
            ]
            .min()
        )

    else:

        max_drawdown = 0.0

        max_drawdown_percent = 0.0

    # ==================================================
    # RIESGO PROMEDIO
    # ==================================================

    if total_closed > 0:

        average_risk_amount = (
            closed_trades[
                "risk_amount"
            ]
            .mean()
        )

        average_position_size = (
            closed_trades[
                "position_size"
            ]
            .mean()
        )

        average_r_multiple = (
            closed_trades[
                "r_multiple"
            ]
            .mean()
        )

    else:

        average_risk_amount = 0.0

        average_position_size = 0.0

        average_r_multiple = 0.0

    # ==================================================
    # COMISIONES
    # ==================================================

    total_commissions = df[
        "commission"
    ].sum()

    # ==================================================
    # RACHAS CONSECUTIVAS
    # ==================================================

    max_consecutive_wins = 0

    max_consecutive_losses = 0

    current_wins = 0

    current_losses = 0

    for result in closed_trades["result"]:

        if result == "win":

            current_wins += 1

            current_losses = 0

            max_consecutive_wins = max(
                max_consecutive_wins,
                current_wins
            )

        elif result == "loss":

            current_losses += 1

            current_wins = 0

            max_consecutive_losses = max(
                max_consecutive_losses,
                current_losses
            )

    # ==================================================
    # RESULTADOS LONG / SHORT
    # ==================================================

    long_trades = 0

    short_trades = 0

    long_pnl = 0.0

    short_pnl = 0.0

    long_win_rate = 0.0

    short_win_rate = 0.0

    if "setup_type" in df.columns:

        normalized_setup_type = (
            df["setup_type"]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        long_mask = (
            normalized_setup_type == "long"
        )

        short_mask = (
            normalized_setup_type == "short"
        )

        long_trades = int(
            long_mask.sum()
        )

        short_trades = int(
            short_mask.sum()
        )

        long_pnl = (
            df.loc[
                long_mask,
                "pnl"
            ]
            .sum()
        )

        short_pnl = (
            df.loc[
                short_mask,
                "pnl"
            ]
            .sum()
        )

        # ----------------------------------------------
        # WIN RATE LONG
        # ----------------------------------------------

        long_closed = df.loc[
            long_mask &
            df["result"].isin(
                ["win", "loss"]
            )
        ]

        if len(long_closed) > 0:

            long_win_rate = (
                (
                    long_closed["result"] == "win"
                )
                .sum()
                /
                len(long_closed)
                * 100
            )

        # ----------------------------------------------
        # WIN RATE SHORT
        # ----------------------------------------------

        short_closed = df.loc[
            short_mask &
            df["result"].isin(
                ["win", "loss"]
            )
        ]

        if len(short_closed) > 0:

            short_win_rate = (
                (
                    short_closed["result"] == "win"
                )
                .sum()
                /
                len(short_closed)
                * 100
            )

    # ==================================================
    # CREAR DICCIONARIO DE MÉTRICAS
    # ==================================================

    metrics = {

        # ----------------------------------------------
        # CONFIGURACIÓN
        # ----------------------------------------------

        "initial_capital": round(
            float(initial_capital),
            3
        ),

        "final_capital": round(
            float(final_capital),
            3
        ),

        "return_percent": round(
            float(return_percent),
            3
        ),

        "risk_per_trade_percent": round(
            float(risk_per_trade_percent),
            3
        ),

        # ----------------------------------------------
        # OPERACIONES
        # ----------------------------------------------

        "total_trades": total_trades,

        "closed_trades": total_closed,

        "winning_trades": total_wins,

        "losing_trades": total_losses,

        "unresolved_trades": total_unresolved,

        # ----------------------------------------------
        # PORCENTAJES
        # ----------------------------------------------

        "win_rate": round(
            float(win_rate),
            3
        ),

        "loss_rate": round(
            float(loss_rate),
            3
        ),

        # ----------------------------------------------
        # PNL
        # ----------------------------------------------

        "total_pnl": round(
            float(total_pnl),
            3
        ),

        "average_pnl": round(
            float(average_pnl),
            3
        ),

        "average_win": round(
            float(average_win),
            3
        ),

        "average_loss": round(
            float(average_loss),
            3
        ),

        # ----------------------------------------------
        # RENTABILIDAD
        # ----------------------------------------------

        "gross_profit": round(
            float(gross_profit),
            3
        ),

        "gross_loss": round(
            float(gross_loss),
            3
        ),

        "profit_factor": (
            round(
                float(profit_factor),
                3
            )
            if np.isfinite(profit_factor)
            else np.inf
        ),

        "expectancy": round(
            float(expectancy),
            3
        ),

        # ----------------------------------------------
        # RIESGO
        # ----------------------------------------------

        "average_risk_amount": round(
            float(average_risk_amount),
            3
        ),

        "average_position_size": round(
            float(average_position_size),
            6
        ),

        "average_r_multiple": round(
            float(average_r_multiple),
            3
        ),

        # ----------------------------------------------
        # DRAWDOWN
        # ----------------------------------------------

        "max_drawdown": round(
            float(max_drawdown),
            3
        ),

        "max_drawdown_percent": round(
            float(max_drawdown_percent),
            3
        ),

        # ----------------------------------------------
        # RACHAS
        # ----------------------------------------------

        "max_consecutive_wins": (
            max_consecutive_wins
        ),

        "max_consecutive_losses": (
            max_consecutive_losses
        ),

        # ----------------------------------------------
        # LONG / SHORT
        # ----------------------------------------------

        "long_trades": long_trades,

        "short_trades": short_trades,

        "long_pnl": round(
            float(long_pnl),
            3
        ),

        "short_pnl": round(
            float(short_pnl),
            3
        ),

        "long_win_rate": round(
            float(long_win_rate),
            3
        ),

        "short_win_rate": round(
            float(short_win_rate),
            3
        ),

        # ----------------------------------------------
        # COSTOS
        # ----------------------------------------------

        "total_commissions": round(
            float(total_commissions),
            3
        )
    }

    return df, metrics