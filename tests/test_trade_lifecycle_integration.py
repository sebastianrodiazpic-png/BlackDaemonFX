import pandas as pd

from strategy.execution.multi_timeframe import (
    MultiTimeframeAnalyzer,
    MultiTimeframeConfig,
)

from strategy.smc.trade_simulator import (
    simulate_trade,
)


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

SYMBOL = "Boom 100 Index"

ENTRY_TIME = pd.Timestamp(
    "2026-08-25 15:00:00+00:00"
)

ENTRY_PRICE = 111.0

STOP_LOSS = 109.0

TAKE_PROFIT = 115.0

RISK_REWARD = 2.0


# ============================================================
# PROVEEDOR CONTROLADO MULTI-ESCENARIO
#
# El mismo proveedor genera:
#
# - H1: tendencia alcista
# - M15: setup alcista
# - M5: confirmacion BUY
#
# Las velas posteriores a la entrada cambian segun
# el escenario:
#
# - win
# - loss
# - ambiguous
# - expired
# ============================================================

class ControlledLifecycleDataProvider:

    def __init__(self, scenario):
        self.scenario = scenario

    def get_candles(
        self,
        symbol,
        timeframe,
        count,
    ):

        if symbol != SYMBOL:

            raise ValueError(
                f"Símbolo inesperado: {symbol}"
            )

        # ====================================================
        # H1
        #
        # Tendencia estructural BULLISH
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

            return df.head(count).reset_index(
                drop=True
            )

        # ====================================================
        # M15
        #
        # Setup alcista valido
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

            return df.head(count).reset_index(
                drop=True
            )

        # ====================================================
        # M5
        #
        # Genera:
        #
        # 1. Contexto previo
        # 2. Vela de entrada
        # 3. Velas posteriores controladas
        # ====================================================

        if timeframe == "M5":

            return self._build_m5_candles(
                count=count
            )

        raise ValueError(
            f"Timeframe no controlado: {timeframe}"
        )

    # ========================================================
    # CONSTRUIR VELAS M5
    # ========================================================

    def _build_m5_candles(
        self,
        count,
    ):

        times = pd.date_range(
            "2026-08-25 14:30:00+00:00",
            periods=15,
            freq="5min",
        )

        # ====================================================
        # VELAS BASE
        #
        # La entrada ocurre a las 15:00.
        # ====================================================

        opens = [
            106,
            107,
            108,
            109,
            110,
            110,
            111,
            111,
            111,
            110,
            109,
            108,
            108,
            107,
            107,
        ]

        highs = [
            108,
            109,
            110,
            111,
            112,
            112,
            113,
            113,
            113,
            113,
            113,
            113,
            113,
            113,
            113,
        ]

        lows = [
            105,
            106,
            107,
            108,
            109,
            110,
            110,
            110,
            110,
            110,
            110,
            110,
            110,
            110,
            110,
        ]

        closes = [
            107,
            108,
            109,
            110,
            111,
            111,
            112,
            112,
            112,
            112,
            112,
            112,
            112,
            112,
            113,
        ]

        # ====================================================
        # ESCENARIO WIN
        #
        # Vela 15:10 toca TP primero.
        # ====================================================

        if self.scenario == "win":

            highs[8] = 115.0
            lows[8] = 110.0
            closes[8] = 115.0

        # ====================================================
        # ESCENARIO LOSS
        #
        # Vela 15:10 toca SL.
        # ====================================================

        elif self.scenario == "loss":

            highs[8] = 112.0
            lows[8] = 109.0
            closes[8] = 109.0

        # ====================================================
        # ESCENARIO AMBIGUOUS
        #
        # La misma vela toca SL y TP.
        # ====================================================

        elif self.scenario == "ambiguous":

            highs[8] = 115.0
            lows[8] = 109.0
            closes[8] = 111.0

        # ====================================================
        # ESCENARIO EXPIRED
        #
        # Ninguna de las 8 velas posteriores toca
        # SL ni TP.
        # ====================================================

        elif self.scenario == "expired":

            highs[7:] = [
                113.0,
                113.0,
                113.5,
                114.0,
                113.5,
                114.0,
                114.0,
                114.0,
            ]

            lows[7:] = [
                110.0,
                110.0,
                110.5,
                111.0,
                110.5,
                111.0,
                111.0,
                111.0,
            ]

            closes[7:] = [
                112.0,
                112.0,
                112.5,
                113.0,
                112.5,
                113.0,
                112.5,
                113.0,
            ]

        else:

            raise ValueError(
                f"Escenario desconocido: "
                f"{self.scenario}"
            )

        df = pd.DataFrame({

            "time": times,

            "open": opens,

            "high": highs,

            "low": lows,

            "close": closes,

            "test_timeframe": "M5",
        })

        return df.head(count).reset_index(
            drop=True
        )


