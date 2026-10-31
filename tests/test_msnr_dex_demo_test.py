"""DEX 1500 UP Index en Malaysian SNR en prueba demo con criterio fijado (20-oct-2026).

Replay 2 años: n=210, +0,299 R/t, t=4,1 (supera la corrección por 45 pruebas), y0 +0,241 / y1 +0,398.
"""
import os
import subprocess
import sys
from types import SimpleNamespace

DEX = "DEX 1500 UP Index"


def _policy_in_subprocess(**env_overrides):
    code = ("from config.ict_instrument_policy import ict_active_symbols as a, preventive_prune_reason as r;"
            "print('DEX 1500 UP Index' in a('MALAYSIAN_SNR')); print(r('DEX 1500 UP Index','MALAYSIAN_SNR'))")
    env = {**os.environ, **env_overrides}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd(),
                         encoding="utf-8")
    return out.stdout.strip().splitlines(), out.stderr


def test_dex_pruned_by_acierto47_and_never_in_msnr():
    """25-oct-2026: Malaysian SNR solo con acierto > 47 %; DEX 1500 UP no llega y queda podado."""
    from config.ict_instrument_policy import (MSNR_DEMO_TEST_SYMBOLS, ict_active_symbols, preventive_prune_reason,
                                              sanitize_ict_selection)
    assert MSNR_DEMO_TEST_SYMBOLS == (DEX,)
    assert DEX not in ict_active_symbols("MALAYSIAN_SNR")
    assert sanitize_ict_selection("MALAYSIAN_SNR", [DEX]) == []
    assert "acierto <= 47" in preventive_prune_reason(DEX, "MALAYSIAN_SNR")


def test_bot_profiles_and_strategy_recognize_dex():
    import app.main as m
    from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol
    assert DEX not in m.BOT_PROFILES["MALAYSIAN_SNR"]["symbols"]
    assert DEX in m.BOT_PROFILES["MALAYSIAN_SNR"]["pruned_symbols"]
    assert is_synthetic_symbol(DEX)


def test_env_switches_for_dex():
    lines, err = _policy_in_subprocess(DAEMONBLACKFX_MSNR_ACIERTO47="off")
    assert lines[0] == "True", err  # sin la lista > 47 % vuelve la prueba demo de DEX
    lines, err = _policy_in_subprocess(DAEMONBLACKFX_MSNR_ACIERTO47="off", DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS="off")
    assert lines[0] == "False" and "prueba demo desactivada" in lines[1], err
    lines, err = _policy_in_subprocess(DAEMONBLACKFX_MSNR_SYNTHETICS_ACTIVE="DEX 1500 UP Index,Jump 25 Index")
    assert lines[0] == "True", err  # lista explícita por variable de entorno


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
