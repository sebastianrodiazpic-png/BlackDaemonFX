import csv
import json
import os
import pytest
from app.main import BOT_PROFILES
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def test_indicesb_snr_profile_definition():
    profile = BOT_PROFILES.get("INDICESB_SNR")
    assert profile is not None, "INDICESB_SNR must exist in BOT_PROFILES"
    assert profile["magic"] == 26082042
    assert profile["mode"] == "indicesb-snr-daemon"
    expected_symbols = {"Germany 40", "US SP 500", "US Tech 100", "Wall Street 30"}
    assert set(profile["symbols"]) == expected_symbols


def test_indicesb_snr_pruned_universe():
    universe = PRUNED_ASSET_UNIVERSE.get("INDICESB_SNR")
    assert universe is not None, "INDICESB_SNR must exist in PRUNED_ASSET_UNIVERSE"
    expected_symbols = {"Germany 40", "US SP 500", "US Tech 100", "Wall Street 30"}
    assert set(universe) == expected_symbols


def test_indicesb_snr_worker_rules():
    cfg = LiveTradingConfig(bot_profile="INDICESB_SNR", magic=26082042, execution_enabled=False)
    rules = configure_worker_rules(cfg)

    assert rules.malaysian_snr_enabled is True
    assert rules.dual_m5_m1_trigger_enabled is True
    assert rules.entry_timeframe == "M5"
    assert rules.first_target_rr == 1.0
    assert rules.second_target_rr == 2.0
    assert rules.break_even_enabled is True
    assert rules.break_even_trigger_rr == 1.0
    assert rules.runner_extension_enabled is True


def test_realtime_dashboard_worker_meta():
    meta = _WORKER_PROFILE_META.get("INDICESB_SNR")
    assert meta is not None, "INDICESB_SNR must be in _WORKER_PROFILE_META"
    assert meta["strategy_key"] == "MULTISTRATEGY"
    assert meta["strategy_label"] == "MultiStrategia"
    assert meta["magic"] == 26082042
    assert "MultiStrategia" in meta["label"]
    assert "32180" in meta["label"]


def test_dashboard_file_integrity():
    dashboard_path = "dashboard/realtime_dashboard.py"
    with open(dashboard_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Worker label and display
    assert "Worker INDICESB_SNR (Índices Bursátiles · MultiStrategia · Magic 26082042 · PID 32180)" in content
    assert "INDICES (MULTI)" in content
    assert "Materias Primas y Criptomonedas" in content
    assert "26082042" in content
    assert "26082032" in content


def test_strategy_bases_csv_and_page():
    csv_path = "storage/analysis/replay_5y_perfect_strategy_bases.csv"
    assert os.path.exists(csv_path)

    expected_indices = {"Germany 40", "US SP 500", "US Tech 100", "Wall Street 30"}
    found_in_csv = set()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert len(header) == 39
        for row in reader:
            if not row:
                continue
            assert len(row) == 39
            if row[0] in expected_indices:
                found_in_csv.add(row[0])
                assert row[1] == "MultiStrategia"
                assert "INDICESB_SNR" in row[2]
                assert row[3] == "2600"
                assert "Activo MultiStrategia" in row[12]

    assert found_in_csv == expected_indices, f"Missing indices in CSV: {expected_indices - found_in_csv}"

    # Check strategy_bases_page.py
    py_path = "dashboard/strategy_bases_page.py"
    with open(py_path, mode="r", encoding="utf-8") as f:
        page_content = f.read()

    for sym in expected_indices:
        assert f'"symbol": "{sym}"' in page_content
        assert '"strategy": "MultiStrategia"' in page_content


def test_decisions_page_indices_card():
    decisions_path = "dashboard/decisions_page.py"
    with open(decisions_path, mode="r", encoding="utf-8") as f:
        content = f.read()

    assert "Worker INDICESB_SNR · Índices Bursátiles · MultiStrategia · Magic 26082042 · PID 32180" in content
    assert "Germany 40" in content
    assert "US SP 500" in content
    assert "US Tech 100" in content
    assert "Wall Street 30" in content
    assert "10,400 trades totales" in content
    assert "Win Rate global 66.84%" in content
    assert "+5,110.50 R netos acumulados" in content
