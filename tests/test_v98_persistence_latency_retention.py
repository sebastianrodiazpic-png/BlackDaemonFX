from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3

import database.database as database_module
from database.database import backup_sqlite_database
from database.repository import TradingRepository
from reporting.strategy_evaluation import build_strategy_evaluation
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_sqlite_backup_includes_committed_wal_and_is_integral(tmp_path):
    source = tmp_path / "live.sqlite3"
    destination = tmp_path / "backup.sqlite3"
    connection = sqlite3.connect(source)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
    connection.commit()
    connection.execute("INSERT INTO sample(value) VALUES ('from-wal')")
    connection.commit()

    backup_sqlite_database(source, destination)

    copied = sqlite3.connect(destination)
    try:
        assert copied.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert copied.execute("SELECT value FROM sample").fetchone()[0] == "from-wal"
    finally:
        copied.close()
        connection.close()


def test_sqlite_backup_closes_both_handles_before_windows_replace(tmp_path, monkeypatch):
    source = tmp_path / "source.sqlite3"
    destination = tmp_path / "destination.sqlite3"
    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()

    closed_handles = []

    class TrackedClosing:
        def __init__(self, resource):
            self.resource = resource

        def __enter__(self):
            return self.resource

        def __exit__(self, *_exc):
            self.resource.close()
            closed_handles.append(self.resource)

    monkeypatch.setattr(database_module, "closing", TrackedClosing)
    original_replace = Path.replace

    def assert_closed_before_replace(path, target):
        assert len(closed_handles) == 2
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", assert_closed_before_replace)

    backup_sqlite_database(source, destination)

    assert destination.exists()