# ============================================================
# ANALIZADOR CONTROLADO
#
# Usa MultiTimeframeAnalyzer real.
#
# Solo inyectamos resultados deterministas de los pipelines
# H1, M15 y M5 para aislar el ciclo de vida de la operación.
# ============================================================

class ControlledLifecycleAnalyzer(
    MultiTimeframeAnalyzer
):

    def _run_pipeline(
        self,
        df,
        symbol,
    ):

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

                    "entry_time": ENTRY_TIME,

                    "entry_price": ENTRY_PRICE,

                    "stop_loss": STOP_LOSS,

                    "take_profit": TAKE_PROFIT,

                    "risk_reward_ratio": RISK_REWARD,

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
            f"Pipeline no controlado: {timeframe}"
        )


# ============================================================
# CREAR CONFIGURACION
# ============================================================

def create_config():

    return MultiTimeframeConfig(

        structure_timeframe="H1",

        confirmation_timeframe="M15",

        entry_timeframe="M5",

        # READY_TO_ENTER analiza una ventana controlada.
        # Las velas posteriores se utilizan para simulación.
        entry_candles=10,

        require_h1_trend=True,

        require_m15_setup=True,

        require_m5_confirmation=True,

        require_m5_after_m15=True,

        require_latest_m15_setup=True,

        max_m5_signal_age_candles=3,

        max_m5_signal_age_minutes=None,
    )


# ============================================================
# EJECUTAR CICLO COMPLETO
#
# READY_TO_ENTER
#       ↓
# EXECUTION
#       ↓
# RESULTADO FINAL
# ============================================================

def run_lifecycle(
    scenario,
):

    # ========================================================
    # 1. PROVEEDOR
    # ========================================================

    provider = ControlledLifecycleDataProvider(
        scenario=scenario
    )

    # ========================================================
    # 2. ANALIZADOR
    # ========================================================

    analyzer = ControlledLifecycleAnalyzer(

        data_provider=provider,

        config=create_config(),
    )

    # ========================================================
    # 3. MULTI TIMEFRAME
    # ========================================================

    analysis = analyzer.analyze_symbol(
        SYMBOL
    )

    assert analysis["valid"] is True

    assert analysis["action"] == (
        "MULTI_TIMEFRAME_SIGNAL"
    )

    assert analysis["direction"] == "BUY"

    assert analysis["entry_time"] == ENTRY_TIME

    assert analysis["entry_price"] == (
        ENTRY_PRICE
    )

    assert analysis["stop_loss"] == (
        STOP_LOSS
    )

    assert analysis["take_profit"] == (
        TAKE_PROFIT
    )

    assert analysis["risk_reward_ratio"] == (
        RISK_REWARD
    )

    # ========================================================
    # 4. READY_TO_ENTER
    # ========================================================

    ready_to_enter = {

        "state": "READY_TO_ENTER",

        "symbol": analysis["symbol"],

        "timeframe": analysis["m5_timeframe"],

        "direction": analysis["direction"],

        "entry_time": analysis["entry_time"],

        "entry_price": analysis["entry_price"],

        "stop_loss": analysis["stop_loss"],

        "take_profit": analysis["take_profit"],

        "risk_reward_ratio": (
            analysis["risk_reward_ratio"]
        ),
    }

    assert ready_to_enter["state"] == (
        "READY_TO_ENTER"
    )

    assert ready_to_enter["timeframe"] == "M5"

    # ========================================================
    # 5. RECUPERAR VELAS DE EJECUCION
    # ========================================================

    execution_timeframe = (
        ready_to_enter["timeframe"]
    )

    execution_candles = provider.get_candles(

        symbol=SYMBOL,

        timeframe=execution_timeframe,

        count=100,
    )

    assert execution_candles is not None

    assert not execution_candles.empty

    # ========================================================
    # 6. VALIDAR VELAS POSTERIORES
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

    assert len(future_candles) == 8

    # ========================================================
    # 7. EJECUCION
    # ========================================================

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

    assert simulation is not None

    assert "result" in simulation

    # ========================================================
    # 8. ESTADO EXECUTION
    # ========================================================

    execution_result = {

        "valid": True,

        "state": "EXECUTION",

        "action": "SIMULATED_EXECUTION",

        "symbol": ready_to_enter["symbol"],

        "timeframe": execution_timeframe,

        "direction": ready_to_enter["direction"],

        "entry_time": ready_to_enter["entry_time"],

        "entry_price": ready_to_enter["entry_price"],

        "stop_loss": ready_to_enter["stop_loss"],

        "take_profit": ready_to_enter["take_profit"],

        "simulation": simulation,
    }

    assert execution_result["valid"] is True

    assert execution_result["state"] == (
        "EXECUTION"
    )

    return {

        "analysis": analysis,

        "ready_to_enter": ready_to_enter,

        "execution_candles": execution_candles,

        "future_candles": future_candles,

        "simulation": simulation,

        "execution_result": execution_result,
    }


