"""Bloqueos de RSI2/NIGHT en índices US (22-oct-2026): IA en sombra para estrategias nativas en cualquier símbolo y
límite por símbolo contando solo las posiciones del propio worker."""
import inspect
import os
import subprocess
import sys
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_native_strategies_meta_label_shadow_in_any_symbol_class():
    assert LiveTradingConfig().native_strategy_meta_label_shadow is True
    assert LiveTradingEngine._NATIVE_META_SHADOW_STRATEGIES == {"MSNR_VIDEO", "OVERNIGHT_DRIFT", "DRIFT_BREAKOUT", "CONNORS_RSI2", "FX_CARRY"}
    src = inspect.getsource(LiveTradingEngine)
    i_native = src.index('"shadow_override": "NATIVE_STRATEGY_META_SHADOW"')
    i_block = src.index('"action": "META_LABEL_FILTER_REJECTED"')
    assert i_native < i_block
    # la sombra nativa no depende de que el símbolo sea sintético
    window = src[i_native - 400:i_native]
    assert "_NATIVE_META_SHADOW_STRATEGIES" in window and "_is_synthetic_symbol" not in window


def _engine(profile, owned_tickets):
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source="DEMO")
    trades = [{"id": 1, "instrument": "US SP 500", "broker_position_ticket": "night-1", "status": "OPEN"},
              {"id": 2, "instrument": "US SP 500", "broker_position_ticket": "rsi2-1", "status": "OPEN"},
              {"id": 3, "instrument": "US SP 500", "broker_position_ticket": "rsi2-2", "status": "OPEN"}]
    e.repository = SimpleNamespace(open_trades=lambda source=None: list(trades))
    e._trade_owned_by_current_bot = lambda t: t["broker_position_ticket"] in owned_tickets
    return e


def test_symbol_limit_counts_only_own_positions_for_rsi2_and_night():
    assert LiveTradingConfig().own_symbol_limit_profiles == ("RSI2", "NIGHT", "CARRY")
    rsi2 = _engine("RSI2", {"rsi2-1", "rsi2-2"})._open_trade_diagnostics("US SP 500")
    night = _engine("NIGHT", {"night-1"})._open_trade_diagnostics("US SP 500")
    ict = _engine("ICT", set())._open_trade_diagnostics("US SP 500")
    assert rsi2["symbol_open"] == 2 and night["symbol_open"] == 1
    assert ict["symbol_open"] == 3                      # el resto de workers sigue contando todas
    assert rsi2["total_open"] == 3                      # el límite total sigue siendo global


def test_env_switches():
    code = ("from strategy.execution.live_trading_engine import LiveTradingConfig as C; c=C(); "
            "print(c.native_strategy_meta_label_shadow, c.own_symbol_limit_profiles)")
    env = {**os.environ, "DAEMONBLACKFX_NATIVE_META_SHADOW": "0", "DAEMONBLACKFX_OWN_SYMBOL_LIMIT_PROFILES": ""}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.strip() == "False ()", out.stderr


def test_priority_profiles_get_reserved_slots_over_global_limit():
    cfg = LiveTradingConfig()
    assert cfg.priority_profiles == ("DRIFT", "RSI2", "NIGHT", "CARRY") and cfg.priority_extra_slots == 4
    base_limit = _engine("ICT", set())._total_position_limit()
    assert _engine("ICT", set())._open_trade_diagnostics("US SP 500")["max_total"] == base_limit
    for profile in ("DRIFT", "RSI2", "NIGHT", "CARRY"):
        assert _engine(profile, set())._open_trade_diagnostics("US SP 500")["max_total"] == base_limit + 4


def test_rsi2_and_night_analyze_broker_candles_not_deriv():
    """23-oct-2026: en modo shadow el proveedor principal es Deriv (otra serie para los índices US); RSI2 y NIGHT
    deben analizar las velas del broker MT5 (la referencia), con las que se validaron."""
    deriv, mt5 = SimpleNamespace(get_candles=lambda *a, **k: "deriv"), SimpleNamespace(get_candles=lambda *a, **k: "mt5")
    e = LiveTradingEngine.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile="RSI2", source="DEMO")
    e.provider = SimpleNamespace(get_candles=deriv.get_candles, reference=mt5)
    assert e.config.native_strategies_broker_candles is True
    assert e._broker_candle_provider() is mt5
    assert e.rsi2_strategy.provider is mt5 and e.overnight_strategy.provider is mt5
    e2 = LiveTradingEngine.__new__(LiveTradingEngine)
    e2.config = LiveTradingConfig(bot_profile="RSI2", source="DEMO", native_strategies_broker_candles=False)
    e2.provider = e.provider
    assert e2._broker_candle_provider() is e.provider
    plain = SimpleNamespace(get_candles=lambda *a, **k: "mt5-only")   # modo mt5: sin referencia
    e2.provider = plain
    e2.config = LiveTradingConfig(bot_profile="RSI2", source="DEMO")
    assert e2._broker_candle_provider() is plain
