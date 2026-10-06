"""Pruebas unitarias para la regla de exclusión mutua entre activos estándar y sus variantes micro.

Verifica:
1. Normalización y mapeo canónico en `strategy.execution.symbol_counterpart`.
2. Bloqueo en broker MT5 a través de `strategy.execution.active_position_guard`.
3. Bloqueo en repositorio/motor a través de `strategy.execution.live_trading_engine`.
"""

from types import SimpleNamespace
import pytest

from strategy.execution.active_position_guard import check_active_position_guard
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.symbol_counterpart import (
    canonical_symbol_root,
    counterpart_category,
    is_counterpart_pair,
    is_same_or_counterpart_symbol,
)


class DummyRepository:
    def __init__(self, trades=None):
        self._trades = list(trades or [])

    def open_trades(self, source=None):
        return [t for t in self._trades if t.get("status") == "OPEN"]

    def list_trades(self):
        return list(self._trades)


def _make_engine(profile="FOREX", repo=None):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile=profile,
        source="DEMO",
        execution_enabled=True,
        max_open_positions=6,
        max_open_positions_per_symbol=2,
    )
    engine.repository = repo or DummyRepository()
    return engine


# ==============================================================================
# 1. Pruebas de normalización y detección de contrapartes
# ==============================================================================


def test_canonical_symbol_root_forex():
    assert canonical_symbol_root("EURUSD") == "EURUSD"
    assert canonical_symbol_root("EURUSDmicro") == "EURUSD"
    assert canonical_symbol_root("EURUSD.m") == "EURUSD"
    assert canonical_symbol_root("GBPUSD") == "GBPUSD"
    assert canonical_symbol_root("GBPUSDmicro") == "GBPUSD"
    assert canonical_symbol_root("USDJPY") == "USDJPY"
    assert canonical_symbol_root("USDJPYmicro") == "USDJPY"
    assert canonical_symbol_root("USDCADmicro") == "USDCAD"
    assert canonical_symbol_root("USDCHFmicro") == "USDCHF"


def test_canonical_symbol_root_metals_and_indices():
    assert canonical_symbol_root("XAUUSD") == "XAUUSD"
    assert canonical_symbol_root("XAUUSDmicro") == "XAUUSD"
    assert canonical_symbol_root("microXAUUSD") == "XAUUSD"
    assert canonical_symbol_root("XAGUSD") == "XAGUSD"
    assert canonical_symbol_root("XAGUSDmicro") == "XAGUSD"
    assert canonical_symbol_root("US30") == "US30"
    assert canonical_symbol_root("US30micro") == "US30"


def test_is_counterpart_pair_universal():
    # Forex bidireccional
    assert is_counterpart_pair("EURUSD", "EURUSDmicro") is True
    assert is_counterpart_pair("EURUSDmicro", "EURUSD") is True
    assert is_counterpart_pair("USDJPY", "USDJPYmicro") is True
    assert is_counterpart_pair("USDJPYmicro", "USDJPY") is True
    assert is_counterpart_pair("GBPUSD", "GBPUSDmicro") is True

    # Metales
    assert is_counterpart_pair("XAUUSD", "XAUUSDmicro") is True
    assert is_counterpart_pair("XAUUSDmicro", "XAUUSD") is True
    assert is_counterpart_pair("XAGUSD", "XAGUSDmicro") is True

    # Mismo símbolo exacto no es contraparte (es el mismo contrato)
    assert is_counterpart_pair("EURUSD", "EURUSD") is False
    assert is_counterpart_pair("EURUSDmicro", "EURUSDmicro") is False

    # Activos diferentes no colisionan
    assert is_counterpart_pair("EURUSD", "GBPUSD") is False
    assert is_counterpart_pair("EURUSDmicro", "GBPUSDmicro") is False
    assert is_counterpart_pair("EURUSD", "USDJPY") is False

    # Sintéticos no colisionan entre variantes de índice
    assert is_counterpart_pair("Step Index", "Step Index 500") is False
    assert is_counterpart_pair("Crash 1000 Index", "Crash 500 Index") is False
    assert is_counterpart_pair("Volatility 100 Index", "Volatility 100 (1s) Index") is False


# ==============================================================================
# 2. Pruebas de guardia en MT5 (active_position_guard)
# ==============================================================================


def test_mt5_guard_blocks_eurusdmicro_when_eurusd_open():
    positions = [dict(symbol="EURUSD", ticket=2001, price_open=1.0850, sl=1.0800)]
    orders = []

    res = check_active_position_guard("EURUSDmicro", positions, orders)
    assert not res["can_analyze"]
    assert res["status"] == "BLOCKED_ACTIVE_TRADE"
    assert "EURUSD" in res["reason"]
    assert "contraparte" in res["reason"].lower()
    assert res["counterpart_symbol"] == "EURUSD"
    assert res["ticket"] == 2001


def test_mt5_guard_blocks_eurusd_when_eurusdmicro_open():
    positions = [dict(symbol="EURUSDmicro", ticket=2002, price_open=1.0850, sl=1.0800)]
    orders = []

    res = check_active_position_guard("EURUSD", positions, orders)
    assert not res["can_analyze"]
    assert res["status"] == "BLOCKED_ACTIVE_TRADE"
    assert "EURUSDmicro" in res["reason"]
    assert res["counterpart_symbol"] == "EURUSDmicro"
    assert res["ticket"] == 2002


