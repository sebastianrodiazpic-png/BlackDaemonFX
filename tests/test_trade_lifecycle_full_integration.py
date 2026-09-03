import pandas as pd
import pytest

from strategy.execution.multi_timeframe import (
    MultiTimeframeAnalyzer,
    MultiTimeframeConfig,
)
from strategy.smc.trade_simulator import simulate_trade
from trade_lifecycle_manager import (
    TradeLifecycleManager,
    STATE_WIN,
    STATE_LOSS,
    STATE_AMBIGUOUS,
    STATE_EXPIRED,
)


SYMBOL = "Boom 100 Index"

ENTRY_TIME = pd.Timestamp(
    "2026-08-25 15:00:00+00:00"
)

ENTRY_PRICE = 111.0
STOP_LOSS = 109.0
TAKE_PROFIT = 115.0


# ============================================================
# PROVEEDOR CONTROLADO
#
# Entrega datos reales de velas al MultiTimeframeAnalyzer y
# después permite recuperar el histórico completo M5 para que
# TradeLifecycleManager lo entregue al trade_simulator real.
# ============================================================

class ControlledDataProvider:

    def __init__(self, scenario):

        self.scenario = scenario

    def get_candles(self, symbol, timeframe, count):

        if symbol != SYMBOL:
            raise ValueError(
                f"Símbolo inesperado: {symbol}"
            )

        if timeframe == "H1":
            return self._h1().head(count).reset_index(
                drop=True
            )

        if timeframe == "M15":
            return self._m15().head(count).reset_index(
                drop=True
            )

        if timeframe == "M5":
            return self._m5().head(count).reset_index(
                drop=True
            )

        raise ValueError(
            f"Timeframe no soportado: {timeframe}"
        )

    @staticmethod
    def _h1():

        times = pd.date_range(
            "2026-08-24 00:00:00+00:00",
            periods=10,
            freq="1h",
        )

        return pd.DataFrame({
            "time": times,
            "open": [
                100, 101, 102, 103, 104,
                105, 106, 107, 108, 109,
            ],
            "high": [
                102, 103, 104, 105, 106,
                107, 108, 109, 110, 111,
            ],
            "low": [
                99, 100, 101, 102, 103,
                104, 105, 106, 107, 108,
            ],
            "close": [
                101, 102, 103, 104, 105,
                106, 107, 108, 109, 110,
            ],
            "test_timeframe": "H1",
            "bos_bullish": [
                False, False, False, False, False,
                False, False, False, True, True,
            ],
            "choch_bullish": [
                False, False, False, False, False,
                False, False, False, False, False,
            ],
            "bos_bearish": [
                False, False, False, False, False,
                False, False, False, False, False,
            ],
            "choch_bearish": [
                False, False, False, False, False,
                False, False, False, False, False,
            ],
        })

    @staticmethod
    def _m15():

        times = pd.date_range(
            "2026-08-25 12:00:00+00:00",
            periods=20,
            freq="15min",
        )

        return pd.DataFrame({
            "time": times,
            "open": [
                100, 101, 102, 103, 104,
                105, 106, 107, 108, 109,
                110, 109, 110, 111, 110,
                111, 112, 111, 112, 113,
            ],
            "high": [
                102, 103, 104, 105, 106,
                107, 108, 109, 110, 111,
                112, 112, 113, 114, 113,
                114, 115, 114, 115, 116,
            ],
            "low": [
                99, 100, 101, 102, 103,
                104, 105, 106, 107, 108,
                108, 107, 108, 109, 108,
                109, 110, 109, 110, 111,
            ],
            "close": [
                101, 102, 103, 104, 105,
                106, 107, 108, 109, 110,
                109, 111, 112, 110, 112,
                113, 111, 113, 114, 115,
            ],
            "test_timeframe": "M15",
        })

    def _m5(self):

        times = pd.date_range(
            "2026-08-25 14:30:00+00:00",
            periods=15,
            freq="5min",
        )

        df = pd.DataFrame({
            "time": times,
            "open": [
                106.0, 107.0, 108.0, 109.0, 110.0,
                110.0, 111.0, 111.2, 111.5, 111.7,
                112.0, 112.2, 112.4, 112.6, 112.8,
            ],
            "high": [
                108.0, 109.0, 110.0, 111.0, 112.0,
                112.0, 113.0, 113.0, 114.0, 114.0,
                114.0, 114.0, 114.0, 114.0, 114.0,
            ],
            "low": [
                105.0, 106.0, 107.0, 108.0, 109.0,
                110.0, 110.0, 110.0, 110.0, 110.0,
                110.0, 110.0, 110.0, 110.0, 110.0,
            ],
            "close": [
                107.0, 108.0, 109.0, 110.0, 111.0,
                111.0, 112.0, 111.5, 112.0, 112.2,
                112.4, 112.6, 112.8, 113.0, 113.0,
            ],
            "test_timeframe": "M5",
        })

        # La entrada es 15:00. Las velas posteriores empiezan
        # en 15:05 y la segunda vela posterior es 15:10.

        if self.scenario == "win":

            df.loc[8, "high"] = 115.0
            df.loc[8, "low"] = 110.0
            df.loc[8, "close"] = 115.0

        elif self.scenario == "loss":

            df.loc[8, "high"] = 114.0
            df.loc[8, "low"] = 109.0
            df.loc[8, "close"] = 109.0

        elif self.scenario == "ambiguous":

            df.loc[8, "high"] = 115.0
            df.loc[8, "low"] = 109.0
            df.loc[8, "close"] = 112.0

        elif self.scenario == "expired":

            pass

        else:
            raise ValueError(
                f"Escenario no soportado: {self.scenario}"
            )

        return df


