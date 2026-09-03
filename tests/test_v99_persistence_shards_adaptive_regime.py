from types import SimpleNamespace
import threading

import pandas as pd

from app.main import (
    BOT_PROFILES,
    FULL_MULTI_BOT_PROFILES,
    VOLATILITY_SHARD_PROFILES,
    _stable_symbol_shard,
)
from dashboard.realtime_dashboard import _enrich_recent_row
from database.repository import TradingRepository
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.scalping.adaptive_regime_pullback import (
    AdaptiveRegimePullbackConfig,
    AdaptiveRegimePullbackStrategy,
)


def test_recovery_skips_while_fill_persistence_is_in_progress():
    imported = []

    class Repo:
        def import_open_mt5_positions(self, *args, **kwargs):
            imported.append(True)
            return {"seen": 1, "imported_daemon": 1}

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(execution_enabled=True)
    engine.repository = Repo()
    engine.executor = object()
    engine._execution_persistence_lock = threading.Lock()
    engine._persist_audit_event = lambda *args, **kwargs: None

    assert engine._execution_persistence_lock.acquire()
    try:
        result = engine._recover_unpersisted_open_positions()
    finally:
        engine._execution_persistence_lock.release()

    assert result["reason"] == "EXECUTION_PERSISTENCE_IN_PROGRESS"
    assert imported == []


def test_broker_position_ticket_promotes_recovered_row_without_duplicate(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "v99.sqlite3")
    recovered_id, created = repo.create_trade_once({
        "external_ticket": "MT5POS:7001",
        "execution_key": "mt5-open-position:7001",
        "broker_position_ticket": "7001",
        "source": "DEMO",
        "instrument": "Volatility 50 Index",
        "direction": "BUY",
        "status": "OPEN",
        "strategy_version": "smc-reconciled-mt5-open",
        "details": {"metadata": {"adopted_from_mt5": True}},
    })
    canonical_id, canonical_created = repo.create_trade_once({
        "external_ticket": "ORDER:991",
        "execution_key": "ARPS:VOL50:TP1",
        "broker_position_ticket": "7001",
        "source": "DEMO",
        "instrument": "Volatility 50 Index",
        "direction": "BUY",
        "status": "OPEN",
        "strategy_version": "arps-synthetic-v3-adaptive-regime",
        "details": {"metadata": {"strategy_name": "ARPS_SYNTHETIC_SCALPER"}},
    })

    assert created is True
    assert canonical_created is False
    assert canonical_id == recovered_id
    row = repo.get_trade(canonical_id)
    assert row["execution_key"] == "ARPS:VOL50:TP1"
    assert row["external_ticket"] == "ORDER:991"
    assert len(repo.open_trades(source="DEMO")) == 1


def test_volatility_shards_are_disjoint_complete_and_have_unique_identity():
    symbols = [f"Volatility {number} Index" for number in range(1, 35)]
    parts = [
        _stable_symbol_shard(symbols, index, len(VOLATILITY_SHARD_PROFILES))
        for index in range(len(VOLATILITY_SHARD_PROFILES))
    ]
    flattened = [symbol for part in parts for symbol in part]

    assert set(flattened) == set(symbols)
    assert len(flattened) == len(set(flattened))
    specs = [BOT_PROFILES[name] for name in VOLATILITY_SHARD_PROFILES]
    assert len({spec["mode"] for spec in specs}) == 4
    assert len({spec["magic"] for spec in specs}) == 4
    assert all(name in FULL_MULTI_BOT_PROFILES for name in VOLATILITY_SHARD_PROFILES)
    assert "VOLATILITY" not in FULL_MULTI_BOT_PROFILES


def test_adaptive_adx_is_bounded_and_keeps_structural_floor():
    strategy = AdaptiveRegimePullbackStrategy(
        data_provider=SimpleNamespace(),
        config=AdaptiveRegimePullbackConfig(
            minimum_adx=20.0,
            adaptive_adx_floor=16.0,
            adaptive_adx_percentile=0.35,
        ),
    )
    threshold, reference = strategy._effective_adx_threshold(
        pd.Series([17.0] * 200)
    )
    assert reference == 17.0
    assert threshold == 17.0

    floor_threshold, _ = strategy._effective_adx_threshold(
        pd.Series([8.0] * 200)
    )
    assert floor_threshold == 16.0


def test_dashboard_explains_regime_block_with_actual_adx_values():
    row = _enrich_recent_row({
        "symbol": "Volatility 25 Index",
        "action": "ARPS_REGIME_BLOCKED",
        "reason": "ADX_M15_INSUFICIENTE",
        "arps_metrics": {"adx": 15.4, "effective_minimum_adx": 17.2},
    })

    assert row["operational_state"]["label"] == "ESPERANDO RÉGIMEN"
    assert "15.40" in row["reason_es"]
    assert "17.20" in row["reason_es"]


def test_dashboard_translates_each_missing_arps_confirmation():
    row = _enrich_recent_row({
        "symbol": "Volatility 25 Index",
        "action": "ARPS_WAITING_SETUP",
        "reason": "M5_STRUCTURE_BREAK,M1_FOLLOW_THROUGH",
    })

    assert "ruptura estructural BOS" in row["reason_es"]
    assert "posterior" in row["reason_es"]
