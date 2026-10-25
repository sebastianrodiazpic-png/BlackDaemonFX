"""Escenario MSNR H4→H1 en prueba demo (20-oct-2026).

Replay fiel 2 años, 37 sintéticos: +0,029 R/t (con la política de dirección +0,017), ambos años positivos.
"""
import os
import subprocess
import sys
from types import SimpleNamespace

import pandas as pd

from strategy.malaysian_snr.h4h1_confirmation import (H4H1_CONFIRMATION, H4H1_SCENARIO, H4H1_STRATEGY_VERSION,
                                                      detect_h4h1, line_levels, open_close_break)

T0 = pd.Timestamp("2026-10-01T00:00:00Z")


def _h4():
    closes = [100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100, 99, 106]
    rows = []
    for i, c in enumerate(closes):
        o = closes[i - 1] if i else c
        rows.append({"time": T0 + pd.Timedelta(hours=4 * i), "open": o, "close": c,
                     "high": max(o, c) + 0.2, "low": min(o, c) - 0.2})
    rows[-1].update(open=105, close=106, high=111, low=104.5)  # rechazo del nivel 110 (venta)
    return pd.DataFrame(rows)


def _h1(break_bar=True):
    close_k = T0 + pd.Timedelta(hours=4 * 13)
    rows = []
    for i in range(35):
        if i <= 30:
            o, c = (101.2, 100.8) if i % 2 == 0 else (100.8, 101.2)
        elif i in (31, 32):
            o, c = (100.0, 101.0) if i == 31 else (101.0, 102.0)
        elif i == 33:
            o, c = 102.0, 101.5
        else:
            o, c = (101.8, 100.5) if break_bar else (101.8, 101.4)
        rows.append({"time": close_k - pd.Timedelta(hours=34 - i), "open": o, "close": c,
                     "high": max(o, c) + 0.25, "low": min(o, c) - 0.25})
    return pd.DataFrame(rows)


def _now(h1):
    return h1.time.iloc[-1] + pd.Timedelta(hours=1, seconds=1)


def test_line_levels_and_open_close_break():
    lv = line_levels(_h4(), pd.Timedelta(hours=4))
    assert (T0 + pd.Timedelta(hours=4 * 8), 110.0) in lv
    h1 = _h1()
    assert open_close_break(h1.open.to_numpy(), h1.close.to_numpy(), 34, "SELL") == 101.0
    assert open_close_break(h1.open.to_numpy(), h1.close.to_numpy(), 34, "BUY") is None


def test_detects_sell_with_stop_beyond_h4_extreme():
    h1 = _h1()
    s = detect_h4h1(_h4(), h1, _now(h1), spread=0.05)
    assert s is not None and s["direction"] == "SELL"
    assert s["h4_level"] == 110.0 and s["h1_open_close_level"] == 101.0
    assert s["stop_loss"] > 111.05 and s["entry_reference"] == 100.5
    assert s["setup_id"].startswith("H4H1|")


def test_no_signal_without_break_outside_window_or_when_too_costly():
    h1 = _h1(break_bar=False)
    assert detect_h4h1(_h4(), h1, _now(h1)) is None
    h1 = _h1()
    late = h1.time.iloc[-1] + pd.Timedelta(hours=2, seconds=1)  # ya pasó la vela H1 de entrada
    assert detect_h4h1(_h4(), h1, late) is None
    assert detect_h4h1(_h4(), h1, _now(h1), spread=1.0) is None  # spread/SL > 2 %


class _Provider:
    def __init__(self, h4, h1):
        self.frames = {"H4": h4, "H1": h1}

    def get_candles(self, symbol, timeframe, count=100):
        return self.frames[timeframe].tail(count).copy()

    def get_current_tick(self, symbol):
        return {"bid": 100.5, "ask": 100.55}


def _strategy(enabled=True):
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
    h1 = _h1()
    return MalaysianSNRStrategy(_Provider(_h4(), h1), MalaysianSNRConfig(enabled=True, enable_h4h1_confirmation=enabled,
                                                                         excluded_symbols=("Step Index",))), _now(h1)


