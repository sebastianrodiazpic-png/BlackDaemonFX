"""Los workers no escanean instrumentos en PODA PREVENTIVA aunque la selección guardada los incluya (24-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _engine(profile, selected, enabled=True):
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source="DEMO", policy_cycle_filter=enabled)
    e.repository = SimpleNamespace(latest_instrument_selection_profile=lambda p, source=None: {"selected_symbols": selected})
    e.dashboard_service = None
    return e


def test_pruned_symbols_are_not_scanned():
    base = ["Crash 1000 Index", "Crash 300 Index", "Crash 500 Index"]
    assert _engine("CRASH", base)._selected_base_cycle_symbols(base) == ["Crash 300 Index", "Crash 500 Index"]
    base = ["Volatility 10 Index", "Volatility 90 (1s) Index", "High Frequency Vol 50 Index"]
    assert _engine("VOLATILITY_1", base)._selected_base_cycle_symbols(base) == ["Volatility 10 Index"]


def test_msnr_scans_only_its_synthetics_and_forex_only_active_pairs():
    base = ["Volatility 25 Index", "Boom 1000 Index", "US SP 500"]
    assert _engine("MALAYSIAN_SNR", base)._selected_base_cycle_symbols(base) == ["Volatility 25 Index"]
    base = ["GBPUSD", "EURUSD", "AUDCAD"]
    assert _engine("FOREX_1", base)._selected_base_cycle_symbols(base) == ["GBPUSD"]
    assert _engine("FOREX_2", base)._selected_base_cycle_symbols(base) == ["EURUSD", "AUDCAD"]


def test_profiles_outside_policy_and_switch_off_keep_selection():
    base = ["US SP 500", "US Tech 100"]
    assert _engine("FLIP", base)._selected_base_cycle_symbols(base) == base
    base = ["Step Index", "Step Index 200"]
    assert _engine("STEP", base, enabled=False)._selected_base_cycle_symbols(base) == base


def test_env_switch():
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().policy_cycle_filter)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={**os.environ, "DAEMONBLACKFX_POLICY_CYCLE_FILTER": "0"}, cwd=os.getcwd())
    assert out.stdout.strip() == "False", out.stderr