# ============================================================
# IMPRIMIR RESULTADO DE UN CASO
# ============================================================

def print_case_result(
    scenario,
    lifecycle,
):

    simulation = lifecycle["simulation"]

    print()

    print("-" * 80)

    print(
        f"CASO: {scenario.upper()}"
    )

    print(
        "READY_TO_ENTER -> EXECUTION"
    )

    print("-" * 80)

    print(
        f"DIRECTION: "
        f"{lifecycle['ready_to_enter']['direction']}"
    )

    print(
        f"ENTRY TIME: "
        f"{lifecycle['ready_to_enter']['entry_time']}"
    )

    print(
        f"ENTRY PRICE: "
        f"{lifecycle['ready_to_enter']['entry_price']}"
    )

    print(
        f"STOP LOSS: "
        f"{lifecycle['ready_to_enter']['stop_loss']}"
    )

    print(
        f"TAKE PROFIT: "
        f"{lifecycle['ready_to_enter']['take_profit']}"
    )

    print(
        f"RESULT: "
        f"{simulation['result']}"
    )

    print(
        f"EXIT TIME: "
        f"{simulation['exit_time']}"
    )

    print(
        f"EXIT PRICE: "
        f"{simulation['exit_price']}"
    )

    print(
        f"BARS HELD: "
        f"{simulation['bars_held']}"
    )

    print(
        f"EXIT REASON: "
        f"{simulation['exit_reason']}"
    )

    print(
        f"PNL PRICE: "
        f"{simulation['pnl_price']}"
    )


# ============================================================
# TEST PRINCIPAL DE INTEGRACION
# ============================================================

