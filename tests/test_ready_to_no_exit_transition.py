import pandas as pd

from strategy.execution.multi_timeframe import (
    MultiTimeframeAnalyzer,
    MultiTimeframeConfig,
)

from strategy.smc.trade_simulator import (
    simulate_trade,
)


SYMBOL = "Boom 100 Index"


# ============================================================
# PROVEEDOR CONTROLADO
# ============================================================

class ControlledDataProvider:

    def get_candles(self, symbol, timeframe, count):

        if symbol != SYMBOL:
            raise ValueError(
                f"Símbolo inesperado: {symbol}"
            )

        # ====================================================
        # H1
        # ====================================================

        if timeframe == "H1":

            times = pd.date_range(
                "2026-08-24 00:00:00+00:00",
                periods=10,
                freq="1h",
            )

            df = pd.DataFrame({
                "time": times,

                "open": [
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                ],

                "high": [
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    111,
                ],

                "low": [
                    99,
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                ],

                "close": [
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                ],

                "test_timeframe": "H1",

                "bos_bullish": [
                    False,
                    False,
                    False,
                    False,
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
            })

            return (
                df.head(count)
                .reset_index(drop=True)
            )

        # ====================================================
        # M15
        # ====================================================

        if timeframe == "M15":

            times = pd.date_range(
                "2026-08-25 12:00:00+00:00",
                periods=20,
                freq="15min",
            )

            df = pd.DataFrame({
                "time": times,

                "open": [
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    109,
                    110,
                    111,
                    110,
                    111,
                    112,
                    111,
                    112,
                    113,
                ],

                "high": [
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    111,
                    112,
                    112,
                    113,
                    114,
                    113,
                    114,
                    115,
                    114,
                    115,
                    116,
                ],

                "low": [
                    99,
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    108,
                    107,
                    108,
                    109,
                    108,
                    109,
                    110,
                    109,
                    110,
                    111,
                ],

                "close": [
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    109,
                    111,
                    112,
                    110,
                    112,
                    113,
                    111,
                    113,
                    114,
                    115,
                ],

                "test_timeframe": "M15",
            })

            return (
                df.head(count)
                .reset_index(drop=True)
            )

        # ====================================================
        # M5
        #
        # ESCENARIO CONTROLADO NO_EXIT
        #
        # Entrada:
        #
        # ENTRY = 111.0
        # SL    = 109.0
        # TP    = 115.0
        #
        # Las velas posteriores a 15:00:
        #
        # - NUNCA bajan hasta 109.0
        # - NUNCA suben hasta 115.0
        #
        # Por lo tanto:
        #
        # NO hay STOP LOSS
        # NO hay TAKE PROFIT
        #
        # El simulador debe terminar en:
        #
        # expired
        # ====================================================

        if timeframe == "M5":

            times = pd.date_range(
                "2026-08-25 14:30:00+00:00",
                periods=15,
                freq="5min",
            )

            df = pd.DataFrame({

                "time": times,

                "open": [
                    106,
                    107,
                    108,
                    109,
                    110,
                    110,
                    111,
                    111,
                    112,
                    113,
                    112,
                    111,
                    112,
                    113,
                    112,
                ],

                "high": [
                    108,
                    109,
                    110,
                    111,
                    112,
                    112,
                    113,

                    # FUTURO DESPUÉS DE ENTRY
                    113.0,
                    114.0,
                    114.0,
                    113.5,
                    113.0,
                    114.0,
                    114.5,
                    114.0,
                ],

                "low": [
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    110,

                    # FUTURO DESPUÉS DE ENTRY
                    # Todos los valores son MAYORES que SL = 109.0
                    110.0,
                    111.0,
                    112.0,
                    110.5,
                    110.0,
                    111.0,
                    112.0,
                    111.0,
                ],

                "close": [
                    107,
                    108,
                    109,
                    110,
                    111,
                    111,
                    112,

                    # FUTURO DESPUÉS DE ENTRY
                    112.0,
                    113.0,
                    112.5,
                    111.0,
                    112.0,
                    113.0,
                    112.5,
                    113.0,
                ],

                "test_timeframe": "M5",
            })

            return (
                df.head(count)
                .reset_index(drop=True)
            )

        # ====================================================
        # ERROR CONTROLADO
        # ====================================================

        raise ValueError(
            f"No existe pipeline controlado para: {timeframe}"
        )


# ============================================================
# ANALIZADOR CONTROLADO
#
# Usa la lógica real de MultiTimeframeAnalyzer,
# pero inyecta resultados deterministas.
# ============================================================

class ControlledMultiTimeframeAnalyzer(
    MultiTimeframeAnalyzer
):

    def _run_pipeline(self, df, symbol):

        if df is None or df.empty:

            return {
                "data": pd.DataFrame(),
                "setups": pd.DataFrame(),
                "confirmations": pd.DataFrame(),
                "summary": {},
                "diagnostics": {},
            }

        timeframe = df[
            "test_timeframe"
        ].iloc[0]

        # ====================================================
        # H1
        # ====================================================

        if timeframe == "H1":

            return {

                "data": df.copy(),

                "setups": pd.DataFrame(),

                "confirmations": pd.DataFrame(),

                "summary": {
                    "trend": "BULLISH",
                },

                "diagnostics": {},
            }

        # ====================================================
        # M15
        # ====================================================

        if timeframe == "M15":

            setups = pd.DataFrame([
                {
                    "setup_time": pd.Timestamp(
                        "2026-08-25 14:45:00+00:00"
                    ),

                    "setup_type": "long",

                    "ob_high": 108.0,

                    "ob_low": 104.0,

                    "zone": "DISCOUNT",

                    "sweep_time": pd.Timestamp(
                        "2026-08-25 14:30:00+00:00"
                    ),

                    "structure_break_type": (
                        "BOS_BULLISH"
                    ),
                }
            ])

            return {

                "data": df.copy(),

                "setups": setups,

                "confirmations": pd.DataFrame(),

                "summary": {
                    "trend": "BULLISH",
                },

                "diagnostics": {},
            }

        # ====================================================
        # M5
        # ====================================================

        if timeframe == "M5":

            confirmations = pd.DataFrame([
                {
                    "valid": True,

                    "direction": "BUY",

                    "entry_time": pd.Timestamp(
                        "2026-08-25 15:00:00+00:00"
                    ),

                    "entry_price": 111.0,

                    "stop_loss": 109.0,

                    "take_profit": 115.0,

                    "risk_reward_ratio": 2.0,

                    "confirmation_type": (
                        "CONTROLLED_M5_CONFIRMATION"
                    ),
                }
            ])

            return {

                "data": df.copy(),

                "setups": pd.DataFrame(),

                "confirmations": confirmations,

                "summary": {
                    "trend": "BULLISH",
                },

                "diagnostics": {},
            }

        raise ValueError(
            f"Pipeline no controlado para: {timeframe}"
        )


# ============================================================
# TEST PRINCIPAL
# ============================================================

def test_controlled_ready_to_enter_to_no_exit():

    print()
    print("=" * 80)
    print("PRUEBA CONTROLADA COMPLETA")
    print(
        "READY_TO_ENTER -> EXECUTION -> NO_EXIT -> EXPIRED"
    )
    print("=" * 80)

    # ========================================================
    # 1. CREAR PROVEEDOR
    # ========================================================

    provider = ControlledDataProvider()

    # ========================================================
    # 2. CONFIGURAR ANALIZADOR
    # ========================================================

    config = MultiTimeframeConfig(

        structure_timeframe="H1",

        confirmation_timeframe="M15",

        entry_timeframe="M5",

        # READY_TO_ENTER analiza solamente
        # la ventana necesaria para generar
        # la señal de entrada.
        entry_candles=10,

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

    # ========================================================
    # 3. EJECUTAR ANALISIS MULTI TIMEFRAME
    # ========================================================

    print()
    print(
        "1. EJECUTANDO ANALISIS MULTI TIMEFRAME"
    )
    print()
    print(
        "H1 -> M15 -> M5 -> READY_TO_ENTER"
    )

    result = analyzer.analyze_symbol(
        SYMBOL
    )

    # ========================================================
    # 4. VALIDAR MULTI TIMEFRAME
    # ========================================================

    assert result["valid"] is True

    assert (
        result["action"]
        == "MULTI_TIMEFRAME_SIGNAL"
    )

    assert result["direction"] == "BUY"

    assert result["entry_price"] == 111.0

    assert result["stop_loss"] == 109.0

    assert result["take_profit"] == 115.0

    assert (
        result["risk_reward_ratio"]
        == 2.0
    )

    print()
    print(
        "MULTI_TIMEFRAME_SIGNAL: OK"
    )
    print(
        "STATE: READY_TO_ENTER"
    )
    print(
        f"DIRECTION: {result['direction']}"
    )
    print(
        f"ENTRY TIME: {result['entry_time']}"
    )
    print(
        f"ENTRY PRICE: {result['entry_price']}"
    )
    print(
        f"STOP LOSS: {result['stop_loss']}"
    )
    print(
        f"TAKE PROFIT: {result['take_profit']}"
    )
    print(
        f"RISK REWARD: "
        f"{result['risk_reward_ratio']}"
    )

    # ========================================================
    # 5. TRANSICION READY_TO_ENTER
    # ========================================================

    ready_to_enter = {

        "state": "READY_TO_ENTER",

        "symbol": result["symbol"],

        "timeframe": result["m5_timeframe"],

        "direction": result["direction"],

        "entry_time": result["entry_time"],

        "entry_price": result["entry_price"],

        "stop_loss": result["stop_loss"],

        "take_profit": result["take_profit"],

        "risk_reward_ratio": (
            result["risk_reward_ratio"]
        ),
    }

    assert (
        ready_to_enter["state"]
        == "READY_TO_ENTER"
    )

    assert (
        ready_to_enter["timeframe"]
        == "M5"
    )

    print()
    print(
        "2. READY_TO_ENTER: OK"
    )
    print(
        f"TIMEFRAME DE EJECUCION: "
        f"{ready_to_enter['timeframe']}"
    )

    # ========================================================
    # 6. RECUPERAR VELAS PARA TRADE_SIMULATOR
    # ========================================================

    execution_timeframe = (
        ready_to_enter["timeframe"]
    )

    assert (
        execution_timeframe == "M5"
    )

    execution_candles = provider.get_candles(

        symbol=SYMBOL,

        timeframe=execution_timeframe,

        count=100,
    )

    assert (
        execution_candles
        is not None
    )

    assert not (
        execution_candles.empty
    )

    print()
    print(
        "3. VELAS DE EJECUCION: OK"
    )
    print(
        f"TIMEFRAME: "
        f"{execution_timeframe}"
    )
    print(
        f"TOTAL CANDLES: "
        f"{len(execution_candles)}"
    )

    # ========================================================
    # 7. VERIFICAR VELAS POSTERIORES
    # ========================================================

    entry_time = pd.to_datetime(

        ready_to_enter["entry_time"],

        utc=True,
    )

    future_candles = execution_candles[

        pd.to_datetime(

            execution_candles["time"],

            utc=True,

        ) > entry_time

    ].copy()

    assert not future_candles.empty

    # ========================================================
    # VALIDACION CRITICA DEL ESCENARIO
    #
    # Ninguna vela futura debe tocar:
    #
    # SL = 109.0
    # TP = 115.0
    # ========================================================

    assert (
        future_candles["low"].min()
        > ready_to_enter["stop_loss"]
    )

    assert (
        future_candles["high"].max()
        < ready_to_enter["take_profit"]
    )

    print()
    print(
        "4. VELAS POSTERIORES A LA ENTRADA: OK"
    )
    print(
        f"FUTURE CANDLES: "
        f"{len(future_candles)}"
    )
    print(
        "NINGUNA VELA TOCA STOP LOSS"
    )
    print(
        "NINGUNA VELA TOCA TAKE PROFIT"
    )

    # ========================================================
    # 8. EJECUTAR TRADE_SIMULATOR
    # ========================================================

    print()
    print(
        "5. EJECUTANDO TRADE_SIMULATOR"
    )

    trade = pd.Series({

        "entry_time": (
            ready_to_enter["entry_time"]
        ),

        "entry_price": (
            ready_to_enter["entry_price"]
        ),

        "stop_loss": (
            ready_to_enter["stop_loss"]
        ),

        "take_profit": (
            ready_to_enter["take_profit"]
        ),

        "trade_type": (

            "long"

            if (
                ready_to_enter["direction"]
                == "BUY"
            )

            else "short"
        ),
    })

    simulation = simulate_trade(

        df=execution_candles,

        trade=trade,

        max_bars=500,
    )

    # ========================================================
    # 9. VALIDAR RESULTADO NO_EXIT / EXPIRED
    # ========================================================

    assert simulation is not None

    assert "result" in simulation

    # ========================================================
    # RESULTADO PRINCIPAL
    #
    # El simulador actual procesa todas las velas
    # disponibles.
    #
    # Como ninguna alcanza:
    #
    # STOP LOSS
    #
    # ni
    #
    # TAKE PROFIT
    #
    # el resultado esperado es:
    #
    # expired
    #
    # "expired" significa que terminó la ventana
    # de simulación sin producirse una salida por
    # SL o TP.
    # ========================================================

    assert (
        simulation["result"]
        == "expired"
    )

    # ========================================================
    # CONTROLES CONTRA RESULTADOS INCORRECTOS
    # ========================================================

    assert (
        simulation["result"]
        != "win"
    )

    assert (
        simulation["result"]
        != "loss"
    )

    assert (
        simulation["result"]
        != "ambiguous"
    )

    # ========================================================
    # 10. CREAR RESULTADO DE EJECUCION
    # ========================================================

    execution_result = {

        "valid": True,

        "state": "EXECUTION",

        "action": "SIMULATED_EXECUTION",

        "symbol": (
            ready_to_enter["symbol"]
        ),

        "timeframe": execution_timeframe,

        "direction": (
            ready_to_enter["direction"]
        ),

        "entry_time": (
            ready_to_enter["entry_time"]
        ),

        "entry_price": (
            ready_to_enter["entry_price"]
        ),

        "stop_loss": (
            ready_to_enter["stop_loss"]
        ),

        "take_profit": (
            ready_to_enter["take_profit"]
        ),

        "simulation": simulation,
    }

    assert (
        execution_result["valid"]
        is True
    )

    assert (
        execution_result["state"]
        == "EXECUTION"
    )

    assert (
        execution_result["action"]
        == "SIMULATED_EXECUTION"
    )

    # ========================================================
    # RESULTADOS
    # ========================================================

    print()
    print("=" * 80)
    print(
        "READY_TO_ENTER -> EXECUTION -> NO_EXIT -> EXPIRED"
    )
    print("=" * 80)

    print(
        f"DIRECTION: "
        f"{execution_result['direction']}"
    )

    print(
        f"ENTRY TIME: "
        f"{execution_result['entry_time']}"
    )

    print(
        f"ENTRY PRICE: "
        f"{execution_result['entry_price']}"
    )

    print(
        f"STOP LOSS: "
        f"{execution_result['stop_loss']}"
    )

    print(
        f"TAKE PROFIT: "
        f"{execution_result['take_profit']}"
    )

    print(
        f"SIMULATION RESULT: "
        f"{simulation.get('result')}"
    )

    print(
        f"EXIT TIME: "
        f"{simulation.get('exit_time')}"
    )

    print(
        f"EXIT PRICE: "
        f"{simulation.get('exit_price')}"
    )

    print(
        f"BARS HELD: "
        f"{simulation.get('bars_held')}"
    )

    print(
        f"REASON: "
        f"{simulation.get('exit_reason')}"
    )

    print(
        f"PNL PRICE: "
        f"{simulation.get('pnl_price')}"
    )

    print()
    print("=" * 80)
    print(
        "PRUEBA CONTROLADA EXITOSA"
    )
    print(
        "READY_TO_ENTER -> EXECUTION -> NO_EXIT -> EXPIRED"
    )
    print("=" * 80)