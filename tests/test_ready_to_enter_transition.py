import pandas as pd

from strategy.execution.multi_timeframe import (
    MultiTimeframeAnalyzer,
    MultiTimeframeConfig,
)


SYMBOL = "Boom 100 Index"


class ControlledDataProvider:
    """
    Proveedor artificial para una prueba completamente controlada.

    No conecta a MT5.
    No utiliza datos reales.

    Genera:

        H1  -> contexto BULLISH
        M15 -> setup LONG válido
        M5  -> confirmación BUY posterior al setup
        M5  -> señal fresca

    Resultado esperado:

        MULTI_TIME_FRAME_SIGNAL
        -> READY_TO_ENTER
    """

    def get_candles(self, symbol, timeframe, count):

        if timeframe == "H1":

            times = pd.date_range(
                start="2026-08-25 10:00:00+00:00",
                periods=6,
                freq="1h",
            )

            return pd.DataFrame(
                {
                    "time": times,
                    "open": [100, 101, 102, 103, 104, 105],
                    "high": [101, 102, 103, 104, 105, 106],
                    "low": [99, 100, 101, 102, 103, 104],
                    "close": [101, 102, 103, 104, 105, 106],
                    "test_timeframe": ["H1"] * len(times),

                    # IMPORTANTE:
                    # Esta columna evita el KeyError: 'structure'
                    "structure": [
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                    ],

                    "bos_bullish": [
                        False,
                        False,
                        False,
                        False,
                        True,
                        True,
                    ],

                    "choch_bullish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "bos_bearish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "choch_bearish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],
                }
            )

        if timeframe == "M15":

            times = pd.date_range(
                start="2026-08-25 14:00:00+00:00",
                periods=8,
                freq="15min",
            )

            return pd.DataFrame(
                {
                    "time": times,
                    "open": [106, 105, 104, 103, 104, 105, 106, 107],
                    "high": [107, 106, 105, 105, 106, 107, 108, 109],
                    "low": [105, 103, 102, 102, 103, 104, 105, 106],
                    "close": [105, 104, 103, 104, 105, 106, 107, 108],
                    "test_timeframe": ["M15"] * len(times),

                    # También mantenemos structure
                    # para que cualquier acceso al DataFrame sea seguro.
                    "structure": [
                        None,
                        None,
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                    ],

                    "bos_bullish": [
                        False,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "choch_bullish": [
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "bos_bearish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "choch_bearish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],
                }
            )

        if timeframe == "M5":

            times = pd.date_range(
                start="2026-08-25 15:00:00+00:00",
                periods=10,
                freq="5min",
            )

            return pd.DataFrame(
                {
                    "time": times,
                    "open": [
                        108.0,
                        108.5,
                        109.0,
                        109.5,
                        110.0,
                        110.5,
                        111.0,
                        111.5,
                        112.0,
                        112.5,
                    ],
                    "high": [
                        109.0,
                        109.5,
                        110.0,
                        110.5,
                        111.0,
                        111.5,
                        112.0,
                        112.5,
                        113.0,
                        113.5,
                    ],
                    "low": [
                        107.5,
                        108.0,
                        108.5,
                        109.0,
                        109.5,
                        110.0,
                        110.5,
                        111.0,
                        111.5,
                        112.0,
                    ],
                    "close": [
                        108.5,
                        109.0,
                        109.5,
                        110.0,
                        110.5,
                        111.0,
                        111.5,
                        112.0,
                        112.5,
                        113.0,
                    ],
                    "test_timeframe": ["M5"] * len(times),

                    "structure": [
                        None,
                        None,
                        None,
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                        "BULLISH",
                    ],

                    "bos_bullish": [
                        False,
                        False,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "choch_bullish": [
                        False,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "bos_bearish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],

                    "choch_bearish": [
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],
                }
            )

        raise ValueError(
            f"Timeframe no soportado en la prueba: {timeframe}"
        )


class ControlledMultiTimeframeAnalyzer(MultiTimeframeAnalyzer):
    """
    Analizador controlado.

    La prueba NO ejecuta el pipeline SMC real.

    En cambio, devuelve resultados artificiales completamente
    controlados para validar únicamente la transición:

        H1
        ->
        M15
        ->
        M5
        ->
        señal válida
        ->
        señal fresca
        ->
        MULTI_TIMEFRAME_SIGNAL
        ->
        READY_TO_ENTER
    """

    def _run_pipeline(self, df, symbol):

        if df is None or df.empty:

            return {
                "data": pd.DataFrame(),
                "setups": pd.DataFrame(),
                "confirmations": pd.DataFrame(),
                "summary": {},
                "diagnostics": {},
            }

        timeframe = str(
            df["test_timeframe"].iloc[0]
        ).upper()

        # ======================================================
        # H1
        # ======================================================

        if timeframe == "H1":

            data = df.copy()

            return {
                "data": data,
                "setups": pd.DataFrame(),
                "confirmations": pd.DataFrame(),
                "summary": {
                    "timeframe": "H1",
                    "trend": "BULLISH",
                },
                "diagnostics": {
                    "controlled": True,
                    "stage": "H1",
                },
            }

        # ======================================================
        # M15
        # ======================================================

        if timeframe == "M15":

            data = df.copy()

            setup_time = pd.Timestamp(
                "2026-08-25 14:45:00+00:00"
            )

            setups = pd.DataFrame(
                [
                    {
                        "setup_type": "long",
                        "setup_time": setup_time,

                        "ob_high": 108.0,
                        "ob_low": 104.0,

                        "zone": "DISCOUNT",
                        "sweep_time": pd.Timestamp(
                            "2026-08-25 14:30:00+00:00"
                        ),

                        "structure_break_type": "BOS_BULLISH",
                    }
                ]
            )

            return {
                "data": data,
                "setups": setups,
                "confirmations": pd.DataFrame(),
                "summary": {
                    "timeframe": "M15",
                    "setup": "LONG",
                },
                "diagnostics": {
                    "controlled": True,
                    "stage": "M15",
                },
            }

        # ======================================================
        # M5
        # ======================================================

        if timeframe == "M5":

            data = df.copy()

            # La señal ocurre DESPUÉS del setup M15.
            #
            # Setup M15:
            #   14:45
            #
            # Confirmación M5:
            #   15:30
            #
            # La última vela cerrada será posterior,
            # pero dentro de max_m5_signal_age_candles = 3.
            signal_time = pd.Timestamp(
                "2026-08-25 15:30:00+00:00"
            )

            confirmations = pd.DataFrame(
                [
                    {
                        "valid": True,
                        "direction": "BUY",

                        "entry_time": signal_time,

                        "entry_price": 111.0,
                        "stop_loss": 109.0,
                        "take_profit": 115.0,

                        "risk_reward_ratio": 2.0,

                        "confirmation_type": "CONTROLLED_M5_CONFIRMATION",
                    }
                ]
            )

            return {
                "data": data,
                "setups": pd.DataFrame(),
                "confirmations": confirmations,
                "summary": {
                    "timeframe": "M5",
                    "confirmation": "BUY",
                },
                "diagnostics": {
                    "controlled": True,
                    "stage": "M5",
                },
            }

        raise ValueError(
            f"Timeframe inesperado en pipeline controlado: {timeframe}"
        )


def test_controlled_transition_to_ready_to_enter():

    """
    Prueba completa:

        H1 válido
            ->
        M15 setup válido
            ->
        M5 posterior al setup
            ->
        M5 fresco
            ->
        MULTI_TIME_FRAME_SIGNAL
            ->
        READY_TO_ENTER
    """

    provider = ControlledDataProvider()

    config = MultiTimeframeConfig(

        require_h1_trend=True,

        require_m15_setup=True,

        require_m5_confirmation=True,

        require_m5_after_m15=True,

        require_latest_m15_setup=True,

        max_m5_signal_age_candles=3,

        max_m5_signal_age_minutes=None,
    )

    analyzer = ControlledMultiTimeframeAnalyzer(
        data_provider=provider,
        config=config,
    )

    print()
    print("=" * 80)
    print("PRUEBA CONTROLADA DE TRANSICION COMPLETA")
    print("H1 -> M15 -> M5 -> READY_TO_ENTER")
    print("=" * 80)

    result = analyzer.analyze_symbol(
        SYMBOL
    )

    print()
    print("RESULTADO COMPLETO:")
    print(result)

    print()
    print("-" * 80)
    print("VALIDACION H1")
    print("-" * 80)

    assert result["h1"]["context"]["valid"] is True

    assert (
        result["h1"]["context"]["trend"]
        == "BULLISH"
    )

    print("H1_VALID: OK")
    print(
        "H1 trend:",
        result["h1"]["context"]["trend"],
    )

    print()
    print("-" * 80)
    print("VALIDACION M15")
    print("-" * 80)

    assert result["m15"] is not None

    assert result["m15"]["setup"] is not None

    assert (
        result["m15"]["setup"]["setup_type"].lower()
        == "long"
    )

    print("M15_SETUP_VALID: OK")
    print(
        "M15 setup time:",
        result["m15"]["setup"]["setup_time"],
    )

    print()
    print("-" * 80)
    print("VALIDACION M5")
    print("-" * 80)

    assert result["m5"] is not None

    assert result["m5"]["signal"] is not None

    assert (
        result["m5"]["signal"]["direction"]
        == "BUY"
    )

    print("M5_CONFIRMATION_VALID: OK")
    print(
        "M5 signal time:",
        result["m5"]["signal"]["entry_time"],
    )

    print()
    print("-" * 80)
    print("VALIDACION DE SECUENCIA TEMPORAL")
    print("-" * 80)

    sequence_status = (
        result["diagnostics"]["sequence_status"]
    )

    assert (
        sequence_status
        == "VALID_SEQUENCE"
    )

    setup_time = pd.to_datetime(
        result["m15"]["setup"]["setup_time"],
        utc=True,
    )

    confirmation_time = pd.to_datetime(
        result["m5"]["signal"]["entry_time"],
        utc=True,
    )

    assert confirmation_time >= setup_time

    print("M5_AFTER_M15: OK")
    print("Sequence status:", sequence_status)

    print()
    print("-" * 80)
    print("VALIDACION DE FRESCURA")
    print("-" * 80)

    signal_age = (
        result["diagnostics"]["signal_age"]
    )

    assert signal_age["is_stale"] is False

    assert signal_age["valid"] is True

    assert (
        signal_age["reason"]
        == "M5_SIGNAL_FRESH"
    )

    print("M5_FRESH: OK")
    print(
        "Age candles:",
        signal_age["age_candles"],
    )

    print()
    print("-" * 80)
    print("VALIDACION DE SENAL MULTI TIMEFRAME")
    print("-" * 80)

    assert result["valid"] is True

    assert (
        result["action"]
        == "MULTI_TIMEFRAME_SIGNAL"
    )

    assert result["direction"] == "BUY"

    print("MULTI_TIMEFRAME_SIGNAL: OK")

    print()
    print("=" * 80)
    print("READY_TO_ENTER")
    print("=" * 80)

    ready_to_enter = (
        result["valid"] is True
        and result["action"] == "MULTI_TIMEFRAME_SIGNAL"
        and result["direction"] == "BUY"
        and result["diagnostics"]["sequence_status"]
        == "VALID_SEQUENCE"
        and result["diagnostics"]["signal_age"]["is_stale"]
        is False
    )

    assert ready_to_enter is True

    print()
    print("H1_VALID")
    print("M15_SETUP_VALID")
    print("M5_CONFIRMATION_VALID")
    print("M5_AFTER_M15")
    print("M5_FRESH")
    print("READY_TO_ENTER")
    print()
    print("DIRECTION:", result["direction"])
    print(
        "ENTRY TIME:",
        result["entry_time"],
    )
    print(
        "ENTRY PRICE:",
        result["entry_price"],
    )
    print(
        "STOP LOSS:",
        result["stop_loss"],
    )
    print(
        "TAKE PROFIT:",
        result["take_profit"],
    )
    print(
        "RISK REWARD:",
        result["risk_reward_ratio"],
    )

    print()
    print("=" * 80)
    print("PRUEBA CONTROLADA EXITOSA")
    print("=" * 80)