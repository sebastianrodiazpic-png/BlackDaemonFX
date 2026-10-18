"""Pruebas unitarias para la Arquitectura de IA en Dos Capas (Two-Tier AI Architecture).

Capa 1: MarketRegimeSentinel (Detección macro de regímenes de mercado y filtrado de semanas tóxicas).
Capa 2: CalibratedGBDTModel (Meta-labeling no lineal con LightGBM / árboles de decisión).
"""

import json
import numpy as np
import pandas as pd
import pytest

from strategy.ai import (
    FEATURE_NAMES,
    CalibratedGBDTModel,
    CalibratedLogisticModel,
    MetaLabelingConfig,
    MetaLabelingEngine,
    train_worker_gbdt_model,
)
from strategy.regime import (
    MarketRegimeConfig,
    MarketRegimeSentinel,
    REGIME_CLEAN_RANGE,
    REGIME_STABLE_TREND,
    REGIME_TOXIC_NOISE,
    classify_market_regime,
    compute_regime_metrics,
)


def _generate_synthetic_ohlc(pattern: str = "clean_range", n: int = 50) -> pd.DataFrame:
    """Genera series sintéticas de velas cerradas para simular regímenes de mercado."""
    np.random.seed(42)
    rows = []
    price = 100.0

    if pattern == "stable_trend":
        # Tendencia alcista consistente: velas verdes con cuerpo dominante y poco retroceso
        for i in range(n):
            price += 1.5 + np.random.uniform(-0.2, 0.5)
            high = price + 0.3
            low = price - 0.2
            open_p = price - 0.8
            close_p = price
            rows.append({"open": open_p, "high": high, "low": low, "close": close_p})

    elif pattern == "toxic_choppy":
        # Congestión caótica extrema: mechas bidireccionales gigantes sin avance neto
        for i in range(n):
            noise = np.random.uniform(-0.1, 0.1)
            price = 100.0 + noise
            # Mechas muy largas en ambas direcciones (barrido de stops)
            high = price + 3.0 + np.random.uniform(0.1, 0.5)
            low = price - 3.0 - np.random.uniform(0.1, 0.5)
            open_p = price - 0.05
            close_p = price + 0.05
            rows.append({"open": open_p, "high": high, "low": low, "close": close_p})

    else:  # "clean_range"
        # Rango armónico tipo onda senoidal suave (ideal para SNR)
        for i in range(n):
            oscillation = 5.0 * np.sin(i / 4.0)
            mid = 100.0 + oscillation
            high = mid + 0.8
            low = mid - 0.8
            open_p = mid - 0.3
            close_p = mid + 0.3
            rows.append({"open": open_p, "high": high, "low": low, "close": close_p})

    return pd.DataFrame(rows)


class TestMarketRegimeSentinel:
    """Pruebas para Capa 1: Sentinel de Regímenes de Mercado."""

    def test_stable_trend_classification(self):
        df = _generate_synthetic_ohlc("stable_trend", n=50)
        metrics = compute_regime_metrics(df, period=14)
        classification = classify_market_regime(metrics, symbol="EURUSD")

        assert metrics.candles_evaluated == 50
        assert classification.regime in (REGIME_STABLE_TREND, REGIME_CLEAN_RANGE)
        assert classification.is_toxic is False

    def test_toxic_noise_classification_detects_whipsaws(self):
        df = _generate_synthetic_ohlc("toxic_choppy", n=50)
        metrics = compute_regime_metrics(df, period=14)
        classification = classify_market_regime(metrics, symbol="GBPUSD")

        # Debe identificar las mechas gigantes o choppiness extremo como tóxico
        assert classification.is_toxic is True
        assert classification.regime == REGIME_TOXIC_NOISE
        assert "WHIPSAW" in classification.primary_factor or "CHOPPINESS" in classification.primary_factor

    def test_spread_stress_triggers_toxic(self):
        df = _generate_synthetic_ohlc("clean_range", n=40)
        metrics = compute_regime_metrics(df, current_spread=5.0, baseline_spread=1.0)
        classification = classify_market_regime(metrics, symbol="EURUSD")

        assert classification.is_toxic is True
        assert classification.regime == REGIME_TOXIC_NOISE
        assert classification.primary_factor == "SPREAD_STRESS_SPIKE"

    def test_sentinel_observe_mode_does_not_block_toxic(self):
        sentinel = MarketRegimeSentinel(MarketRegimeConfig(mode="OBSERVE"))
        df = _generate_synthetic_ohlc("toxic_choppy", n=40)
        decision = sentinel.evaluate_symbol("EURUSD", df)

        # En OBSERVE detecta que es tóxico pero allowed sigue siendo True
        assert decision.is_toxic is True
        assert decision.allowed is True
        assert "OBSERVED_TOXIC" in decision.reason

    def test_sentinel_filter_mode_blocks_toxic_forex(self):
        sentinel = MarketRegimeSentinel(MarketRegimeConfig(mode="FILTER", forex_strict_filter=True))
        df = _generate_synthetic_ohlc("toxic_choppy", n=40)
        decision = sentinel.evaluate_symbol("EURUSD", df)

        # En FILTER veta de inmediato para proteger el capital
        assert decision.is_toxic is True
        assert decision.allowed is False
        assert "MARKET_REGIME_TOXIC_BLOCKED" in decision.reason