# ============================================================
# ANALIZADOR CONTROLADO
#
# Utiliza la lógica real de MultiTimeframeAnalyzer. Solo se
# controlan las salidas del pipeline para hacer la prueba
# determinista y concentrada en la integración del ciclo real.
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

        timeframe = df["test_timeframe"].iloc[0]

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

        if timeframe == "M5":

            confirmations = pd.DataFrame([
                {
                    "valid": True,
                    "direction": "BUY",
                    "entry_time": ENTRY_TIME,
                    "entry_price": ENTRY_PRICE,
                    "stop_loss": STOP_LOSS,
                    "take_profit": TAKE_PROFIT,
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
# CONFIGURACIÓN COMÚN
# ============================================================

def create_config():

    return MultiTimeframeConfig(
        structure_timeframe="H1",
        confirmation_timeframe="M15",
        entry_timeframe="M5",

        structure_candles=10,
        confirmation_candles=20,
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
# PRUEBA COMPLETA
#
# MultiTimeframeAnalyzer
#       ->
# MULTI_TIMEFRAME_SIGNAL / READY_TO_ENTER
#       ->
# TradeLifecycleManager
#       ->
# EXECUTION
#       ->
# trade_simulator REAL
#       ->
# WIN / LOSS / AMBIGUOUS / EXPIRED
# ============================================================

@pytest.mark.parametrize(
    (
        "scenario",
        "expected_state",
        "expected_result",
        "expected_exit_time",
        "expected_exit_price",
        "expected_exit_reason",
        "expected_bars_held",
        "expected_pnl_price",
    ),
    [
        (
            "win",
            STATE_WIN,
            "win",
            pd.Timestamp("2026-08-25 15:10:00+00:00"),
            115.0,
            "take_profit",
            2,
            4.0,
        ),
        (
            "loss",
            STATE_LOSS,
            "loss",
            pd.Timestamp("2026-08-25 15:10:00+00:00"),
            109.0,
            "stop_loss",
            2,
            -2.0,
        ),
        (
            "ambiguous",
            STATE_AMBIGUOUS,
            "ambiguous",
            pd.Timestamp("2026-08-25 15:10:00+00:00"),
            None,
            "sl_and_tp_same_bar",
            2,
            0.0,
        ),
        (
            "expired",
            STATE_EXPIRED,
            "expired",
            pd.Timestamp("2026-08-25 15:40:00+00:00"),
            113.0,
            "max_bars_reached",
            8,
            0.0,
        ),
    ],
)
def test_trade_lifecycle_full_integration(
    scenario,
    expected_state,
    expected_result,
    expected_exit_time,
    expected_exit_price,
    expected_exit_reason,
    expected_bars_held,
    expected_pnl_price,
):

    print()
    print("=" * 80)
    print("INTEGRACIÓN COMPLETA DEL CICLO DE VIDA")
    print(
        "MULTI_TIMEFRAME_ANALYZER -> "
        "TRADE_LIFECYCLE_MANAGER -> "
        "TRADE_SIMULATOR"
    )
    print("=" * 80)
    print(f"ESCENARIO: {scenario.upper()}")

    # ========================================================
    # 1. MULTI TIMEFRAME ANALYZER REAL
    # ========================================================

    provider = ControlledDataProvider(
        scenario=scenario
    )

    analyzer = ControlledMultiTimeframeAnalyzer(
        data_provider=provider,
        config=create_config(),
    )

    signal = analyzer.analyze_symbol(
        SYMBOL
    )

    assert signal is not None
    assert signal["valid"] is True
    assert signal["action"] == (
        "MULTI_TIMEFRAME_SIGNAL"
    )
    assert signal["state"] == "READY_TO_ENTER"

    assert signal["symbol"] == SYMBOL
    assert signal["direction"] == "BUY"
    assert signal["m5_timeframe"] == "M5"
    assert signal["entry_time"] == ENTRY_TIME
    assert signal["entry_price"] == ENTRY_PRICE
    assert signal["stop_loss"] == STOP_LOSS
    assert signal["take_profit"] == TAKE_PROFIT
    assert signal["risk_reward_ratio"] == 2.0

    print()
    print("1. MULTI_TIMEFRAME_ANALYZER: OK")
    print(
        f"SIGNAL STATE: {signal['state']}"
    )
    print(
        f"DIRECTION: {signal['direction']}"
    )
    print(
        f"ENTRY TIME: {signal['entry_time']}"
    )
    print(
        f"ENTRY PRICE: {signal['entry_price']}"
    )
    print(
        f"STOP LOSS: {signal['stop_loss']}"
    )
    print(
        f"TAKE PROFIT: {signal['take_profit']}"
    )

    # ========================================================
    # 2. RECUPERAR VELAS REALES DE EJECUCIÓN
    # ========================================================

    execution_candles = provider.get_candles(
        symbol=SYMBOL,
        timeframe=signal["m5_timeframe"],
        count=100,
    )

    assert execution_candles is not None
    assert not execution_candles.empty

    entry_time = pd.to_datetime(
        signal["entry_time"],
        utc=True,
    )

    future_candles = execution_candles[
        pd.to_datetime(
            execution_candles["time"],
            utc=True,
        ) > entry_time
    ].copy()

    assert len(future_candles) == 8

    print()
    print("2. VELAS DE EJECUCIÓN: OK")
    print(
        f"TIMEFRAME: {signal['m5_timeframe']}"
    )
    print(
        f"TOTAL CANDLES: "
        f"{len(execution_candles)}"
    )
    print(
        f"FUTURE CANDLES: "
        f"{len(future_candles)}"
    )

    # ========================================================
    # 3. TRADE LIFECYCLE MANAGER REAL
    #
    # Se inyecta el trade_simulator REAL del proyecto.
    # ========================================================

    manager = TradeLifecycleManager(
        trade_simulator=simulate_trade
    )

    lifecycle = manager.process_signal(
        signal=signal,
        candles=execution_candles,
        max_bars=500,
    )

    # ========================================================
    # 4. VALIDAR RESULTADO FINAL
    # ========================================================

    assert lifecycle is not None

    assert lifecycle.state == expected_state
    assert lifecycle.result == expected_result

    assert lifecycle.symbol == SYMBOL
    assert lifecycle.timeframe == "M5"
    assert lifecycle.direction == "BUY"

    assert lifecycle.entry_time == ENTRY_TIME
    assert lifecycle.entry_price == ENTRY_PRICE
    assert lifecycle.stop_loss == STOP_LOSS
    assert lifecycle.take_profit == TAKE_PROFIT
    assert lifecycle.risk_reward_ratio == 2.0

    assert lifecycle.exit_time == expected_exit_time
    assert lifecycle.exit_price == expected_exit_price
    assert lifecycle.exit_reason == (
        expected_exit_reason
    )
    assert lifecycle.bars_held == expected_bars_held
    assert lifecycle.pnl_price == expected_pnl_price

    assert lifecycle.is_final() is True

    # ========================================================
    # 5. VALIDAR HISTORIAL DEL MANAGER
    # ========================================================

    history = manager.get_history()

    assert len(history) == 1
    assert history[0] is lifecycle

    completed = manager.get_completed_trades()

    assert len(completed) == 1
    assert completed[0] is lifecycle

    print()
    print("3. TRADE_LIFECYCLE_MANAGER: OK")
    print(
        f"FINAL STATE: {lifecycle.state}"
    )
    print(
        f"SIMULATION RESULT: {lifecycle.result}"
    )
    print(
        f"EXIT TIME: {lifecycle.exit_time}"
    )
    print(
        f"EXIT PRICE: {lifecycle.exit_price}"
    )
    print(
        f"EXIT REASON: {lifecycle.exit_reason}"
    )
    print(
        f"BARS HELD: {lifecycle.bars_held}"
    )
    print(
        f"PNL PRICE: {lifecycle.pnl_price}"
    )

    print()
    print("4. HISTORIAL DEL LIFECYCLE: OK")
    print(
        f"COMPLETED TRADES: {len(completed)}"
    )

    print()
    print("INTEGRACIÓN EXITOSA")
    print(
        "READY_TO_ENTER -> EXECUTION -> "
        f"{expected_state}"
    )