def test_mt5_guard_blocks_counterpart_pending_order():
    positions = []
    orders = [dict(symbol="USDJPY", ticket=3001, price_open=150.0)]

    res = check_active_position_guard("USDJPYmicro", positions, orders)
    assert not res["can_analyze"]
    assert res["status"] == "BLOCKED_PENDING_ORDER"
    assert "USDJPY" in res["reason"]
    assert res["counterpart_symbol"] == "USDJPY"


def test_mt5_guard_allows_unrelated_forex_symbols():
    positions = [dict(symbol="EURUSD", ticket=2003, price_open=1.0850, sl=1.0800)]
    orders = []

    # GBPUSD y GBPUSDmicro no deben verse afectados por EURUSD
    res_gbp = check_active_position_guard("GBPUSD", positions, orders)
    assert res_gbp["can_analyze"]

    res_gbpmic = check_active_position_guard("GBPUSDmicro", positions, orders)
    assert res_gbpmic["can_analyze"]


# ==============================================================================
# 3. Pruebas de motor y repositorio (LiveTradingEngine)
# ==============================================================================


def test_forex_worker_blocks_eurusdmicro_when_eurusd_is_open():
    repo = DummyRepository(
        trades=[
            {
                "id": 101,
                "instrument": "EURUSD",
                "direction": "BUY",
                "status": "OPEN",
                "broker_position_ticket": "5001",
            }
        ]
    )
    engine = _make_engine("FOREX", repo=repo)

    counterpart = engine._counterpart_asset_open("EURUSDmicro")
    assert counterpart is not None
    assert counterpart["category"] == "FOREX"
    assert counterpart["instrument"] == "EURUSD"
    assert counterpart["candidate_symbol"] == "EURUSDmicro"
    assert counterpart["canonical_root"] == "EURUSD"
    assert counterpart["action"] == "FOREX_COUNTERPART_EXPOSURE_ALREADY_OPEN"
    assert counterpart["reason"] == "YA_EXISTE_POSICION_ABIERTA_EN_CONTRATO_CONTRAPARTE_EURUSD"

    # Verificar a través de _position_limit_result
    limit_res = engine._position_limit_result("EURUSDmicro", "exec_key_micro_1")
    assert limit_res is not None
    assert limit_res["action"] == "FOREX_COUNTERPART_EXPOSURE_ALREADY_OPEN"
    assert limit_res["reason"] == "YA_EXISTE_POSICION_ABIERTA_EN_CONTRATO_CONTRAPARTE_EURUSD"


def test_forex_worker_blocks_eurusd_when_eurusdmicro_is_open():
    repo = DummyRepository(
        trades=[
            {
                "id": 102,
                "instrument": "EURUSDmicro",
                "direction": "SELL",
                "status": "OPEN",
                "broker_position_ticket": "5002",
            }
        ]
    )
    engine = _make_engine("FOREX", repo=repo)

    counterpart = engine._counterpart_asset_open("EURUSD")
    assert counterpart is not None
    assert counterpart["category"] == "FOREX"
    assert counterpart["instrument"] == "EURUSDmicro"
    assert counterpart["candidate_symbol"] == "EURUSD"
    assert counterpart["canonical_root"] == "EURUSD"
    assert counterpart["action"] == "FOREX_COUNTERPART_EXPOSURE_ALREADY_OPEN"

    limit_res = engine._position_limit_result("EURUSD", "exec_key_std_1")
    assert limit_res is not None
    assert limit_res["action"] == "FOREX_COUNTERPART_EXPOSURE_ALREADY_OPEN"


def test_forex_worker_blocks_usdjpy_and_usdjpymicro():
    repo = DummyRepository(
        trades=[
            {
                "id": 103,
                "instrument": "USDJPYmicro",
                "direction": "BUY",
                "status": "OPEN",
                "broker_position_ticket": "5003",
            }
        ]
    )
    engine = _make_engine("FOREX", repo=repo)

    assert engine._counterpart_asset_open("USDJPY") is not None
    assert engine._counterpart_asset_open("EURUSD") is None


def test_forex_diagnostics_track_counterpart_trades():
    repo = DummyRepository(
        trades=[
            {
                "id": 104,
                "instrument": "EURUSDmicro",
                "direction": "BUY",
                "status": "OPEN",
                "broker_position_ticket": "5004",
            }
        ]
    )
    engine = _make_engine("FOREX", repo=repo)

    diag = engine._open_trade_diagnostics("EURUSD")
    assert diag["symbol_open"] == 0
    assert diag["counterpart_open"] == 1
    assert len(diag["counterpart_open_trades"]) == 1
    assert diag["counterpart_open_trades"][0]["instrument"] == "EURUSDmicro"


def test_closed_forex_trades_do_not_block_counterpart():
    repo = DummyRepository(
        trades=[
            {
                "id": 105,
                "instrument": "EURUSDmicro",
                "direction": "BUY",
                "status": "CLOSED",
                "broker_position_ticket": "5005",
            }
        ]
    )
    engine = _make_engine("FOREX", repo=repo)

    assert engine._counterpart_asset_open("EURUSD") is None