class TestCalibratedGBDTModel:
    """Pruebas para Capa 2: LightGBM Meta-Labeler."""

    def test_gbdt_model_training_and_probability(self):
        np.random.seed(42)
        n_samples = 60
        n_features = len(FEATURE_NAMES)
        X = np.random.randn(n_samples, n_features)
        # El target tiene correlación con las primeras 2 features
        y = ((X[:, 0] + X[:, 1]) > 0).astype(int)

        model = CalibratedGBDTModel(worker="FOREX", strategy_name="MALAYSIAN_SNR")
        model.fit(X[:45], y[:45], X_val=X[45:], y_val=y[45:], n_estimators=30, max_depth=3)

        assert model.trained is True
        assert model.samples == 45
        assert len(model.model_str) > 0
        assert len(model.feature_importances) > 0

        # Evaluar predicción
        sample_vec = list(X[0])
        prob = model.probability(sample_vec)
        assert 0.0 <= prob <= 1.0

        expectancy = model.net_expectancy_r(prob)
        assert isinstance(expectancy, float)

    def test_gbdt_json_serialization_roundtrip(self):
        np.random.seed(42)
        X = np.random.randn(30, len(FEATURE_NAMES))
        y = (X[:, 0] > 0).astype(int)

        model = CalibratedGBDTModel(worker="TEST", strategy_name="SNR")
        model.fit(X, y, n_estimators=20, max_depth=2)

        data = model.to_dict()
        assert data["model_type"] == "LIGHTGBM"
        assert "model_str" in data

        # Serializar a JSON string y recuperar
        json_str = json.dumps(data)
        restored = CalibratedGBDTModel.from_dict(json.loads(json_str))

        assert restored.trained is True
        assert restored.worker == "TEST"
        assert restored.strategy_name == "SNR"

        # Predicción idéntica tras deserialización
        orig_prob = model.probability(list(X[0]))
        restored_prob = restored.probability(list(X[0]))
        assert abs(orig_prob - restored_prob) < 1e-6

    def test_calibrated_logistic_model_from_dict_delegates_to_gbdt(self):
        np.random.seed(42)
        X = np.random.randn(25, len(FEATURE_NAMES))
        y = (X[:, 0] > 0).astype(int)

        gbdt = CalibratedGBDTModel(worker="JUMP", strategy_name="ALL")
        gbdt.fit(X, y, n_estimators=15)
        gbdt_dict = gbdt.to_dict()

        # CalibratedLogisticModel.from_dict debe detectar model_type='LIGHTGBM' y devolver CalibratedGBDTModel
        loaded = CalibratedLogisticModel.from_dict(gbdt_dict)
        assert isinstance(loaded, CalibratedGBDTModel)
        assert loaded.worker == "JUMP"
        assert loaded.trained is True


class TestLiveEngineRegimeIntegration:
    """Verificación de la integración del gate en LiveTradingEngine."""

    def test_engine_has_regime_sentinel_initialized(self):
        from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
        from unittest.mock import MagicMock

        provider = MagicMock()
        executor = MagicMock()
        repo = MagicMock()

        config = LiveTradingConfig(
            market_regime_sentinel_enabled=True,
            market_regime_sentinel_mode="OBSERVE",
        )
        engine = LiveTradingEngine(provider=provider, executor=executor, repository=repo, config=config)

        assert hasattr(engine, "regime_sentinel")
        assert engine.regime_sentinel.config.mode == "OBSERVE"
        assert hasattr(engine, "_market_regime_entry_gate")

    def test_market_regime_entry_gate_blocks_when_filter_mode(self):
        from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
        from unittest.mock import MagicMock

        provider = MagicMock()
        executor = MagicMock()
        repo = MagicMock()

        # Simular velas tóxicas
        df_toxic = _generate_synthetic_ohlc("toxic_choppy", n=40)
        provider.get_candles.return_value = df_toxic

        config = LiveTradingConfig(
            market_regime_sentinel_enabled=True,
            market_regime_sentinel_mode="FILTER",
        )
        engine = LiveTradingEngine(provider=provider, executor=executor, repository=repo, config=config)
        engine.executor.get_current_tick.return_value = {"bid": 1.1000, "ask": 1.1002, "time": "2026-10-13T12:00:00Z"}

        result = engine._market_regime_entry_gate("EURUSD")
        assert result is not None
        assert result["action"] == "MARKET_REGIME_BLOCKED"
        assert "TOXIC" in result["reason"]
