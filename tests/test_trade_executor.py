import pytest

from strategy.execution.trade_executor import (
    TradeExecutionRequest,
    TradeExecutor,
)


# ============================================================
# TEST 1
#
# TRADE EXECUTOR ES ABSTRACTO
# ============================================================

def test_trade_executor_is_abstract():

    print()
    print("=" * 80)
    print("TEST 1")
    print("TRADE EXECUTOR ABSTRACTO")
    print("=" * 80)

    with pytest.raises(TypeError):

        TradeExecutor()

    print()
    print("TRADE EXECUTOR: ABSTRACTO")
    print("VALIDACION: OK")


# ============================================================
# TEST 2
#
# CREAR REQUEST DESDE SIGNAL
# ============================================================

def test_execution_request_from_signal():

    print()
    print("=" * 80)
    print("TEST 2")
    print("CREAR EXECUTION REQUEST")
    print("=" * 80)

    signal = {

        "symbol": "Boom 100 Index",

        "m5_timeframe": "M5",

        "direction": "BUY",

        "entry_time": (
            "2026-08-25 15:00:00+00:00"
        ),

        "entry_price": 111.0,

        "stop_loss": 109.0,

        "take_profit": 115.0,
    }

    request = (
        TradeExecutionRequest.from_signal(
            signal=signal,
            volume=0.01,
        )
    )

    assert request.symbol == (
        "Boom 100 Index"
    )

    assert request.timeframe == "M5"

    assert request.direction == "BUY"

    assert request.entry_price == 111.0

    assert request.stop_loss == 109.0

    assert request.take_profit == 115.0

    assert request.volume == 0.01

    print()
    print("REQUEST CREADO: OK")
    print(
        f"SYMBOL: {request.symbol}"
    )
    print(
        f"DIRECTION: {request.direction}"
    )
    print(
        f"VOLUME: {request.volume}"
    )


# ============================================================
# TEST 3
#
# SIGNAL INCOMPLETO
# ============================================================

def test_execution_request_invalid_signal():

    print()
    print("=" * 80)
    print("TEST 3")
    print("SIGNAL INCOMPLETO")
    print("=" * 80)

    signal = {

        "symbol": "Boom 100 Index",

        "direction": "BUY",

        "entry_time": (
            "2026-08-25 15:00:00+00:00"
        ),
    }

    with pytest.raises(
        ValueError,
        match="Faltan campos requeridos",
    ):

        TradeExecutionRequest.from_signal(
            signal=signal
        )

    print()
    print("SIGNAL INCOMPLETO: BLOQUEADO")
    print("VALIDACION: OK")