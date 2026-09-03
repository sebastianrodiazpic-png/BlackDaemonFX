import pytest

from position_manager import (
    PositionManager,
    POSITION_OPEN,
    POSITION_CLOSED,
)


def create_buy_position():

    return {
        "ticket": "PAPER-000001",
        "symbol": "Boom 100 Index",
        "direction": "BUY",
        "volume": 0.01,
        "filled_price": 111.0,
        "stop_loss": 109.0,
        "take_profit": 115.0,
        "status": "FILLED",
    }


def create_sell_position():

    return {
        "ticket": "PAPER-000002",
        "symbol": "Boom 100 Index",
        "direction": "SELL",
        "volume": 0.01,
        "filled_price": 111.0,
        "stop_loss": 113.0,
        "take_profit": 107.0,
        "status": "FILLED",
    }


# ============================================================
# TEST 1
# REGISTRAR POSICIÓN
# ============================================================

def test_register_position():

    print()
    print("=" * 80)
    print("TEST 1")
    print("REGISTRAR POSICION")
    print("=" * 80)

    manager = PositionManager()

    position = manager.register_position(
        create_buy_position()
    )

    assert position["ticket"] == (
        "PAPER-000001"
    )

    assert position["status"] == (
        POSITION_OPEN
    )

    assert manager.open_positions_count() == 1

    print()
    print("POSICION REGISTRADA: OK")
    print(f"TICKET: {position['ticket']}")
    print(f"STATUS: {position['status']}")
    print("PASSED")


# ============================================================
# TEST 2
# NO DUPLICAR POSICIÓN
# ============================================================

def test_duplicate_position_is_blocked():

    print()
    print("=" * 80)
    print("TEST 2")
    print("NO DUPLICAR POSICION")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    with pytest.raises(ValueError):

        manager.register_position(
            create_buy_position()
        )

    print()
    print("POSICION DUPLICADA: BLOQUEADA")
    print("VALIDACION: OK")
    print("PASSED")


# ============================================================
# TEST 3
# OBTENER POSICIÓN
# ============================================================

def test_get_position():

    print()
    print("=" * 80)
    print("TEST 3")
    print("OBTENER POSICION")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    position = manager.get_position(
        "PAPER-000001"
    )

    assert position is not None

    assert position["ticket"] == (
        "PAPER-000001"
    )

    print()
    print("POSICION ENCONTRADA: OK")
    print(f"TICKET: {position['ticket']}")
    print("PASSED")


# ============================================================
# TEST 4
# LISTAR POSICIONES ABIERTAS
# ============================================================

def test_get_open_positions():

    print()
    print("=" * 80)
    print("TEST 4")
    print("LISTAR POSICIONES ABIERTAS")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.register_position(
        create_sell_position()
    )

    positions = manager.get_open_positions()

    assert len(positions) == 2

    assert manager.open_positions_count() == 2

    print()
    print(
        f"POSICIONES ABIERTAS: {len(positions)}"
    )
    print("PASSED")


# ============================================================
# TEST 5
# ACTUALIZAR PRECIO BUY
# ============================================================

def test_update_price_buy():

    print()
    print("=" * 80)
    print("TEST 5")
    print("ACTUALIZAR PRECIO BUY")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    position = manager.update_price(
        ticket="PAPER-000001",
        current_price=113.0,
    )

    assert position["current_price"] == 113.0

    assert position["floating_pnl_price"] == 2.0

    print()
    print("PRECIO ACTUALIZADO: OK")
    print(
        f"CURRENT PRICE: "
        f"{position['current_price']}"
    )
    print(
        f"FLOATING PNL: "
        f"{position['floating_pnl_price']}"
    )
    print("PASSED")


# ============================================================
# TEST 6
# ACTUALIZAR PRECIO SELL
# ============================================================

def test_update_price_sell():

    print()
    print("=" * 80)
    print("TEST 6")
    print("ACTUALIZAR PRECIO SELL")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_sell_position()
    )

    position = manager.update_price(
        ticket="PAPER-000002",
        current_price=109.0,
    )

    assert position["current_price"] == 109.0

    assert position["floating_pnl_price"] == 2.0

    print()
    print("PRECIO ACTUALIZADO: OK")
    print(
        f"FLOATING PNL: "
        f"{position['floating_pnl_price']}"
    )
    print("PASSED")


