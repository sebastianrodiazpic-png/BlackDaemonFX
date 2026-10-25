"""Worker NIGHT: sesgo nocturno en US SP 500 / US Tech 100 en prueba demo (21-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

from strategy.overnight.overnight_drift import (OVERNIGHT_STRATEGY, OVERNIGHT_VERSION, OvernightDriftStrategy, daily_atr,
                                                exit_time_for_entry, in_entry_window)

# 21-oct-2026 es martes; NY en horario de verano (UTC-4): 16:00 NY = 20:00 UTC.
TUE_1605_NY = pd.Timestamp("2026-10-21T20:05:00Z")


def _d1(n=30, start="2026-09-01"):
    t = pd.date_range(start, periods=n, freq="1D", tz="UTC")
    c = np.linspace(6000, 6100, n)
    return pd.DataFrame({"time": t, "open": c - 5, "high": c + 30, "low": c - 30, "close": c})


class _Provider:
    def __init__(self, ask=6100.0):
        self.ask = ask

    def get_candles(self, symbol, timeframe, count=40):
        return _d1()

    def get_current_tick(self, symbol):
        return {"bid": self.ask - 0.5, "ask": self.ask}


def test_entry_window_and_exit_time_respect_ny_sessions():
    assert in_entry_window(TUE_1605_NY)
    assert not in_entry_window(pd.Timestamp("2026-10-21T19:55:00Z"))   # 15:55 NY
    assert not in_entry_window(pd.Timestamp("2026-10-21T20:16:00Z"))   # 16:16 NY
    assert not in_entry_window(pd.Timestamp("2026-10-24T20:05:00Z"))   # sábado
    assert exit_time_for_entry(TUE_1605_NY) == pd.Timestamp("2026-10-22T13:30:00Z")  # miércoles 09:30 NY
    friday = pd.Timestamp("2026-10-23T20:05:00Z")
    assert exit_time_for_entry(friday) == pd.Timestamp("2026-10-26T13:30:00Z")  # lunes 09:30 NY
    winter = pd.Timestamp("2026-12-01T21:05:00Z")  # 16:05 NY en invierno (UTC-5)
    assert in_entry_window(winter) and exit_time_for_entry(winter) == pd.Timestamp("2026-12-02T14:30:00Z")


def test_daily_atr_uses_only_closed_days():
    d1 = _d1()
    atr = daily_atr(d1, pd.Timestamp("2026-09-25T20:00:00Z"))
    assert atr is not None and 59 <= atr <= 61  # rango diario 60
    assert daily_atr(d1.head(5), TUE_1605_NY) is None


def test_signal_buy_with_atr_stop_far_target_and_time_exit():
    res = OvernightDriftStrategy(_Provider()).analyze_symbol("US SP 500", TUE_1605_NY.to_pydatetime())
    sig = res["signal"]
    assert res["valid"] and res["strategy_name"] == OVERNIGHT_STRATEGY and sig["strategy_version"] == OVERNIGHT_VERSION
    assert sig["direction"] == "BUY" and sig["split_execution"] is False
    risk = sig["entry_price"] - sig["stop_loss"]
    assert 59 <= risk <= 61                                    # 1 × ATR D1
    assert abs(sig["take_profit"] - (sig["entry_price"] + 20 * risk)) < 1e-3  # sin objetivo real
    assert sig["time_exit_at"] == "2026-10-22T13:30:00+00:00"


def test_signal_scope():
    strat = OvernightDriftStrategy(_Provider())
    assert strat.analyze_symbol("Wall Street 30", TUE_1605_NY.to_pydatetime())["reason"] == "OVERNIGHT_SYMBOL_NOT_ALLOWED"
    assert strat.analyze_symbol("US Tech 100", pd.Timestamp("2026-10-21T15:00:00Z").to_pydatetime())["reason"] == "OUTSIDE_NY_CLOSE_ENTRY_WINDOW"


# ----------------------------------------------------------------------------- motor
def _engine(mode="demo_test", source="DEMO", results=None, profile="NIGHT", open_trades=None, closer=None):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    cfg = LiveTradingConfig(bot_profile=profile, source=source, overnight_mode=mode, execution_enabled=True)
    e.config = cfg
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.repository = SimpleNamespace(
        closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []),
        open_trades=lambda source=None: list(open_trades or []))
    e._trade_owned_by_current_bot = lambda trade: True
    e.lifecycle_manager = SimpleNamespace(trade_executor=SimpleNamespace(close_position=closer or (lambda **k: {"closed": True})))
    return e


def test_night_profile_single_entry_without_be_or_extension():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    src = open(sys.modules[LiveTradingEngine.__module__].__file__, encoding="utf-8").read()
    assert 'if str(getattr(self.config, "bot_profile", "") or "").upper() == "NIGHT":' in src
    assert "self.config.split_entries_enabled = False" in src and "self.config.break_even_enabled = False" in src
    cfg = LiveTradingConfig()
    assert (cfg.overnight_mode, cfg.overnight_review_trades, cfg.overnight_min_r) == ("demo_test", 120, 0.0)


def test_overnight_gate_and_criterion():
    sig = {"scenario": "NY_CLOSE_TO_OPEN"}
    assert _engine()._overnight_gate("US SP 500", dict(sig), "OVERNIGHT_DRIFT") is None
    assert _engine(source="LIVE")._overnight_gate("US SP 500", dict(sig), "OVERNIGHT_DRIFT")["action"] == "OVERNIGHT_DISABLED"
    assert _engine(results=[-0.1] * 120)._overnight_gate("X", dict(sig), "OVERNIGHT_DRIFT")["action"] == "OVERNIGHT_DEMO_TEST_FAILED"
    assert _engine(results=[0.05] * 120)._overnight_status()["verdict"] == "SUPERA"
    assert _engine(mode="off")._overnight_gate("X", dict(sig), "ICT_SABRI_MALLE") is None


def test_time_exit_closes_only_due_night_positions():
    closed = []
    trades = [{"broker_position_ticket": "1", "instrument": "US SP 500", "entry_time": "2026-10-21 20:05:00"},
              {"broker_position_ticket": "2", "instrument": "US Tech 100", "entry_time": "2026-10-22 20:05:00"}]
    e = _engine(open_trades=trades, closer=lambda **k: closed.append(k["position_ticket"]) or {"closed": True})
    out = e._close_overnight_positions_at_open(now=pd.Timestamp("2026-10-22T13:31:00Z"))
    assert closed == ["1"] and out["closed"] == 1
    assert ("OVERNIGHT_TIME_EXIT", "CLOSED") in e.events
    # otros workers no cierran por tiempo
    assert _engine(profile="ICT", open_trades=trades)._close_overnight_positions_at_open()["checked"] == 0


def test_regime_sentinel_observe_only_for_night():
    assert _engine()._market_regime_observe_only("US SP 500") is True
    assert _engine(profile="ICT")._market_regime_observe_only("US SP 500") is False


def test_worker_wiring_profile_tab_and_repository(tmp_path):
    import app.main as m
    from dashboard import realtime_dashboard as rd
    from database.repository import TradingRepository
    spec = m.BOT_PROFILES["NIGHT"]
    assert spec["mode"] == "night-daemon" and spec["magic"] == 26082034 and spec["symbols"] == ["US SP 500", "US Tech 100"]
    assert "NIGHT" in m.FULL_MULTI_BOT_PROFILES and m._selection_profile_for_bot("NIGHT") == "NIGHT"
    assert rd._selection_profile_for_category("night_indices") == "NIGHT" and 'data-profile="NIGHT"' in rd._INSTRUMENTS_HTML
    assert rd.DEFAULT_PRIORITIZED_SYMBOLS["NIGHT"] == ["US SP 500", "US Tech 100"]
    repo = TradingRepository(tmp_path / "n.sqlite")
    repo.save_instrument_selection_profile(["US SP 500"], selection_profile="NIGHT", source="DEMO")
    assert repo.latest_instrument_selection_profile("NIGHT", source="DEMO")["selected_symbols"] == ["US SP 500"]


def test_env_switches_mode():
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().overnight_mode)"
    env = {**os.environ, "DAEMONBLACKFX_OVERNIGHT": "off"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "off", out.stderr