def test_trade_lifecycle_integration():

    print()

    print("=" * 80)

    print(
        "PRUEBA DE INTEGRACION COMPLETA"
    )

    print(
        "TRADE LIFECYCLE"
    )

    print("=" * 80)

    print()

    print(
        "CASOS A VALIDAR:"
    )

    print(
        "1. READY_TO_ENTER -> EXECUTION -> WIN"
    )

    print(
        "2. READY_TO_ENTER -> EXECUTION -> LOSS"
    )

    print(
        "3. READY_TO_ENTER -> EXECUTION -> AMBIGUOUS"
    )

    print(
        "4. READY_TO_ENTER -> EXECUTION -> EXPIRED"
    )

    # ========================================================
    # CASO 1
    #
    # WIN
    # ========================================================

    win_case = run_lifecycle(
        scenario="win"
    )

    win = win_case["simulation"]

    assert win["result"] == "win"

    assert win["exit_price"] == 115.0

    assert win["exit_time"] == pd.Timestamp(
        "2026-08-25 15:10:00+00:00"
    )

    assert win["bars_held"] == 2

    assert win["exit_reason"] == (
        "take_profit"
    )

    assert win["pnl_price"] == 4.0

    print_case_result(
        "WIN",
        win_case,
    )

    # ========================================================
    # CASO 2
    #
    # LOSS
    # ========================================================

    loss_case = run_lifecycle(
        scenario="loss"
    )

    loss = loss_case["simulation"]

    assert loss["result"] == "loss"

    assert loss["exit_price"] == 109.0

    assert loss["exit_time"] == pd.Timestamp(
        "2026-08-25 15:10:00+00:00"
    )

    assert loss["bars_held"] == 2

    assert loss["exit_reason"] == (
        "stop_loss"
    )

    assert loss["pnl_price"] == -2.0

    print_case_result(
        "LOSS",
        loss_case,
    )

    # ========================================================
    # CASO 3
    #
    # AMBIGUOUS
    # ========================================================

    ambiguous_case = run_lifecycle(
        scenario="ambiguous"
    )

    ambiguous = ambiguous_case["simulation"]

    assert ambiguous["result"] == "ambiguous"

    assert ambiguous["exit_price"] is None

    assert ambiguous["exit_time"] == pd.Timestamp(
        "2026-08-25 15:10:00+00:00"
    )

    assert ambiguous["bars_held"] == 2

    assert ambiguous["exit_reason"] == (
        "sl_and_tp_same_bar"
    )

    assert ambiguous["pnl_price"] == 0.0

    print_case_result(
        "AMBIGUOUS",
        ambiguous_case,
    )

    # ========================================================
    # CASO 4
    #
    # EXPIRED
    # ========================================================

    expired_case = run_lifecycle(
        scenario="expired"
    )

    expired = expired_case["simulation"]

    assert expired["result"] == "expired"

    assert expired["exit_price"] == 113.0

    assert expired["exit_time"] == pd.Timestamp(
        "2026-08-25 15:40:00+00:00"
    )

    assert expired["bars_held"] == 8

    assert expired["exit_reason"] == (
        "max_bars_reached"
    )

    assert expired["pnl_price"] == 0.0

    print_case_result(
        "EXPIRED",
        expired_case,
    )

    # ========================================================
    # VALIDACION GLOBAL
    # ========================================================

    all_results = {

        "win": win,

        "loss": loss,

        "ambiguous": ambiguous,

        "expired": expired,
    }

    assert len(all_results) == 4

    assert all_results["win"]["result"] == (
        "win"
    )

    assert all_results["loss"]["result"] == (
        "loss"
    )

    assert (
        all_results["ambiguous"]["result"]
        == "ambiguous"
    )

    assert (
        all_results["expired"]["result"]
        == "expired"
    )

    # ========================================================
    # CONTROL DE SESGO
    #
    # Debe existir exactamente:
    #
    # 1 WIN
    # 1 LOSS
    # 1 AMBIGUOUS
    # 1 EXPIRED
    # ========================================================

    results = [

        item["result"]

        for item in all_results.values()
    ]

    assert results.count("win") == 1

    assert results.count("loss") == 1

    assert results.count("ambiguous") == 1

    assert results.count("expired") == 1

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()

    print("=" * 80)

    print(
        "RESUMEN INTEGRACION COMPLETA"
    )

    print("=" * 80)

    print()

    print(
        f"WIN: "
        f"{win['result'].upper()}"
    )

    print(
        f"LOSS: "
        f"{loss['result'].upper()}"
    )

    print(
        f"AMBIGUOUS: "
        f"{ambiguous['result'].upper()}"
    )

    print(
        f"EXPIRED: "
        f"{expired['result'].upper()}"
    )

    print()

    print("=" * 80)

    print(
        "PRUEBA DE INTEGRACION EXITOSA"
    )

    print(
        "READY_TO_ENTER -> EXECUTION"
    )

    print(
        "WIN + LOSS + AMBIGUOUS + EXPIRED"
    )

    print("=" * 80)