# ============================================================
# TEST 7
# CERRAR POSICIÓN BUY
# ============================================================

def test_close_buy_position():

    print()
    print("=" * 80)
    print("TEST 7")
    print("CERRAR POSICION BUY")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    position = manager.close_position(
        ticket="PAPER-000001",
        exit_price=115.0,
        exit_reason="take_profit",
    )

    assert position["status"] == (
        POSITION_CLOSED
    )

    assert position["exit_price"] == 115.0

    assert position["realized_pnl_price"] == 4.0

    assert manager.open_positions_count() == 0

    assert manager.closed_positions_count() == 1

    print()
    print("POSICION CERRADA: OK")
    print(
        f"REALIZED PNL: "
        f"{position['realized_pnl_price']}"
    )
    print("PASSED")


# ============================================================
# TEST 8
# CERRAR POSICIÓN SELL
# ============================================================

def test_close_sell_position():

    print()
    print("=" * 80)
    print("TEST 8")
    print("CERRAR POSICION SELL")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_sell_position()
    )

    position = manager.close_position(
        ticket="PAPER-000002",
        exit_price=107.0,
        exit_reason="take_profit",
    )

    assert position["status"] == (
        POSITION_CLOSED
    )

    assert position["realized_pnl_price"] == 4.0

    print()
    print("POSICION SELL CERRADA: OK")
    print(
        f"REALIZED PNL: "
        f"{position['realized_pnl_price']}"
    )
    print("PASSED")


# ============================================================
# TEST 9
# NO CERRAR DOS VECES
# ============================================================

def test_cannot_close_position_twice():

    print()
    print("=" * 80)
    print("TEST 9")
    print("NO CERRAR DOS VECES")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.close_position(
        ticket="PAPER-000001",
        exit_price=115.0,
    )

    with pytest.raises(ValueError):

        manager.close_position(
            ticket="PAPER-000001",
            exit_price=115.0,
        )

    print()
    print("SEGUNDO CIERRE: BLOQUEADO")
    print("VALIDACION: OK")
    print("PASSED")


# ============================================================
# TEST 10
# POSICIÓN DESCONOCIDA
# ============================================================

def test_unknown_position():

    print()
    print("=" * 80)
    print("TEST 10")
    print("POSICION DESCONOCIDA")
    print("=" * 80)

    manager = PositionManager()

    position = manager.get_position(
        "UNKNOWN"
    )

    assert position is None

    print()
    print("POSICION DESCONOCIDA: OK")
    print("PASSED")


# ============================================================
# TEST 11
# HISTORIAL CERRADO
# ============================================================

def test_closed_positions_history():

    print()
    print("=" * 80)
    print("TEST 11")
    print("HISTORIAL DE POSICIONES CERRADAS")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.close_position(
        ticket="PAPER-000001",
        exit_price=115.0,
    )

    closed = manager.get_closed_positions()

    assert len(closed) == 1

    assert closed[0]["status"] == (
        POSITION_CLOSED
    )

    print()
    print(
        f"POSICIONES CERRADAS: "
        f"{len(closed)}"
    )
    print("PASSED")


# ============================================================
# TEST 12
# LIMPIAR HISTORIAL
# ============================================================

def test_clear_closed_positions():

    print()
    print("=" * 80)
    print("TEST 12")
    print("LIMPIAR HISTORIAL")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.close_position(
        ticket="PAPER-000001",
        exit_price=115.0,
    )

    assert manager.closed_positions_count() == 1

    manager.clear_closed_positions()

    assert manager.closed_positions_count() == 0

    print()
    print("HISTORIAL LIMPIADO: OK")
    print("PASSED")


# ============================================================
# TEST 13
# LIMPIAR TODO
# ============================================================

def test_clear_all():

    print()
    print("=" * 80)
    print("TEST 13")
    print("LIMPIAR TODAS LAS POSICIONES")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.register_position(
        create_sell_position()
    )

    manager.close_position(
        ticket="PAPER-000001",
        exit_price=115.0,
    )

    manager.clear_all()

    assert manager.open_positions_count() == 0

    assert manager.closed_positions_count() == 0

    print()
    print("TODAS LAS POSICIONES LIMPIADAS: OK")
    print("PASSED")

