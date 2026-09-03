import pandas as pd
import pytest

from trade_lifecycle_manager import (
    TradeLifecycleManager,
    STATE_READY_TO_ENTER,
    STATE_EXECUTION,
    STATE_WIN,
    STATE_LOSS,
    STATE_AMBIGUOUS,
    STATE_EXPIRED,
)


# ============================================================
# DATOS BASE
# ============================================================

SYMBOL = "TEST_SYMBOL"

ENTRY_TIME = pd.Timestamp(
    "2026-08-25 15:00:00+00:00"
)

ENTRY_PRICE = 111.0

STOP_LOSS = 109.0

TAKE_PROFIT = 115.0


# ============================================================
# CREAR SIGNAL CONTROLADO
# ============================================================

def create_signal():

    return {

        "action": "MULTI_TIMEFRAME_SIGNAL",

        "symbol": SYMBOL,

        "m5_timeframe": "M5",

        "direction": "BUY",

        "entry_time": ENTRY_TIME,

        "entry_price": ENTRY_PRICE,

        "stop_loss": STOP_LOSS,

        "take_profit": TAKE_PROFIT,

        "risk_reward_ratio": 2.0,
    }


# ============================================================
# CREAR CANDLES CONTROLADAS
# ============================================================

def create_candles():

    times = pd.date_range(

        start="2026-08-25 14:50:00+00:00",

        periods=10,

        freq="5min",
    )

    return pd.DataFrame({

        "time": times,

        "open": [

            110.0,
            110.2,
            110.5,
            110.8,
            111.0,
            111.2,
            111.4,
            111.6,
            111.8,
            112.0,
        ],

        "high": [

            110.5,
            110.7,
            111.0,
            111.2,
            111.5,
            112.0,
            112.2,
            112.5,
            112.8,
            113.0,
        ],

        "low": [

            109.8,
            110.0,
            110.2,
            110.5,
            110.8,
            111.0,
            111.2,
            111.4,
            111.6,
            111.8,
        ],

        "close": [

            110.2,
            110.5,
            110.8,
            111.0,
            111.2,
            111.4,
            111.6,
            111.8,
            112.0,
            112.2,
        ],
    })


# ============================================================
# TRADE SIMULATOR CONTROLADO
# ============================================================

def create_controlled_simulator(
    simulation_result,
):

    def controlled_trade_simulator(
        df,
        trade,
        max_bars=500,
    ):

        return simulation_result

    return controlled_trade_simulator


# ============================================================
# CREAR RESULTADO WIN
# ============================================================

def create_win_result():

    return {

        "result": "win",

        "exit_time": pd.Timestamp(
            "2026-08-25 15:10:00+00:00"
        ),

        "exit_price": 115.0,

        "exit_reason": "take_profit",

        "bars_held": 2,

        "pnl_price": 4.0,
    }


# ============================================================
# CREAR RESULTADO LOSS
# ============================================================

def create_loss_result():

    return {

        "result": "loss",

        "exit_time": pd.Timestamp(
            "2026-08-25 15:10:00+00:00"
        ),

        "exit_price": 109.0,

        "exit_reason": "stop_loss",

        "bars_held": 2,

        "pnl_price": -2.0,
    }


# ============================================================
# CREAR RESULTADO AMBIGUOUS
# ============================================================

def create_ambiguous_result():

    return {

        "result": "ambiguous",

        "exit_time": pd.Timestamp(
            "2026-08-25 15:10:00+00:00"
        ),

        "exit_price": None,

        "exit_reason": "sl_and_tp_same_bar",

        "bars_held": 2,

        "pnl_price": 0.0,
    }


# ============================================================
# CREAR RESULTADO EXPIRED
# ============================================================

def create_expired_result():

    return {

        "result": "expired",

        "exit_time": pd.Timestamp(
            "2026-08-25 15:40:00+00:00"
        ),

        "exit_price": 113.0,

        "exit_reason": "max_bars_reached",

        "bars_held": 8,

        "pnl_price": 0.0,
    }


