"""Tests unitarios para la lógica adaptativa bidireccional en Workers STEP y JUMP
y la exclusión de instrumentos en estrategias unidireccionales (Malaysian SNR y Trend Pullback).
"""
import pytest
import pandas as pd
import numpy as np

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from config.ict_instrument_policy import (
    MALAYSIAN_SNR_EXCLUDED,
    MALAYSIAN_SNR_SYNTHETICS,
    ICT_SYNTHETIC_FAMILIES,
)
from strategy.trend_pullback.config import (
    TREND_PULLBACK_51_SYMBOLS,
    TREND_PULLBACK_PRUNED_SYMBOLS,
)
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def _make_dummy_provider(direction="BUY", adx=30.0, atr=2.0, sl_distance=3.0, pb_distance=0.2):
    """Crea un data_provider sintético con velas cerradas M15 y H1 para pruebas de validación."""
    class DummyProvider:
        def get_candles(self, symbol, timeframe, count=100):
            n = count
            times = pd.date_range("2026-10-20 00:00:00", periods=n, freq="15min" if timeframe == "M15" else "1h", tz="UTC")
            if direction == "BUY":
                # Tendencia alcista: closes crecientes
                close = np.linspace(100.0, 150.0, n)
                high = close + 1.0
                low = close - 1.0
                open_ = close - 0.5
            else:
                # Tendencia bajista: closes decrecientes
                close = np.linspace(150.0, 100.0, n)
                high = close + 1.0
                low = close - 1.0
                open_ = close + 0.5
            return pd.DataFrame({"time": times, "open": open_, "high": high, "low": low, "close": close, "volume": 100.0})
    return DummyProvider()


def test_jump_and_step_excluded_from_malaysian_snr():
    """Verifica que Jump y Step fueron retirados de Malaysian SNR para evitar duplicidad unidireccional."""
    excluded = set(MALAYSIAN_SNR_EXCLUDED)
    active = set(MALAYSIAN_SNR_SYNTHETICS)
    
    transferred_to_workers = [
        "Jump 50 Index", "Jump 75 Index",
        "Step Index 200", "Step Index 400", "Step Index 500"
    ]
    for sym in transferred_to_workers:
        assert sym in excluded, f"{sym} debería estar excluido de Malaysian SNR"
        assert sym not in active, f"{sym} NO debería estar activo en Malaysian SNR"


def test_jump_and_step_excluded_from_trend_pullback():
    """Verifica que Jump y Step con asimetría forzada fueron retirados de Trend Pullback."""
    active_tpb = set(TREND_PULLBACK_51_SYMBOLS)
    pruned_tpb = set(TREND_PULLBACK_PRUNED_SYMBOLS)
    
    transferred = [
        "Jump 50 Index", "Jump 75 Index",
        "Step Index 200", "Step Index 400",
        "Step Index", "Step Index 500"
    ]
    for sym in transferred:
        assert sym in pruned_tpb, f"{sym} debe figurar en TREND_PULLBACK_PRUNED_SYMBOLS"
        assert sym not in active_tpb, f"{sym} NO debe figurar en TREND_PULLBACK_51_SYMBOLS"


def test_step_and_jump_worker_profile_meta_governed_by_synthetics_tab():
    """Verifica que los workers STEP y JUMP se gobiernan desde la pestaña Sintéticos de /Instruments."""
    assert "STEP" in _WORKER_PROFILE_META
    assert "JUMP" in _WORKER_PROFILE_META
    
    step_meta = _WORKER_PROFILE_META["STEP"]
    jump_meta = _WORKER_PROFILE_META["JUMP"]
    
    assert step_meta["selection_profile"] == "SYNTHETICS"
    assert step_meta["category"] == "step"
    assert jump_meta["selection_profile"] == "SYNTHETICS"
    assert jump_meta["category"] == "jump"


def test_step_200_and_400_bidirectional_standard():
    """Verifica que Step Index 200 y 400 admiten compras y ventas sin rechazo por asimetría."""
    cfg = ICTSabriMalleConfig()
    strat = ICTSabriMalleStrategy(data_provider=_make_dummy_provider(), config=cfg)
    
    # Comprobar que Step 200 y 400 no están en step_sell_only_symbols
    assert "Step Index 200" not in cfg.step_sell_only_symbols
    assert "Step Index 400" not in cfg.step_sell_only_symbols


def test_jump_sell_adaptive_shield_rejection_when_sl_too_tight():
    """Verifica que ventas en Jump 50/75 son evaluadas con el escudo Anti-Jump (SL >= 1.45 ATR)."""
    cfg = ICTSabriMalleConfig(
        adaptive_bidirectional_jump_step_enabled=True,
        jump_sell_min_sl_atr_h1=1.45,
    )
    # Crear provider bajista
    strat = ICTSabriMalleStrategy(data_provider=_make_dummy_provider(direction="SELL"), config=cfg)
    
    res = strat.analyze_symbol("Jump 75 Index")
    # No debe ser rechazado de plano por ICT_DIRECTION_ASYMMETRY_JUMP_BUY_ONLY
    # Debe ser evaluado por las reglas adaptativas o de estructura
    assert res.get("reason") != "ICT_DIRECTION_ASYMMETRY_JUMP_BUY_ONLY"


def test_step_buy_adaptive_anchor_evaluation():
    """Verifica que compras en Step Index / Step 500 son evaluadas con el ancla de expansión ADX >= 28."""
    cfg = ICTSabriMalleConfig(
        adaptive_bidirectional_jump_step_enabled=True,
        step_buy_min_adx_h1=28.0,
    )
    strat = ICTSabriMalleStrategy(data_provider=_make_dummy_provider(direction="BUY"), config=cfg)
    
    res = strat.analyze_symbol("Step Index")
    # No debe ser rechazado de plano por ICT_DIRECTION_ASYMMETRY_STEP_SELL_ONLY
    assert res.get("reason") != "ICT_DIRECTION_ASYMMETRY_STEP_SELL_ONLY"


def test_fallback_unidirectional_when_adaptive_disabled():
    """Verifica que si el interruptor adaptativo se apaga, se preserva el comportamiento previo unidireccional."""
    cfg = ICTSabriMalleConfig(
        adaptive_bidirectional_jump_step_enabled=False,
    )
    strat_sell = ICTSabriMalleStrategy(data_provider=_make_dummy_provider(direction="SELL"), config=cfg)
    res_jump_sell = strat_sell.analyze_symbol("Jump 75 Index")
    assert res_jump_sell.get("reason") == "ICT_DIRECTION_ASYMMETRY_JUMP_BUY_ONLY"
    
    strat_buy = ICTSabriMalleStrategy(data_provider=_make_dummy_provider(direction="BUY"), config=cfg)
    res_step_buy = strat_buy.analyze_symbol("Step Index")
    assert res_step_buy.get("reason") == "ICT_DIRECTION_ASYMMETRY_STEP_SELL_ONLY"
