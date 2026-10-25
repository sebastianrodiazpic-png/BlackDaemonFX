"""Poda de sintéticos con acierto <= 45% en el replay fiel (ICT y MSNR), configurable."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from config.strategy_config import ICT_WR45_PRUNED, MSNR_WR45_PRUNED, PRUNED_ASSET_UNIVERSE
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy

ROOT = Path(__file__).resolve().parents[1]


def test_pruned_sets():
    from config.synth_wr45 import REAL_SPREAD_PRUNED  # 23-oct-2026: poda por spread real, sumada a ambas listas
    assert set(ICT_WR45_PRUNED) == {"Boom 300 Index", "Crash 1000 Index", "Vol over Boom 550", "Volatility 90 (1s) Index"} | set(REAL_SPREAD_PRUNED)
    assert set(MSNR_WR45_PRUNED) == {"Step Index", "Volatility 100 Index", "Jump 50 Index", "Crash 300 Index",
                                     "Crash 600 Index", "Boom 1000 Index", "Volatility 90 (1s) Index"} | set(REAL_SPREAD_PRUNED)


def test_ict_pruned_everywhere():
    c = LiveTradingConfig()
    workers = set(c.boom_allowed_symbols) | set(c.crash_allowed_symbols) | set(c.volatility_allowed_symbols)
    universe = {s for k in ("STEP", "JUMP", "VOLATILITY", "BOOM", "CRASH", "ICT") for s in PRUNED_ASSET_UNIVERSE[k]}
    assert not set(ICT_WR45_PRUNED) & workers
    assert not set(ICT_WR45_PRUNED) & universe
    from dashboard.realtime_dashboard import DEFAULT_PRIORITIZED_SYMBOLS, ICT_PRUNED_INFO, PRUNED_INSTRUMENTS_INFO
    assert not set(ICT_WR45_PRUNED) & set(DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"])
    assert set(ICT_WR45_PRUNED) <= set(PRUNED_INSTRUMENTS_INFO) and set(ICT_WR45_PRUNED) <= set(ICT_PRUNED_INFO)


@pytest.mark.parametrize("symbol,pruned", [("Boom 300 Index", True), ("Crash 1000 Index", True),
                                           ("Boom 500 Index", False), ("Volatility 10 Index", False)])
def test_ict_strategy_rejects_pruned(symbol, pruned):
    provider = SimpleNamespace(get_candles=lambda *a, **k: None)
    res = ICTSabriMalleStrategy(provider, ICTSabriMalleConfig()).analyze_symbol(symbol)
    assert (res.get("reason") == "ICT_SYMBOL_PRUNED_WINRATE_LE_45") is pruned


def test_msnr_pruned_everywhere():
    engine = LiveTradingEngine(provider=SimpleNamespace(), repository=SimpleNamespace(), executor=SimpleNamespace(),
                               config=LiveTradingConfig(bot_profile="MALAYSIAN_SNR"))
    assert set(engine.malaysian_snr_strategy.config.excluded_symbols) == set(MSNR_WR45_PRUNED)
    from app.main import BOT_PROFILES
    spec = BOT_PROFILES["MALAYSIAN_SNR"]
    assert not set(MSNR_WR45_PRUNED) & set(spec["symbols"]) and set(MSNR_WR45_PRUNED) <= set(spec["pruned_symbols"])
    from dashboard.realtime_dashboard import DEFAULT_PRIORITIZED_SYMBOLS, MALAYSIAN_SNR_PRUNED_INFO
    assert not set(MSNR_WR45_PRUNED) & set(DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"])
    assert set(MSNR_WR45_PRUNED) <= set(MALAYSIAN_SNR_PRUNED_INFO)


@pytest.mark.parametrize("symbol,pruned", [("Step Index", True), ("Boom 1000 Index", True), ("Jump 75 Index", False)])
def test_msnr_strategy_rejects_pruned(symbol, pruned):
    provider = SimpleNamespace(get_candles=lambda *a, **k: None)
    cfg = MalaysianSNRConfig(synthetics_only=True, allowed_symbols=(), excluded_symbols=tuple(MSNR_WR45_PRUNED))
    res = MalaysianSNRStrategy(provider, cfg).analyze_symbol(symbol)
    assert (res.get("reason") == "MSNR_SYMBOL_PRUNED_WINRATE_LE_45") is pruned


def test_env_disables_prune():
    code = ("from config.strategy_config import ICT_WR45_PRUNED as a, MSNR_WR45_PRUNED as b;"
            "from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
            "print(len(a), len(b), 'Boom 300 Index' in C().boom_allowed_symbols)")
    out = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), capture_output=True, text=True, timeout=300,
                         env={**os.environ, "DAEMONBLACKFX_SYNTH_WR45_PRUNE": "0", "DAEMONBLACKFX_REAL_SPREAD_PRUNE": "0"})
    assert out.returncode == 0, out.stderr[-400:]
    assert out.stdout.strip().splitlines()[-1] == "0 0 True"
