"""Modelo probabilístico del meta-etiquetado.

Regresión logística implementada con NumPy (sin dependencias nuevas) y una
calibración isotónica ligera para que la probabilidad sea comparable entre
workers e instrumentos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from strategy.ai.feature_extraction import FEATURE_NAMES


@dataclass
class LogisticRegressionModel:
    """Clasificador binario entrenado por descenso de gradiente."""

    feature_names: tuple[str, ...] = FEATURE_NAMES
    weights: list[float] = field(default_factory=list)
    bias: float = 0.0
    mean: list[float] = field(default_factory=list)
    scale: list[float] = field(default_factory=list)
    trained: bool = False
    samples: int = 0
    positive_rate: float = 0.0

    @staticmethod
    def _sigmoid(values: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(values, -35.0, 35.0)))

    def fit(
        self,
        features: np.ndarray | list[list[float]],
        labels: np.ndarray | list[int],
        *,
        learning_rate: float = 0.10,
        epochs: int = 600,
        l2: float = 1e-3,
    ) -> "LogisticRegressionModel":
        matrix = np.asarray(features, dtype=float)
        target = np.asarray(labels, dtype=float).ravel()
        if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[0] != target.shape[0]:
            self.trained = False
            return self

        mean = matrix.mean(axis=0)
        scale = matrix.std(axis=0)
        scale[scale < 1e-9] = 1.0
        standard = (matrix - mean) / scale

        rows, columns = standard.shape
        weights = np.zeros(columns, dtype=float)
        bias = 0.0
        # Arranque informado: el sesgo parte del log-odds de la muestra.
        positive_rate = float(np.clip(target.mean(), 1e-6, 1 - 1e-6))
        bias = float(np.log(positive_rate / (1.0 - positive_rate)))

        for _ in range(max(1, int(epochs))):
            predictions = self._sigmoid(standard @ weights + bias)
            error = predictions - target
            gradient_w = (standard.T @ error) / rows + l2 * weights
            gradient_b = float(error.mean())
            weights -= learning_rate * gradient_w
            bias -= learning_rate * gradient_b

        self.weights = [float(value) for value in weights]
        self.bias = float(bias)
        self.mean = [float(value) for value in mean]
        self.scale = [float(value) for value in scale]
        self.samples = int(rows)
        self.positive_rate = float(target.mean())
        self.trained = True
        return self

    def predict_proba(self, features: np.ndarray | list[list[float]]) -> np.ndarray:
        matrix = np.asarray(features, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        if not self.trained or not self.weights:
            return np.full(matrix.shape[0], float(self.positive_rate or 0.5))
        mean = np.asarray(self.mean, dtype=float)
        scale = np.asarray(self.scale, dtype=float)
        weights = np.asarray(self.weights, dtype=float)
        standard = (matrix - mean) / scale
        return self._sigmoid(standard @ weights + self.bias)

    def predict_one(self, vector: list[float]) -> float:
        return float(self.predict_proba([vector])[0])

    def to_dict(self) -> dict:
        return {
            "feature_names": list(self.feature_names),
            "weights": list(self.weights),
            "bias": float(self.bias),
            "mean": list(self.mean),
            "scale": list(self.scale),
            "trained": bool(self.trained),
            "samples": int(self.samples),
            "positive_rate": float(self.positive_rate),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "LogisticRegressionModel":
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            feature_names=tuple(payload.get("feature_names") or FEATURE_NAMES),
            weights=[float(v) for v in (payload.get("weights") or [])],
            bias=float(payload.get("bias", 0.0)),
            mean=[float(v) for v in (payload.get("mean") or [])],
            scale=[float(v) for v in (payload.get("scale") or [])],
            trained=bool(payload.get("trained", False)),
            samples=int(payload.get("samples", 0)),
            positive_rate=float(payload.get("positive_rate", 0.0)),
        )


@dataclass
class ProbabilityCalibrator:
    """Calibración por binning isotónico: ajusta la probabilidad a la frecuencia real."""

    bin_edges: list[float] = field(default_factory=list)
    bin_values: list[float] = field(default_factory=list)
    trained: bool = False

    def fit(
        self,
        probabilities: np.ndarray | list[float],
        labels: np.ndarray | list[int],
        *,
        bins: int = 10,
    ) -> "ProbabilityCalibrator":
        probs = np.asarray(probabilities, dtype=float).ravel()
        target = np.asarray(labels, dtype=float).ravel()
        if probs.size == 0 or probs.size != target.size:
            self.trained = False
            return self

        bins = max(2, min(int(bins), max(2, probs.size // 5 or 2)))
        edges = np.linspace(0.0, 1.0, bins + 1)
        values = []
        global_rate = float(target.mean())
        for index in range(bins):
            low, high = edges[index], edges[index + 1]
            if index == bins - 1:
                mask = (probs >= low) & (probs <= high)
            else:
                mask = (probs >= low) & (probs < high)
            values.append(float(target[mask].mean()) if mask.any() else global_rate)

        # Monotonía: la probabilidad calibrada nunca debe decrecer.
        for index in range(1, len(values)):
            values[index] = max(values[index], values[index - 1])

        self.bin_edges = [float(v) for v in edges]
        self.bin_values = values
        self.trained = True
        return self

    def calibrate(self, probability: float) -> float:
        value = float(np.clip(probability, 0.0, 1.0))
        if not self.trained or not self.bin_values:
            return value
        edges = self.bin_edges
        for index in range(len(self.bin_values)):
            high = edges[index + 1]
            if value < high or index == len(self.bin_values) - 1:
                return float(np.clip(self.bin_values[index], 0.0, 1.0))
        return value

    def to_dict(self) -> dict:
        return {
            "bin_edges": list(self.bin_edges),
            "bin_values": list(self.bin_values),
            "trained": bool(self.trained),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ProbabilityCalibrator":
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            bin_edges=[float(v) for v in (payload.get("bin_edges") or [])],
            bin_values=[float(v) for v in (payload.get("bin_values") or [])],
            trained=bool(payload.get("trained", False)),
        )


@dataclass
class CalibratedLogisticModel:
    """Modelo entrenado por worker: regresión logística + calibración."""

    worker: str = "DEFAULT"
    strategy_name: str = "ALL"
    model: LogisticRegressionModel = field(default_factory=LogisticRegressionModel)
    calibrator: ProbabilityCalibrator = field(default_factory=ProbabilityCalibrator)
    trained_at: str | None = None
    average_win_rr: float = 1.0
    average_loss_rr: float = 1.0

    @property
    def trained(self) -> bool:
        return bool(self.model.trained)

    def probability(self, vector: list[float]) -> float:
        raw = self.model.predict_one(vector)
        return float(self.calibrator.calibrate(raw))

    def net_expectancy_r(self, probability: float) -> float:
        """Expectativa neta en R: p*ganancia media - (1-p)*pérdida media."""
        probability = float(np.clip(probability, 0.0, 1.0))
        win = abs(float(self.average_win_rr or 0.0))
        loss = abs(float(self.average_loss_rr or 0.0))
        return probability * win - (1.0 - probability) * loss

    def to_dict(self) -> dict:
        return {
            "worker": self.worker,
            "strategy_name": self.strategy_name,
            "model": self.model.to_dict(),
            "calibrator": self.calibrator.to_dict(),
            "trained_at": self.trained_at,
            "average_win_rr": float(self.average_win_rr),
            "average_loss_rr": float(self.average_loss_rr),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "CalibratedLogisticModel":
        payload = payload if isinstance(payload, dict) else {}
        return cls(
            worker=str(payload.get("worker") or "DEFAULT"),
            strategy_name=str(payload.get("strategy_name") or "ALL"),
            model=LogisticRegressionModel.from_dict(payload.get("model") or {}),
            calibrator=ProbabilityCalibrator.from_dict(payload.get("calibrator") or {}),
            trained_at=payload.get("trained_at"),
            average_win_rr=float(payload.get("average_win_rr", 1.0)),
            average_loss_rr=float(payload.get("average_loss_rr", 1.0)),
        )