# ============================================================
# TEST 14
# BREAK EVEN BUY AL ALCANZAR 1:1
# ============================================================

def test_apply_break_even_buy_at_one_to_one():

    print()
    print("=" * 80)
    print("TEST 14")
    print("BREAK EVEN BUY AL ALCANZAR 1:1")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.update_price(
        ticket="PAPER-000001",
        current_price=113.0,
    )

    position = manager.apply_break_even(
        ticket="PAPER-000001",
        trigger_rr=1.0,
    )

    assert position["initial_stop_loss"] == 109.0
    assert position["break_even_trigger_price"] == 113.0
    assert position["break_even_activated"] is True
    assert position["break_even_price"] == 111.0
    assert position["stop_loss"] == 111.0

    print()
    print("BREAK EVEN BUY: OK")
    print(f"TRIGGER PRICE: {position['break_even_trigger_price']}")
    print(f"STOP LOSS NUEVO: {position['stop_loss']}")
    print("PASSED")


# ============================================================
# TEST 15
# BREAK EVEN SELL AL ALCANZAR 1:1
# ============================================================

def test_apply_break_even_sell_at_one_to_one():

    print()
    print("=" * 80)
    print("TEST 15")
    print("BREAK EVEN SELL AL ALCANZAR 1:1")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_sell_position()
    )

    manager.update_price(
        ticket="PAPER-000002",
        current_price=109.0,
    )

    position = manager.apply_break_even(
        ticket="PAPER-000002",
        trigger_rr=1.0,
    )

    assert position["initial_stop_loss"] == 113.0
    assert position["break_even_trigger_price"] == 109.0
    assert position["break_even_activated"] is True
    assert position["break_even_price"] == 111.0
    assert position["stop_loss"] == 111.0

    print()
    print("BREAK EVEN SELL: OK")
    print(f"TRIGGER PRICE: {position['break_even_trigger_price']}")
    print(f"STOP LOSS NUEVO: {position['stop_loss']}")
    print("PASSED")


# ============================================================
# TEST 16
# NO ACTIVAR BREAK EVEN ANTES DE 1:1
# ============================================================

def test_break_even_is_not_activated_before_one_to_one():

    print()
    print("=" * 80)
    print("TEST 16")
    print("NO ACTIVAR BREAK EVEN ANTES DE 1:1")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.update_price(
        ticket="PAPER-000001",
        current_price=112.9,
    )

    position = manager.apply_break_even(
        ticket="PAPER-000001",
        trigger_rr=1.0,
    )

    assert position["break_even_trigger_price"] == 113.0
    assert position["break_even_activated"] is False
    assert position["break_even_price"] is None
    assert position["stop_loss"] == 109.0

    print()
    print("BREAK EVEN ANTES DE 1:1: BLOQUEADO")
    print(f"STOP LOSS SE MANTIENE: {position['stop_loss']}")
    print("PASSED")


# ============================================================
# TEST 17
# BREAK EVEN ES IDEMPOTENTE
# ============================================================

def test_break_even_cannot_be_applied_twice():

    print()
    print("=" * 80)
    print("TEST 17")
    print("BREAK EVEN NO SE APLICA DOS VECES")
    print("=" * 80)

    manager = PositionManager()

    manager.register_position(
        create_buy_position()
    )

    manager.update_price(
        ticket="PAPER-000001",
        current_price=114.0,
    )

    first = manager.apply_break_even(
        ticket="PAPER-000001",
        trigger_rr=1.0,
    )

    second = manager.apply_break_even(
        ticket="PAPER-000001",
        trigger_rr=1.0,
    )

    assert first["break_even_activated"] is True
    assert first["stop_loss"] == 111.0
    assert second["break_even_activated"] is True
    assert second["stop_loss"] == 111.0
    assert manager.get_position(
        "PAPER-000001"
    )["initial_stop_loss"] == 109.0

    print()
    print("PRIMER BREAK EVEN: OK")
    print("SEGUNDO BREAK EVEN: SIN CAMBIOS")
    print("VALIDACION: OK")
    print("PASSED")
