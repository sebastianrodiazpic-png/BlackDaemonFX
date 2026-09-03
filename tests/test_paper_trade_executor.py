import pytest

from strategy.execution.paper_trade_executor import (
    PaperTradeExecutor,
)

from strategy.execution.trade_executor import (
    EXECUTION_STATUS_CLOSED,
    EXECUTION_STATUS_FILLED,
    TradeExecutionRequest,
)


SYMBOL = "Boom 100 Index"

ENTRY_TIME = (
    "2026-08-25 15:00:00+00:00"
)


# ============================================================
# HELPERS
# ============================================================

def create_buy_request():

    return TradeExecutionRequest(

        symbol=SYMBOL,

        timeframe="M5",

        direction="BUY",

        entry_time=ENTRY_TIME,

        entry_price=111.0,

        stop_loss=109.0,

        take_profit=115.0,

        volume=0.01,
    )


def create_sell_request():

    return TradeExecutionRequest(

        symbol=SYMBOL,

        timeframe="M5",

        direction="SELL",

        entry_time=ENTRY_TIME,

        entry_price=111.0,

        stop_loss=115.0,

        take_profit=107.0,

        volume=0.01,
    )


# ============================================================
# TEST 1
#
# PAPER BUY
# ============================================================

def test_paper_execute_buy():

    print()
    print("=" * 80)
    print("TEST 1")
    print("PAPER TRADE BUY")
    print("=" * 80)

    executor = PaperTradeExecutor()

    result = executor.execute_trade(

        create_buy_request()
    )

    assert result.accepted is True

    assert result.status == (
        EXECUTION_STATUS_FILLED
    )

    assert result.broker == "PAPER"

    assert result.direction == "BUY"

    assert result.filled_price == 111.0

    assert result.stop_loss == 109.0

    assert result.take_profit == 115.0

    assert result.position_ticket is not None

    assert result.duplicate is False

    assert result.is_filled() is True

    print()
    print("BUY EJECUTADO: OK")
    print(
        f"TICKET: {result.position_ticket}"
    )
    print(
        f"FILLED PRICE: {result.filled_price}"
    )
    print("STATUS: FILLED")


# ============================================================
# TEST 2
#
# PAPER SELL
# ============================================================

def test_paper_execute_sell():

    print()
    print("=" * 80)
    print("TEST 2")
    print("PAPER TRADE SELL")
    print("=" * 80)

    executor = PaperTradeExecutor()

    result = executor.execute_trade(

        create_sell_request()
    )

    assert result.accepted is True

    assert result.direction == "SELL"

    assert result.status == (
        EXECUTION_STATUS_FILLED
    )

    assert result.filled_price == 111.0

    assert result.stop_loss == 115.0

    assert result.take_profit == 107.0

    print()
    print("SELL EJECUTADO: OK")
    print(
        f"TICKET: {result.position_ticket}"
    )


# ============================================================
# TEST 3
#
# BUY CON NIVELES INVALIDOS
# ============================================================

def test_invalid_buy_levels():

    print()
    print("=" * 80)
    print("TEST 3")
    print("BUY CON SL/TP INVALIDO")
    print("=" * 80)

    executor = PaperTradeExecutor()

    request = TradeExecutionRequest(

        symbol=SYMBOL,

        timeframe="M5",

        direction="BUY",

        entry_time=ENTRY_TIME,

        entry_price=111.0,

        stop_loss=112.0,

        take_profit=115.0,

        volume=0.01,
    )

    with pytest.raises(
        ValueError,
        match="BUY inválido",
    ):

        executor.execute_trade(
            request
        )

    print()
    print("BUY INVALIDO: BLOQUEADO")
    print("VALIDACION: OK")


# ============================================================
# TEST 4
#
# SELL CON NIVELES INVALIDOS
# ============================================================

def test_invalid_sell_levels():

    print()
    print("=" * 80)
    print("TEST 4")
    print("SELL CON SL/TP INVALIDO")
    print("=" * 80)

    executor = PaperTradeExecutor()

    request = TradeExecutionRequest(

        symbol=SYMBOL,

        timeframe="M5",

        direction="SELL",

        entry_time=ENTRY_TIME,

        entry_price=111.0,

        stop_loss=109.0,

        take_profit=107.0,

        volume=0.01,
    )

    with pytest.raises(
        ValueError,
        match="SELL inválido",
    ):

        executor.execute_trade(
            request
        )

    print()
    print("SELL INVALIDO: BLOQUEADO")
    print("VALIDACION: OK")


# ============================================================
# TEST 5
#
# DIRECCION INVALIDA
# ============================================================

def test_invalid_direction():

    print()
    print("=" * 80)
    print("TEST 5")
    print("DIRECCION INVALIDA")
    print("=" * 80)

    executor = PaperTradeExecutor()

    request = TradeExecutionRequest(

        symbol=SYMBOL,

        timeframe="M5",

        direction="LONG",

        entry_time=ENTRY_TIME,

        entry_price=111.0,

        stop_loss=109.0,

        take_profit=115.0,

        volume=0.01,
    )

    with pytest.raises(
        ValueError,
        match="direction debe ser BUY o SELL",
    ):

        executor.execute_trade(
            request
        )

    print()
    print("DIRECCION INVALIDA: BLOQUEADA")
    print("VALIDACION: OK")


