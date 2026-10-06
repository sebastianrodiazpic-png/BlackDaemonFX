"""Pruebas unitarias para las 4 mejoras críticas de aprendizaje e IA en storage/ai_models.

1. Mejora 1: Agrupamiento Jerárquico Global (Cross-Worker Pooling)
2. Mejora 2: Estabilización Numérica y Gradient Clipping en model.py
3. Mejora 3: 4 Nuevas Variables Predictivas Clave y Migración de Esquema v4 -> v5
4. Mejora 4: Bucle de Aprendizaje Continuo en Tiempo Real (Online Feedback Loop)
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from strategy.ai import (
    FEATURE_NAMES,
    CalibratedLogisticModel,
    LogisticRegressionModel,
    MetaLabelingConfig,
    MetaLabelingEngine,
    ProbabilityCalibrator,
    build_training_dataset,
    extract_meta_features,
    feature_vector,
    train_worker_model,
)
from strategy.ai.feature_extraction import (
    FEATURE_NAMES_V4,
    FEATURE_SCHEMA,
    NEW_PREDICTIVE_FEATURES,
    upgrade_v4_features_to_v5,
)
from strategy.execution.trade_executor import TradeExecutor
from trade_lifecycle_manager import (
    EVENT_POSITION_CLOSED,
    STATE_EXECUTION,
    TradeLifecycle,
    TradeLifecycleManager,
)


BASE_TIME = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def _make_sample_signal(
    *,
    symbol="Boom 1000 Index",
    worker="BOOM",
    score=88.0,
    adx=24.0,
    entry=1000.0,
    sl=990.0,
    tp=1020.0,
    age_minutes=0.5,
    hour=13,
):
    eval_time = datetime(2026, 9, 29, hour, 30, tzinfo=timezone.utc)
    return {
        "symbol": symbol,
        "worker": worker,
        "bot_profile": worker,
        "direction": "BUY",
        "trade_score": score,
        "confirmation_percentage": score,
        "adx": adx,
        "atr": 5.0,
        "spread": 1.0,
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "risk_reward_ratio": 2.0,
        "signal_age_minutes": age_minutes,
        "entry_time": eval_time.isoformat(),
        "timeframe": "M5",
        "action": "SMC_CONFIRMATION_ENTRY",
    }


class TestMejora1HierarchicalCrossWorkerPooling:
    """Mejora 1: Agrupamiento Jerárquico Global."""

    def test_categorical_family_features_exist_in_schema(self):
        """Verifica que las variables categóricas de familia pertenezcan al esquema canónico."""
        for name in ("is_boom", "is_crash", "is_volatility", "is_forex", "is_gold", "is_step", "is_jump"):
            assert name in FEATURE_NAMES
            assert name in NEW_PREDICTIVE_FEATURES

    def test_worker_pooling_when_samples_below_threshold(self, tmp_path):
        """Si un worker no alcanza min_samples, debe entrenar usando el dataset global compartido."""
        trades = []
        # Crear 20 operaciones globales mixtas
        for i in range(20):
            win = i % 2 == 0
            is_boom = i < 3  # BOOM solo tiene 3 operaciones
            prof = "BOOM" if is_boom else "VOLATILITY"
            t_time = BASE_TIME + timedelta(hours=i)
            sig = _make_sample_signal(symbol="Boom 1000" if is_boom else "Volatility 75", worker=prof)
            feat = extract_meta_features(signal=sig, analysis=sig, market=sig, evaluated_at=t_time)
            trades.append({
                "entry_time": t_time.isoformat(),
                "exit_time": (t_time + timedelta(minutes=30)).isoformat(),
                "status": "CLOSED",
                "realized_rr": 2.0 if win else -1.0,
                "net_pnl": 20.0 if win else -10.0,
                "details": {
                    "metadata": {
                        "bot_profile": prof,
                        "strategy_name": "SMC",
                        "entry_learning_snapshot": {
                            "schema": "entry-learning-v5",
                            "features": feat,
                            "feature_names": list(FEATURE_NAMES),
                        },
                    }
                },
            })

        # Sin pooling, BOOM fallaría por tener solo 3 muestras < 15
        model_no_pool = train_worker_model(trades, worker="BOOM", min_samples=15, allow_global_pooling=False)
        assert not model_no_pool.trained

        # Con pooling jerárquico global, BOOM entrena usando el dataset global
        model_pooled = train_worker_model(trades, worker="BOOM", min_samples=15, allow_global_pooling=True)
        assert model_pooled.trained
        assert model_pooled.samples == 20
        assert len(model_pooled.model.weights) == len(FEATURE_NAMES)

    def test_hierarchical_fallback_to_global_model_on_engine_load(self, tmp_path):
        """Un worker sin modelo propio entrenado hereda el modelo GLOBAL_ALL si existe."""
        config = MetaLabelingConfig(model_directory=str(tmp_path))
        global_engine = MetaLabelingEngine(config, worker="GLOBAL")
        
        # Crear y guardar un modelo global válido
        m = LogisticRegressionModel(
            feature_names=FEATURE_NAMES,
            weights=[0.1] * len(FEATURE_NAMES),
            bias=0.2,
            mean=[0.0] * len(FEATURE_NAMES),
            scale=[1.0] * len(FEATURE_NAMES),
            trained=True,
            samples=50,
            positive_rate=0.55,
        )
        global_calibrated = CalibratedLogisticModel(
            worker="GLOBAL",
            strategy_name="ALL",
            model=m,
            calibrator=ProbabilityCalibrator().fit([0.5, 0.6], [0, 1]),
            trained_at=datetime.now(timezone.utc).isoformat(),
        )
        global_engine.save_model(global_calibrated)

        # Worker nuevo (ej. JUMP) que no tiene archivo propio
        jump_engine = MetaLabelingEngine(config, worker="JUMP")
        loaded_model = jump_engine.load_model("SMC")
        assert loaded_model.trained
        assert loaded_model.model.samples == 50
        assert loaded_model.model.weights == m.weights


class TestMejora2NumericalStabilityAndGradientClipping:
    """Mejora 2: Estabilización Numérica y Gradient Clipping."""

    def test_gradient_clipping_prevents_overflow_on_exploding_gradients(self):
        """Valores extremos o desescalados no deben provocar NaN ni divergencia infinita."""
        rows = 100
        cols = len(FEATURE_NAMES)
        # Matriz con valores gigantescos que normalmente causarían overflow/NaN
        np.random.seed(42)
        extreme_features = np.random.randn(rows, cols) * 1000.0
        labels = np.random.randint(0, 2, size=rows)

        model = LogisticRegressionModel(feature_names=FEATURE_NAMES)
        model.fit(extreme_features, labels, learning_rate=0.5, epochs=100)

        assert model.trained
        assert np.all(np.isfinite(model.weights))
        assert np.isfinite(model.bias)
        assert not any(math.isnan(w) for w in model.weights)

    def test_online_sgd_step_is_clipped(self):
        """Paso estocástico individual con vector desproporcionado debe clipear a norma 5.0."""
        model = LogisticRegressionModel(
            feature_names=FEATURE_NAMES,
            weights=[0.0] * len(FEATURE_NAMES),
            bias=0.0,
            mean=[0.0] * len(FEATURE_NAMES),
            scale=[1.0] * len(FEATURE_NAMES),
            trained=True,
            samples=10,
            positive_rate=0.5,
        )
        vector = [1e6] * len(FEATURE_NAMES)
        ok = model.update_one(vector, label=1, learning_rate=0.1)
        assert ok
        assert np.all(np.isfinite(model.weights))
        # El cambio máximo en peso debe estar acotado por learning_rate * clipping (0.1 * 5.0 = 0.5)
        max_delta = max(abs(w) for w in model.weights)
        assert max_delta <= 1.0


class TestMejora3PredictiveFeaturesAndSchemaUpgrade:
    """Mejora 3: 4 Nuevas Variables Predictivas Clave."""

    def test_adx_regime_boolean_threshold(self):
        """ADX >= 20 debe marcar 1.0; ADX < 20 debe marcar 0.0."""
        sig_active = _make_sample_signal(adx=20.5)
        f_active = extract_meta_features(signal=sig_active, analysis=sig_active, market=sig_active)
        assert f_active["adx_regime"] == 1.0

        sig_weak = _make_sample_signal(adx=16.1)
        f_weak = extract_meta_features(signal=sig_weak, analysis=sig_weak, market=sig_weak)
        assert f_weak["adx_regime"] == 0.0

    def test_signal_age_penalty_exponential_decay(self):
        """Edad cero debe tener penalización neutra (1.0); edad mayor decae exponencialmente."""
        sig_fresh = _make_sample_signal(age_minutes=0.0)
        f_fresh = extract_meta_features(signal=sig_fresh, analysis={"signal_age": {"age_minutes": 0.0}}, market=sig_fresh)
        assert pytest.approx(f_fresh["signal_age_penalty"], rel=1e-3) == 1.0

        sig_delayed = _make_sample_signal(age_minutes=2.0)
        f_delayed = extract_meta_features(signal=sig_delayed, analysis={"signal_age": {"age_minutes": 2.0}}, market=sig_delayed)
        assert f_delayed["signal_age_penalty"] < 1.0
        assert f_delayed["signal_age_penalty"] > 0.0

    def test_spread_to_sl_ratio_calculation(self):
        """Spread / distancia al SL."""
        # Entry 1000, SL 990 -> dist = 10. Spread = 1.0 -> ratio = 0.10 (10%)
        sig = _make_sample_signal(entry=1000.0, sl=990.0)
        sig["spread"] = 1.0
        features = extract_meta_features(signal=sig, analysis=sig, market=sig)
        assert pytest.approx(features["spread_to_sl_ratio"], abs=1e-4) == 0.10

    def test_session_killzone_active(self):
        """Horas de Londres (7-10 UTC) y NY (12-16 UTC) marcan 1.0; otras marcan 0.0."""
        # 13:00 UTC (NY)
        sig_ny = _make_sample_signal(hour=13)
        t_ny = datetime(2026, 9, 29, 13, 0, tzinfo=timezone.utc)
        f_ny = extract_meta_features(signal=sig_ny, analysis=sig_ny, market=sig_ny, evaluated_at=t_ny)
        assert f_ny["session_killzone_active"] == 1.0

        # 08:00 UTC (Londres)
        sig_lon = _make_sample_signal(hour=8)
        t_lon = datetime(2026, 9, 29, 8, 0, tzinfo=timezone.utc)
        f_lon = extract_meta_features(signal=sig_lon, analysis=sig_lon, market=sig_lon, evaluated_at=t_lon)
        assert f_lon["session_killzone_active"] == 1.0

        # 21:00 UTC (Fuera de killzone)
        sig_off = _make_sample_signal(hour=21)
        t_off = datetime(2026, 9, 29, 21, 0, tzinfo=timezone.utc)
        f_off = extract_meta_features(signal=sig_off, analysis=sig_off, market=sig_off, evaluated_at=t_off)
        assert f_off["session_killzone_active"] == 0.0

    def test_upgrade_v4_features_to_v5_preserves_evidence(self):
        """Un snapshot capturado en v4 se completa a v5 sin perder causalidad."""
        v4_dict = {name: 0.5 for name in FEATURE_NAMES_V4}
        v4_dict["adx"] = 25.0
        v4_dict["signal_age_minutes"] = 0.5
        v4_dict["spread_ratio"] = 0.05

        v5_dict = upgrade_v4_features_to_v5(
            v4_dict,
            row_meta={"bot_profile": "CRASH", "instrument": "Crash 500 Index"},
            entry_time=datetime(2026, 9, 29, 14, 0, tzinfo=timezone.utc),
        )
        assert len(v5_dict) == len(FEATURE_NAMES)
        assert v5_dict["adx_regime"] == 1.0
        assert v5_dict["is_crash"] == 1.0
        assert v5_dict["is_boom"] == 0.0
        assert v5_dict["session_killzone_active"] == 1.0


class TestMejora4OnlineFeedbackLoop:
    """Mejora 4: Bucle de Aprendizaje Continuo en Tiempo Real (Online SGD)."""

    def test_trade_lifecycle_manager_emits_position_closed_and_updates_ai(self, tmp_path):
        """Al cerrarse una posición en TradeLifecycleManager, el evento POSITION_CLOSED actualiza la IA."""
        config = MetaLabelingConfig(model_directory=str(tmp_path))
        engine = MetaLabelingEngine(config, worker="BOOM")
        
        # Guardar modelo base
        base_model = CalibratedLogisticModel(
            worker="BOOM",
            strategy_name="ALL",
            model=LogisticRegressionModel(
                feature_names=FEATURE_NAMES,
                weights=[0.0] * len(FEATURE_NAMES),
                bias=0.0,
                mean=[0.0] * len(FEATURE_NAMES),
                scale=[1.0] * len(FEATURE_NAMES),
                trained=True,
                samples=20,
                positive_rate=0.5,
            ),
            calibrator=ProbabilityCalibrator().fit([0.4, 0.6], [0, 1]),
            trained_at=datetime.now(timezone.utc).isoformat(),
        )
        engine.save_model(base_model)

        # También crear el global
        global_engine = MetaLabelingEngine(config, worker="GLOBAL")
        global_model = CalibratedLogisticModel(
            worker="GLOBAL",
            strategy_name="ALL",
            model=LogisticRegressionModel(
                feature_names=FEATURE_NAMES,
                weights=[0.0] * len(FEATURE_NAMES),
                bias=0.0,
                mean=[0.0] * len(FEATURE_NAMES),
                scale=[1.0] * len(FEATURE_NAMES),
                trained=True,
                samples=20,
                positive_rate=0.5,
            ),
            calibrator=ProbabilityCalibrator().fit([0.4, 0.6], [0, 1]),
            trained_at=datetime.now(timezone.utc).isoformat(),
        )
        global_engine.save_model(global_model)

        received_events = []
        def on_closed_callback(lifecycle):
            received_events.append(lifecycle)

        tlm = TradeLifecycleManager(
            trade_simulator=lambda **kwargs: {"result": "win"},
            on_position_closed=on_closed_callback,
            meta_labeling_engine=engine,
        )

        signal = _make_sample_signal(symbol="Boom 1000 Index", worker="BOOM", entry=1000.0, sl=990.0, tp=1020.0)
        feat = extract_meta_features(signal=signal, analysis=signal, market=signal)
        signal["entry_learning_snapshot"] = {
            "schema": "entry-learning-v5",
            "features": feat,
            "feature_names": list(FEATURE_NAMES),
        }
        signal["model_directory"] = str(tmp_path)

        lifecycle = tlm.create_from_signal(signal)
        lifecycle.state = STATE_EXECUTION
        lifecycle.position_ticket = "12345"

        # Simular cierre manual de la posición
        class FakeExecutor(TradeExecutor):
            def execute_trade(self, request):
                pass
            def close_position(self, position_ticket, reason):
                return {
                    "closed": True,
                    "exit_price": 1020.0,
                    "realized_pnl_price": 20.0,
                    "reason": "take_profit",
                }
            def get_position(self, ticket):
                return None

        tlm._active_lifecycles[str(lifecycle.position_ticket)] = lifecycle
        res = tlm.close_execution(lifecycle, trade_executor=FakeExecutor(), reason="take_profit")
        assert res["closed"]

        # Verificar que callback se invocó
        assert len(received_events) == 1
        assert received_events[0] is lifecycle

        # Verificar que el modelo se actualizó y persistió en caliente
        reloaded = engine.load_model("ALL", reload=True)
        assert reloaded.model.samples == 21
        assert reloaded.model.weights != [0.0] * len(FEATURE_NAMES)
        assert reloaded.average_win_rr > 1.0  # Realized RR = 2.0 subió la media

    def test_isotonic_calibrator_online_recalibration(self):
        """ProbabilityCalibrator.update_one ajusta el bin manteniendo la monotonía."""
        calibrator = ProbabilityCalibrator().fit([0.2, 0.4, 0.6, 0.8], [0, 0, 1, 1], bins=4)
        assert calibrator.trained
        old_val = calibrator.bin_values[-1]

        # Actualizar el bin alto con una victoria
        updated = calibrator.update_one(probability=0.85, label=1, weight=0.1)
        assert updated
        # Debe mantenerse la monotonía no decreciente
        for i in range(1, len(calibrator.bin_values)):
            assert calibrator.bin_values[i] >= calibrator.bin_values[i - 1]

    def test_cache_freshness_reloads_on_external_file_update(self, tmp_path):
        """Si otro proceso/worker modifica el JSON en disco, el siguiente score recarga el modelo fresco."""
        config = MetaLabelingConfig(model_directory=str(tmp_path))
        engine1 = MetaLabelingEngine(config, worker="VOLATILITY")
        engine2 = MetaLabelingEngine(config, worker="VOLATILITY")

        model1 = CalibratedLogisticModel(
            worker="VOLATILITY",
            strategy_name="ALL",
            model=LogisticRegressionModel(
                feature_names=FEATURE_NAMES,
                weights=[1.0] * len(FEATURE_NAMES),
                bias=0.0,
                mean=[0.0] * len(FEATURE_NAMES),
                scale=[1.0] * len(FEATURE_NAMES),
                trained=True,
                samples=20,
            ),
        )
        engine1.save_model(model1)

        # Engine 2 carga el modelo inicial
        m2 = engine2.load_model("ALL")
        assert m2.model.weights[0] == 1.0

        # Engine 1 actualiza el archivo en disco (simulando cierre de posición)
        time.sleep(0.05)
        model1.model.weights = [2.5] * len(FEATURE_NAMES)
        engine1.save_model(model1)

        # Engine 2 debe detectar el mtime modificado y recargar los pesos nuevos sin reiniciar
        m2_refreshed = engine2.load_model("ALL")
        assert m2_refreshed.model.weights[0] == 2.5