# ============================================================
# TEST 1
#
# CREAR READY_TO_ENTER
# ============================================================

def test_create_lifecycle_from_signal():

    print()

    print("=" * 80)

    print("TEST 1")
    print("CREAR TRADE LIFECYCLE DESDE SIGNAL")

    print("=" * 80)

    manager = TradeLifecycleManager(

        trade_simulator=lambda **kwargs: {}
    )

    signal = create_signal()

    lifecycle = manager.create_from_signal(
        signal=signal
    )

    assert lifecycle is not None

    assert lifecycle.state == STATE_READY_TO_ENTER

    assert lifecycle.symbol == SYMBOL

    assert lifecycle.timeframe == "M5"

    assert lifecycle.direction == "BUY"

    assert lifecycle.entry_time == ENTRY_TIME

    assert lifecycle.entry_price == ENTRY_PRICE

    assert lifecycle.stop_loss == STOP_LOSS

    assert lifecycle.take_profit == TAKE_PROFIT

    assert lifecycle.risk_reward_ratio == 2.0

    assert lifecycle.result is None

    assert lifecycle.exit_time is None

    assert lifecycle.exit_price is None

    assert lifecycle.exit_reason is None

    assert lifecycle.bars_held is None

    assert lifecycle.pnl_price == 0.0

    assert lifecycle.is_final() is False

    print()

    print("READY_TO_ENTER CREADO: OK")

    print(f"SYMBOL: {lifecycle.symbol}")

    print(f"TIMEFRAME: {lifecycle.timeframe}")

    print(f"DIRECTION: {lifecycle.direction}")

    print(f"ENTRY TIME: {lifecycle.entry_time}")

    print(f"ENTRY PRICE: {lifecycle.entry_price}")

    print(f"STOP LOSS: {lifecycle.stop_loss}")

    print(f"TAKE PROFIT: {lifecycle.take_profit}")


# ============================================================
# TEST 2
#
# READY_TO_ENTER -> EXECUTION -> WIN
# ============================================================

