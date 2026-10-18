"""Modelo de Meta-Etiquetado basado en Gradient Boosted Decision Trees (GBDT / LightGBM).

Capa 2 (Micro / Puntería Quirúrgica): Evalúa la probabilidad de éxito de cada
señal candidata individual considerando relaciones no lineales complejas entre
score técnico, spread, hora de sesión, alineación y confirmaciones.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from strategy.ai.feature_extraction import FEATURE_NAMES
from strategy.ai.model import ProbabilityCalibrator

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


@dataclass
class CalibratedGBDTModel:
    """Modelo meta-etiquetador ensamblado con árboles de gradiente calibrados.

    Guarda su estructura de árboles como texto nativo de LightGBM (model_str),
    lo que permite serializarlo íntegramente en formato JSON sin pickles binarios
    y ejecutar inferencias ultrarrápidas (< 0.5 ms).
    """

    worker: str = "DEFAULT"
    strategy_name: str = "ALL"
    model_type: str = "LIGHTGBM"
    feature_names: tuple[str, ...] = FEATURE_NAMES
    model_str: str = ""
    calibrator: ProbabilityCalibrator = field(default_factory=ProbabilityCalibrator)
    trained: bool = False
    samples: int = 0
    positive_rate: float = 0.0
    average_win_rr: float = 1.0
    average_loss_rr: float = 1.0
    trained_at: str | None = None
    feature_importances: dict[str, float] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._booster: Any = None
        if self.model_str and LIGHTGBM_AVAILABLE:
            try:
                self._booster = lgb.Booster(model_str=self.model_str)
            except Exception:
                self._booster = None

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        *,
        n_estimators: int = 80,
        max_depth: int = 4,
        learning_rate: float = 0.03,
        min_child_samples: int = 8,
    ) -> CalibratedGBDTModel:
        """Entrena los árboles de decisión por boosting y calibra las probabilidades."""
        if not LIGHTGBM_AVAILABLE:
            raise RuntimeError("LightGBM no está instalado en este entorno.")

        X_arr = np.asarray(X_train, dtype=float)
        y_arr = np.asarray(y_train, dtype=int)
        n_samples = len(y_arr)
        if n_samples < 5 or len(set(y_arr.tolist())) < 2:
            return self

        # Crear y entrenar clasificador LightGBM
        clf = lgb.LGBMClassifier(
            n_estimators=max(10, int(n_estimators)),
            max_depth=max(2, int(max_depth)),
            learning_rate=float(learning_rate),
            min_child_samples=max(2, min(min_child_samples, n_samples // 3)),
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            verbose=-1,
        )

        clf.fit(X_arr, y_arr)
        booster = clf.booster_
        self.model_str = booster.model_to_string()
        self._booster = booster
        self.trained = True
        self.samples = n_samples
        self.positive_rate = float(np.mean(y_arr))

        # Importancia de características normalizada
        raw_importances = booster.feature_importance(importance_type="gain")
        total_gain = float(np.sum(raw_importances)) if np.sum(raw_importances) > 1e-12 else 1.0
        self.feature_importances = {
            name: round(float(raw_importances[i]) / total_gain, 4)
            for i, name in enumerate(self.feature_names[: len(raw_importances)])
        }

        # Calibración de probabilidad con split de validación si está disponible
        if X_val is not None and y_val is not None and len(y_val) >= 2:
            val_probs = self.predict_proba(X_val)
            self.calibrator = ProbabilityCalibrator().fit(val_probs, np.asarray(y_val, dtype=int))
        else:
            # Calibración in-sample si no hay holdout explícito
            train_probs = self.predict_proba(X_arr)
            self.calibrator = ProbabilityCalibrator().fit(train_probs, y_arr)

        self.trained_at = datetime.now(timezone.utc).isoformat()
        return self

    def predict_proba(self, X: np.ndarray | list[list[float]]) -> np.ndarray:
        """Calcula probabilidades brutas previas a la calibración."""
        if not self.trained or not LIGHTGBM_AVAILABLE:
            base = max(0.01, min(0.99, self.positive_rate or 0.50))
            arr = np.asarray(X, dtype=float)
            length = arr.shape[0] if arr.ndim > 1 else 1
            return np.full(length, base, dtype=float)

        if self._booster is None and self.model_str:
            try:
                self._booster = lgb.Booster(model_str=self.model_str)
            except Exception:
                return np.full(len(X), self.positive_rate or 0.50, dtype=float)

        arr = np.asarray(X, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        raw_preds = self._booster.predict(arr)
        return np.asarray(raw_preds, dtype=float)

    def probability(self, features: list[float] | np.ndarray) -> float:
        """Devuelve la probabilidad calibrada final para un vector de características."""
        if not self.trained:
            return float(self.positive_rate or 0.50)

        vec = np.asarray(features, dtype=float)
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)

        raw_p = float(self.predict_proba(vec)[0])
        if self.calibrator.trained:
            calibrated = float(self.calibrator.calibrate(raw_p))
            return float(np.clip(calibrated, 0.0, 1.0))
        return float(np.clip(raw_p, 0.0, 1.0))

    def net_expectancy_r(self, probability: float) -> float:
        """Calcula la expectativa neta esperada en múltiplos de riesgo (R)."""
        p = float(np.clip(probability, 0.0, 1.0))
        win_rr = max(0.1, float(self.average_win_rr))
        loss_rr = max(0.1, float(self.average_loss_rr))
        return float(p * win_rr - (1.0 - p) * loss_rr)

    def to_dict(self) -> dict[str, Any]:
        """Serializa el modelo completo en un diccionario JSON-compatible."""
        return {
            "worker": self.worker,
            "strategy_name": self.strategy_name,
            "model_type": self.model_type,
            "trained": self.trained,
            "samples": self.samples,
            "positive_rate": self.positive_rate,
            "average_win_rr": self.average_win_rr,
            "average_loss_rr": self.average_loss_rr,
            "trained_at": self.trained_at,
            "feature_names": list(self.feature_names),
            "feature_importances": self.feature_importances,
            "model_str": self.model_str,
            "calibrator": self.calibrator.to_dict(),
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibratedGBDTModel:
        """Reconstruye un modelo desde su representación JSON serializada."""
        calibrator_data = data.get("calibrator", {})
        calibrator = ProbabilityCalibrator.from_dict(calibrator_data) if calibrator_data else ProbabilityCalibrator()
        return cls(
            worker=str(data.get("worker", "DEFAULT")),
            strategy_name=str(data.get("strategy_name", "ALL")),
            model_type=str(data.get("model_type", "LIGHTGBM")),
            feature_names=tuple(data.get("feature_names", FEATURE_NAMES)),
            model_str=str(data.get("model_str", "")),
            calibrator=calibrator,
            trained=bool(data.get("trained", False)),
            samples=int(data.get("samples", 0)),
            positive_rate=float(data.get("positive_rate", 0.0)),
            average_win_rr=float(data.get("average_win_rr", 1.0)),
            average_loss_rr=float(data.get("average_loss_rr", 1.0)),
            trained_at=data.get("trained_at"),
            feature_importances=dict(data.get("feature_importances", {})),
            provenance=dict(data.get("provenance", {})),
        )
