"""MSNR solo en sintéticos (todos), sin C2 ni lista, y runner hacia TP3/TP4 (replay fiel 2 años)."""
import inspect
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy


def engine_msnr_config():
    engine = LiveTradingEngine(provider=SimpleNamespace(), repository=SimpleNamespace(), executor=SimpleNamespace(),
                               config=LiveTradingConfig(bot_profile="MALAYSIAN_SNR"))
    return engine, engine.malaysian_snr_strategy.config


def test_live_defaults_all_synthetics_without_c2():
    _, cfg = engine_msnr_config()
    assert cfg.strategy_version == "msnr-v3.1-synthetics"
    assert cfg.enable_c2_fx_metals_atr_cap is False
    assert cfg.synthetics_only is True
    assert tuple(cfg.allowed_symbols) == ()


def test_env_restores_previous_behaviour(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_C2", "1")
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_ALL_SYNTHETICS", "0")
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY", "0")
    _, cfg = engine_msnr_config()
    assert cfg.strategy_version == "msnr-v3.0-c2" and cfg.enable_c2_fx_metals_atr_cap is True
    assert cfg.synthetics_only is False
    assert tuple(cfg.allowed_symbols) == tuple(MalaysianSNRConfig().allowed_symbols)


@pytest.mark.parametrize("symbol,blocked", [("EURUSD", True), ("XAUUSD", True), ("Wall Street 30", True),
                                            ("Volatility 75 Index", False), ("Boom 900 Index", False)])
def test_strategy_rejects_real_markets(symbol, blocked):
    provider = SimpleNamespace(get_candles=lambda *a, **k: None)
    strat = MalaysianSNRStrategy(provider, MalaysianSNRConfig(synthetics_only=True, allowed_symbols=(),
                                                              enable_session_killzones_filter=False))
    res = strat.analyze_symbol(symbol)
    assert (res.get("reason") == "MSNR_SYNTHETICS_ONLY") is blocked


def test_msnr_runner_extends_to_tp4():
    assert LiveTradingConfig().msnr_runner_max_target_rr == pytest.approx(4.0)
    src = inspect.getsource(LiveTradingEngine)
    assert src.count('float(self.config.msnr_runner_max_target_rr) if strategy_name == "MALAYSIAN_SNR"') == 2
