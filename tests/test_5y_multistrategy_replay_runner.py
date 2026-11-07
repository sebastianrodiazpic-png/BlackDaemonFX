import os
from pathlib import Path

import numpy as np
import pytest

from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
from tools.run_multistrategy_5y_replay import (
    ALL_SYMBOLS_FLAT,
    CATALOG_ALL_INSTRUMENTS,
    DEFAULT_5Y_DAYS,
    STRATEGIES,
    MultiStrategy5YReplayRunner,
    calculate_metrics,
    simulate_blackdaemon_dual_leg,
)


def test_5y_replay_default_days_and_configurable_switch(monkeypatch):
    assert DEFAULT_5Y_DAYS == 1825

    monkeypatch.setenv("DAEMONBLACKFX_REPLAY_DAYS", "1000")
    runner = MultiStrategy5YReplayRunner(days=int(os.getenv("DAEMONBLACKFX_REPLAY_DAYS", "1825")))
    assert runner.days == 1000

    runner_default = MultiStrategy5YReplayRunner()
    assert runner_default.days == 1825


def test_5y_replay_universe_covers_all_instruments():
    # Covers synthetics, forex, metals, crypto, indices, commodities
    assert len(CATALOG_ALL_INSTRUMENTS["SYNTHETICS"]) >= 38
    assert len(CATALOG_ALL_INSTRUMENTS["FOREX"]) >= 24
    assert "XAUUSD" in CATALOG_ALL_INSTRUMENTS["METALS"]
    assert "BTCUSD" in CATALOG_ALL_INSTRUMENTS["CRYPTO"]
    assert "Wall Street 30" in CATALOG_ALL_INSTRUMENTS["INDICES"]
    assert "US Oil" in CATALOG_ALL_INSTRUMENTS["COMMODITIES"]

    assert len(ALL_SYMBOLS_FLAT) >= 73


def test_5y_replay_supports_all_four_official_strategies():
    expected_strats = {"MALAYSIAN_SNR", "ORB", "ICT", "TREND_PULLBACK"}
    assert set(STRATEGIES) == expected_strats


def test_dual_leg_contract_simulation_tp1_then_be():
    # BUY @ 100, SL @ 90 (risk = 10), TP1 = 110, TP2 = 120
    # Bar 1 reaches 112 (TP1 touched), Bar 2 drops to 100 (BE hit)
    highs = np.array([112.0, 105.0])
    lows = np.array([98.0, 99.5])
    r, reason, bars = simulate_blackdaemon_dual_leg("BUY", 100.0, 90.0, highs, lows, spread=0.0)
    assert r == 0.50
    assert reason == "BE_OR_TRAILING_EXIT"


def test_dual_leg_contract_simulation_tp2_reached():
    # BUY @ 100, SL @ 90, reaches 125 (TP2 reached -> trailing stop at 110 -> closes above BE)
    highs = np.array([112.0, 125.0, 122.0])
    lows = np.array([98.0, 105.0, 108.0])
    r, reason, bars = simulate_blackdaemon_dual_leg("BUY", 100.0, 90.0, highs, lows, spread=0.0)
    assert r >= 1.0  # At least +1.0R total profit
    assert reason == "BE_OR_TRAILING_EXIT"


def test_dual_leg_contract_simulation_initial_sl():
    # BUY @ 100, SL @ 90, Bar 1 drops to 89
    highs = np.array([102.0])
    lows = np.array([89.0])
    r, reason, bars = simulate_blackdaemon_dual_leg("BUY", 100.0, 90.0, highs, lows, spread=0.0)
    assert r == -1.0
    assert reason == "INITIAL_SL"


def test_5y_replay_runner_execution_on_complete_universe(tmp_path):
    runner = MultiStrategy5YReplayRunner(
        days=1825,
        strategies=["MALAYSIAN_SNR", "ORB", "ICT", "TREND_PULLBACK"],
        data_cache_dir=tmp_path,
    )
    runner.output_dir = tmp_path
    summary = runner.run_replay()

    assert summary["days"] == 1825
    assert len(summary["strategies_evaluated"]) == 4
    # 4 strategies * 73 symbols = 292 evaluations
    assert summary["total_evaluations"] >= 292
    assert Path(summary["summary_path"]).exists()


def test_strategy_bases_ui_reflects_5y_replay_horizon():
    assert "Replay Histórico 5 Años" in STRATEGY_BASES_HTML
    assert "5 años en el pasado" in STRATEGY_BASES_HTML
