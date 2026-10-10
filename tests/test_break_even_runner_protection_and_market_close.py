"""Pruebas unitarias para la protección de la segunda pierna (RUNNER) en Break Even:
1. Protección estricta de Spread ejecutable (desde executor MT5 o provider) y compensación
   exacta de SWAP acumulado negativo en el cálculo del Break Even (PnL >= 0.00 USD).
2. Si el mercado o broker NO es capaz de proteger el RUNNER (distancia mínima de stops violada,
   rechazo de modificación o confirmación fallida en el broker), se cierra la operación a mercado
   en lugar de dejarla desprotegida.
3. Cierre defensivo ante cierres de mercado (fin de semana, cierre diario de sesión, rollover)
   para Forex, Cripto, Índices Bursátiles y Metales (Gold/Silver), preservando el funcionamiento
   continuo 24/7 de Sintéticos.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
import pytest

from strategy.execution.live_trading_engine import (
    LiveTradingConfig,
    LiveTradingEngine,
)


class MockRepo:
    def __init__(self, trades=None):
        self.trades = {int(t["id"]): dict(t) for t in (trades or [])}
        self.updates = []

    def open_trades(self, source=None):
        return [dict(t) for t in self.trades.values() if t.get("status", "OPEN") == "OPEN"]

    def get_trade(self, trade_id):
        return self.trades.get(int(trade_id))

    def get_trade_by_execution_key(self, key):
        for t in self.trades.values():
            if t.get("execution_key") == key:
                return dict(t)
            meta = (t.get("details") or {}).get("metadata") or {}
            if meta.get("execution_key") == key:
                return dict(t)
            parent = meta.get("parent_execution_key")
            leg = meta.get("trade_leg")
            if parent and leg and f"{parent}:{leg}" == key:
                return dict(t)
        return None

    def update_trade(self, trade_id, data):
        self.updates.append((int(trade_id), data))
        if int(trade_id) in self.trades:
            self.trades[int(trade_id)].update(data)


class MockBrokerExecutor:
    def __init__(self, positions=None, constraints=None, tick=None):
        self.positions = dict(positions or {})
        self.constraints = dict(constraints or {
            "point": 0.01,
            "tick_size": 0.01,
            "digits": 2,
            "trade_contract_size": 1.0,
            "stops_level_points": 5,
            "min_stop_distance": 0.05,
        })
        self.tick = tick or {"bid": 100.0, "ask": 100.02}
        self.confirm_changes = True

    def get_position(self, ticket):
        return self.positions.get(int(ticket))

    def get_symbol_constraints(self, symbol):
        return dict(self.constraints)

    def get_current_tick(self, symbol):
        return dict(self.tick)


class MockTradeExecutor:
    def __init__(self, broker):
        self.broker = broker
        self.modify_calls = []
        self.close_calls = []
        self.allow_modify = True
        self.allow_close = True

    def move_stop_loss(self, position_ticket, stop_loss, take_profit=None, reason=""):
        self.modify_calls.append({
            "ticket": str(position_ticket),
            "sl": float(stop_loss),
            "tp": float(take_profit or 0.0),
            "reason": reason,
        })
        if not self.allow_modify:
            return {"modified": False, "error": "ERR_INVALID_STOPS", "retcode": 10016}
        pos = self.broker.get_position(int(position_ticket))
        if pos and self.broker.confirm_changes:
            pos.sl = float(stop_loss)
        return {"modified": True, "retcode": 10009}

    def close_position(self, position_ticket, reason=""):
        self.close_calls.append({
            "ticket": str(position_ticket),
            "reason": reason,
        })
        if not self.allow_close:
            return {"closed": False, "error": "ERR_BROKER_BUSY"}
        ticket_int = int(position_ticket)
        if ticket_int in self.broker.positions:
            del self.broker.positions[ticket_int]
        return {"closed": True, "status": "CLOSED", "ticket": str(position_ticket), "reason": reason}


class MockLifecycle:
    def __init__(self, trade_executor):
        self.trade_executor = trade_executor


def _build_engine(trades, positions, constraints=None, tick=None, config_overrides=None):
    import pandas as pd
    repo = MockRepo(trades)
    broker = MockBrokerExecutor(positions=positions, constraints=constraints, tick=tick)
    trade_exec = MockTradeExecutor(broker)
    lifecycle = MockLifecycle(trade_exec)
    provider = SimpleNamespace(
        get_current_tick=lambda s: broker.get_current_tick(s),
        resolve_symbol=lambda s: s,
        ensure_symbol=lambda s: None,
        get_candles=lambda *a, **k: pd.DataFrame([{"time": pd.Timestamp("2026-01-01"), "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5}]),
    )
    cfg_kwargs = {
        "execution_enabled": True,
        "break_even_enabled": True,
        "break_even_offset_points": 2,
        "break_even_profit_lock_rr_fraction": 0.0,
        "break_even_confirmation_retries": 2,
        "break_even_confirmation_delay_seconds": 0.0,
        "break_even_close_if_unprotectable": True,
        "forex_rollover_guard_enabled": True,
        "forex_force_flat_daily": True,
        "forex_force_flat_friday": True,
    }
    cfg_kwargs.update(config_overrides or {})
    cfg = LiveTradingConfig(**cfg_kwargs)
    engine = LiveTradingEngine(
        provider=provider,
        repository=repo,
        config=cfg,
        executor=broker,
        lifecycle_manager=lifecycle,
    )
    return engine, repo, broker, trade_exec


# ==============================================================================
# TEST SUITE 1: CÁLCULO DE BREAK EVEN PROTEGIENDO SPREAD Y SWAP
# ==============================================================================

def test_break_even_target_stop_uses_executor_tick_spread_and_offset():
    """Valida que BE sume el spread ejecutable de MT5 y el offset configurado."""
    broker = MockBrokerExecutor(
        constraints={"point": 0.01, "digits": 2, "trade_contract_size": 1.0},
        tick={"bid": 2000.00, "ask": 2000.30},  # Spread de 0.30
    )
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(break_even_offset_points=2)  # 2 * 0.01 = 0.02
    engine.executor = broker
    engine.provider = SimpleNamespace(get_current_tick=lambda s: {"bid": 2000.0, "ask": 2000.10})

    # BUY: entry + offset (0.02 + 0.30 spread = 0.32)
    target_buy, offset_buy = engine._break_even_target_stop("XAUUSD", "BUY", 2000.00)
    assert round(offset_buy, 2) == 0.32
    assert round(target_buy, 2) == 2000.32

    # SELL: entry - offset
    target_sell, offset_sell = engine._break_even_target_stop("XAUUSD", "SELL", 2000.00)
    assert round(offset_sell, 2) == 0.32
    assert round(target_sell, 2) == 1999.68


def test_break_even_target_stop_negative_swap_monetary_compensation():
    """Valida que el SWAP devengado negativo se compense exactamente en el precio de Break Even."""
    # 0.10 lotes de EURUSD, punto = 0.00001, tick_size = 0.00001, tick_value = 1.00 USD por lote
    # monetary_per_price_unit = 0.10 * (1.0 / 0.00001) = 10,000 USD por 1.00 de movimiento
    # Si pos_swap = -5.0 USD: swap_points = 5.0 / 10000 = 0.0005 (5 pips)
    broker = MockBrokerExecutor(
        constraints={
            "point": 0.00001,
            "digits": 5,
            "trade_contract_size": 100000.0,
            "tick_size": 0.00001,
            "tick_value": 1.00,
        },
        tick={"bid": 1.10000, "ask": 1.10010},  # Spread = 0.00010
    )
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(break_even_offset_points=0)  # offset base 0
    engine.executor = broker
    engine.provider = broker

    pos = {"swap": -5.0, "volume": 0.10}
    target_buy, offset_buy = engine._break_even_target_stop("EURUSD", "BUY", 1.10000, position=pos)
    # Spread (0.00010) + Swap (0.00050) = 0.00060
    assert round(offset_buy, 5) == 0.00060
    assert round(target_buy, 5) == 1.10060


# ==============================================================================
# TEST SUITE 2: CIERRE DEFENSIVO SI NO ES CAPAZ DE PROTEGERLO EN BREAK EVEN
# ==============================================================================

def test_runner_closed_at_market_if_price_too_close_to_be_stop():
    """Si el precio retrocedió y está dentro de stops_level, cierra a mercado para proteger ganancias."""
    # TP1 ya cerró con éxito. El RUNNER debe ir a BE, pero el precio ya está pegado a la entrada.
    trade_runner = {
        "id": 10,
        "broker_position_ticket": "1001",
        "instrument": "NAS100",
        "direction": "BUY",
        "status": "OPEN",
        "stop_loss": 18000.0,
        "take_profit": 18200.0,
        "planned_rr": 2.0,
        "details": {
            "metadata": {
                "initial_stop_loss": 18000.0,
                "trade_leg": "RUNNER",
                "parent_execution_key": "PARENT_KEY",
                "break_even_activated": False,
            }
        }
    }
    trade_tp1 = {
        "id": 9,
        "execution_key": "PARENT_KEY:TP1",
        "status": "CLOSED",
        "result": "WIN",
        "realized_rr": 1.0,
        "exit_price": 18100.0,
        "details": {"metadata": {"trade_leg": "TP1"}}
    }
    # Entrada 18050. BE target es 18050.50. min_stop_distance = 5.0 puntos.
    # El precio actual es 18052.00 (distancia = 1.5 < 5.0).
    pos = SimpleNamespace(
        ticket=1001,
        price_open=18050.0,
        price_current=18052.0,
        sl=18000.0,
        tp=18200.0,
        swap=0.0,
        volume=1.0,
    )
    constraints = {
        "point": 0.1,
        "tick_size": 0.1,
        "digits": 2,
        "stops_level_points": 50,  # 5.0 puntos de distancia mínima requerida
        "min_stop_distance": 5.0,
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[trade_runner, trade_tp1],
        positions={1001: pos},
        constraints=constraints,
        tick={"bid": 18052.0, "ask": 18052.2},
    )

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 1
    # Se activó el cierre defensivo
    assert len(trade_exec.close_calls) == 1
    assert trade_exec.close_calls[0]["ticket"] == "1001"
    assert "unprotected_be" in trade_exec.close_calls[0]["reason"]
    # En repo se marcó el fallback closed
    trade_updated = repo.get_trade(10)
    meta = trade_updated["details"]["metadata"]
    assert meta["break_even_fallback_closed"] is True
    assert meta["break_even_fallback_reason"] == "PRICE_TOO_CLOSE_TO_PROTECT_BE"


def test_runner_closed_at_market_if_broker_rejects_modification():
    """Si el broker rechaza la modificación de SL a BE, el bot cierra la posición a mercado para no dejarla desprotegida."""
    trade_runner = {
        "id": 20,
        "broker_position_ticket": "2001",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "OPEN",
        "stop_loss": 1.0900,
        "take_profit": 1.1100,
        "details": {
            "metadata": {
                "initial_stop_loss": 1.0900,
                "trade_leg": "RUNNER",
                "parent_execution_key": "PARENT_EUR",
                "break_even_activated": False,
            }
        }
    }
    trade_tp1 = {
        "id": 19,
        "execution_key": "PARENT_EUR:TP1",
        "status": "CLOSED",
        "result": "WIN",
        "realized_rr": 1.0,
        "details": {"metadata": {"trade_leg": "TP1"}}
    }
    pos = SimpleNamespace(
        ticket=2001,
        price_open=1.1000,
        price_current=1.1080,
        sl=1.0900,
        tp=1.1100,
        swap=0.0,
        volume=0.5,
    )
    engine, repo, broker, trade_exec = _build_engine(
        trades=[trade_runner, trade_tp1],
        positions={2001: pos},
        constraints={"point": 0.0001, "digits": 4, "min_stop_distance": 0.0005},
        tick={"bid": 1.1080, "ask": 1.1081},
    )
    trade_exec.allow_modify = False  # Simula rechazo del broker (10016 / invalid stops)

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 1
    assert len(trade_exec.close_calls) == 1
    assert trade_exec.close_calls[0]["ticket"] == "2001"
    assert "modification_rejected" in trade_exec.close_calls[0]["reason"]
    meta = repo.get_trade(20)["details"]["metadata"]
    assert meta["break_even_fallback_closed"] is True
    assert meta["break_even_fallback_reason"] == "MODIFICATION_REJECTED"


def test_runner_closed_at_market_if_broker_does_not_confirm_be():
    """Si tras reintentos el broker nunca aplicó el nuevo stop, el bot cierra a mercado."""
    trade_runner = {
        "id": 30,
        "broker_position_ticket": "3001",
        "instrument": "US30",
        "direction": "SELL",
        "status": "OPEN",
        "stop_loss": 39000.0,
        "take_profit": 38000.0,
        "details": {
            "metadata": {
                "initial_stop_loss": 39000.0,
                "trade_leg": "RUNNER",
                "parent_execution_key": "PARENT_US30",
                "break_even_activated": False,
            }
        }
    }
    trade_tp1 = {
        "id": 29,
        "execution_key": "PARENT_US30:TP1",
        "status": "CLOSED",
        "result": "WIN",
        "realized_rr": 1.0,
        "details": {"metadata": {"trade_leg": "TP1"}}
    }
    pos = SimpleNamespace(
        ticket=3001,
        price_open=38500.0,
        price_current=38200.0,
        sl=39000.0,
        tp=38000.0,
        swap=0.0,
        volume=1.0,
    )
    engine, repo, broker, trade_exec = _build_engine(
        trades=[trade_runner, trade_tp1],
        positions={3001: pos},
        constraints={"point": 1.0, "digits": 1, "min_stop_distance": 5.0},
        tick={"bid": 38200.0, "ask": 38202.0},
    )
    broker.confirm_changes = False  # Simula que broker devuelve OK pero nunca actualiza el SL en MT5

    result = engine._monitor_break_even_positions()

    assert result["activated"] == 1
    assert len(trade_exec.close_calls) == 1
    assert trade_exec.close_calls[0]["ticket"] == "3001"
    assert "unconfirmed" in trade_exec.close_calls[0]["reason"]
    meta = repo.get_trade(30)["details"]["metadata"]
    assert meta["break_even_fallback_closed"] is True
    assert meta["break_even_fallback_reason"] == "NOT_CONFIRMED_BY_BROKER"


# ==============================================================================
# TEST SUITE 3: PROTECCIÓN ANTE CIERRES DE MERCADO (FOREX, ÍNDICES, METALES)
# ==============================================================================

def test_market_close_closes_indices_metals_and_forex_before_closure():
    """Valida que _close_forex_positions_for_rollover cierre Índices, Metales y Forex 15 min antes del cierre o fin de semana."""
    trades = [
        {"id": 1, "broker_position_ticket": "101", "instrument": "EURUSD", "status": "OPEN", "details": {"metadata": {"daemon_magic": 26082026}}},
        {"id": 2, "broker_position_ticket": "102", "instrument": "US Tech 100", "status": "OPEN", "details": {"metadata": {"daemon_magic": 26082026}}},
        {"id": 3, "broker_position_ticket": "103", "instrument": "XAUUSD", "status": "OPEN", "details": {"metadata": {"daemon_magic": 26082026}}},
        {"id": 4, "broker_position_ticket": "104", "instrument": "BTCUSD", "status": "OPEN", "details": {"metadata": {"daemon_magic": 26082026}}},
        # Sintético: NO debe cerrarse, opera 24/7
        {"id": 5, "broker_position_ticket": "105", "instrument": "Crash 500 Index", "status": "OPEN", "details": {"metadata": {"daemon_magic": 26082026}}},
    ]
    positions = {
        101: SimpleNamespace(ticket=101, price_open=1.1, sl=1.09, tp=1.2),
        102: SimpleNamespace(ticket=102, price_open=18000, sl=17900, tp=18200),
        103: SimpleNamespace(ticket=103, price_open=2000, sl=1990, tp=2020),
        104: SimpleNamespace(ticket=104, price_open=60000, sl=59000, tp=62000),
        105: SimpleNamespace(ticket=105, price_open=5000, sl=4900, tp=5200),
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=trades,
        positions=positions,
        config_overrides={
            "magic": 26082026,
            "forex_force_flat_hour": 16,
            "forex_force_flat_minute": 45,
            "crypto_force_flat_hour": 16,
            "crypto_force_flat_minute": 45,
        }
    )

    # Viernes 16:50 NY (20:50 UTC en verano) -> force_flat_now = True
    now_friday_close = datetime(2026, 9, 4, 20, 50, tzinfo=timezone.utc)
    engine._forex_rollover_status = lambda now_utc=None: {
        "force_flat_now": True,
        "weekend": False,
        "block_new_entries": True,
    }
    engine._crypto_rollover_status = lambda now_utc=None: {
        "force_flat_now": True,
        "weekend": False,
        "block_new_entries": True,
    }

    res = engine._close_market_close_positions()

    assert res["closed"] == 4  # EURUSD, US Tech 100, XAUUSD, BTCUSD cerrados
    assert res["checked"] == 4
    closed_tickets = {c["ticket"] for c in trade_exec.close_calls}
    assert closed_tickets == {"101", "102", "103", "104"}
    # El sintético 105 NUNCA debe ser cerrado por rollover
    assert "105" not in closed_tickets


def test_symbol_classifier_helpers():
    """Valida que los nuevos métodos clasificadores identifiquen correctamente las familias de activos."""
    assert LiveTradingEngine._is_forex_symbol("GBPUSD") is True
    assert LiveTradingEngine._is_forex_symbol("USDJPYmicro") is True
    assert LiveTradingEngine._is_forex_symbol("XAUUSD") is False

    assert LiveTradingEngine._is_metal_symbol("XAUUSD") is True
    assert LiveTradingEngine._is_metal_symbol("XAGUSD") is True
    assert LiveTradingEngine._is_metal_symbol("GOLD") is True
    assert LiveTradingEngine._is_metal_symbol("EURUSD") is False

    assert LiveTradingEngine._is_index_symbol("US Tech 100") is True
    assert LiveTradingEngine._is_index_symbol("US30") is True
    assert LiveTradingEngine._is_index_symbol("SPX500") is True
    assert LiveTradingEngine._is_index_symbol("GER40") is True
    assert LiveTradingEngine._is_index_symbol("Crash 500 Index") is False

    assert LiveTradingEngine._is_synthetic_symbol("Crash 500 Index") is True
    assert LiveTradingEngine._is_synthetic_symbol("Volatility 75 Index") is True
    assert LiveTradingEngine._is_synthetic_symbol("Jump 100 Index") is True
    assert LiveTradingEngine._is_synthetic_symbol("EURUSD") is False

    assert LiveTradingEngine._is_market_closing_symbol("EURUSD") is True
    assert LiveTradingEngine._is_market_closing_symbol("XAUUSD") is True
    assert LiveTradingEngine._is_market_closing_symbol("US Tech 100") is True
    assert LiveTradingEngine._is_market_closing_symbol("Volatility 75 Index") is False


def test_runner_closes_at_tp2_when_extension_disabled_or_fixed_target():
    """Valida que la Pierna 2 (RUNNER) se cierre inmediatamente a mercado al tocar TP2 (2.0R) si la extensión está desactivada."""
    runner_trade = {
        "id": 10,
        "broker_position_ticket": "201",
        "instrument": "Boom 1000 Index",
        "direction": "BUY",
        "status": "OPEN",
        "planned_rr": 2.0,
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": "SMC",
                "bot_profile": "BOOM",
                "target_rr": 2.0,
                "initial_stop_loss": 90.0,
                "break_even_confirmed": True,
            }
        },
    }
    # price_open=100.0, sl=90.0 (risk=10.0), price_current=120.0 (exactamente 2.0R)
    positions = {
        201: SimpleNamespace(ticket=201, price_open=100.0, price_current=120.0, sl=100.0, tp=120.0)
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[runner_trade],
        positions=positions,
        config_overrides={
            "runner_extension_enabled": False,
            "split_entries_enabled": True,
            "break_even_enabled": True,
        }
    )

    result = engine._monitor_break_even_positions()

    # Debe haberse cerrado a mercado
    assert any(c["ticket"] == "201" for c in trade_exec.close_calls)
    assert any(u.get("action") == "RUNNER_TARGET_CLOSED_AT_MARKET" for u in result.get("updates", []))


def test_runner_closes_at_tp2_when_extension_evaluates_no_continuation(monkeypatch):
    """Valida que si la extensión está activa pero en TP2 no hay continuación, la Pierna 2 se cierre a mercado en TP2."""
    runner_trade = {
        "id": 11,
        "broker_position_ticket": "202",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "OPEN",
        "planned_rr": 2.0,
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": "ICT",
                "bot_profile": "FOREX",
                "target_rr": 2.0,
                "initial_stop_loss": 90.0,
                "break_even_confirmed": True,
            }
        },
    }
    # price_open=100.0, sl=90.0 (risk=10), current=120.5 (2.05R)
    positions = {
        202: SimpleNamespace(ticket=202, price_open=100.0, price_current=120.5, sl=100.0, tp=140.0)
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[runner_trade],
        positions=positions,
        config_overrides={
            "runner_extension_enabled": True,
            "forex_runner_max_target_rr": 4.0,
        }
    )
    # Mock evaluate_runner_continuation -> False
    import strategy.execution.live_trading_engine as lte
    from strategy.execution.runner_extension_manager import RunnerExtensionDecision
    monkeypatch.setattr(
        lte, "evaluate_runner_continuation",
        lambda *args, **kwargs: RunnerExtensionDecision(False, "ESTRUCTURA_AGOTADA_EN_TP2", {})
    )

    res = engine._manage_runner_extension(
        trade=runner_trade,
        position=positions[202],
        metadata=dict(runner_trade["details"]["metadata"]),
        initial_stop_loss=90.0,
        current_rr=2.05,
        move_stop=trade_exec.move_stop_loss,
    )

    assert res["managed"] is True
    assert res["closed"] is True
    assert any(c["ticket"] == "202" for c in trade_exec.close_calls)


def test_runner_seeking_tp3_protects_tp1(monkeypatch):
    """Valida que si la Pierna 2 busca TP3, el Stop Loss proteja TP1 (+1.0R)."""
    runner_trade = {
        "id": 12,
        "broker_position_ticket": "203",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "OPEN",
        "planned_rr": 2.0,
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": "ICT",
                "bot_profile": "FOREX",
                "initial_stop_loss": 90.0,
                "break_even_confirmed": True,
            }
        },
    }
    positions = {
        203: SimpleNamespace(ticket=203, price_open=100.0, price_current=120.5, sl=100.0, tp=140.0)
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[runner_trade],
        positions=positions,
        config_overrides={
            "runner_extension_enabled": True,
            "runner_extension_first_trigger_rr": 2.0,
            "runner_extension_first_lock_rr": 1.0,
            "forex_runner_tp3_lock_rr": 1.0,
            "forex_runner_max_target_rr": 4.0,
        }
    )
    import strategy.execution.live_trading_engine as lte
    from strategy.execution.runner_extension_manager import RunnerExtensionDecision
    monkeypatch.setattr(
        lte, "evaluate_runner_continuation",
        lambda *args, **kwargs: RunnerExtensionDecision(True, "CONTINUACION_HACIA_TP3", {})
    )

    res = engine._manage_runner_extension(
        trade=runner_trade,
        position=positions[203],
        metadata=dict(runner_trade["details"]["metadata"]),
        initial_stop_loss=90.0,
        current_rr=2.05,
        move_stop=trade_exec.move_stop_loss,
    )

    assert res["managed"] is True
    assert res["extended"] is True
    assert res["stage"] == "2R_TO_3R"
    # El profit lock debe ser exactamente +1.0R (protegiendo TP1)
    assert res["profit_lock_rr"] == 1.0
    # Stop loss en precio = 100 + 1.0 * 10 = 110.0
    assert res["profit_lock_price"] == 110.0
    assert broker.positions[203].sl == 110.0


def test_runner_seeking_tp4_protects_tp3_maximizing_profits(monkeypatch):
    """Valida que si la Pierna 2 busca TP4, el Stop Loss proteja TP3 (+3.0R) maximizando las ganancias."""
    runner_trade = {
        "id": 13,
        "broker_position_ticket": "204",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "OPEN",
        "planned_rr": 3.0,
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": "ICT",
                "bot_profile": "FOREX",
                "initial_stop_loss": 90.0,
                "runner_extension_completed_stages": ["2R_TO_3R"],
                "runner_extension_stage": "EXTENDED_TO_3R",
                "break_even_confirmed": True,
            }
        },
    }
    # price_open=100.0, sl=110.0 (+1R), current=130.5 (+3.05R)
    positions = {
        204: SimpleNamespace(ticket=204, price_open=100.0, price_current=130.5, sl=110.0, tp=140.0)
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[runner_trade],
        positions=positions,
        config_overrides={
            "runner_extension_enabled": True,
            "runner_extension_second_trigger_rr": 3.0,
            "runner_extension_second_lock_rr": 2.0,
            "runner_extension_tp4_protect_tp3": True,
            "forex_runner_max_target_rr": 4.0,
            "smc_runner_max_target_rr": 4.0,
        }
    )
    import strategy.execution.live_trading_engine as lte
    from strategy.execution.runner_extension_manager import RunnerExtensionDecision
    monkeypatch.setattr(
        lte, "evaluate_runner_continuation",
        lambda *args, **kwargs: RunnerExtensionDecision(True, "CONTINUACION_HACIA_TP4", {})
    )

    res = engine._manage_runner_extension(
        trade=runner_trade,
        position=positions[204],
        metadata=dict(runner_trade["details"]["metadata"]),
        initial_stop_loss=90.0,
        current_rr=3.05,
        move_stop=trade_exec.move_stop_loss,
    )

    assert res["managed"] is True
    assert res["extended"] is True
    assert res["stage"] == "3R_TO_4R"
    # Al buscar TP4, el profit lock DEBE proteger TP3 (+3.0R) para maximizar ganancias
    assert res["profit_lock_rr"] == 3.0
    # Stop loss en precio = 100 + 3.0 * 10 = 130.0
    assert res["profit_lock_price"] == 130.0
    assert broker.positions[204].sl == 130.0


def test_runner_closes_at_max_target_tp4():
    """Valida que la Pierna 2 se cierre inmediatamente a mercado al alcanzar el objetivo máximo TP4 (4.0R)."""
    runner_trade = {
        "id": 14,
        "broker_position_ticket": "205",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "OPEN",
        "planned_rr": 4.0,
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": "ICT",
                "bot_profile": "FOREX",
                "initial_stop_loss": 90.0,
                "runner_extension_completed_stages": ["2R_TO_3R", "3R_TO_4R"],
                "break_even_confirmed": True,
            }
        },
    }
    # price_open=100.0, sl=130.0, current=140.0 (+4.0R exactos)
    positions = {
        205: SimpleNamespace(ticket=205, price_open=100.0, price_current=140.0, sl=130.0, tp=140.0)
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[runner_trade],
        positions=positions,
        config_overrides={
            "runner_extension_enabled": True,
            "forex_runner_max_target_rr": 4.0,
            "smc_runner_max_target_rr": 4.0,
        }
    )

    res = engine._manage_runner_extension(
        trade=runner_trade,
        position=positions[205],
        metadata=dict(runner_trade["details"]["metadata"]),
        initial_stop_loss=90.0,
        current_rr=4.0,
        move_stop=trade_exec.move_stop_loss,
    )

    assert res["managed"] is True
    assert res["closed"] is True
    assert res["stage"] == "MAX_TARGET_REACHED"
    assert any(c["ticket"] == "205" for c in trade_exec.close_calls)


def test_runner_break_even_activated_immediately_when_leg_1_tp1_closes_with_spread_and_swap():
    """Valida que cuando la Pierna 1 se cierra (alcanzando TP1), la Pierna 2 queda inmediatamente en Break Even protegiendo Spread y SWAP."""
    tp1_trade = {
        "id": 30,
        "broker_position_ticket": "301",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "CLOSED",
        "result": "WIN",
        "realized_rr": 1.0,
        "exit_price": 110.0,
        "details": {
            "metadata": {
                "trade_leg": "TP1",
                "parent_execution_key": "PARENT_ORDER_1",
            }
        },
    }
    runner_trade = {
        "id": 31,
        "broker_position_ticket": "302",
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "OPEN",
        "planned_rr": 2.0,
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "parent_execution_key": "PARENT_ORDER_1",
                "break_even_activated": False,
                "break_even_confirmed": False,
                "initial_stop_loss": 90.0,
            }
        },
    }
    # price_open=100.0, sl=90.0, swap acumulado = -$1.00 USD
    positions = {
        302: SimpleNamespace(
            ticket=302,
            price_open=100.0,
            price_current=105.0,  # El precio aún no ha llegado a TP2 pero TP1 ya cerró
            sl=90.0,
            tp=120.0,
            swap=-1.0,
            volume=0.10,
        )
    }
    engine, repo, broker, trade_exec = _build_engine(
        trades=[tp1_trade, runner_trade],
        positions=positions,
        config_overrides={
            "split_entries_enabled": True,
            "break_even_enabled": True,
            "break_even_trigger_rr": 1.0,
            "break_even_offset_points": 2,
        }
    )
    # Mock constraints y tick para spread y swap
    broker.get_symbol_constraints = lambda sym: {
        "point": 0.00001,
        "tick_size": 0.00001,
        "tick_value": 1.0,
        "contract_size": 100000.0,
        "digits": 5,
        "stops_level_points": 0,
    }
    broker.get_current_tick = lambda sym: {"bid": 1.05000, "ask": 1.05010}  # Spread = 0.00010

    # Ejecutar el monitor
    res = engine._monitor_break_even_positions()

    # La pierna 2 debe haberse activado en Break Even por el cierre en profit de TP1
    assert res["activated"] == 1
    assert any(u.get("ticket") == "302" and u.get("activation_reason") == "TP1_CLOSED_IN_PROFIT" for u in res.get("updates", []))
    # SL en broker debe ser estrictamente mayor al precio de entrada (protegiendo spread + swap)
    new_sl = broker.positions[302].sl
    assert new_sl > 100.0

