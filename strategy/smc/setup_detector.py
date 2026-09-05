"""Deteccion de setups SMC combinando ruptura, Order Block y zona.

Version independiente del detector de setups. La logica equivalente que se
ejecuta EN PRODUCCION vive dentro de
`strategy.execution.trade_pipeline.run_pipeline`, que ademas rellena el
checklist completo y encadena la confirmacion M5.

ESTADO: ningun modulo de produccion importa este fichero. Solo lo usan tests
(`test_setup_detector.py`, `test_entry_confirmation.py`, `test_risk_reward.py`,
`test_trade_simulator.py`, `test_backtest_metric.py`, `test_money_management.py`
y `test_position_sizing.py`), donde sirve para montar escenarios SMC de forma
compacta. Si vas a cambiar el comportamiento del bot en vivo, el fichero que
debes tocar es `trade_pipeline.py`, no este.

Vinculaciones:
- Consume las columnas de `strategy.smc.choch_bos` y
  `strategy.smc.order_blocks`, y la columna `zone` de
  `strategy.smc.premium_discount`.
- Su salida la encadenan los tests hacia
  `strategy.smc.entry_confirmation.detect_entry_confirmations`.
"""

import pandas as pd


def detect_setups(
    df: pd.DataFrame,
    order_blocks: pd.DataFrame,
    structure_lookback: int = 100
) -> pd.DataFrame:
    """
    Detecta setups SMC utilizando una secuencia temporal.

    Setup LONG:
        - CHOCH bullish o BOS bullish reciente.
        - Bullish Order Block.
        - Order Block ubicado en Discount.

    Setup SHORT:
        - CHOCH bearish o BOS bearish reciente.
        - Bearish Order Block.
        - Order Block ubicado en Premium.

    structure_lookback:
        Número máximo de velas después de una ruptura
        estructural para considerar válido el contexto.

    El orden temporal es la clave: la ruptura debe ser ANTERIOR al OB y no
    puede quedar mas lejos de `structure_lookback` velas, para que el contexto
    estructural siga vigente cuando se opera la zona.

    Args:
        df: DataFrame con las columnas de ruptura (`choch_*`, `bos_*`).
        order_blocks: DataFrame de OB con su zona premium/discount asignada.
        structure_lookback: antiguedad maxima admitida de la ruptura.

    Returns:
        DataFrame de setups. Devuelve uno vacio si cualquiera de las entradas
        esta vacia.

    Raises:
        ValueError: si faltan columnas obligatorias en `df`.

    Vinculaciones:
    - Sin llamadores de produccion; lo usan varios tests. El equivalente vivo
      es `strategy.execution.trade_pipeline.run_pipeline`.
    """

    # ==================================================
    # VALIDACIONES
    # ==================================================

    if df.empty:
        return pd.DataFrame()

    if order_blocks.empty:
        return pd.DataFrame()

    required_df_columns = [
        "time",
        "choch_bullish",
        "choch_bearish",
        "bos_bullish",
        "bos_bearish"
    ]

    missing_df_columns = [
        column
        for column in required_df_columns
        if column not in df.columns
    ]

    if missing_df_columns:
        raise ValueError(
            f"Faltan columnas en df: {missing_df_columns}"
        )

    required_ob_columns = [
        "time",
        "ob_high",
        "ob_low",
        "ob_type",
        "zone"
    ]

    missing_ob_columns = [
        column
        for column in required_ob_columns
        if column not in order_blocks.columns
    ]

    if missing_ob_columns:
        raise ValueError(
            f"Faltan columnas en order_blocks: "
            f"{missing_ob_columns}"
        )

    # ==================================================
    # COPIAS DE SEGURIDAD
    # ==================================================

    structure_data = df.copy()
    ob_data = order_blocks.copy()

    # ==================================================
    # NORMALIZAR FECHAS EN UTC
    # IMPORTANTE: evita conflicto datetime con/sin timezone
    # ==================================================

    structure_data["time"] = pd.to_datetime(
        structure_data["time"],
        utc=True
    )

    ob_data["time"] = pd.to_datetime(
        ob_data["time"],
        utc=True
    )

    structure_data = structure_data.sort_values(
        "time"
    ).reset_index(drop=True)

    ob_data = ob_data.sort_values(
        "time"
    ).reset_index(drop=True)

    # ==================================================
    # ASEGURAR COLUMNAS BOOLEANAS
    # ==================================================

    bool_columns = [
        "choch_bullish",
        "choch_bearish",
        "bos_bullish",
        "bos_bearish"
    ]

    for column in bool_columns:

        structure_data[column] = (
            structure_data[column]
            .fillna(False)
            .astype(bool)
        )

    # ==================================================
    # CREAR EVENTOS DE ESTRUCTURA
    # ==================================================

    structure_data["bullish_structure_event"] = (
        structure_data["choch_bullish"]
        |
        structure_data["bos_bullish"]
    )

    structure_data["bearish_structure_event"] = (
        structure_data["choch_bearish"]
        |
        structure_data["bos_bearish"]
    )

    # ==================================================
    # CREAR COLUMNA PARA ÚLTIMO EVENTO ALCISTA
    # CON EL MISMO TIPO UTC
    # ==================================================

    structure_data["bullish_structure_time"] = pd.Series(
        pd.NaT,
        index=structure_data.index,
        dtype="datetime64[ns, UTC]"
    )

    bullish_mask = (
        structure_data["bullish_structure_event"]
    )

    structure_data.loc[
        bullish_mask,
        "bullish_structure_time"
    ] = structure_data.loc[
        bullish_mask,
        "time"
    ]

    structure_data["bullish_structure_time"] = (
        structure_data["bullish_structure_time"]
        .ffill()
    )

    # ==================================================
    # CREAR COLUMNA PARA ÚLTIMO EVENTO BAJISTA
    # CON EL MISMO TIPO UTC
    # ==================================================

    structure_data["bearish_structure_time"] = pd.Series(
        pd.NaT,
        index=structure_data.index,
        dtype="datetime64[ns, UTC]"
    )

    bearish_mask = (
        structure_data["bearish_structure_event"]
    )

    structure_data.loc[
        bearish_mask,
        "bearish_structure_time"
    ] = structure_data.loc[
        bearish_mask,
        "time"
    ]

    structure_data["bearish_structure_time"] = (
        structure_data["bearish_structure_time"]
        .ffill()
    )

    # ==================================================
    # ÍNDICE DE VELAS
    # ==================================================

    structure_data["bar_index"] = range(
        len(structure_data)
    )

    # ==================================================
    # CALCULAR DISTANCIA DESDE ÚLTIMA ESTRUCTURA ALCISTA
    # ==================================================

    bullish_event_index = structure_data[
        "bar_index"
    ].where(
        structure_data["bullish_structure_event"]
    )

    structure_data["last_bullish_event_index"] = (
        bullish_event_index.ffill()
    )

    structure_data["bullish_bars_since_structure"] = (
        structure_data["bar_index"]
        -
        structure_data["last_bullish_event_index"]
    )

    # ==================================================
    # CALCULAR DISTANCIA DESDE ÚLTIMA ESTRUCTURA BAJISTA
    # ==================================================

    bearish_event_index = structure_data[
        "bar_index"
    ].where(
        structure_data["bearish_structure_event"]
    )

    structure_data["last_bearish_event_index"] = (
        bearish_event_index.ffill()
    )

    structure_data["bearish_bars_since_structure"] = (
        structure_data["bar_index"]
        -
        structure_data["last_bearish_event_index"]
    )

    # ==================================================
    # PREPARAR INFORMACIÓN DE ESTRUCTURA
    # ==================================================

    columns_to_merge = [
        "time",
        "choch_bullish",
        "choch_bearish",
        "bos_bullish",
        "bos_bearish",
        "bullish_structure_time",
        "bearish_structure_time",
        "bullish_bars_since_structure",
        "bearish_bars_since_structure"
    ]

    structure_merge_data = structure_data[
        columns_to_merge
    ].copy()

    # ==================================================
    # UNIR ESTRUCTURA CON ORDER BLOCKS
    # ==================================================

    merged = ob_data.merge(
        structure_merge_data,
        on="time",
        how="left"
    )

    # ==================================================
    # VALIDAR CONTEXTO ALCISTA RECIENTE
    # ==================================================

    merged["bullish_structure_valid"] = (
        merged["bullish_structure_time"].notna()
        &
        (
            merged["bullish_bars_since_structure"]
            <= structure_lookback
        )
    )

    # ==================================================
    # VALIDAR CONTEXTO BAJISTA RECIENTE
    # ==================================================

    merged["bearish_structure_valid"] = (
        merged["bearish_structure_time"].notna()
        &
        (
            merged["bearish_bars_since_structure"]
            <= structure_lookback
        )
    )

    # ==================================================
    # CONDICIÓN LONG
    # ==================================================

    long_condition = (
        (merged["ob_type"] == "bullish")
        &
        (merged["zone"] == "discount")
        &
        (merged["bullish_structure_valid"])
    )

    # ==================================================
    # CONDICIÓN SHORT
    # ==================================================

    short_condition = (
        (merged["ob_type"] == "bearish")
        &
        (merged["zone"] == "premium")
        &
        (merged["bearish_structure_valid"])
    )

    # ==================================================
    # FILTRAR SETUPS LONG
    # ==================================================

    long_setups = merged[
        long_condition
    ].copy()

    if not long_setups.empty:

        long_setups["setup_type"] = "long"

        long_setups["structure_time"] = (
            long_setups["bullish_structure_time"]
        )

        long_setups["bars_since_structure"] = (
            long_setups[
                "bullish_bars_since_structure"
            ]
        )

    # ==================================================
    # FILTRAR SETUPS SHORT
    # ==================================================

    short_setups = merged[
        short_condition
    ].copy()

    if not short_setups.empty:

        short_setups["setup_type"] = "short"

        short_setups["structure_time"] = (
            short_setups["bearish_structure_time"]
        )

        short_setups["bars_since_structure"] = (
            short_setups[
                "bearish_bars_since_structure"
            ]
        )

    # ==================================================
    # UNIR RESULTADOS
    # ==================================================

    setups = pd.concat(
        [
            long_setups,
            short_setups
        ],
        ignore_index=True
    )

    # ==================================================
    # ORDENAR RESULTADOS
    # ==================================================

    if not setups.empty:

        setups = setups.sort_values(
            "time"
        ).reset_index(drop=True)

    return setups