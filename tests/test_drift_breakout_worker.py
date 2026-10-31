"""Worker DRIFT: ruptura tras compresión en Drift Switch Index 10/20/30 en prueba demo (21-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

from strategy.drift_breakout.compression_breakout import (DRIFT_DEFAULT_SYMBOLS, DRIFT_STRATEGY, DRIFT_VERSION,
                                                          DriftBreakoutStrategy, breakout_frame)

SYM = "Drift Switch Index 20"


def _market(n=3000, seed=3):
    """Paseo aleatorio M15 con tramos de compresión y H1 agregada de esas mismas velas."""
    rng = np.random.default_rng(seed)
    vol = np.where((np.arange(n) // 150) % 2 == 0, 0.4, 2.0)
    close = 3000 + np.cumsum(rng.normal(0, vol))
    t = pd.date_range("2026-08-01", periods=n, freq="15min", tz="UTC")
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0, vol)) + 0.05
    m15 = pd.DataFrame({"time": t, "open": open_, "high": np.maximum(open_, close) + spread,
                        "low": np.minimum(open_, close) - spread, "close": close, "spread": 50})
    h1 = (m15.set_index("time").resample("1h")
          .agg({"open": "first", "high": "max", "low": "min", "close": "last", "spread": "last"}).reset_index())
    return m15, h1


class _Provider:
    def __init__(self, m15, h1, bid=3000.0, ask=3000.5):
        self.m15, self.h1, self.bid, self.ask = m15, h1, bid, ask

    def get_candles(self, symbol, timeframe, count=100):
        return (self.m15 if timeframe == "M15" else self.h1).tail(count).copy()

    def get_current_tick(self, symbol):
        return {"bid": self.bid, "ask": self.ask}


def _first_signal():
    m15, h1 = _market()
    f = breakout_frame(m15, h1)
    idx = [i for i in np.flatnonzero(f["side"].to_numpy() != 0) if i > 600]
    assert idx, "el mercado sintético del test debe producir rupturas"
    i = idx[0]
    close_t = f["close_time"].iloc[i]
    return m15.iloc[:i + 1], h1[h1["time"] + pd.Timedelta(hours=1) <= close_t], int(f["side"].iloc[i]), close_t, f.iloc[i]


def test_rules_identical_to_preregistered_replay():
    import tools.research_synthetic_indicators as research
    m15, h1 = _market()
    ref = research.signals(research.features(m15, h1).reset_index(drop=True))["C_RUPTURA"]
    live = breakout_frame(m15, h1)["side"].to_numpy()
    assert (ref != 0).sum() >= 5 and np.array_equal(ref, live)


def test_signal_geometry_contract_and_dedupe():
    m15, h1, side, close_t, row = _first_signal()
    strat = DriftBreakoutStrategy(_Provider(m15, h1))
    now = (close_t + pd.Timedelta(minutes=1)).to_pydatetime()
    res = strat.analyze_symbol(SYM, now)
    sig = res["signal"]
    assert res["valid"] and res["strategy_name"] == DRIFT_STRATEGY and sig["strategy_version"] == DRIFT_VERSION
    assert sig["direction"] == ("BUY" if side > 0 else "SELL")
    entry = 3000.5 if side > 0 else 3000.0
    risk = 1.5 * float(row["h_atr"])
    assert abs(sig["entry_price"] - entry) < 1e-6 and abs(side * (entry - sig["stop_loss"]) - risk) < 1e-3
    assert abs(sig["tp1_price"] - (entry + side * risk)) < 1e-3 and abs(sig["tp2_price"] - (entry + 2 * side * risk)) < 1e-3
    assert sig["split_execution"] is True and sig["tp1_rr"] == 1.0 and sig["runner_rr"] == 2.0
    assert sig["entry_time"] == close_t.isoformat()
    # sin marcado en la estrategia: si el motor la bloqueó por algo pasajero, se reintenta (el motor deduplica)
    assert strat.analyze_symbol(SYM, now)["valid"] is True
    from strategy.drift_breakout.compression_breakout import DriftBreakoutConfig
    strict = DriftBreakoutStrategy(_Provider(m15, h1), DriftBreakoutConfig(setup_dedupe=True))
    assert strict.analyze_symbol(SYM, now)["valid"] and strict.analyze_symbol(SYM, now)["reason"] == "DRIFT_SETUP_ALREADY_FIRED"


def test_scope_and_stale_signal():
    m15, h1, _, close_t, _ = _first_signal()
    strat = DriftBreakoutStrategy(_Provider(m15, h1))
    assert strat.analyze_symbol("Volatility 75 Index", close_t.to_pydatetime())["reason"] == "DRIFT_SYMBOL_NOT_ALLOWED"
    late = (close_t + pd.Timedelta(minutes=14)).to_pydatetime()
    assert strat.analyze_symbol(SYM, late)["reason"] == "DRIFT_SIGNAL_STALE"
    assert set(DRIFT_DEFAULT_SYMBOLS) == {"Drift Switch Index 10", "Drift Switch Index 20", "Drift Switch Index 30"}


# ----------------------------------------------------------------------------- motor
def _engine(mode="demo_test", source="DEMO", results=None, profile="DRIFT"):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source=source, drift_mode=mode)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.repository = SimpleNamespace(
        closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []))
    return e


def test_drift_gate_and_fixed_criterion():
    sig = {"scenario": "BB_SQUEEZE_DONCHIAN_BREAKOUT"}
    assert _engine()._drift_gate(SYM, dict(sig), "DRIFT_BREAKOUT") is None
    assert _engine(source="LIVE")._drift_gate(SYM, dict(sig), "DRIFT_BREAKOUT")["action"] == "DRIFT_DISABLED"
    assert _engine(source="LIVE", mode="live")._drift_gate(SYM, dict(sig), "DRIFT_BREAKOUT") is None
    assert _engine(results=[-0.05] * 200)._drift_gate(SYM, dict(sig), "DRIFT_BREAKOUT")["action"] == "DRIFT_DEMO_TEST_FAILED"
    assert _engine(results=[0.05] * 200)._drift_status()["verdict"] == "SUPERA"
    assert _engine(results=[-0.05] * 199)._drift_status()["verdict"] == "EN_PRUEBA"
    assert _engine(mode="off")._drift_gate(SYM, dict(sig), "ICT_SABRI_MALLE") is None


def test_drift_profile_contract_without_runner_extension():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    src = open(sys.modules[LiveTradingEngine.__module__].__file__, encoding="utf-8").read()
    assert 'if str(getattr(self.config, "bot_profile", "") or "").upper() == "DRIFT":' in src
    assert '"ICT_SABRI_MALLE", "DRIFT_BREAKOUT"' in src  # TP1/runner del propio signal
    assert 'family_gates = str(self.config.bot_profile or "").upper() != "DRIFT"' in src
    cfg = LiveTradingConfig()
    # desactivado por defecto desde el 23-oct-2026 (sin ventaja con el spread real de ticks)
    assert (cfg.drift_mode, cfg.drift_review_trades, cfg.drift_min_r, cfg.drift_runner_extension) == ("off", 200, 0.0, False)
    assert cfg.split_entries_enabled and cfg.break_even_enabled  # contrato de dos piernas con BE intacto


def test_regime_sentinel_observe_only_for_drift():
    assert _engine()._market_regime_observe_only(SYM) is True


def test_worker_wiring_profile_tab_repository_and_tracking(tmp_path):
    import app.main as m
    from dashboard import realtime_dashboard as rd
    from database.repository import TradingRepository
    from tools.daily_tracking_report import EXPECTED, family
    spec = m.BOT_PROFILES["DRIFT"]
    assert spec["mode"] == "drift-daemon" and spec["magic"] == 26082035 and spec["symbols"] == list(DRIFT_DEFAULT_SYMBOLS)
    assert "DRIFT" in m.FULL_MULTI_BOT_PROFILES and m._selection_profile_for_bot("DRIFT") == "DRIFT"
    assert rd._selection_profile_for_category("drift_switch") == "DRIFT" and 'data-profile="DRIFT"' in rd._INSTRUMENTS_HTML
    assert rd.DEFAULT_PRIORITIZED_SYMBOLS["DRIFT"] == list(DRIFT_DEFAULT_SYMBOLS)
    repo = TradingRepository(tmp_path / "d.sqlite")
    repo.save_instrument_selection_profile([SYM], selection_profile="DRIFT", source="DEMO")
    assert repo.latest_instrument_selection_profile("DRIFT", source="DEMO")["selected_symbols"] == [SYM]
    assert family(DRIFT_VERSION, SYM) == "Ruptura Drift" and "Ruptura Drift" in EXPECTED


def test_env_switches_mode():
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().drift_mode)"
    env = {**os.environ, "DAEMONBLACKFX_DRIFT": "demo_test"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "demo_test", out.stderr


def test_drift_disabled_by_default_blocks_dispatch_and_gate():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile="DRIFT", source="DEMO")
    assert e.config.drift_mode == "off" and e._drift_active() is False
    assert e._drift_gate(SYM, {}, "DRIFT_BREAKOUT")["action"] == "DRIFT_DISABLED"
