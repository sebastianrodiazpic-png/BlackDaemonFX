import pytest

from monitoring.position_monitoring_service import (
    MONITOR_ACTION_BREAK_EVEN_ACTIVATED,
    MONITOR_ACTION_BREAK_EVEN_STOP,
    MONITOR_ACTION_PRICE_UPDATED,
    MONITOR_ACTION_STOP_LOSS,
    MONITOR_ACTION_TAKE_PROFIT,
    PositionMonitoringService,
)
from position_manager import (
    POSITION_CLOSED,
    POSITION_OPEN,
    PositionManager,
)


def create_buy_position(ticket="PAPER-000001"):
    return {
        "ticket": ticket,
        "symbol": "Boom 100 Index",
        "direction": "BUY",
        "volume": 0.01,
        "filled_price": 111.0,
        "stop_loss": 109.0,
        "take_profit": 115.0,
        "status": "FILLED",
    }


def create_sell_position(ticket="PAPER-000002"):
    return {
        "ticket": ticket,
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
# ACTUALIZAR POSICION SIN BREAK EVEN
# ============================================================

def test_monitor_buy_updates_price_without_break_even():
    print()
    print("=" * 80)
    print("TEST 1")
    print("MONITOREAR BUY SIN BREAK EVEN")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_buy_position())
    service = PositionMonitoringService(manager)

    result = service.monitor_position(
        ticket="PAPER-000001",
        current_price=112.0,
    )

    assert result["closed"] is False
    assert result["action"] == MONITOR_ACTION_PRICE_UPDATED
    assert result["position"]["status"] == POSITION_OPEN
    assert result["position"]["current_price"] == 112.0
    assert result["position"]["floating_pnl_price"] == 1.0
    assert result["position"]["break_even_activated"] is False

    print("PRECIO ACTUALIZADO: OK")
    print("BREAK EVEN: NO ACTIVADO")
    print("PASSED")


# ============================================================
# TEST 2
# BREAK EVEN BUY EN 1:1
# ============================================================

def test_monitor_buy_activates_break_even_at_one_to_one():
    print()
    print("=" * 80)
    print("TEST 2")
    print("MONITOREAR BUY Y ACTIVAR BREAK EVEN 1:1")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_buy_position())
    service = PositionMonitoringService(manager)

    result = service.monitor_position(
        ticket="PAPER-000001",
        current_price=113.0,
    )

    assert result["closed"] is False
    assert result["action"] == MONITOR_ACTION_BREAK_EVEN_ACTIVATED
    assert result["break_even_activated"] is True
    assert result["position"]["stop_loss"] == 111.0
    assert result["position"]["break_even_trigger_price"] == 113.0

    print("BREAK EVEN BUY: OK")
    print("STOP LOSS MOVIDO A ENTRADA: 111.0")
    print("PASSED")


# ============================================================
# TEST 3
# BREAK EVEN SELL EN 1:1
# ============================================================

def test_monitor_sell_activates_break_even_at_one_to_one():
    print()
    print("=" * 80)
    print("TEST 3")
    print("MONITOREAR SELL Y ACTIVAR BREAK EVEN 1:1")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_sell_position())
    service = PositionMonitoringService(manager)

    result = service.monitor_position(
        ticket="PAPER-000002",
        current_price=109.0,
    )

    assert result["closed"] is False
    assert result["action"] == MONITOR_ACTION_BREAK_EVEN_ACTIVATED
    assert result["position"]["stop_loss"] == 111.0
    assert result["position"]["break_even_trigger_price"] == 109.0

    print("BREAK EVEN SELL: OK")
    print("STOP LOSS MOVIDO A ENTRADA: 111.0")
    print("PASSED")


# ============================================================
# TEST 4
# RETROCESO A BREAK EVEN
# ============================================================

