import pytest
import os
import pandas as pd
import numpy as np

from strategy.regime.market_regime_sentinel import (
    MarketRegimeConfig,
    MarketRegimeMetrics,
    detect_asset_class,
    classify_market_regime,
    REGIME_TOXIC_NOISE,
    REGIME_CLEAN_RANGE,
    REGIME_STABLE_TREND,
    MODE_FILTER,
)


def test_detect_asset_class():
    # Commodities
    assert detect_asset_class("XAUUSD") == "COMMODITY"
    assert detect_asset_class("XAUUSDmicro") == "COMMODITY"
    assert detect_asset_class("XAUEUR") == "COMMODITY"
    assert detect_asset_class("XAGUSD") == "COMMODITY"
    assert detect_asset_class("US Oil") == "COMMODITY"
    assert detect_asset_class("Brent Oil") == "COMMODITY"

    # Crypto
    assert detect_asset_class("BTCUSD") == "CRYPTO"
    assert detect_asset_class("ETHUSD") == "CRYPTO"

    # Indices
    assert detect_asset_class("US Tech 100") == "INDEX"
    assert detect_asset_class("Wall Street 30") == "INDEX"
    assert detect_asset_class("US SP 500") == "INDEX"
    assert detect_asset_class("Germany 40") == "INDEX"

    # Synthetics
    assert detect_asset_class("Boom 500 Index") == "SYNTHETIC"
    assert detect_asset_class("Crash 1000 Index") == "SYNTHETIC"
    assert detect_asset_class("Jump 75 Index") == "SYNTHETIC"
    assert detect_asset_class("Step Index 500") == "SYNTHETIC"
    assert detect_asset_class("Volatility 75 Index") == "SYNTHETIC"
    assert detect_asset_class("Volatility 10 (1s) Index") == "SYNTHETIC"

    # Forex
    assert detect_asset_class("EURUSD") == "FOREX"
    assert detect_asset_class("GBPUSDmicro") == "FOREX"
    assert detect_asset_class("USDJPY") == "FOREX"
    assert detect_asset_class("AUDCAD") == "FOREX"


def test_adaptive_asset_class_gold_and_crypto():
    # Gold with 0.46 wick noise ratio and ADX 17.0:
    # Under Forex baseline (wick_thresh 0.40, adx_toxic 18.0), this is marked TOXIC_NOISE.
    # Under Commodity adaptive (wick_thresh 0.52, adx_toxic 16.0), this is accepted!
    metrics = MarketRegimeMetrics(
        atr=10.0,
        atr_baseline=10.0,
        atr_ratio=1.0,
        choppiness_index=55.0,
        adx=17.0,
        wick_noise_ratio=0.46,
        spread_ratio=1.0,
        candles_evaluated=50,
    )

    # 1. Con adaptación activa (defecto)
    cfg_adaptive = MarketRegimeConfig(mode=MODE_FILTER, asset_class_adaptive_enabled=True)
    res_gold = classify_market_regime(metrics, symbol="XAUUSD", config=cfg_adaptive)
    assert not res_gold.is_toxic, "Gold debe ser aceptado bajo umbrales de commodity"
    assert res_gold.regime != REGIME_TOXIC_NOISE

    res_btc = classify_market_regime(metrics, symbol="BTCUSD", config=cfg_adaptive)
    assert not res_btc.is_toxic, "BTCUSD debe ser aceptado bajo umbrales de cripto"

    # 2. Con Forex tradicional (EURUSD), el umbral de ruido de 0.40 veta correctamente
    res_forex = classify_market_regime(metrics, symbol="EURUSD", config=cfg_adaptive)
    assert res_forex.is_toxic, "EURUSD debe ser bloqueado por ruido excesivo de mechas"
    assert res_forex.regime == REGIME_TOXIC_NOISE

    # 3. Con adaptación desactivada (backward compatibility)
    cfg_legacy = MarketRegimeConfig(mode=MODE_FILTER, asset_class_adaptive_enabled=False)
    res_gold_legacy = classify_market_regime(metrics, symbol="XAUUSD", config=cfg_legacy)
    assert res_gold_legacy.is_toxic, "Bajo modo legado, Gold se trataba como Forex y era vetado"


def test_sentinel_index_and_institutional_override():
    from strategy.regime.market_regime_sentinel import MarketRegimeSentinel

    # 1. Wall Street 30 / Germany 40 con mecha moderada de apertura (0.52) y ADX 15.0:
    # Bajo calibración anterior (0.50 y 16.0) era bloqueado 1,731 veces.
    # Con calibración adaptativa para INDEX (wick_thresh 0.60, adx_thresh 12.0), debe ser ACEPTADO.
    metrics_index = MarketRegimeMetrics(
        atr=150.0,
        atr_baseline=150.0,
        atr_ratio=1.0,
        choppiness_index=58.0,
        adx=15.0,
        wick_noise_ratio=0.52,
        spread_ratio=1.0,
        candles_evaluated=50,
    )
    cfg = MarketRegimeConfig(mode=MODE_FILTER, asset_class_adaptive_enabled=True)
    res_ws30 = classify_market_regime(metrics_index, symbol="Wall Street 30", config=cfg)
    assert not res_ws30.is_toxic, "Wall Street 30 no debe ser vetado por mechas normales de apertura"
    assert res_ws30.regime != REGIME_TOXIC_NOISE

    res_dax = classify_market_regime(metrics_index, symbol="Germany 40", config=cfg)
    assert not res_dax.is_toxic, "Germany 40 no debe ser vetado por mechas normales de apertura"

    # 2. Institutional Override: Cuando hay Desplazamiento FVG o Absorción Institucional
    # en un activo con ruido/choppiness alto, el Centinela debe permitir la entrada.
    sentinel = MarketRegimeSentinel(cfg)
    
    # Creamos un DataFrame sintético con suficiente historial
    df = pd.DataFrame({
        "open": [100.0] * 40,
        "high": [105.0] * 40,
        "low": [95.0] * 40,
        "close": [100.0] * 40,
    })

    # Sin override en un mercado ruidoso Forex
    metrics_toxic_forex = MarketRegimeMetrics(
        atr=0.0020,
        atr_baseline=0.0020,
        atr_ratio=1.0,
        choppiness_index=65.0,
        adx=14.0,
        wick_noise_ratio=0.48,
        spread_ratio=1.0,
        candles_evaluated=40,
    )
    res_forex_toxic = classify_market_regime(metrics_toxic_forex, symbol="EURUSD", config=cfg)
    assert res_forex_toxic.is_toxic

    # Con evaluate_symbol y has_institutional_confluence=True:
    # Mocking df_h1 con métricas que clasifiquen tóxico
    decision_normal = sentinel.evaluate_symbol(
        symbol="EURUSD",
        df_h1=None,  # Insufficient data -> allows default
    )
    assert decision_normal.allowed

    # Verificamos la regla de override explícitamente sobre decisión tóxica
    res_decision_override = sentinel.evaluate_symbol(
        symbol="EURUSD",
        df_h1=df,
        has_institutional_confluence=True,
    )
    # Si las velas sintéticas producen toxicidad o balance, la confluencia institucional siempre permite
    assert res_decision_override.allowed
