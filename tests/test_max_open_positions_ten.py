"""Pruebas unitarias para validar el límite de 5 instrumentos abiertos y 10 posiciones físicas (TP1 + RUNNER)."""

import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from config.strategy_config import RISK_CONFIG
from risk.portfolio_accounting import PortfolioLimits


class DummyRepository:
    def __init__(self, trades=None):
        self.trades = list(trades or [])

    def open_trades(self, source="DEMO"):
        return list(self.trades)


def _make_engine(repo=None, max_open_positions=10, max_per_symbol=2):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="SYNTHETICS",
        source="DEMO",
        execution_enabled=True,
        max_open_positions=max_open_positions,
        max_open_positions_per_symbol=max_per_symbol,
        split_entries_enabled=True,
    )
    engine.repository = repo or DummyRepository()
    return engine


def test_default_config_limits():
    cfg = LiveTradingConfig()
    assert cfg.max_open_positions == 10
    assert cfg.max_open_positions_per_symbol == 2
    assert cfg.split_entries_enabled is True
    assert cfg.forex_max_total_risk_percent == 5.0
    assert RISK_CONFIG["max_open_positions"] == 5
    assert PortfolioLimits().max_open_positions == 10


def test_allows_up_to_five_instruments_ten_positions():
    # 4 instrumentos ya abiertos (8 posiciones físicas, 2 por cada uno: TP1 + RUNNER)
    existing_trades = []
    instruments = ["Volatility 75 Index", "Volatility 50 (1s) Index", "Step Index", "Jump 75 Index"]
    ticket_counter = 1000
    for inst in instruments:
        existing_trades.append({
            "id": ticket_counter,
            "instrument": inst,
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": str(ticket_counter),
        })
        ticket_counter += 1
        existing_trades.append({
            "id": ticket_counter,
            "instrument": inst,
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": str(ticket_counter),
        })
        ticket_counter += 1

    assert len(existing_trades) == 8  # 4 instrumentos x 2 piernas

    repo = DummyRepository(trades=existing_trades)
    engine = _make_engine(repo=repo)

    # El 5to instrumento debe permitirse (8 + 2 <= 10)
    candidate_5 = "Boom 1000 Index"
    result_5 = engine._position_limit_result(candidate_5, "exec_key_cand_5")
    assert result_5 is None, f"Se esperaba permitir el 5to instrumento pero retornó: {result_5}"

    # Ahora agregamos las 2 posiciones del 5to instrumento (total 10 posiciones) en repo.trades
    repo.trades.append({
        "id": ticket_counter,
        "instrument": candidate_5,
        "direction": "BUY",
        "status": "OPEN",
        "broker_position_ticket": str(ticket_counter),
    })
    ticket_counter += 1
    repo.trades.append({
        "id": ticket_counter,
        "instrument": candidate_5,
        "direction": "BUY",
        "status": "OPEN",
        "broker_position_ticket": str(ticket_counter),
    })

    assert len(repo.trades) == 10  # 5 instrumentos x 2 piernas = 10 posiciones

    # Intentar un 6to instrumento debe ser bloqueado por MAX_TOTAL_OPEN_POSITIONS
    candidate_6 = "Crash 500 Index"
    result_6 = engine._position_limit_result(candidate_6, "exec_key_cand_6")
    assert result_6 is not None
    assert result_6["action"] == "MAX_TOTAL_OPEN_POSITIONS"
    assert result_6["reason"] == "MAX_TOTAL_OPEN_POSITIONS_REACHED"


def test_blocks_second_trade_on_same_instrument():
    # Un instrumento con sus 2 posiciones abiertas (TP1 + RUNNER)
    existing_trades = [
        {
            "id": 101,
            "instrument": "Step Index",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1001",
        },
        {
            "id": 102,
            "instrument": "Step Index",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1002",
        },
    ]
    repo = DummyRepository(trades=existing_trades)
    engine = _make_engine(repo=repo)

    # Intentar abrir una nueva señal en Step Index debe bloquearse
    result = engine._position_limit_result("Step Index", "exec_key_step_2")
    assert result is not None
    assert result["action"] == "POSITION_ALREADY_OPEN_FOR_SYMBOL"
    assert result["reason"] == "MAX_OPEN_POSITIONS_PER_SYMBOL_REACHED"
