"""Topes de spread/SL de ICT en mercados reales y bloqueo de ICT en cripto (replay fiel 2 años)."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def make_engine(bid, ask, profile="ICT", **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile=profile, **cfg)
    engine.executor = SimpleNamespace(get_current_tick=lambda _s: {"bid": bid, "ask": ask, "time": datetime.now(timezone.utc)})
    engine.audits = []
    engine._persist_audit_event = lambda event, **kw: engine.audits.append((event, kw.get("action")))
    return engine


def test_defaults():
    cfg = LiveTradingConfig()
    assert cfg.forex_spread_max_risk_ratio == pytest.approx(0.05)
    assert cfg.ict_metals_spread_max_risk_ratio == pytest.approx(0.02)
    assert cfg.ict_crypto_enabled is False


def test_ict_metals_cap_blocks_above_two_percent():
    # SELL al bid 2000.0, SL 2010.0 -> distancia 10; spread 0.30 -> 3%
    engine = make_engine(2000.0, 2000.30)
    blocked = engine._ict_real_market_spread_gate("XAUUSD", "SELL", 2010.0, "ICT_SABRI_MALLE")
    assert blocked["action"] == "ICT_METALS_SPREAD_TO_SL_EXCEEDED"
    assert engine._ict_real_market_spread_gate("XAUUSD", "SELL", 2020.0, "ICT_SABRI_MALLE") is None  # 1.5%


@pytest.mark.parametrize("strategy", ["ORB_NEW_YORK", "GOLD_QUARTERS", "MALAYSIAN_SNR"])
def test_metals_cap_only_applies_to_ict(strategy):
    engine = make_engine(2000.0, 2000.30)
    assert engine._ict_real_market_spread_gate("XAUUSD", "SELL", 2010.0, strategy) is None
    assert engine.audits == []


def test_ict_forex_cap_five_percent_in_ict_worker():
    # BUY al ask 1.10010, SL 1.09810 -> distancia 0.0020; spread 0.00012 -> 6%
    engine = make_engine(1.09998, 1.10010)
    blocked = engine._ict_real_market_spread_gate("EURUSD", "BUY", 1.09810, "ICT_SABRI_MALLE")
    assert blocked["action"] == "ICT_FOREX_SPREAD_TO_SL_EXCEEDED"
    assert engine._ict_real_market_spread_gate("EURUSD", "BUY", 1.09700, "ICT_SABRI_MALLE") is None  # ~3.9%


def test_forex_workers_use_existing_forex_guard_not_duplicate():
    engine = make_engine(1.09998, 1.10010, profile="FOREX_1")
    assert engine._ict_real_market_spread_gate("EURUSD", "BUY", 1.09810, "ICT_SABRI_MALLE") is None


def test_configurable_caps():
    engine = make_engine(2000.0, 2000.30, ict_metals_spread_max_risk_ratio=0.05)
    assert engine._ict_real_market_spread_gate("XAUUSD", "SELL", 2010.0, "ICT_SABRI_MALLE") is None


def test_execution_gate_passes_strategy_name():
    engine = make_engine(2000.0, 2000.30)
    blocked = engine._forex_execution_gate("XAUUSD", "SELL", 2010.0, strategy_name="ICT_SABRI_MALLE")
    assert blocked is not None and blocked["action"] == "ICT_METALS_SPREAD_TO_SL_EXCEEDED"
    import inspect
    src = inspect.getsource(LiveTradingEngine)
    assert src.count("self._forex_execution_gate(exact_symbol, direction, sl, strategy_name=strategy_name)") == 3


@pytest.mark.parametrize("symbol,enabled,blocked", [("BTCUSD", False, True), ("ETHUSD", False, True),
                                                    ("BTCUSD", True, False), ("XAUUSD", False, False)])
def test_ict_crypto_block(symbol, enabled, blocked):
    engine = make_engine(100.0, 100.1, ict_crypto_enabled=enabled)
    engine.ict_strategy = SimpleNamespace(analyze_symbol=lambda _s: {"valid": False, "action": "WAITING_ICT"})
    res = engine._ict_analysis_with_virtual_limit(symbol)
    assert (res.get("action") == "ICT_CRYPTO_DISABLED") is blocked
