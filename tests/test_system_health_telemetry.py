"""tests/test_system_health_telemetry.py - Tests unitarios del monitor de salud y telemetría."""

from __future__ import annotations

from pathlib import Path
import pytest

from tools.system_health_telemetry import (
    check_sqlite_health,
    check_active_calibrations,
    inspect_system_telemetry,
)


def test_sqlite_health_returns_metrics(tmp_path):
    db_file = tmp_path / "test_health.sqlite3"
    import sqlite3
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, symbol TEXT)")
    conn.commit()
    conn.close()

    res = check_sqlite_health(db_file)
    assert res["status"] == "HEALTHY"
    assert res["journal_mode"] == "WAL"
    assert res["ping_us"] > 0
    assert "trades" in res["row_counts"]


def test_check_active_calibrations_includes_all_pillars():
    cals = check_active_calibrations()
    assert "pilar_1_tecnico" in cals
    assert "pilar_2_cuantitativo" in cals
    assert "pilar_3_infraestructura" in cals

    p1 = cals["pilar_1_tecnico"]
    assert p1["smc_jit_warmup"] is True
    assert p1["candle_zero_copy_cache"] is True

    p2 = cals["pilar_2_cuantitativo"]
    assert p2["runner_extension_first_trigger_rr"] == 2.0
    assert p2["runner_extension_first_lock_rr"] == 1.0
    assert p2["runner_extension_max_target_rr"] == 3.0
    assert p2["step_jump_adx_guard_exempt"] is True
    assert p2["synthetic_climax_body_ratio"] == 0.80
    assert p2["max_spread_to_sl_ratio"] == 0.12


def test_inspect_system_telemetry_persists_json(tmp_path):
    rep = inspect_system_telemetry()
    assert rep["overall_status"] == "OPTIMIZED_AND_STABLE"
    assert "sqlite_health" in rep
    assert "calibrations" in rep

    out_json = Path("storage/system_health_latest.json")
    assert out_json.exists()
