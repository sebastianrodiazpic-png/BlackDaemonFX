"""Ocupación fantasma tras descarte por spread en ICT sintéticos (20-oct-2026).

Replay fiel 2 años: una señal descartada por spread/SL > 2 % debe ocupar el símbolo hasta su resultado virtual;
las señales que llegan mientras tanto pierden −0,11/−0,16 R/t. Año previo +0,004 -> +0,022 R/t.
"""
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class _Provider:
    def __init__(self, candles=None):
        self.candles = candles

    def get_candles(self, symbol, timeframe="M15", count=10):
        return self.candles


def _engine(enabled=True, candles=None, spread=2.0, entry=100.0):
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile="VOLATILITY_1", ict_spread_block_lock_enabled=enabled)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action"), k.get("reason")))
    e._meta_execution_spread = lambda s: {"spread": spread, "execution_ask": entry, "execution_bid": entry - spread}
    e.provider = _Provider(candles)
    return e


def _bars(rows, start):
    t = pd.Timestamp(start).floor("15min")
    return pd.DataFrame([{"time": t + pd.Timedelta(minutes=15 * i), "high": h, "low": l} for i, (h, l) in enumerate(rows)])


def test_spread_block_registers_lock_for_ict_synthetic():
    e = _engine()
    out = e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE")  # 20 % > 2 %
    assert out["action"] == "SYNTHETIC_SPREAD_TO_SL_EXCEEDED"
    lock = e._ict_spread_locks["Volatility 10 Index"]
    assert (lock["entry"], lock["stop"], lock["tp1"], lock["tp2"]) == (100.0, 90.0, 110.0, 120.0)
    assert ("ICT_SPREAD_LOCK", "LOCKED", "ICT_SIGNAL_SPREAD_BLOCKED_VIRTUAL_TRADE_OCCUPIES_SYMBOL") in e.events


def test_no_lock_for_other_strategies_disabled_or_allowed():
    e = _engine()
    e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="MALAYSIAN_SNR")
    assert not getattr(e, "_ict_spread_locks", {})
    e = _engine(enabled=False)
    e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE")
    assert not getattr(e, "_ict_spread_locks", {})
    e = _engine(spread=0.1)  # spread/SL 1 %: no se bloquea ni se ocupa
    assert e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE") is None
    assert not getattr(e, "_ict_spread_locks", {})


def test_lock_blocks_until_virtual_sl():
    e = _engine()
    e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE")
    created = e._ict_spread_locks["Volatility 10 Index"]["created_at"]
    e.provider.candles = _bars([(105, 95), (104, 96)], created)
    assert e._ict_spread_lock_gate("Volatility 10 Index")["action"] == "ICT_SPREAD_LOCK_ACTIVE"
    e._ict_spread_locks["Volatility 10 Index"]["created_at"] = (pd.Timestamp(created) - pd.Timedelta(hours=1)).isoformat()
    e.provider.candles = _bars([(105, 95), (104, 89)], pd.Timestamp(created) - pd.Timedelta(hours=1))
    assert e._ict_spread_lock_gate("Volatility 10 Index") is None
    assert e.events[-1] == ("ICT_SPREAD_LOCK", "RELEASED", "VIRTUAL_TRADE_SL")
    assert "Volatility 10 Index" not in e._ict_spread_locks


def test_virtual_trade_outcomes_buy_and_sell():
    base = {"direction": "BUY", "entry": 100.0, "stop": 90.0, "tp1": 110.0, "tp2": 120.0, "spread": 0.0,
            "created_at": "2026-10-20T10:00:00+00:00"}
    r = LiveTradingEngine._resolve_virtual_trade
    assert r(dict(base, tp1_hit=False), _bars([(111, 101), (121, 105)], base["created_at"])) == "TP2"
    assert r(dict(base, tp1_hit=False), _bars([(111, 101), (108, 99)], base["created_at"])) == "TP1+BE"
    assert r(dict(base, tp1_hit=False), _bars([(111, 99)], base["created_at"])) == "TP1+BE"  # ambigua: BE
    assert r(dict(base, tp1_hit=False), _bars([(105, 95)], base["created_at"])) is None
    sell = {"direction": "SELL", "entry": 100.0, "stop": 110.0, "tp1": 90.0, "tp2": 80.0, "spread": 1.0,
            "created_at": base["created_at"], "tp1_hit": False}
    assert r(dict(sell), _bars([(109.5, 95)], base["created_at"])) == "SL"  # ask = bid + spread toca el SL
    assert r(dict(sell), _bars([(98, 79)], base["created_at"])) == "TP2"
    assert r(dict(sell), _bars([(105, 79)], base["created_at"])) == "TP1+BE"  # vuelve a la entrada en la misma vela
    # Las velas anteriores a la señal no cuentan
    assert r(dict(base, tp1_hit=False), _bars([(105, 80), (105, 95)], "2026-10-20T09:45:00+00:00")) is None


def test_lock_expires_after_max_hours():
    e = _engine()
    e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE")
    e._ict_spread_locks["Volatility 10 Index"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    assert e._ict_spread_lock_gate("Volatility 10 Index") is None
    assert e.events[-1] == ("ICT_SPREAD_LOCK", "RELEASED", "VIRTUAL_TRADE_TIMEOUT")


def test_candle_errors_keep_lock_and_unlocked_symbol_passes():
    e = _engine()
    assert e._ict_spread_lock_gate("Volatility 10 Index") is None
    e._forex_execution_gate("Volatility 10 Index", "BUY", 90.0, strategy_name="ICT_SABRI_MALLE")

    def boom(*a, **k):
        raise RuntimeError("sin velas")
    e.provider.get_candles = boom
    assert e._ict_spread_lock_gate("Volatility 10 Index")["action"] == "ICT_SPREAD_LOCK_ACTIVE"


def test_defaults_and_env():
    cfg = LiveTradingConfig()
    assert cfg.ict_spread_block_lock_enabled is True and cfg.ict_spread_block_lock_max_hours == 1.0
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().ict_spread_block_lock_enabled)"
    env = {**os.environ, "DAEMONBLACKFX_ICT_SPREAD_LOCK": "0"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "False", out.stderr
