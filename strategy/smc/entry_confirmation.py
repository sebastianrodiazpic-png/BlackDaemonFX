"""Confirmacion de entrada tras el retest del Order Block.

Enlaza el setup detectado con el motor de confirmacion M5: espera el retest de
la zona y delega en `strategy.smc.confirmation_engine` la decision de si la
vela candidata confirma.

ESTADO: no lo importa ningun modulo de produccion. En vivo, esta misma
secuencia (retest + confirmacion) la ejecuta
`strategy.execution.trade_pipeline.run_pipeline`. Aqui se conserva como camino
alternativo usado por los tests.

Vinculaciones:
- Importa `strategy.smc.confirmation_engine` (`M5ConfirmationConfig` y
  `evaluate_m5_confirmation`), que es el mismo motor que usa produccion.
- Recibe los setups de `strategy.smc.setup_detector.detect_setups`.
- Su salida la consume `strategy.smc.risk_reward.calculate_risk_reward`.
"""

import pandas as pd

from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation


def detect_entry_confirmations(
    df: pd.DataFrame,
    setups: pd.DataFrame,
    max_wait_candles: int = 50,
    min_wait_candles: int = 1,
    confirmation_config: M5ConfirmationConfig | None = None,
) -> pd.DataFrame:
    """
    Detecta confirmaciones de entrada después de un setup SMC.

    La lógica busca evitar confirmar automáticamente todos los setups.

    LONG:
        1. Existe un setup LONG.
        2. El precio realiza un retest del Bullish Order Block.
        3. Después del retest aparece una vela alcista.
        4. La vela alcista cierra por encima del máximo
           de la vela anterior.
        5. Se genera la confirmación LONG.

    SHORT:
        1. Existe un setup SHORT.
        2. El precio realiza un retest del Bearish Order Block.
        3. Después del retest aparece una vela bajista.
        4. La vela bajista cierra por debajo del mínimo
           de la vela anterior.
        5. Se genera la confirmación SHORT.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame con velas OHLC.

    setups : pd.DataFrame
        DataFrame generado por setup_detector.py.

    max_wait_candles : int
        Máximo número de velas para esperar un retest
        y su confirmación.

    min_wait_candles : int
        Número mínimo de velas posteriores al setup
        antes de permitir una confirmación.

    Retorna
    -------
    pd.DataFrame
        DataFrame con entradas confirmadas.

    Notas de proceso
    ----------------
    `min_wait_candles` evita confirmar en la misma vela del setup, lo que
    produciria entradas irreales imposibles de reproducir en vivo.
    `max_wait_candles` descarta el setup si el retest nunca llega: una zona
    que tarda demasiado deja de ser valida.

    La decision final NO se toma aqui: cada vela candidata se envia a
    `strategy.smc.confirmation_engine.evaluate_m5_confirmation`, que aplica
    rechazo, desplazamiento, micro estructura y score.

    Vinculaciones
    -------------
    - Llama a `evaluate_m5_confirmation` del confirmation engine.
    - Consume los setups de `strategy.smc.setup_detector.detect_setups`.
    - Su salida alimenta `strategy.smc.risk_reward.calculate_risk_reward`.
    - Sin llamadores de produccion; solo lo usan tests.
    """

    # ==================================================
    # VALIDACIONES
    # ==================================================

    if df.empty:
        return pd.DataFrame()

    if setups.empty:
        return pd.DataFrame()

    required_price_columns = [
        "time",
        "open",
        "high",
        "low",
        "close"
    ]

    missing_price_columns = [
        column
        for column in required_price_columns
        if column not in df.columns
    ]

    if missing_price_columns:
        raise ValueError(
            "Faltan columnas en df: "
            f"{missing_price_columns}"
        )

    required_setup_columns = [
        "time",
        "setup_type",
        "ob_high",
        "ob_low"
    ]

    missing_setup_columns = [
        column
        for column in required_setup_columns
        if column not in setups.columns
    ]

    if missing_setup_columns:
        raise ValueError(
            "Faltan columnas en setups: "
            f"{missing_setup_columns}"
        )

    # ==================================================
    # COPIAS DE SEGURIDAD
    # ==================================================

    price_data = df.copy()
    setup_data = setups.copy()

    # ==================================================
    # NORMALIZAR FECHAS
    # ==================================================

    price_data["time"] = pd.to_datetime(
        price_data["time"],
        utc=True
    )

    setup_data["time"] = pd.to_datetime(
        setup_data["time"],
        utc=True
    )

    price_data = (
        price_data
        .sort_values("time")
        .drop_duplicates("time")
        .reset_index(drop=True)
    )

    setup_data = (
        setup_data
        .sort_values("time")
        .reset_index(drop=True)
    )

    # ==================================================
    # RESULTADOS
    # ==================================================

    confirmations = []
    rejected_candidates = []
    confirmation_config = confirmation_config or M5ConfirmationConfig()

    # ==================================================
    # RECORRER CADA SETUP
    # ==================================================

    for _, setup in setup_data.iterrows():

        setup_time = setup["time"]
        setup_type = setup["setup_type"]

        ob_high = float(setup["ob_high"])
        ob_low = float(setup["ob_low"])

        # Asegurar orden correcto
        if ob_low > ob_high:
            ob_low, ob_high = ob_high, ob_low

        # --------------------------------------------------
        # BUSCAR POSICIÓN DEL SETUP
        # --------------------------------------------------

        setup_positions = price_data.index[
            price_data["time"] == setup_time
        ]

        if len(setup_positions) == 0:
            continue

        setup_index = setup_positions[0]

        # --------------------------------------------------
        # DEFINIR VENTANA DE BÚSQUEDA
        # --------------------------------------------------

        start_index = (
            setup_index
            + max(min_wait_candles, 1)
        )

        end_index = min(
            setup_index + max_wait_candles + 1,
            len(price_data)
        )

        if start_index >= len(price_data):
            continue

        # ==================================================
        # ESTADO DEL RETEST
        # ==================================================

        retest_detected = False
        retest_time = None
        retest_index = None

        # ==================================================
        # BUSCAR RETEST
        # ==================================================

        for i in range(start_index, end_index):

            candle = price_data.iloc[i]

            candle_high = float(candle["high"])
            candle_low = float(candle["low"])

            # --------------------------------------------------
            # LA VELA INTERSECTA EL ORDER BLOCK
            # --------------------------------------------------

            touches_ob = (
                candle_low <= ob_high
                and candle_high >= ob_low
            )

            if not touches_ob:
                continue

            # Guardamos el primer retest válido
            retest_detected = True
            retest_time = candle["time"]
            retest_index = i

            # ==================================================
            # BUSCAR CONFIRMACIÓN DESPUÉS DEL RETEST
            # ==================================================

            confirmation_start = retest_index + 1

            for j in range(
                confirmation_start,
                end_index
            ):

                confirmation_candle = (
                    price_data.iloc[j]
                )

                previous_candle = (
                    price_data.iloc[j - 1]
                )

                confirmation_time = (
                    confirmation_candle["time"]
                )

                candle_open = float(
                    confirmation_candle["open"]
                )

                candle_high = float(
                    confirmation_candle["high"]
                )

                candle_low = float(
                    confirmation_candle["low"]
                )

                candle_close = float(
                    confirmation_candle["close"]
                )

                previous_high = float(
                    previous_candle["high"]
                )

                previous_low = float(
                    previous_candle["low"]
                )

                # ==============================================
                # CONFIRMACIÓN LONG
                # ==============================================

                if setup_type == "long":

                    bullish_candle = (
                        candle_close > candle_open
                    )

                    breaks_previous_high = (
                        candle_close > previous_high
                    )

                    # El precio no debe cerrar por debajo
                    # del límite inferior del Order Block
                    respects_ob = (
                        candle_close >= ob_low
                    )

                    long_confirmation = (
                        bullish_candle
                        and breaks_previous_high
                        and respects_ob
                    )

                    if long_confirmation:

                        quality = evaluate_m5_confirmation(
                            data=price_data,
                            setup=setup,
                            retest_index=retest_index,
                            confirmation_index=j,
                            direction="long",
                            config=confirmation_config,
                        )

                        if not quality["confirmation_valid"]:
                            rejected_candidates.append({
                                "setup_time": setup_time,
                                "retest_time": retest_time,
                                "confirmation_time": confirmation_time,
                                "setup_type": "long",
                                "direction": "BUY",
                                "entry_price": candle_close,
                                "stop_loss": ob_low,
                                "entry_time": confirmation_time,
                                **quality,
                            })
                            continue

                        confirmations.append(
                            {
                                "setup_time": setup_time,
                                "retest_time": retest_time,
                                "confirmation_time": confirmation_time,
                                "entry_time": confirmation_time,

                                "setup_type": "long",

                                "confirmation_type":
                                    "bullish_retest_break",

                                "ob_high": ob_high,
                                "ob_low": ob_low,

                                "entry_price": candle_close,

                                "stop_loss": ob_low,

                                "candle_open": candle_open,
                                "candle_high": candle_high,
                                "candle_low": candle_low,
                                "candle_close": candle_close,

                                "previous_high": previous_high,
                                "previous_low": previous_low,

                                "candles_to_retest":
                                    retest_index - setup_index,

                                "candles_to_confirmation":
                                    j - setup_index,

                                "zone": setup.get(
                                    "zone",
                                    None
                                ),

                                "equilibrium": setup.get(
                                    "equilibrium",
                                    None
                                ),
                                **quality,
                            }
                        )

                        break

                # ==============================================
                # CONFIRMACIÓN SHORT
                # ==============================================

                elif setup_type == "short":

                    bearish_candle = (
                        candle_close < candle_open
                    )

                    breaks_previous_low = (
                        candle_close < previous_low
                    )

                    # El precio no debe cerrar por encima
                    # del límite superior del Order Block
                    respects_ob = (
                        candle_close <= ob_high
                    )

                    short_confirmation = (
                        bearish_candle
                        and breaks_previous_low
                        and respects_ob
                    )

                    if short_confirmation:

                        quality = evaluate_m5_confirmation(
                            data=price_data,
                            setup=setup,
                            retest_index=retest_index,
                            confirmation_index=j,
                            direction="short",
                            config=confirmation_config,
                        )

                        if not quality["confirmation_valid"]:
                            rejected_candidates.append({
                                "setup_time": setup_time,
                                "retest_time": retest_time,
                                "confirmation_time": confirmation_time,
                                "setup_type": "short",
                                "direction": "SELL",
                                "entry_price": candle_close,
                                "stop_loss": ob_high,
                                "entry_time": confirmation_time,
                                **quality,
                            })
                            continue

                        confirmations.append(
                            {
                                "setup_time": setup_time,
                                "retest_time": retest_time,
                                "confirmation_time": confirmation_time,
                                "entry_time": confirmation_time,

                                "setup_type": "short",

                                "confirmation_type":
                                    "bearish_retest_break",

                                "ob_high": ob_high,
                                "ob_low": ob_low,

                                "entry_price": candle_close,

                                "stop_loss": ob_high,

                                "candle_open": candle_open,
                                "candle_high": candle_high,
                                "candle_low": candle_low,
                                "candle_close": candle_close,

                                "previous_high": previous_high,
                                "previous_low": previous_low,

                                "candles_to_retest":
                                    retest_index - setup_index,

                                "candles_to_confirmation":
                                    j - setup_index,

                                "zone": setup.get(
                                    "zone",
                                    None
                                ),

                                "equilibrium": setup.get(
                                    "equilibrium",
                                    None
                                ),
                                **quality,
                            }
                        )

                        break

            # --------------------------------------------------
            # Si encontramos un retest, no buscamos otro
            # para este setup.
            # --------------------------------------------------

            break

    # ==================================================
    # SI NO HAY RESULTADOS
    # ==================================================

    result_columns = [
        "setup_time",
        "retest_time",
        "confirmation_time",
        "entry_time",
        "setup_type",
        "confirmation_type",
        "ob_high",
        "ob_low",
        "entry_price",
        "stop_loss",
        "candle_open",
        "candle_high",
        "candle_low",
        "candle_close",
        "previous_high",
        "previous_low",
        "candles_to_retest",
        "candles_to_confirmation",
        "zone",
        "equilibrium",
        "trade_score", "trade_grade", "confirmation_valid", "confirmation_decision",
        "confirmation_percentage", "confirmations_passed", "confirmations_total",
        "passed_confirmations", "missing_confirmations", "critical_confirmations_ok",
        "critical_confirmation_failures", "strict_rejection_reasons", "rejection_reasons",
        "ob_touches", "ob_fresh", "confirmation_mode", "average_range",
        "candle_range", "body_ratio", "lower_wick_ratio", "upper_wick_ratio",
        "prior_high", "prior_low", "confirmations",
        "divergence_enabled", "divergence_confirmation", "divergence_structure_pressure",
        "divergence_detected", "divergence_type", "divergence_reason",
        "divergence_price_1", "divergence_price_2", "divergence_rsi_1", "divergence_rsi_2"
    ]

    if not confirmations:
        result = pd.DataFrame(columns=result_columns)
        result.attrs["rejected_candidates"] = rejected_candidates
        return result

    # ==================================================
    # DATAFRAME FINAL
    # ==================================================

    result = pd.DataFrame(
        confirmations
    )

    result = (
        result
        .sort_values("entry_time")
        .reset_index(drop=True)
    )

    return result