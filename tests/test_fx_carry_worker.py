"""Worker CARRY: carry en Forex G10 con el swap real de MT5 en prueba demo (24-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

from strategy.fx_carry.carry_strategy import (CARRY_DEFAULT_SYMBOLS, CARRY_STRATEGY, CARRY_VERSION, CarryConfig,
                                              FxCarryStrategy, carry_of, exit_due, month_key)

SWAPS = {  # swap en puntos (modo 1), punto y precio: AUDCHF > AUDJPY > USDCHF > EURUSD (corto) > resto
    "AUDCHF": {"swap_long": 5.0, "swap_short": -9.0, "point": 0.00001, "swap_mode": 1, "price": 0.52},
    "AUDJPY": {"swap_long": 0.9, "swap_short": -2.0, "point": 0.001, "swap_mode": 1, "price": 100.0},
    "USDCHF": {"swap_long": 6.5, "swap_short": -12.0, "point": 0.00001, "swap_mode": 1, "price": 0.80},
    "EURUSD": {"swap_long": -8.0, "swap_short": 1.0, "point": 0.00001, "swap_mode": 1, "price": 1.16},
    "EURGBP": {"swap_long": -3.0, "swap_short": -1.0, "point": 0.00001, "swap_mode": 1, "price": 0.87},
    "GBPUSD": {"swap_long": 9.0, "swap_short": -9.0, "point": 0.00001, "swap_mode": 2, "price": 1.33},
}


def _reader(symbol):
    return SWAPS.get(symbol)


class _Provider:
    def __init__(self, month_start="2026-10-01", ask=0.5201, bid=0.5200):
        start = pd.Timestamp(month_start, tz="UTC")
        self.d1 = pd.DataFrame({"time": pd.date_range(start - pd.Timedelta(days=60), periods=60, freq="1D")})
        self.d1["open"] = 0.52
        self.d1["high"] = 0.523
        self.d1["low"] = 0.517
        self.d1["close"] = 0.52
        self.m15 = pd.DataFrame({"time": pd.date_range(start - pd.Timedelta(hours=2), periods=12, freq="15min")})
        for c in ("open", "high", "low", "close"):
            self.m15[c] = 0.52
        self.ask, self.bid = ask, bid

    def get_candles(self, symbol, timeframe, count=100):
        return (self.d1 if timeframe == "D1" else self.m15).tail(count).copy()

    def get_current_tick(self, symbol):
        return {"bid": self.bid, "ask": self.ask}


def _strategy(**cfg):
    return FxCarryStrategy(_Provider(), CarryConfig(**cfg), swap_reader=_reader)


def test_carry_of_annualizes_points_and_picks_side():
    side, c = carry_of(SWAPS["AUDCHF"])
    assert side == 1 and abs(c - 5.0 * 0.00001 / 0.52 * 360) < 1e-12
    assert carry_of(SWAPS["EURUSD"])[0] == -1
    assert carry_of(SWAPS["GBPUSD"])[0] == 0  # solo se entiende el modo en puntos
    assert carry_of(None)[0] == 0


def test_ranking_top_three_positive_carry_only():
    strat = _strategy(symbols=tuple(SWAPS))
    assert [s for s, _, _ in strat.selected()] == ["AUDCHF", "USDCHF", "AUDJPY"]
    assert all(c > 0 for _, _, c in strat.selected())
    assert "EURGBP" not in [s for s, _, _ in strat.ranking()] or strat.ranking()[-1][2] < 0
    strict = _strategy(symbols=tuple(SWAPS), min_carry=0.032)
    assert [s for s, _, _ in strict.selected()] == ["AUDCHF"]


def test_signal_at_month_open_atr_stop_two_entries():
    strat = _strategy(symbols=tuple(SWAPS))
    now = pd.Timestamp("2026-10-01T06:00:00Z").to_pydatetime()
    res = strat.analyze_symbol("AUDCHF", now)
    sig = res["signal"]
    assert res["valid"] and res["strategy_name"] == CARRY_STRATEGY and sig["strategy_version"] == CARRY_VERSION
    risk = 3.0 * 0.006  # TR constante 0,006 con ATR20 simple
    assert sig["direction"] == "BUY" and abs(sig["entry_price"] - 0.5201) < 1e-9
    assert abs((sig["entry_price"] - sig["stop_loss"]) - risk) < 1e-6
    assert abs(sig["tp1_price"] - (0.5201 + risk)) < 1e-6 and abs(sig["tp2_price"] - (0.5201 + 2 * risk)) < 1e-6
    assert sig["split_execution"] is True and sig["leg1_risk_ratio"] == 0.5 and sig["leg2_risk_ratio"] == 0.5
    assert sig["entry_time"] == pd.Timestamp("2026-10-01T00:00:00Z").isoformat()
    assert sig["setup_id"] == "AUDCHF|2026-10|BUY" and sig["exit_policy"] == "CARRY_MONTHLY_REBALANCE"
    short = strat.analyze_symbol("EURUSD", now)
    assert short["reason"] == "CARRY_NOT_IN_TOP"  # EURUSD corto tiene carry positivo pero no está en el top 3


def test_waiting_states():
    strat = _strategy(symbols=tuple(SWAPS))
    assert strat.analyze_symbol("AUDCHF", pd.Timestamp("2026-10-02T01:00:00Z"))["reason"] == "CARRY_ENTRY_WINDOW_EXPIRED"
    assert strat.analyze_symbol("XAUUSD", pd.Timestamp("2026-10-01T06:00:00Z"))["reason"] == "CARRY_SYMBOL_NOT_ALLOWED"
    early = FxCarryStrategy(_Provider(month_start="2026-11-01"), CarryConfig(symbols=tuple(SWAPS)), swap_reader=_reader)
    early.provider.m15 = early.provider.m15[early.provider.m15["time"] < pd.Timestamp("2026-11-01", tz="UTC")]
    assert early.analyze_symbol("AUDCHF", pd.Timestamp("2026-11-01T00:05:00Z"))["reason"] == "CARRY_WAITING_MONTH_OPEN"
    assert len(CARRY_DEFAULT_SYMBOLS) == 28 and len(set(CARRY_DEFAULT_SYMBOLS)) == 28


def test_monthly_rebalance_exit_rule():
    assert month_key("2026-10-31T23:59:00Z") == "2026-10"
    assert exit_due("2026-10-01T00:15:00+00:00", pd.Timestamp("2026-10-31T23:00:00Z")) is None
    assert exit_due("2026-10-01T00:15:00+00:00", pd.Timestamp("2026-11-01T00:00:00Z")) == "CARRY_MONTHLY_REBALANCE"


def test_rules_match_research_replay():
    import tools.research_fx_carry_mt5 as research
    assert research.TOP_N == CarryConfig().top_n == 3 and CarryConfig().stop_atr_multiple == 3.0


# ----------------------------------------------------------------------------- motor
def _engine(mode="demo_test", source="DEMO", results=None, profile="CARRY", open_trades=None, closer=None):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source=source, carry_mode=mode, execution_enabled=True)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.repository = SimpleNamespace(
        closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []),
        open_trades=lambda source=None: list(open_trades or []))
    e._trade_owned_by_current_bot = lambda trade: True
    e.lifecycle_manager = SimpleNamespace(trade_executor=SimpleNamespace(close_position=closer or (lambda **k: {"closed": True})))
    return e


def test_carry_gate_criterion_and_one_position_per_symbol():
    sig = {"scenario": "MONTHLY_TOP_CARRY"}
    assert _engine()._carry_gate("AUDCHF", dict(sig), "FX_CARRY") is None
    assert _engine(source="LIVE")._carry_gate("AUDCHF", dict(sig), "FX_CARRY")["action"] == "CARRY_DISABLED"
    assert _engine(mode="live", source="LIVE")._carry_gate("AUDCHF", dict(sig), "FX_CARRY") is None
    assert _engine(results=[-0.1] * 36)._carry_gate("AUDCHF", dict(sig), "FX_CARRY")["action"] == "CARRY_DEMO_TEST_FAILED"
    assert _engine(results=[0.1] * 36)._carry_status()["verdict"] == "SUPERA"
    assert _engine(results=[-0.1] * 35)._carry_status()["verdict"] == "EN_PRUEBA"
    held = _engine(open_trades=[{"instrument": "AUDCHF", "broker_position_ticket": "9"}])
    assert held._carry_gate("AUDCHF", dict(sig), "FX_CARRY")["action"] == "CARRY_POSITION_ALREADY_OPEN"
    assert _engine(mode="off")._carry_gate("AUDCHF", dict(sig), "CONNORS_RSI2") is None


def test_rebalance_exit_closes_only_previous_month_positions():
    closed = []
    trades = [{"broker_position_ticket": "1", "instrument": "AUDCHF", "entry_time": "2026-10-01T00:15:00+00:00"},
              {"broker_position_ticket": "1", "instrument": "AUDCHF", "entry_time": "2026-10-01T00:15:00+00:00"},
              {"broker_position_ticket": "2", "instrument": "USDCHF", "entry_time": "2026-11-01T00:15:00+00:00"}]
    e = _engine(open_trades=trades, closer=lambda **k: closed.append(k["position_ticket"]) or {"closed": True})
    out = e._close_carry_positions_on_rebalance(now=pd.Timestamp("2026-11-01T01:00:00Z"))
    assert closed == ["1"] and out["closed"] == 1 and out["checked"] == 2
    assert ("CARRY_REBALANCE_EXIT", "CLOSED") in e.events
    assert _engine(profile="RSI2", open_trades=trades)._close_carry_positions_on_rebalance(
        now=pd.Timestamp("2026-11-01T01:00:00Z"))["checked"] == 0


def test_carry_exempt_from_forex_forced_closes_but_keeps_entry_gate():
    e = _engine(open_trades=[{"instrument": "AUDCHF", "broker_position_ticket": "1"}])
    e._forex_rollover_status = lambda: (_ for _ in ()).throw(AssertionError("CARRY no debe consultar el cierre forzado"))
    assert e._close_forex_positions_for_rollover()["checked"] == 0
    assert e._close_market_close_positions()["checked"] == 0
    from strategy.execution.live_trading_engine import LiveTradingEngine
    src = open(sys.modules[LiveTradingEngine.__module__].__file__, encoding="utf-8").read()
    gate = src[src.index("def _forex_rollover_entry_gate"):src.index("def _close_forex_positions_for_rollover")]
    assert "CARRY" not in gate  # la puerta de entrada del rollover sigue protegiendo del spread ancho


def test_carry_profile_config_and_wiring_in_engine():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    src = open(sys.modules[LiveTradingEngine.__module__].__file__, encoding="utf-8").read()
    assert 'self.config.runner_extension_enabled = bool(getattr(self.config, "carry_runner_extension", True))' in src
    assert "self._close_carry_positions_on_rebalance()" in src and src.count("_close_carry_positions_on_rebalance()") >= 2
    assert 'elif str(self.config.bot_profile or "").upper() == "CARRY":' in src
    cfg = LiveTradingConfig()
    assert (cfg.carry_mode, cfg.carry_review_trades, cfg.carry_min_r, cfg.carry_runner_extension) == ("demo_test", 36, 0.0, True)
    assert "CARRY" in cfg.priority_profiles and "CARRY" in cfg.own_symbol_limit_profiles
    assert "FX_CARRY" in LiveTradingEngine._NATIVE_META_SHADOW_STRATEGIES
    eng = _engine()
    eng.config.market_regime_ict_synthetic_mode = "OBSERVE"
    assert eng._market_regime_observe_only("AUDCHF") is True


def test_worker_wiring_profile_tab_repository_and_tracking(tmp_path):
    import app.main as m
    from dashboard import realtime_dashboard as rd
    from database.repository import TradingRepository
    from tools.daily_tracking_report import EXPECTED, family
    spec = m.BOT_PROFILES["CARRY"]
    assert spec["mode"] == "carry-daemon" and spec["magic"] == 26082037 and spec["symbols"] == list(CARRY_DEFAULT_SYMBOLS)
    assert "CARRY" in m.FULL_MULTI_BOT_PROFILES and m._selection_profile_for_bot("CARRY") == "CARRY"
    assert rd._selection_profile_for_category("carry_fx_g10") == "CARRY" and 'data-profile="CARRY"' in rd._INSTRUMENTS_HTML
    assert rd.DEFAULT_PRIORITIZED_SYMBOLS["CARRY"] == list(CARRY_DEFAULT_SYMBOLS)
    repo = TradingRepository(tmp_path / "r.sqlite")
    repo.save_instrument_selection_profile(["AUDCHF"], selection_profile="CARRY", source="DEMO")
    assert repo.latest_instrument_selection_profile("CARRY", source="DEMO")["selected_symbols"] == ["AUDCHF"]
    assert family(CARRY_VERSION, "AUDCHF") == "Carry Forex" and "Carry Forex" in EXPECTED


def test_env_switches_mode_and_parameters():
    code = ("from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
            "from strategy.fx_carry.carry_strategy import CarryConfig as K; k=K();"
            "print(C().carry_mode, k.top_n, k.stop_atr_multiple, k.symbols)")
    env = {**os.environ, "DAEMONBLACKFX_CARRY": "off", "DAEMONBLACKFX_CARRY_TOP_N": "2",
           "DAEMONBLACKFX_CARRY_STOP_ATR": "2.5", "DAEMONBLACKFX_CARRY_SYMBOLS": "AUDJPY,USDCHF"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "off 2 2.5 ('AUDJPY', 'USDCHF')", out.stderr
