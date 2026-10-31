"""Detección ampliada de sintéticos y Centinela de Régimen en OBSERVE para ICT en sintéticos (20-oct-2026).

- High Frequency Vol 50/100 y VolSwitch High Vol no se reconocían como sintéticos: sin entrada limitada, sin tope
  spread/SL 2 % y sin IA en sombra.
- Replay fiel ICT: el centinela bloqueaba el 18 % de señales con +0,067 R/t (permitidas +0,045).
"""
import os
import subprocess
import sys
from types import SimpleNamespace

import pandas as pd

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine

NEW_SYNTHETICS = ("High Frequency Vol 50 Index", "High Frequency Vol 100 Index", "VolSwitch High Vol Index")
REAL_MARKETS = ("EURUSD", "USDJPYmicro", "XAUUSD", "XAGUSD", "US Oil", "Wall Street 30", "US Tech 100", "US SP 500", "BTCUSD")


def test_new_synthetics_detected_and_real_markets_not():
    for sym in NEW_SYNTHETICS:
        assert LiveTradingEngine._is_synthetic_symbol(sym), sym
    for sym in REAL_MARKETS:
        assert not LiveTradingEngine._is_synthetic_symbol(sym), sym
    for sym in ("Volatility 10 Index", "Boom 500 Index", "Crash 300 Index", "Step Index 400", "Jump 75 Index"):
        assert LiveTradingEngine._is_synthetic_symbol(sym)


def test_detection_matches_replay_classifier_on_policy_universe():
    from config.ict_instrument_policy import MSNR_SYNTHETIC_UNIVERSE, ict_active_symbols
    from strategy.ict.ict_strategy import is_synthetic_asset
    for sym in set(MSNR_SYNTHETIC_UNIVERSE) | set(ict_active_symbols("SYNTHETICS")):
        assert LiveTradingEngine._is_synthetic_symbol(sym) == is_synthetic_asset(sym) is True, sym


def test_synthetic_spread_cap_now_applies_to_hf_vol():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_2")
    engine._persist_audit_event = lambda *a, **k: None
    engine._meta_execution_spread = lambda s: {"spread": 1.0, "execution_ask": 100.0, "execution_bid": 99.0}
    out = engine._synthetic_spread_gate("High Frequency Vol 100 Index", "BUY", 90.0)  # spread/SL = 10 %
    assert out is not None and "SPREAD" in out["action"]


def test_env_disables_extended_detection():
    code = ("from strategy.execution.live_trading_engine import LiveTradingEngine as E;"
            "print(E._is_synthetic_symbol('High Frequency Vol 50 Index'))")
    env = {**os.environ, "DAEMONBLACKFX_SYNTH_DETECTION_EXTENDED": "0"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "False", out.stderr


# ------------------------------------------------------------------ Centinela de régimen
class _Sentinel:
    def __init__(self, toxic=True):
        self.config = SimpleNamespace(enabled=True, mode="FILTER", min_candles_required=20)
        self.toxic = toxic

    def evaluate_symbol(self, **kw):
        return SimpleNamespace(is_toxic=self.toxic, reason="MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY",
                               to_dict=lambda: {"regime": "TOXIC_NOISE"})


def _engine(profile, mode="OBSERVE", toxic=True):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile=profile, market_regime_ict_synthetic_mode=mode)
    engine.regime_sentinel = _Sentinel(toxic)
    engine.provider = SimpleNamespace(get_candles=lambda *a, **k: pd.DataFrame({"close": range(40)}))
    engine._meta_execution_spread = lambda s: {}
    engine.events = []
    engine._persist_audit_event = lambda *a, **k: engine.events.append(a[0])
    return engine


def test_default_is_observe_for_ict_synthetics():
    assert LiveTradingConfig().market_regime_ict_synthetic_mode == "OBSERVE"


def test_ict_workers_on_synthetics_only_observe():
    for profile in ("ICT", "STEP", "JUMP", "BOOM", "CRASH", "VOLATILITY_1", "VOLATILITY_4"):
        e = _engine(profile)
        assert e._market_regime_entry_gate("Volatility 10 Index") is None, profile
        assert e.events == ["MARKET_REGIME_OBSERVED"]


def test_other_strategies_and_real_markets_still_blocked():
    assert _engine("MALAYSIAN_SNR")._market_regime_entry_gate("Volatility 10 Index")["action"] == "MARKET_REGIME_BLOCKED"
    assert _engine("FLIP")._market_regime_entry_gate("Crash Boom Flip 1000 Index")["action"] == "MARKET_REGIME_BLOCKED"
    assert _engine("FOREX_1")._market_regime_entry_gate("EURUSD")["action"] == "MARKET_REGIME_BLOCKED"
    # ICT en mercados reales (Oro/Petróleo/Índices) por defecto en OBSERVE para capturar la ventaja del replay
    e_ict_real = _engine("ICT")
    assert e_ict_real._market_regime_entry_gate("US Oil") is None
    assert e_ict_real.events == ["MARKET_REGIME_OBSERVED"]
    # Con FILTER explícito restaura el bloqueo
    e_ict_filter = _engine("ICT")
    e_ict_filter.config.market_regime_ict_real_mode = "FILTER"
    assert e_ict_filter._market_regime_entry_gate("US Oil")["action"] == "MARKET_REGIME_BLOCKED"


def test_filter_mode_restores_veto_and_non_toxic_passes():
    assert _engine("ICT", mode="FILTER")._market_regime_entry_gate("Volatility 10 Index")["action"] == "MARKET_REGIME_BLOCKED"
    e = _engine("ICT", toxic=False)
    assert e._market_regime_entry_gate("Volatility 10 Index") is None and e.events == []


def test_env_sets_regime_mode():
    code = ("from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
            "print(C().market_regime_ict_synthetic_mode)")
    env = {**os.environ, "DAEMONBLACKFX_MARKET_REGIME_ICT_SYNTH_MODE": "filter"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "FILTER", out.stderr
