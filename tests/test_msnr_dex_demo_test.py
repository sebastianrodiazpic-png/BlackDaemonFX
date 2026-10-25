"""DEX 1500 UP Index en Malaysian SNR en prueba demo con criterio fijado (20-oct-2026).

Replay 2 años: n=210, +0,299 R/t, t=4,1 (supera la corrección por 45 pruebas), y0 +0,241 / y1 +0,398.
"""
import os
import subprocess
import sys
from types import SimpleNamespace

DEX = "DEX 1500 UP Index"


def test_dex_active_only_in_malaysian_snr():
    from config.ict_instrument_policy import (MSNR_DEMO_TEST_SYMBOLS, ict_active_symbols, preventive_prune_reason,
                                              sanitize_ict_selection)
    assert MSNR_DEMO_TEST_SYMBOLS == (DEX,)
    assert DEX in ict_active_symbols("MALAYSIAN_SNR") and DEX not in ict_active_symbols("MSNR")
    assert sanitize_ict_selection("MALAYSIAN_SNR", [DEX]) == [DEX]
    assert sanitize_ict_selection("MSNR", [DEX]) == []
    assert "prueba demo solo para Malaysian SNR" in preventive_prune_reason(DEX, "MSNR")


def test_bot_profiles_and_strategy_recognize_dex():
    import app.main as m
    from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol
    assert DEX in m.BOT_PROFILES["MALAYSIAN_SNR"]["symbols"] and DEX not in m.BOT_PROFILES["MSNR"]["symbols"]
    assert is_synthetic_symbol(DEX)


def test_env_switch_removes_dex():
    code = ("from config.ict_instrument_policy import ict_active_symbols as a, preventive_prune_reason as r;"
            "print('DEX 1500 UP Index' in a('MALAYSIAN_SNR')); print(r('DEX 1500 UP Index','MALAYSIAN_SNR'))")
    env = {**os.environ, "DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS": "off"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd(),
                         encoding="utf-8")
    lines = out.stdout.strip().splitlines()
    assert lines[0] == "False" and "prueba demo desactivada" in lines[1], out.stderr


def _engine(results=None, source="DEMO"):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", source=source)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.calls = []

    def reader(inst, strategy_version, source, since=None):
        e.calls.append((inst, strategy_version, source))
        return list(results or [])

    e.repository = SimpleNamespace(closed_operations_r=reader)
    e.malaysian_snr_strategy = SimpleNamespace(config=SimpleNamespace(strategy_version="msnr-v3.1-synthetics"))
    return e


def test_defaults_and_gate_during_test():
    from strategy.execution.live_trading_engine import LiveTradingConfig
    cfg = LiveTradingConfig()
    assert (cfg.msnr_symbol_test_review_trades, cfg.msnr_symbol_test_min_r) == (40, 0.0)
    e = _engine(results=[1.0] * 5)
    sig = {}
    assert e._msnr_symbol_test_gate(DEX, sig, "MALAYSIAN_SNR") is None
    assert sig["msnr_symbol_demo_test"]["verdict"] == "EN_PRUEBA"
    assert e.calls[0] == (DEX, "msnr-v3.1-synthetics", "DEMO")  # solo las operaciones MSNR de DEX


def test_criterion_supera_and_no_supera():
    assert _engine(results=[0.2] * 40)._msnr_symbol_test_status(DEX)["verdict"] == "SUPERA"
    failed = _engine(results=[-0.1] * 40)._msnr_symbol_test_gate(DEX, {}, "MALAYSIAN_SNR")
    assert failed["action"] == "MSNR_SYMBOL_DEMO_TEST_FAILED"


def test_scope_other_symbols_strategies_and_live():
    e = _engine(results=[-1.0] * 40)
    assert e._msnr_symbol_test_gate("Jump 25 Index", {}, "MALAYSIAN_SNR") is None
    assert e._msnr_symbol_test_gate(DEX, {}, "ICT_SABRI_MALLE") is None
    assert _engine(source="LIVE")._msnr_symbol_test_gate(DEX, {}, "MALAYSIAN_SNR")["action"] == "MSNR_SYMBOL_DEMO_TEST_ONLY"