def test_lifecycle_win():

    print()

    print("=" * 80)

    print("TEST 2")
    print("READY_TO_ENTER -> EXECUTION -> WIN")

    print("=" * 80)

    simulation_result = create_win_result()

    simulator = create_controlled_simulator(
        simulation_result
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.create_from_signal(
        signal=create_signal()
    )

    assert lifecycle.state == STATE_READY_TO_ENTER

    result = manager.execute(

        lifecycle=lifecycle,

        candles=create_candles(),

        max_bars=500,
    )

    assert result is lifecycle

    assert lifecycle.state == STATE_WIN

    assert lifecycle.result == "win"

    assert lifecycle.exit_time == pd.Timestamp(
        "2026-08-25 15:10:00+00:00"
    )

    assert lifecycle.exit_price == 115.0

    assert lifecycle.exit_reason == "take_profit"

    assert lifecycle.bars_held == 2

    assert lifecycle.pnl_price == 4.0

    assert lifecycle.is_final() is True

    print()

    print("RESULTADO: WIN")

    print(f"STATE: {lifecycle.state}")

    print(f"EXIT TIME: {lifecycle.exit_time}")

    print(f"EXIT PRICE: {lifecycle.exit_price}")

    print(f"EXIT REASON: {lifecycle.exit_reason}")

    print(f"PNL PRICE: {lifecycle.pnl_price}")


# ============================================================
# TEST 3
#
# READY_TO_ENTER -> EXECUTION -> LOSS
# ============================================================

def test_lifecycle_loss():

    print()

    print("=" * 80)

    print("TEST 3")
    print("READY_TO_ENTER -> EXECUTION -> LOSS")

    print("=" * 80)

    simulation_result = create_loss_result()

    simulator = create_controlled_simulator(
        simulation_result
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.create_from_signal(
        signal=create_signal()
    )

    assert lifecycle.state == STATE_READY_TO_ENTER

    manager.execute(

        lifecycle=lifecycle,

        candles=create_candles(),

        max_bars=500,
    )

    assert lifecycle.state == STATE_LOSS

    assert lifecycle.result == "loss"

    assert lifecycle.exit_time == pd.Timestamp(
        "2026-08-25 15:10:00+00:00"
    )

    assert lifecycle.exit_price == 109.0

    assert lifecycle.exit_reason == "stop_loss"

    assert lifecycle.bars_held == 2

    assert lifecycle.pnl_price == -2.0

    assert lifecycle.is_final() is True

    print()

    print("RESULTADO: LOSS")

    print(f"STATE: {lifecycle.state}")

    print(f"EXIT PRICE: {lifecycle.exit_price}")

    print(f"EXIT REASON: {lifecycle.exit_reason}")

    print(f"PNL PRICE: {lifecycle.pnl_price}")


# ============================================================
# TEST 4
#
# READY_TO_ENTER -> EXECUTION -> AMBIGUOUS
# ============================================================

def test_lifecycle_ambiguous():

    print()

    print("=" * 80)

    print("TEST 4")
    print("READY_TO_ENTER -> EXECUTION -> AMBIGUOUS")

    print("=" * 80)

    simulation_result = create_ambiguous_result()

    simulator = create_controlled_simulator(
        simulation_result
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.create_from_signal(
        signal=create_signal()
    )

    manager.execute(

        lifecycle=lifecycle,

        candles=create_candles(),

        max_bars=500,
    )

    assert lifecycle.state == STATE_AMBIGUOUS

    assert lifecycle.result == "ambiguous"

    assert lifecycle.exit_time == pd.Timestamp(
        "2026-08-25 15:10:00+00:00"
    )

    assert lifecycle.exit_price is None

    assert lifecycle.exit_reason == (
        "sl_and_tp_same_bar"
    )

    assert lifecycle.bars_held == 2

    assert lifecycle.pnl_price == 0.0

    assert lifecycle.is_final() is True

    print()

    print("RESULTADO: AMBIGUOUS")

    print(f"STATE: {lifecycle.state}")

    print(f"EXIT PRICE: {lifecycle.exit_price}")

    print(f"EXIT REASON: {lifecycle.exit_reason}")


# ============================================================
# TEST 5
#
# READY_TO_ENTER -> EXECUTION -> EXPIRED
# ============================================================

def test_lifecycle_expired():

    print()

    print("=" * 80)

    print("TEST 5")
    print("READY_TO_ENTER -> EXECUTION -> EXPIRED")

    print("=" * 80)

    simulation_result = create_expired_result()

    simulator = create_controlled_simulator(
        simulation_result
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.create_from_signal(
        signal=create_signal()
    )

    manager.execute(

        lifecycle=lifecycle,

        candles=create_candles(),

        max_bars=500,
    )

    assert lifecycle.state == STATE_EXPIRED

    assert lifecycle.result == "expired"

    assert lifecycle.exit_time == pd.Timestamp(
        "2026-08-25 15:40:00+00:00"
    )

    assert lifecycle.exit_price == 113.0

    assert lifecycle.exit_reason == (
        "max_bars_reached"
    )

    assert lifecycle.bars_held == 8

    assert lifecycle.pnl_price == 0.0

    assert lifecycle.is_final() is True

    print()

    print("RESULTADO: EXPIRED")

    print(f"STATE: {lifecycle.state}")

    print(f"EXIT TIME: {lifecycle.exit_time}")

    print(f"EXIT PRICE: {lifecycle.exit_price}")

    print(f"EXIT REASON: {lifecycle.exit_reason}")


# ============================================================
# TEST 6
#
# PROCESS_SIGNAL
# ============================================================

def test_process_signal():

    print()

    print("=" * 80)

    print("TEST 6")
    print("PROCESS_SIGNAL COMPLETO")

    print("=" * 80)

    simulation_result = create_win_result()

    simulator = create_controlled_simulator(
        simulation_result
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.process_signal(

        signal=create_signal(),

        candles=create_candles(),

        max_bars=500,
    )

    assert lifecycle.state == STATE_WIN

    assert lifecycle.result == "win"

    assert len(manager.get_history()) == 1

    assert len(
        manager.get_completed_trades()
    ) == 1

    print()

    print("PROCESS_SIGNAL: OK")

    print(f"RESULT: {lifecycle.result}")

    print(f"FINAL STATE: {lifecycle.state}")


# ============================================================
# TEST 7
#
# HISTORIAL
# ============================================================

def test_manager_history():

    print()

    print("=" * 80)

    print("TEST 7")
    print("GESTION DE HISTORIAL")

    print("=" * 80)

    simulator = create_controlled_simulator(
        create_win_result()
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle_1 = manager.process_signal(

        signal=create_signal(),

        candles=create_candles(),
    )

    lifecycle_2 = manager.process_signal(

        signal=create_signal(),

        candles=create_candles(),
    )

    history = manager.get_history()

    completed = manager.get_completed_trades()

    assert len(history) == 2

    assert history[0] is lifecycle_1

    assert history[1] is lifecycle_2

    assert len(completed) == 2

    assert all(
        lifecycle.is_final()
        for lifecycle in completed
    )

    manager.clear_history()

    assert len(manager.get_history()) == 0

    assert len(
        manager.get_completed_trades()
    ) == 0

    print()

    print("HISTORIAL ANTES DE LIMPIAR: 2")

    print("HISTORIAL DESPUES DE LIMPIAR: 0")

    print("CLEAR_HISTORY: OK")


# ============================================================
# TEST 8
#
# NO EJECUTAR DOS VECES UN TRADE FINALIZADO
# ============================================================

def test_cannot_execute_final_lifecycle_twice():

    print()

    print("=" * 80)

    print("TEST 8")
    print("NO EJECUTAR TRADE FINALIZADO DOS VECES")

    print("=" * 80)

    simulator = create_controlled_simulator(
        create_win_result()
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.process_signal(

        signal=create_signal(),

        candles=create_candles(),
    )

    assert lifecycle.state == STATE_WIN

    with pytest.raises(
        RuntimeError,
        match="ya está finalizado",
    ):

        manager.execute(

            lifecycle=lifecycle,

            candles=create_candles(),
        )

    print()

    print("PRIMERA EJECUCION: WIN")

    print("SEGUNDA EJECUCION: BLOQUEADA")

    print("PROTECCION: OK")


# ============================================================
# TEST 9
#
# RESULTADO DESCONOCIDO
# ============================================================

def test_unknown_simulation_result():

    print()

    print("=" * 80)

    print("TEST 9")
    print("RESULTADO DESCONOCIDO DEL SIMULADOR")

    print("=" * 80)

    simulation_result = {

        "result": "unknown_result",

        "exit_time": None,

        "exit_price": None,

        "exit_reason": None,

        "bars_held": 0,

        "pnl_price": 0.0,
    }

    simulator = create_controlled_simulator(
        simulation_result
    )

    manager = TradeLifecycleManager(
        trade_simulator=simulator
    )

    lifecycle = manager.create_from_signal(
        signal=create_signal()
    )

    with pytest.raises(
        ValueError,
        match="Resultado desconocido",
    ):

        manager.execute(

            lifecycle=lifecycle,

            candles=create_candles(),
        )

    print()

    print("RESULTADO DESCONOCIDO: BLOQUEADO")

    print("VALIDACION: OK")


# ============================================================
# TEST 10
#
# SIGNAL INVALIDO
# ============================================================

def test_invalid_signal():

    print()

    print("=" * 80)

    print("TEST 10")
    print("VALIDACION DE SIGNAL INVALIDO")

    print("=" * 80)

    manager = TradeLifecycleManager(

        trade_simulator=lambda **kwargs: {}
    )

    invalid_signal = {

        "symbol": SYMBOL,

        "direction": "BUY",

        "entry_time": ENTRY_TIME,
    }

    with pytest.raises(
        ValueError,
        match="Faltan campos requeridos",
    ):

        manager.create_from_signal(
            signal=invalid_signal
        )

    print()

    print("SIGNAL INCOMPLETO: BLOQUEADO")

    print("VALIDACION: OK")