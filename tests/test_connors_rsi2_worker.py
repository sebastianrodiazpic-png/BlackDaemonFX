"""Worker RSI2: RSI(2) diario de Connors en los 5 índices US en prueba demo (21-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

from strategy.connors_rsi2.rsi2_daily import (RSI2_DEFAULT_SYMBOLS, RSI2_STRATEGY, RSI2_VERSION, ConnorsRsi2Strategy,
                                              daily_indicators, exit_due)

SYM = "US SP 500"


def _daily(n=320, seed=2):
    """Tendencia alcista con ruido: produce retrocesos con RSI(2) < 10 sobre la SMA200."""
    rng = np.random.default_rng(seed)
    close = 5000 + np.cumsum(rng.normal(5.0, 30.0, n))
    t = pd.date_range("2025-06-01", periods=n, freq="1D", tz="UTC")
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({"time": t, "open": open_, "high": np.maximum(open_, close) + 15,
                         "low": np.minimum(open_, close) - 15, "close": close})


class _Provider:
    def __init__(self, d1, ask=6000.0):
        self.d1, self.ask = d1, ask

    def get_candles(self, symbol, timeframe, count=100):
        if timeframe == "D1":
            return self.d1.tail(count).copy()
        start = self.d1["time"].iloc[-1]
        return pd.DataFrame({"time": [start, start + pd.Timedelta(minutes=15)], "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0})

    def get_current_tick(self, symbol):
        return {"bid": self.ask - 0.3, "ask": self.ask}


def _signal_case():
    d1 = _daily()
    ind = daily_indicators(d1)
    i = int(np.flatnonzero(ind["signal"].to_numpy())[-1])
    return d1.iloc[:i + 2], ind.iloc[i]   # vela i cerrada + vela i+1 en formación


def test_rules_identical_to_preregistered_replay():
    import tools.research_index_indicators as research
    d1 = _daily()
    ref = research.daily_signals(research.daily_frame(d1))["REV_D"] != 0
    assert ref.sum() >= 3 and np.array_equal(ref, daily_indicators(d1)["signal"].to_numpy())


def test_signal_long_only_atr_stop_two_entries_and_dedupe():
    d1, row = _signal_case()
    strat = ConnorsRsi2Strategy(_Provider(d1))
    now = (d1["time"].iloc[-1] + pd.Timedelta(minutes=20)).to_pydatetime()
    res = strat.analyze_symbol(SYM, now)
    sig = res["signal"]
    assert res["valid"] and res["strategy_name"] == RSI2_STRATEGY and sig["strategy_version"] == RSI2_VERSION
    risk = 2.0 * float(row["atr"])
    assert sig["direction"] == "BUY" and sig["split_execution"] is True
    assert abs((6000.0 - sig["stop_loss"]) - risk) < 1e-3
    assert abs(sig["tp1_price"] - (6000.0 + risk)) < 1e-3 and abs(sig["tp2_price"] - (6000.0 + 2 * risk)) < 1e-3
    assert sig["tp1_rr"] == 1.0 and sig["runner_rr"] == 2.0 and sig["leg1_risk_ratio"] == 0.5
    assert sig["entry_time"] == d1["time"].iloc[-1].isoformat()
    assert strat.analyze_symbol(SYM, now)["valid"] is True  # reintento; el motor deduplica por clave de ejecución
    from strategy.connors_rsi2.rsi2_daily import Rsi2Config
    strict = ConnorsRsi2Strategy(_Provider(d1), Rsi2Config(setup_dedupe=True))
    assert strict.analyze_symbol(SYM, now)["valid"] and strict.analyze_symbol(SYM, now)["reason"] == "RSI2_SETUP_ALREADY_FIRED"


def test_entry_window_scope_and_waiting_states():
    d1, _ = _signal_case()
    strat = ConnorsRsi2Strategy(_Provider(d1))
    late = (d1["time"].iloc[-1] + pd.Timedelta(hours=3)).to_pydatetime()
    assert strat.analyze_symbol(SYM, late)["reason"] == "RSI2_ENTRY_WINDOW_EXPIRED"
    assert strat.analyze_symbol("Germany 40", late)["reason"] == "RSI2_SYMBOL_NOT_ALLOWED"
    closed_only = ConnorsRsi2Strategy(_Provider(d1.iloc[:-1]))
    at_close = (d1["time"].iloc[-1] + pd.Timedelta(minutes=5)).to_pydatetime()
    assert closed_only.analyze_symbol(SYM, at_close)["reason"] == "RSI2_WAITING_NEXT_DAILY_OPEN"
    assert set(RSI2_DEFAULT_SYMBOLS) == {"US SP 500", "US Tech 100", "Wall Street 30", "US Small Cap 2000", "US Mid Cap 400"}


def test_exit_rule_close_above_sma5_or_ten_days():
    d1 = _daily()
    ind = daily_indicators(d1)
    entry = d1["time"].iloc[250]
    above = ind.index[(ind.index >= 250) & (ind["close"] > ind["sma_exit"])][0]
    before = d1["time"].iloc[above] + pd.Timedelta(hours=12)          # vela de la regla aún abierta
    after = d1["time"].iloc[above] + pd.Timedelta(days=1, minutes=1)  # ya cerrada
    assert exit_due(d1, entry, before) != "RSI2_CLOSE_ABOVE_SMA5"  # la vela de la regla aún no ha cerrado
    assert exit_due(d1, entry, after) == "RSI2_CLOSE_ABOVE_SMA5"
    flat = d1.copy()
    flat.loc[250:, "close"] = np.linspace(flat["close"].iloc[245:250].min() - 50, flat["close"].iloc[249] - 900, len(flat) - 250)
    assert exit_due(flat, entry, flat["time"].iloc[259] + pd.Timedelta(days=1)) == "RSI2_MAX_HOLD_DAYS"


# ----------------------------------------------------------------------------- motor
def _engine(mode="demo_test", source="DEMO", results=None, profile="RSI2", open_trades=None, closer=None, provider=None):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source=source, rsi2_mode=mode, execution_enabled=True)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.repository = SimpleNamespace(
        closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []),
        open_trades=lambda source=None: list(open_trades or []))
    e._trade_owned_by_current_bot = lambda trade: True
    e.lifecycle_manager = SimpleNamespace(trade_executor=SimpleNamespace(close_position=closer or (lambda **k: {"closed": True})))
    e.provider = provider
    return e


def test_rsi2_gate_criterion_and_one_position_per_symbol():
    sig = {"scenario": "RSI2_PULLBACK_ABOVE_SMA200"}
    assert _engine()._rsi2_gate(SYM, dict(sig), "CONNORS_RSI2") is None
    assert _engine(source="LIVE")._rsi2_gate(SYM, dict(sig), "CONNORS_RSI2")["action"] == "RSI2_DISABLED"
    assert _engine(results=[-0.1] * 60)._rsi2_gate(SYM, dict(sig), "CONNORS_RSI2")["action"] == "RSI2_DEMO_TEST_FAILED"
    assert _engine(results=[0.1] * 60)._rsi2_status()["verdict"] == "SUPERA"
    assert _engine(results=[-0.1] * 59)._rsi2_status()["verdict"] == "EN_PRUEBA"
    held = _engine(open_trades=[{"instrument": SYM, "broker_position_ticket": "9"}])
    assert held._rsi2_gate(SYM, dict(sig), "CONNORS_RSI2")["action"] == "RSI2_POSITION_ALREADY_OPEN"
    assert _engine(mode="off")._rsi2_gate(SYM, dict(sig), "ICT_SABRI_MALLE") is None


def test_rule_exit_closes_only_due_rsi2_positions():
    d1 = _daily()
    ind = daily_indicators(d1)
    above = ind.index[(ind.index >= 250) & (ind["close"] > ind["sma_exit"])][0]
    now = d1["time"].iloc[above] + pd.Timedelta(days=1, minutes=1)
    closed = []
    trades = [{"broker_position_ticket": "1", "instrument": SYM, "entry_time": str(d1["time"].iloc[250])},
              {"broker_position_ticket": "2", "instrument": "US Tech 100", "entry_time": str(now)}]
    e = _engine(open_trades=trades, provider=_Provider(d1),
                closer=lambda **k: closed.append(k["position_ticket"]) or {"closed": True})
    out = e._close_rsi2_positions_on_rule(now=now)
    assert closed == ["1"] and out["closed"] == 1 and ("RSI2_RULE_EXIT", "CLOSED") in e.events
    assert _engine(profile="NIGHT", open_trades=trades)._close_rsi2_positions_on_rule(now=now)["checked"] == 0


def test_rsi2_profile_two_entries_and_config():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    src = open(sys.modules[LiveTradingEngine.__module__].__file__, encoding="utf-8").read()
    assert 'if str(getattr(self.config, "bot_profile", "") or "").upper() == "RSI2":' in src
    assert "self._close_rsi2_positions_on_rule()" in src
    assert 'elif strategy_name in {"ICT", "ICT_SABRI_MALLE", "DRIFT_BREAKOUT", "CONNORS_RSI2", "FX_CARRY"}:' in src
    assert 'if not bool(getattr(self.config, "rsi2_split", True)):' in src
    assert LiveTradingConfig().rsi2_split is True
    cfg = LiveTradingConfig()
    assert (cfg.rsi2_mode, cfg.rsi2_review_trades, cfg.rsi2_min_r) == ("demo_test", 60, 0.0)
    assert _engine()._market_regime_observe_only(SYM) is True


def test_worker_wiring_profile_tab_repository_and_tracking(tmp_path):
    import app.main as m
    from dashboard import realtime_dashboard as rd
    from database.repository import TradingRepository
    from tools.daily_tracking_report import EXPECTED, family
    spec = m.BOT_PROFILES["RSI2"]
    assert spec["mode"] == "rsi2-daemon" and spec["magic"] == 26082036 and spec["symbols"] == list(RSI2_DEFAULT_SYMBOLS)
    assert "RSI2" in m.FULL_MULTI_BOT_PROFILES and m._selection_profile_for_bot("RSI2") == "RSI2"
    assert rd._selection_profile_for_category("rsi2_us_indices") == "RSI2" and 'data-profile="RSI2"' in rd._INSTRUMENTS_HTML
    assert rd.DEFAULT_PRIORITIZED_SYMBOLS["RSI2"] == list(RSI2_DEFAULT_SYMBOLS)
    repo = TradingRepository(tmp_path / "r.sqlite")
    repo.save_instrument_selection_profile([SYM], selection_profile="RSI2", source="DEMO")
    assert repo.latest_instrument_selection_profile("RSI2", source="DEMO")["selected_symbols"] == [SYM]
    assert family(RSI2_VERSION, SYM) == "RSI(2) EE. UU." and "RSI(2) EE. UU." in EXPECTED


def test_env_switches_mode():
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().rsi2_mode)"
    env = {**os.environ, "DAEMONBLACKFX_RSI2": "off"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "off", out.stderr


def test_single_position_fallback_by_env():
    code = ("from strategy.connors_rsi2.rsi2_daily import Rsi2Config as R; "
            "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(R().split_execution, C().rsi2_split)")
    env = {**os.environ, "DAEMONBLACKFX_RSI2_SPLIT": "0"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "False False", out.stderr
