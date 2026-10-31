"""Tests para las 3 mejoras validadas cuantitativamente de Malaysian SNR v3.2:
1. Clearance de obstáculo reducido a 1.2R (alineado a TP1 1:1).
2. Buffer dinámico de retest activado en vivo (+0.20 ATR H1) y ventana a 180 min.
3. Asimetría direccional en Jump (BUY only) y Step (SELL only).
"""

import pytest
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from tests.test_msnr_dynamic_d1_settings import market


def test_msnr_v32_live_trading_engine_configuration():
    """Verifica que el motor en vivo inicialice Malaysian SNR con la configuración v3.2 validada."""
    from types import SimpleNamespace
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    
    class DummyProvider:
        def get_candles(self, *args, **kwargs):
            return None

    cfg = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", magic=26082031)
    engine = LiveTradingEngine(provider=DummyProvider(), repository=SimpleNamespace(), executor=SimpleNamespace(), config=cfg)
    strat_cfg = engine.malaysian_snr_strategy.config

    assert strat_cfg.min_obstacle_rr == 1.2
    assert strat_cfg.retest_window_minutes == 180
    assert strat_cfg.dynamic_retest_buffer_enabled is True
    assert strat_cfg.dynamic_retest_buffer_atr == 0.20
    assert strat_cfg.directional_asymmetry_enabled is True
    assert strat_cfg.strategy_version == "msnr-v3.2-hybrid-alchemist"
    assert "Jump 75 Index" in strat_cfg.jump_buy_only_symbols
    assert "Step Index 200" in strat_cfg.step_sell_only_symbols
    assert "Step Index 400" in strat_cfg.step_sell_only_symbols
    assert "Step Index 500" in strat_cfg.step_sell_only_symbols


def test_msnr_directional_asymmetry_jump_and_step():
    config = MalaysianSNRConfig(allowed_symbols=(), directional_asymmetry_enabled=True)
    provider_buy, _, now_buy = market("BUY", "SELL")
    provider_sell, _, now_sell = market("SELL", "BUY")

    strat_buy = MalaysianSNRStrategy(provider_buy, config)
    strat_sell = MalaysianSNRStrategy(provider_sell, config)

    # Step Index 200: Bloqueado en BUY, Válido en SELL
    res_step_buy = strat_buy.analyze_symbol("Step Index 200", now_buy)
    assert res_step_buy.get("reason") == "DIRECTION_ASYMMETRY_STEP_SELL_ONLY"
    res_step_sell = strat_sell.analyze_symbol("Step Index 200", now_sell)
    assert res_step_sell.get("valid") is True

    # Jump 75 Index: Bloqueado en SELL, Válido en BUY
    res_jump_sell = strat_sell.analyze_symbol("Jump 75 Index", now_sell)
    assert res_jump_sell.get("reason") == "DIRECTION_ASYMMETRY_JUMP_BUY_ONLY"
    res_jump_buy = strat_buy.analyze_symbol("Jump 75 Index", now_buy)
    assert res_jump_buy.get("valid") is True

    # Jump 50 Index: Bloqueado en SELL, Válido en BUY
    res_j50_sell = strat_sell.analyze_symbol("Jump 50 Index", now_sell)
    assert res_j50_sell.get("reason") == "DIRECTION_ASYMMETRY_JUMP_BUY_ONLY"

    # Step Index 400: Bloqueado en BUY, Válido en SELL
    res_s400_buy = strat_buy.analyze_symbol("Step Index 400", now_buy)
    assert res_s400_buy.get("reason") == "DIRECTION_ASYMMETRY_STEP_SELL_ONLY"

    # Activo no restringido (Volatility 75 Index): Válido en BUY
    res_vol = strat_buy.analyze_symbol("Volatility 75 Index", now_buy)
    assert res_vol.get("valid") is True


def test_msnr_directional_asymmetry_can_be_disabled():
    config = MalaysianSNRConfig(allowed_symbols=(), directional_asymmetry_enabled=False)
    provider_buy, _, now_buy = market("BUY", "SELL")
    strat = MalaysianSNRStrategy(provider_buy, config)
    res = strat.analyze_symbol("Step Index 200", now_buy)
    # Al estar desactivada la asimetría, Step Index 200 puede confirmar BUY
    assert res.get("valid") is True