def test_retention_deletes_only_old_operational_events(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "retention.sqlite3")
    old = datetime.now(timezone.utc) - timedelta(days=40)
    repo.save_audit_event(
        "SYMBOL_PROCESS_RESULT", action="NO_SIGNAL", event_time=old,
        payload={"result": {"action": "NO_SIGNAL"}},
    )
    repo.save_audit_event(
        "TRADE_ENTRY_AUDIT_ERROR", action="ENTRY_AUDIT_PERSIST_FAILED", event_time=old,
        payload={"trade_id": 10},
    )
    repo.save_audit_event(
        "SYMBOL_PROCESS_RESULT", action="ARPS_WAITING_SETUP",
        payload={"result": {"action": "ARPS_WAITING_SETUP"}},
    )

    result = repo.prune_operational_audit_events(retention_days=14, max_rows=10_000)

    assert result["deleted_total"] == 1
    connection = sqlite3.connect(repo.db_path)
    try:
        remaining = connection.execute(
            "SELECT event_type, action FROM daemon_audit_events ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    assert ("TRADE_ENTRY_AUDIT_ERROR", "ENTRY_AUDIT_PERSIST_FAILED") in remaining
    assert ("SYMBOL_PROCESS_RESULT", "ARPS_WAITING_SETUP") in remaining
    assert ("SYMBOL_PROCESS_RESULT", "NO_SIGNAL") not in remaining


def test_symbol_audit_payload_is_compact_and_keeps_arps_metrics():
    huge = "X" * 250_000
    result = {
        "symbol": "Volatility 50 Index",
        "action": "ARPS_WAITING_SETUP",
        "reason": "m5_pullback,m1_rejection",
        "analysis": {
            "strategy_name": "ARPS_SYNTHETIC_SCALPER",
            "strategy_version": "arps-test",
            "diagnostics": {
                "adx": 24.5,
                "atr": 3.1,
                "spread_atr_ratio": 0.08,
                "confirmations": {
                    "m15_adx_strength": True,
                    "m5_pullback": False,
                    "m1_rejection": False,
                },
                "raw_candles": huge,
            },
            "full_analysis_dump": huge,
        },
    }

    compact = LiveTradingEngine._compact_symbol_result(result)

    assert compact["strategy_name"] == "ARPS_SYNTHETIC_SCALPER"
    assert compact["arps_metrics"]["adx"] == 24.5
    assert compact["missing_confirmations"] == ["m5_pullback", "m1_rejection"]
    assert "full_analysis_dump" not in json.dumps(compact)
    assert len(json.dumps(compact)) < 10_000


def test_strategy_evaluation_summarizes_arps_and_risk_without_changing_thresholds():
    class Repo:
        def recent_symbol_evaluation_events(self, source="DEMO", hours=24.0):
            return [
                {
                    "event_time": datetime.now(timezone.utc),
                    "instrument": "Jump 25 Index",
                    "action": "ARPS_WAITING_SETUP",
                    "reason": "m1_rejection",
                    "payload": {
                        "elapsed_seconds": 0.4,
                        "result": {
                            "strategy_name": "ARPS_SYNTHETIC_SCALPER",
                            "action": "ARPS_WAITING_SETUP",
                            "missing_confirmations": ["m1_rejection"],
                            "arps_metrics": {"adx": 21.0, "spread_atr_ratio": 0.09},
                        },
                    },
                },
                {
                    "event_time": datetime.now(timezone.utc),
                    "instrument": "Wall Street 30",
                    "action": "REJECTED_RISK_TARGET_UNREACHABLE",
                    "reason": "BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK",
                    "payload": {
                        "elapsed_seconds": 0.2,
                        "result": {
                            "strategy_name": "ORB_NEW_YORK",
                            "action": "REJECTED_RISK_TARGET_UNREACHABLE",
                            "risk_metrics": {"risk_amount": 100.0, "actual_risk_amount": 82.0},
                        },
                    },
                },
            ]

    report = build_strategy_evaluation(Repo(), hours=24)

    assert report["total_evaluations"] == 2
    assert report["missing_confirmations"]["ARPS_SYNTHETIC_SCALPER"]["m1_rejection"] == 1
    assert report["arps_metrics"]["adx"]["median"] == 21.0
    assert report["risk_reachability"]["rows"][0]["actual_to_requested_ratio"] == 0.82
    assert not any(report["configuration_guardrails"].values())


def test_repeated_waiting_evaluation_is_sampled_but_runtime_keeps_updating():
    class Repo:
        def __init__(self):
            self.runtime = 0
            self.audit = 0

        def upsert_worker_runtime_state(self, *args, **kwargs):
            self.runtime += 1
            return self.runtime

        def save_audit_event(self, *args, **kwargs):
            self.audit += 1
            return self.audit

    engine = object.__new__(LiveTradingEngine)
    engine.repository = Repo()
    engine.config = LiveTradingConfig(
        bot_profile="SCALP_VOLATILITY",
        magic=26082303,
        strategy_evaluation_audit_interval_seconds=300,
    )
    payload = {
        "schema_version": "strategy-evaluation-v1",
        "result": {
            "symbol": "Volatility 50 Index",
            "action": "ARPS_WAITING_SETUP",
            "reason": "m1_rejection",
            "missing_confirmations": ["m1_rejection"],
        },
        "elapsed_seconds": 0.2,
        "index": 1,
        "total": 1,
    }

    first = engine._persist_audit_event(
        "SYMBOL_PROCESS_RESULT",
        instrument="Volatility 50 Index",
        action="ARPS_WAITING_SETUP",
        reason="m1_rejection",
        payload=payload,
    )
    second = engine._persist_audit_event(
        "SYMBOL_PROCESS_RESULT",
        instrument="Volatility 50 Index",
        action="ARPS_WAITING_SETUP",
        reason="m1_rejection",
        payload=payload,
    )

    assert first == 1
    assert second["sampled_out"] is True
    assert engine.repository.audit == 1
    assert engine.repository.runtime == 2


def test_background_monitor_is_enabled_without_changing_strategy_thresholds():
    config = LiveTradingConfig()
    assert config.background_position_monitor_enabled is True
    assert config.visual_audit_refresh_seconds == 30.0
    assert config.max_m5_signal_age_candles == 2
    assert config.minimum_confirmation_ratio == 0.80
    assert config.minimum_viable_trade_score == 75.0
    assert config.min_actual_risk_ratio == 0.99