def test_monitor_buy_closes_at_break_even_after_retrace():
    print()
    print("=" * 80)
    print("TEST 4")
    print("CERRAR BUY EN BREAK EVEN DESPUES DEL RETROCESO")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_buy_position())
    service = PositionMonitoringService(manager)

    service.monitor_position("PAPER-000001", 113.0)
    result = service.monitor_position("PAPER-000001", 111.0)

    assert result["closed"] is True
    assert result["action"] == MONITOR_ACTION_BREAK_EVEN_STOP
    assert result["position"]["status"] == POSITION_CLOSED
    assert result["position"]["exit_price"] == 111.0
    assert result["position"]["exit_reason"] == MONITOR_ACTION_BREAK_EVEN_STOP
    assert result["position"]["realized_pnl_price"] == 0.0

    print("CIERRE BREAK EVEN: OK")
    print("REALIZED PNL: 0.0")
    print("PASSED")


# ============================================================
# TEST 5
# TAKE PROFIT BUY
# ============================================================

def test_monitor_buy_closes_at_take_profit():
    print()
    print("=" * 80)
    print("TEST 5")
    print("CERRAR BUY EN TAKE PROFIT")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_buy_position())
    service = PositionMonitoringService(manager)

    result = service.monitor_position(
        ticket="PAPER-000001",
        current_price=115.0,
    )

    assert result["closed"] is True
    assert result["action"] == MONITOR_ACTION_TAKE_PROFIT
    assert result["position"]["status"] == POSITION_CLOSED
    assert result["position"]["realized_pnl_price"] == 4.0

    print("TAKE PROFIT BUY: OK")
    print("PASSED")


# ============================================================
# TEST 6
# STOP LOSS SELL
# ============================================================

def test_monitor_sell_closes_at_stop_loss():
    print()
    print("=" * 80)
    print("TEST 6")
    print("CERRAR SELL EN STOP LOSS")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_sell_position())
    service = PositionMonitoringService(manager)

    result = service.monitor_position(
        ticket="PAPER-000002",
        current_price=113.0,
    )

    assert result["closed"] is True
    assert result["action"] == MONITOR_ACTION_STOP_LOSS
    assert result["position"]["status"] == POSITION_CLOSED
    assert result["position"]["realized_pnl_price"] == -2.0

    print("STOP LOSS SELL: OK")
    print("PASSED")


# ============================================================
# TEST 7
# MONITOREAR TODAS LAS ABIERTAS
# ============================================================

def test_monitor_open_positions_processes_available_prices_only():
    print()
    print("=" * 80)
    print("TEST 7")
    print("MONITOREAR TODAS LAS POSICIONES ABIERTAS")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_buy_position("PAPER-000001"))
    manager.register_position(create_sell_position("PAPER-000002"))
    service = PositionMonitoringService(manager)

    results = service.monitor_open_positions({
        "PAPER-000001": 113.0,
    })

    assert len(results) == 1
    assert results[0]["ticket"] == "PAPER-000001"
    assert results[0]["action"] == MONITOR_ACTION_BREAK_EVEN_ACTIVATED
    assert manager.get_position("PAPER-000002")["current_price"] == 111.0

    print("POSICIONES MONITOREADAS: 1")
    print("POSICION SIN PRECIO: NO PROCESADA")
    print("PASSED")


# ============================================================
# TEST 8
# POSICION DESCONOCIDA
# ============================================================

def test_monitor_unknown_position_is_blocked():
    print()
    print("=" * 80)
    print("TEST 8")
    print("POSICION DESCONOCIDA")
    print("=" * 80)

    service = PositionMonitoringService(PositionManager())

    with pytest.raises(ValueError, match="No existe una posición"):
        service.monitor_position("UNKNOWN", 100.0)

    print("POSICION DESCONOCIDA: BLOQUEADA")
    print("PASSED")


# ============================================================
# TEST 9
# POSICION CERRADA NO SE MONITOREA
# ============================================================

def test_closed_position_cannot_be_monitored():
    print()
    print("=" * 80)
    print("TEST 9")
    print("POSICION CERRADA NO SE MONITOREA")
    print("=" * 80)

    manager = PositionManager()
    manager.register_position(create_buy_position())
    manager.close_position("PAPER-000001", 115.0)
    service = PositionMonitoringService(manager)

    with pytest.raises(ValueError, match="no está abierta"):
        service.monitor_position("PAPER-000001", 114.0)

    print("POSICION CERRADA: BLOQUEADA")
    print("PASSED")
