"""Workers sin ventaja desactivados para entradas nuevas por configuración (24-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine

DEFAULT = ("FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "ICT", "GOLD", "IDX_OPEN")


def _cfg_in_clean_env(value=None):
    env = {k: v for k, v in os.environ.items() if k != "DAEMONBLACKFX_DISABLED_WORKERS"}
    if value is not None:
        env["DAEMONBLACKFX_DISABLED_WORKERS"] = value
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(','.join(C().disabled_entry_profiles))"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.returncode == 0, out.stderr[-400:]
    return out.stdout.strip()


def test_default_disables_workers_without_edge():
    assert _cfg_in_clean_env() == ",".join(DEFAULT)


def test_env_can_reactivate_all_or_some():
    assert _cfg_in_clean_env("") == ""
    assert _cfg_in_clean_env("forex_3, gold") == "FOREX_3,GOLD"


def _engine(profile, disabled):
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source="DEMO", disabled_entry_profiles=disabled)
    e.provider = SimpleNamespace(resolve_symbol=lambda s: s)
    return e


def test_disabled_worker_skips_analysis_and_entries():
    for profile in DEFAULT:
        res = _engine(profile, DEFAULT)._process_symbol_impl("EURUSD")
        assert res["action"] == "WORKER_DISABLED" and res["bot_profile"] == profile


def test_other_workers_not_affected():
    e = _engine("RSI2", DEFAULT)
    called = []
    e._process_symbol_guarded = lambda *a, **k: called.append(a) or {"action": "WAITING"}
    e.config.execution_enabled = False
    assert e._process_symbol_impl("US SP 500")["action"] == "WAITING" and called
