"""Calculo de Stop Loss, Take Profit y ratio Riesgo/Beneficio.

Traduce una confirmacion de entrada en niveles operables concretos. Es la
frontera entre el analisis SMC y la gestion de riesgo: a partir de aqui el
resultado se mide en R (multiplos del riesgo inicial).

Vinculaciones:
- Lo importa `strategy.execution.trade_pipeline`, que lo aplica sobre las
  confirmaciones antes de publicar la senal.
- Recibe la salida de
  `strategy.smc.entry_confirmation.detect_entry_confirmations`.
- Los niveles que calcula los consume despues la capa de riesgo
  (`strategy.risk.position_sizing`) para dimensionar el lote.
"""

import pandas as pd


def calculate_risk_reward(
    confirmations: pd.DataFrame,
    risk_reward_ratio: float = 2.0
) -> pd.DataFrame:
    """
    Calcula Stop Loss, Take Profit y Risk/Reward
    para las confirmaciones de entrada.

    LONG:
        riesgo = entry_price - stop_loss
        take_profit = entry_price + (riesgo * ratio)

    SHORT:
        riesgo = stop_loss - entry_price
        take_profit = entry_price - (riesgo * ratio)

    Parameters
    ----------
    confirmations : pd.DataFrame
        DataFrame generado por entry_confirmation.py.

    risk_reward_ratio : float
        Relación recompensa/riesgo.
        Ejemplo:
            2.0 = Risk/Reward 1:2
            3.0 = Risk/Reward 1:3

    Returns
    -------
    pd.DataFrame
        DataFrame con los cálculos de riesgo y recompensa.

    Raises
    ------
    ValueError
        Si `risk_reward_ratio` no es mayor que 0, o si faltan las columnas
        `setup_type`, `entry_price` o `stop_loss`.

    Notas
    -----
    Con un DataFrame vacio o `None` devuelve un DataFrame vacio sin fallar.
    El Stop Loss NO se calcula aqui: viene ya definido desde la confirmacion,
    derivado del extremo del Order Block. Esta funcion solo proyecta el Take
    Profit a partir de esa distancia de riesgo.

    Vinculaciones
    -------------
    - Lo llama `strategy.execution.trade_pipeline` como ultimo paso antes de
      emitir la senal.
    - `entry_price`, `stop_loss` y `take_profit` los consume despues la capa
      de riesgo para calcular el lotaje y, en vivo,
      `strategy.execution.live_trading_engine` para enviar la orden.
    """

    # ==================================================
    # VALIDAR DATAFRAME
    # ==================================================

    if confirmations is None or confirmations.empty:
        return pd.DataFrame()

    if risk_reward_ratio <= 0:
        raise ValueError(
            "risk_reward_ratio debe ser mayor que 0."
        )

    # ==================================================
    # VALIDAR COLUMNAS
    # ==================================================

    required_columns = [
        "setup_type",
        "entry_price",
        "stop_loss"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in confirmations.columns
    ]

    if missing_columns:
        raise ValueError(
            "Faltan columnas para calcular Risk/Reward: "
            f"{missing_columns}"
        )

    # ==================================================
    # COPIA DE SEGURIDAD
    # ==================================================

    results = confirmations.copy()

    # ==================================================
    # CONVERTIR A NUMÉRICO
    # ==================================================

    results["entry_price"] = pd.to_numeric(
        results["entry_price"],
        errors="coerce"
    )

    results["stop_loss"] = pd.to_numeric(
        results["stop_loss"],
        errors="coerce"
    )

    # ==================================================
    # CREAR COLUMNAS
    # ==================================================

    results["risk"] = 0.0
    results["reward"] = 0.0
    results["take_profit"] = 0.0
    results["risk_reward_ratio"] = risk_reward_ratio
    results["trade_valid"] = False

    # ==================================================
    # CALCULAR LONG
    # ==================================================

    long_mask = (
        results["setup_type"]
        .astype(str)
        .str.lower()
        .eq("long")
    )

    long_risk = (
        results.loc[long_mask, "entry_price"]
        -
        results.loc[long_mask, "stop_loss"]
    )

    valid_long_mask = (
        long_mask
        &
        (results["entry_price"] > results["stop_loss"])
        &
        results["entry_price"].notna()
        &
        results["stop_loss"].notna()
    )

    results.loc[
        valid_long_mask,
        "risk"
    ] = (
        results.loc[
            valid_long_mask,
            "entry_price"
        ]
        -
        results.loc[
            valid_long_mask,
            "stop_loss"
        ]
    )

    results.loc[
        valid_long_mask,
        "reward"
    ] = (
        results.loc[
            valid_long_mask,
            "risk"
        ]
        * risk_reward_ratio
    )

    results.loc[
        valid_long_mask,
        "take_profit"
    ] = (
        results.loc[
            valid_long_mask,
            "entry_price"
        ]
        +
        results.loc[
            valid_long_mask,
            "reward"
        ]
    )

    results.loc[
        valid_long_mask,
        "trade_valid"
    ] = True

    # ==================================================
    # CALCULAR SHORT
    # ==================================================

    short_mask = (
        results["setup_type"]
        .astype(str)
        .str.lower()
        .eq("short")
    )

    valid_short_mask = (
        short_mask
        &
        (results["stop_loss"] > results["entry_price"])
        &
        results["entry_price"].notna()
        &
        results["stop_loss"].notna()
    )

    results.loc[
        valid_short_mask,
        "risk"
    ] = (
        results.loc[
            valid_short_mask,
            "stop_loss"
        ]
        -
        results.loc[
            valid_short_mask,
            "entry_price"
        ]
    )

    results.loc[
        valid_short_mask,
        "reward"
    ] = (
        results.loc[
            valid_short_mask,
            "risk"
        ]
        * risk_reward_ratio
    )

    results.loc[
        valid_short_mask,
        "take_profit"
    ] = (
        results.loc[
            valid_short_mask,
            "entry_price"
        ]
        -
        results.loc[
            valid_short_mask,
            "reward"
        ]
    )

    results.loc[
        valid_short_mask,
        "trade_valid"
    ] = True

    # ==================================================
    # LIMPIAR OPERACIONES INVÁLIDAS
    # ==================================================

    results = results[
        results["trade_valid"]
    ].copy()

    # ==================================================
    # REDONDEAR RESULTADOS
    # ==================================================

    numeric_columns = [
        "entry_price",
        "stop_loss",
        "risk",
        "reward",
        "take_profit",
        "risk_reward_ratio"
    ]

    for column in numeric_columns:

        if column in results.columns:

            results[column] = (
                results[column]
                .round(3)
            )

    # ==================================================
    # ORDENAR POR FECHA
    # ==================================================

    if "entry_time" in results.columns:

        results["entry_time"] = pd.to_datetime(
            results["entry_time"]
        )

        results = (
            results
            .sort_values("entry_time")
            .reset_index(drop=True)
        )

    return results