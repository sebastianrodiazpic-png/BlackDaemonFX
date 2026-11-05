"""Entrada limitada virtual de ICT en sintéticos (réplica en vivo de tools/replay_ict_limit_entry.py)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine

BAR = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)  # apertura de la vela M15 de señal


class Clock:
    def __init__(self, t):
        self.t = t


def signal_analysis(direction="BUY", entry=100.0, sl=98.0, bar=BAR):
    return {"valid": True, "strategy_name": "ICT_SABRI_MALLE", "strategy_version": "test",
            "signal": {"direction": direction, "entry_price": entry, "stop_loss": sl,
                       "entry_time": bar.isoformat(), "tp1_price": entry + 2, "tp2_price": entry + 4}}


def make_engine(results, quotes, now, **cfg):
    """results: lista de análisis devueltos por ICT en cada ciclo; quotes: lista de (bid, ask)."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_1", **cfg)
    it_res, it_q = iter(results), iter(quotes)
    engine.ict_strategy = SimpleNamespace(analyze_symbol=lambda _s: next(it_res))
    clock = Clock(now)
    engine._virtual_limit_now = lambda: clock.t

    def tick(_s):
        bid, ask = next(it_q)
        return {"bid": bid, "ask": ask, "time": datetime.now(timezone.utc)}

    engine.executor = SimpleNamespace(get_current_tick=tick)
    engine.audits = []
    engine._persist_audit_event = lambda event, **kw: engine.audits.append((kw.get("action"), kw.get("reason")))
    return engine, clock


def none_signal():
    return {"valid": False, "action": "WAITING_ICT", "reason": "NO_SETUP"}


def test_defaults():
    cfg = LiveTradingConfig()
    assert cfg.ict_virtual_limit_enabled is True
    assert cfg.ict_virtual_limit_bars == 12


def test_signal_waits_then_triggers_when_ask_touches_limit():
    now = BAR + timedelta(minutes=16)
    engine, clock = make_engine([signal_analysis(), none_signal(), none_signal()],
                                [(100.4, 100.5), (100.2, 100.3), (99.9, 100.0)], now)
    first = engine._ict_analysis_with_virtual_limit("Volatility 75 Index")
    assert first["valid"] is False and first["action"] == "ICT_VIRTUAL_LIMIT_WAITING"
    assert engine.audits[0][0] == "CREATED"
    second = engine._ict_analysis_with_virtual_limit("Volatility 75 Index")
    assert second["action"] == "ICT_VIRTUAL_LIMIT_WAITING"
    third = engine._ict_analysis_with_virtual_limit("Volatility 75 Index")
    assert third["valid"] is True and third["signal"]["entry_price"] == 100.0
    assert third["virtual_limit"]["trigger_price"] == 100.0
    assert engine.audits[-1][0] == "TRIGGERED"
    assert "Volatility 75 Index" not in engine._ict_virtual_limits


def test_sell_triggers_when_bid_reaches_limit():
    engine, _ = make_engine([signal_analysis("SELL", 100.0, 102.0)], [(100.0, 100.1)], BAR + timedelta(minutes=16))
    res = engine._ict_analysis_with_virtual_limit("Crash 500 Index")
    assert res["valid"] is True  # fill inmediato: el bid ya está en el límite


def test_limit_expires_after_configured_bars():
    engine, clock = make_engine([signal_analysis(), none_signal()], [(100.5, 100.6), (100.5, 100.6)],
                                BAR + timedelta(minutes=16), ict_virtual_limit_bars=8)
    assert engine._ict_analysis_with_virtual_limit("Step Index 400")["action"] == "ICT_VIRTUAL_LIMIT_WAITING"
    clock.t = BAR + timedelta(minutes=15 * 9)  # cierre de la vela de señal + 8 velas
    res = engine._ict_analysis_with_virtual_limit("Step Index 400")
    assert res["action"] == "ICT_VIRTUAL_LIMIT_EXPIRED" and res["valid"] is False
    assert engine.audits[-1][0] == "EXPIRED"


def test_stop_touched_before_fill_cancels():
    engine, _ = make_engine([signal_analysis("BUY", 100.0, 98.0), none_signal()], [(100.5, 100.6), (97.9, 98.0)],
                            BAR + timedelta(minutes=16))
    engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    res = engine._ict_analysis_with_virtual_limit("Jump 25 Index")
    assert res["action"] == "ICT_VIRTUAL_LIMIT_INVALIDATED"


def test_same_signal_repeated_each_cycle_does_not_reset_expiry():
    engine, clock = make_engine([signal_analysis(), signal_analysis()], [(100.5, 100.6), (100.5, 100.6)],
                                BAR + timedelta(minutes=16))
    engine._ict_analysis_with_virtual_limit("Boom 500 Index")
    expires = engine._ict_virtual_limits["Boom 500 Index"]["expires_at"]
    clock.t += timedelta(minutes=5)
    engine._ict_analysis_with_virtual_limit("Boom 500 Index")
    assert engine._ict_virtual_limits["Boom 500 Index"]["expires_at"] == expires
    assert [a for a in engine.audits if a[0] == "CREATED"] == [("CREATED", "LIMIT_PENDING")]


def test_newer_signal_replaces_pending():
    newer = signal_analysis(entry=101.0, sl=99.0, bar=BAR + timedelta(minutes=15))
    engine, _ = make_engine([signal_analysis(), newer], [(100.5, 100.6), (101.5, 101.6)], BAR + timedelta(minutes=31))
    engine._ict_analysis_with_virtual_limit("Volatility 10 Index")
    engine._ict_analysis_with_virtual_limit("Volatility 10 Index")
    assert engine._ict_virtual_limits["Volatility 10 Index"]["limit"] == 101.0


@pytest.mark.parametrize("symbol,cfg", [("EURUSD", {}), ("Volatility 75 Index", {"ict_virtual_limit_enabled": False})])
def test_forex_or_disabled_keeps_market_entry(symbol, cfg):
    engine, _ = make_engine([signal_analysis()], [], BAR + timedelta(minutes=16), **cfg)
    res = engine._ict_analysis_with_virtual_limit(symbol)
    assert res["valid"] is True and engine.audits == []


def test_process_symbol_routes_ict_through_virtual_limit():
    import inspect
    source = inspect.getsource(LiveTradingEngine)  # process_symbol delega en un método interno
    assert "analysis = self._ict_analysis_with_virtual_limit(exact_symbol)" in source
    assert "analysis = self.ict_strategy.analyze_symbol(exact_symbol)" not in source
