"""Tests exhaustivos para la regla de cierre automático 15 minutos antes del cierre de mercado
para órdenes abiertas de Forex y Criptomonedas (evitando costes excesivos de spread y SWAP).
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


def make_engine(bot_profile="FOREX_1"):
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(
        bot_profile=bot_profile,
        execution_enabled=True,
        forex_rollover_guard_enabled=True,
        crypto_rollover_guard_enabled=True,
        forex_rollover_timezone="America/New_York",
        crypto_rollover_timezone="America/New_York",
        forex_new_entry_cutoff_hour=14,
        forex_new_entry_cutoff_minute=0,
        crypto_new_entry_cutoff_hour=14,
        crypto_new_entry_cutoff_minute=0,
        forex_force_flat_hour=16,
        forex_force_flat_minute=45,
        crypto_force_flat_hour=16,
        crypto_force_flat_minute=45,
        forex_market_reopen_hour=17,
        forex_market_reopen_minute=0,
        crypto_market_reopen_hour=17,
        crypto_market_reopen_minute=0,
        forex_force_flat_daily=True,
        forex_force_flat_friday=True,
        crypto_force_flat_daily=True,
        crypto_force_flat_friday=True,
        market_close_force_flat_minutes_before=15,
    )
    return e


# ============================================================================
# 1. CLASIFICACIÓN PRECISA DE ACTIVOS (FOREX, CRYPTO, SINTÉTICOS, METALES)
# ============================================================================

def test_symbol_classification_forex_vs_crypto():
    e = make_engine()

    # Forex reconocidos
    assert e._is_forex_symbol("EURUSD")
    assert e._is_forex_symbol("GBPUSDmicro")
    assert e._is_forex_symbol("USDJPYm")
    assert e._is_forex_symbol("USDCAD")
    assert e._is_forex_symbol("AUDNZD")

    # Forex NO es crypto
    assert not e._is_crypto_symbol("EURUSD")
    assert not e._is_crypto_symbol("GBPUSD")

    # Crypto reconocidos
    assert e._is_crypto_symbol("BTCUSD")
    assert e._is_crypto_symbol("ETHUSD")
    assert e._is_crypto_symbol("LTCUSD")
    assert e._is_crypto_symbol("SOLUSD")
    assert e._is_crypto_symbol("XRPUSD")
    assert e._is_crypto_symbol("ADAUSD")
    assert e._is_crypto_symbol("DOGUSD")
    assert e._is_crypto_symbol("BTCETH")
    assert e._is_crypto_symbol("BTCUSD.conv")
    assert e._is_crypto_symbol("ETHUSDmicro")

    # Crypto NO es forex
    assert not e._is_forex_symbol("BTCUSD")
    assert not e._is_forex_symbol("ETHUSD")

    # Sintéticos NO son ni forex ni crypto
    for synth in ["Volatility 75 Index", "Boom 1000 Index", "Crash 500 Index", "Step Index", "Jump 10 Index"]:
        assert not e._is_forex_symbol(synth)
        assert not e._is_crypto_symbol(synth)
        assert not e._is_forex_or_crypto_symbol(synth)

    # Metales (XAU/XAG) NO son clasificados como forex ni crypto aquí
    assert not e._is_forex_symbol("XAUUSD")
    assert not e._is_crypto_symbol("XAUUSD")
    assert not e._is_forex_or_crypto_symbol("XAUUSD")

    # Helper unificado
    assert e._is_forex_or_crypto_symbol("EURUSD")
    assert e._is_forex_or_crypto_symbol("BTCUSD")


# ============================================================================
# 2. LÍMITES TEMPORALES EXACTOS (15 MINUTOS ANTES DEL CIERRE DE MERCADO)
# ============================================================================

@pytest.mark.parametrize("stamp,expected_blocked,expected_flat", [
    # Antes del cutoff: abierto normal
    ("2026-09-22T17:59:59+00:00", False, False),
    # En ventana de corte de nuevas entradas (14:00 NY = 18:00 UTC en verano EDT):
    ("2026-09-22T18:00:00+00:00", True, False),
    # Exactamente 15 minutos antes del cierre (16:45 NY = 20:45 UTC en EDT):
    ("2026-09-22T20:45:00+00:00", True, True),
    # 5 minutos antes del cierre (16:55 NY = 20:55 UTC en EDT):
    ("2026-09-22T20:55:00+00:00", True, True),
    # Reapertura del mercado (17:00 NY = 21:00 UTC en EDT): flat se desactiva
    ("2026-09-22T21:00:00+00:00", False, False),
    # Invierno EST (UTC-5): 16:45 NY = 21:45 UTC
    ("2026-12-01T21:44:59+00:00", True, False),
    ("2026-12-01T21:45:00+00:00", True, True),
    ("2026-12-01T22:00:00+00:00", False, False),
])
def test_15_minutes_before_close_boundaries_forex_and_crypto(stamp, expected_blocked, expected_flat):
    e = make_engine()
    dt = datetime.fromisoformat(stamp)

    s_fx = e._forex_rollover_status(dt)
    assert s_fx["block_new_entries"] == expected_blocked
    assert s_fx["force_flat_now"] == expected_flat

    s_cr = e._crypto_rollover_status(dt)
    assert s_cr["block_new_entries"] == expected_blocked
    assert s_cr["force_flat_now"] == expected_flat
    assert s_cr["minutes_before_close"] == 15


# ============================================================================
# 3. CIERRE AUTOMÁTICO DE ÓRDENES ABIERTAS DE FOREX Y CRYPTO
# ============================================================================

def test_auto_closes_both_forex_and_crypto_positions_15_min_before_close():
    e = make_engine()
    # Simulamos que ambos mercados se encuentran en la ventana force_flat_now (16:45 NY)
    e._forex_rollover_status = lambda: {"force_flat_now": True}
    e._crypto_rollover_status = lambda: {"force_flat_now": True}

    closed_calls = []

    def fake_close(position_ticket, reason):
        closed_calls.append({"ticket": position_ticket, "reason": reason})
        return {"closed": True, "status": "CLOSED"}

    e.lifecycle_manager = SimpleNamespace(
        trade_executor=SimpleNamespace(close_position=fake_close)
    )

    # 4 posiciones abiertas:
    # - 1: GBPCAD (Forex, owned) -> DEBE CERRARSE
    # - 2: BTCUSD (Crypto, owned) -> DEBE CERRARSE
    # - 3: ETHUSD (Crypto, owned) -> DEBE CERRARSE
    # - 4: Volatility 75 Index (Sintético, owned) -> NO DEBE CERRARSE
    # - 5: EURUSD (Forex, no owned por otro bot) -> NO DEBE TOCARSE
    e.repository = SimpleNamespace(open_trades=lambda **kw: [
        {"id": 1, "instrument": "GBPCAD", "broker_position_ticket": "1001", "net_pnl": 50},
        {"id": 2, "instrument": "BTCUSD", "broker_position_ticket": "1002", "net_pnl": -20},
        {"id": 3, "instrument": "ETHUSD", "broker_position_ticket": "1003", "net_pnl": 15},
        {"id": 4, "instrument": "Volatility 75 Index", "broker_position_ticket": "1004", "net_pnl": 10},
        {"id": 5, "instrument": "EURUSD", "broker_position_ticket": "1005", "net_pnl": 0},
    ])

    e._trade_owned_by_current_bot = lambda trade: trade["id"] != 5
    audit_events = []
    e._persist_audit_event = lambda event, **kwargs: audit_events.append((event, kwargs))

    res = e._close_forex_positions_for_rollover()

    assert res["checked"] == 3
    assert res["closed"] == 3
    assert len(closed_calls) == 3

    # Verificar tickets cerrados
    tickets_closed = {c["ticket"] for c in closed_calls}
    assert tickets_closed == {"1001", "1002", "1003"}

    # Verificar razones y eventos de auditoría específicos
    reasons = {c["ticket"]: c["reason"] for c in closed_calls}
    assert reasons["1001"] == "forex_pre_new_york_close"
    assert reasons["1002"] == "crypto_pre_market_close"
    assert reasons["1003"] == "crypto_pre_market_close"

    event_names = [ev[0] for ev in audit_events]
    assert "FOREX_SCHEDULED_CLOSE" in event_names
    assert "CRYPTO_SCHEDULED_CLOSE" in event_names


def test_does_not_close_when_outside_flat_window():
    e = make_engine()
    e._forex_rollover_status = lambda: {"force_flat_now": False}
    e._crypto_rollover_status = lambda: {"force_flat_now": False}

    close_mock = Mock()
    e.lifecycle_manager = SimpleNamespace(trade_executor=SimpleNamespace(close_position=close_mock))
    e.repository = SimpleNamespace(open_trades=lambda **kw: [
        {"id": 1, "instrument": "EURUSD", "broker_position_ticket": "1001"},
        {"id": 2, "instrument": "BTCUSD", "broker_position_ticket": "1002"},
    ])
    e._trade_owned_by_current_bot = lambda trade: True

    res = e._close_forex_positions_for_rollover()
    assert res["closed"] == 0
    assert res["checked"] == 0
    assert close_mock.call_count == 0


# ============================================================================
# 4. PUERTAS DE ENTRADA (BLOQUEO DE NUEVAS ÓRDENES CERCA DEL CIERRE)
# ============================================================================

def test_entry_gates_block_new_entries_for_both_forex_and_crypto():
    e = make_engine()
    # 20:45 UTC = 16:45 NY (dentro de la ventana de bloqueo de nuevas entradas)
    dt = datetime(2026, 9, 22, 20, 45, tzinfo=timezone.utc)
    e._forex_rollover_status = lambda: {"block_new_entries": True, "force_flat_now": True}
    e._crypto_rollover_status = lambda: {"block_new_entries": True, "force_flat_now": True}

    gate_fx = e._forex_rollover_entry_gate("EURUSD")
    assert gate_fx is not None
    assert gate_fx["action"] == "FOREX_ROLLOVER_ENTRY_BLOCKED"

    gate_cr = e._crypto_rollover_entry_gate("BTCUSD")
    assert gate_cr is not None
    assert gate_cr["action"] == "CRYPTO_ROLLOVER_ENTRY_BLOCKED"

    # Sintéticos no se bloquean por la regla de rollover Forex/Crypto
    gate_synth = e._forex_rollover_entry_gate("Volatility 75 Index")
    assert gate_synth is None
    gate_synth_cr = e._crypto_rollover_entry_gate("Volatility 75 Index")
    assert gate_synth_cr is None