def test_strategy_builds_contract_signal_once():
    strat, now = _strategy()
    res = strat._h4h1_signal("Volatility 10 Index", now.to_pydatetime())
    sig = res["signal"]
    assert res["valid"] and sig["scenario"] == H4H1_SCENARIO and sig["strategy_version"] == H4H1_STRATEGY_VERSION
    assert sig["entry_confirmation"] == H4H1_CONFIRMATION and sig["direction"] == "SELL"
    risk = sig["stop_loss"] - sig["entry_price"]
    assert abs((sig["entry_price"] - sig["tp1_price"]) - risk) < 1e-4  # TP1 = 1R
    assert abs((sig["entry_price"] - sig["tp2_price"]) - 2 * risk) < 1e-4 and sig["runner_rr"] == 2.0
    assert strat._h4h1_signal("Volatility 10 Index", now.to_pydatetime()) is None  # misma configuración: una vez


def test_strategy_skips_real_markets_and_pruned():
    strat, now = _strategy()
    assert strat._h4h1_signal("EURUSD", now.to_pydatetime()) is None
    assert strat._h4h1_signal("Step Index", now.to_pydatetime()) is None


# ----------------------------------------------------------------------------- motor
def _engine(mode="demo_test", source="DEMO", results=None):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", source=source, msnr_h4h1_mode=mode)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.repository = SimpleNamespace(closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []))
    return e


SIG = {"scenario": H4H1_SCENARIO, "entry_confirmation": H4H1_CONFIRMATION, "adx": 30}


def test_modes_and_defaults():
    from strategy.execution.live_trading_engine import LiveTradingConfig
    cfg = LiveTradingConfig()
    # 20-oct-2026: el escenario vive en el worker MSNR; en Malaysian SNR queda apagado por defecto (sin duplicar).
    assert cfg.msnr_h4h1_mode == "off" and cfg.msnr_h4h1_review_trades == 200 and cfg.msnr_h4h1_min_r == 0.0
    assert _engine()._msnr_h4h1_active() and not _engine(source="LIVE")._msnr_h4h1_active()
    assert _engine(mode="live", source="LIVE")._msnr_h4h1_active() and not _engine(mode="off")._msnr_h4h1_active()


def test_gate_allows_in_test_and_blocks_when_off_or_failed():
    assert _engine()._msnr_h4h1_gate("Volatility 10 Index", dict(SIG), "MALAYSIAN_SNR") is None
    assert _engine(mode="off")._msnr_h4h1_gate("X", dict(SIG), "MALAYSIAN_SNR")["action"] == "MSNR_H4H1_DISABLED"
    failed = _engine(results=[-0.2] * 200)._msnr_h4h1_gate("X", dict(SIG), "MALAYSIAN_SNR")
    assert failed["action"] == "MSNR_H4H1_DEMO_TEST_FAILED"
    assert _engine(results=[0.1] * 200)._msnr_h4h1_status()["verdict"] == "SUPERA"
    assert _engine(results=[0.1] * 50)._msnr_h4h1_status()["verdict"] == "EN_PRUEBA"
    # otras señales MSNR no pasan por este control
    assert _engine(mode="off")._msnr_h4h1_gate("X", {"scenario": "ESC_3_QMC"}, "MALAYSIAN_SNR") is None


def test_h4h1_exempt_from_m15_regime_filter_and_step_adx():
    e = _engine()
    e.config.msnr_regime_filter_mode = "demo_test"
    e._msnr_regime_filter_status = lambda force=False: {"verdict": "EN_PRUEBA"}
    assert e._msnr_regime_filter_gate("Volatility 10 Index", dict(SIG), "MALAYSIAN_SNR") is None
    assert e._msnr_regime_filter_gate("Volatility 10 Index", {"adx": 30}, "MALAYSIAN_SNR")["action"] == "MSNR_REGIME_ADX_BLOCKED"
    assert e._step_quality_gate("Step Index 400", dict(SIG)) is None


def test_engine_wires_flag_into_msnr_config_and_env():
    code = ("from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
            "c=C(); print(c.msnr_h4h1_mode, c.msnr_h4h1_review_trades)")
    env = {**os.environ, "DAEMONBLACKFX_MSNR_H4H1": "off", "DAEMONBLACKFX_MSNR_H4H1_REVIEW_TRADES": "300"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.split() == ["off", "300"], out.stderr
    from strategy.execution import live_trading_engine as eng
    src = open(eng.__file__, encoding="utf-8").read()
    assert "enable_h4h1_confirmation=self._msnr_h4h1_active()" in src