# ============================================================
# TEST 6
#
# VOLUMEN INVALIDO
# ============================================================

def test_invalid_volume():

    print()
    print("=" * 80)
    print("TEST 6")
    print("VOLUMEN INVALIDO")
    print("=" * 80)

    executor = PaperTradeExecutor()

    request = TradeExecutionRequest(

        symbol=SYMBOL,

        timeframe="M5",

        direction="BUY",

        entry_time=ENTRY_TIME,

        entry_price=111.0,

        stop_loss=109.0,

        take_profit=115.0,

        volume=0.0,
    )

    with pytest.raises(
        ValueError,
        match="volume debe ser mayor que cero",
    ):

        executor.execute_trade(
            request
        )

    print()
    print("VOLUMEN INVALIDO: BLOQUEADO")
    print("VALIDACION: OK")


# ============================================================
# TEST 7
#
# NO DUPLICAR EJECUCION
# ============================================================

def test_duplicate_execution_is_blocked():

    print()
    print("=" * 80)
    print("TEST 7")
    print("NO DUPLICAR EJECUCION")
    print("=" * 80)

    executor = PaperTradeExecutor()

    request = create_buy_request()

    first = executor.execute_trade(
        request
    )

    second = executor.execute_trade(
        request
    )

    assert first.duplicate is False

    assert second.duplicate is True

    assert (
        first.position_ticket
        ==
        second.position_ticket
    )

    assert len(
        executor.get_positions()
    ) == 1

    print()
    print(
        f"PRIMER TICKET: "
        f"{first.position_ticket}"
    )
    print(
        f"SEGUNDA EJECUCION: "
        f"DUPLICADA"
    )
    print("PROTECCION: OK")


# ============================================================
# TEST 8
#
# OBTENER POSICION
# ============================================================

def test_get_position():

    print()
    print("=" * 80)
    print("TEST 8")
    print("OBTENER POSICION")
    print("=" * 80)

    executor = PaperTradeExecutor()

    result = executor.execute_trade(

        create_buy_request()
    )

    position = executor.get_position(

        result.position_ticket
    )

    assert position is not None

    assert position["symbol"] == SYMBOL

    assert position["direction"] == "BUY"

    assert position["status"] == (
        EXECUTION_STATUS_FILLED
    )

    assert position["entry_price"] == 111.0

    print()
    print("POSICION ENCONTRADA: OK")
    print(
        f"STATUS: {position['status']}"
    )


# ============================================================
# TEST 9
#
# CERRAR POSICION
# ============================================================

def test_close_position():

    print()
    print("=" * 80)
    print("TEST 9")
    print("CERRAR POSICION PAPER")
    print("=" * 80)

    executor = PaperTradeExecutor()

    result = executor.execute_trade(

        create_buy_request()
    )

    position = executor.close_position(

        position_ticket=(
            result.position_ticket
        ),

        exit_price=113.0,

        reason="manual_close",
    )

    assert position["status"] == (
        EXECUTION_STATUS_CLOSED
    )

    assert position["exit_price"] == 113.0

    assert position["exit_reason"] == (
        "manual_close"
    )

    assert position["exit_time"] is not None

    print()
    print("POSICION CERRADA: OK")
    print(
        f"EXIT PRICE: "
        f"{position['exit_price']}"
    )


# ============================================================
# TEST 10
#
# NO CERRAR DOS VECES
# ============================================================

def test_cannot_close_position_twice():

    print()
    print("=" * 80)
    print("TEST 10")
    print("NO CERRAR DOS VECES")
    print("=" * 80)

    executor = PaperTradeExecutor()

    result = executor.execute_trade(

        create_buy_request()
    )

    executor.close_position(

        result.position_ticket,

        exit_price=113.0,
    )

    with pytest.raises(
        RuntimeError,
        match="ya está cerrada",
    ):

        executor.close_position(

            result.position_ticket
        )

    print()
    print(
        "SEGUNDO CIERRE: BLOQUEADO"
    )
    print("VALIDACION: OK")


# ============================================================
# TEST 11
#
# POSICION INEXISTENTE
# ============================================================

def test_unknown_position():

    print()
    print("=" * 80)
    print("TEST 11")
    print("POSICION DESCONOCIDA")
    print("=" * 80)

    executor = PaperTradeExecutor()

    position = executor.get_position(

        "PAPER-999999"
    )

    assert position is None

    with pytest.raises(
        ValueError,
        match="No existe la posición",
    ):

        executor.close_position(
            "PAPER-999999"
        )

    print()
    print(
        "POSICION DESCONOCIDA: "
        "BLOQUEADA"
    )
    print("VALIDACION: OK")