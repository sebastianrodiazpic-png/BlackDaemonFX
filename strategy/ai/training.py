"""Entrenamiento y validación temporal del meta-etiquetado.

La validación es estrictamente temporal (walk-forward): un modelo sólo se
evalúa sobre operaciones posteriores a las que usó para entrenar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from strategy.ai.feature_extraction import (
    FEATURE_NAMES,
    extract_meta_features,
    feature_vector,
)
from strategy.ai.model import CalibratedLogisticModel, LogisticRegressionModel, ProbabilityCalibrator


MIN_TRAINING_SAMPLES = 30


def _parse_details(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _row_metadata(row) -> dict:
    for key in ("details", "details_json"):
        details = _parse_details(row.get(key) if hasattr(row, "get") else None)
        metadata = details.get("metadata")
        if isinstance(metadata, dict):
            return metadata
    return {}


def _trade_label(row) -> int | None:
    """1 si la operación fue ganadora; 0 si fue perdedora. None si es indecisa."""
    status = str(row.get("status") or "").upper()
    if status == "OPEN":
        return None
    rr = row.get("realized_rr")
    pnl = row.get("net_pnl")
    try:
        rr = float(rr) if rr is not None else None
    except (TypeError, ValueError):
        rr = None
    try:
        pnl = float(pnl) if pnl is not None else None
    except (TypeError, ValueError):
        pnl = None
    # NaN aparece cuando el journal no registró el RR realizado.
    if rr is not None and rr != rr:
        rr = None
    if pnl is not None and pnl != pnl:
        pnl = None
    if rr is not None and abs(rr) > 1e-9:
        return 1 if rr > 0 else 0
    if pnl is not None and abs(pnl) > 1e-9:
        return 1 if pnl > 0 else 0
    return None


def _canonical_profile(value) -> str:
    """Normaliza `VOLATILITY_3`, `FOREX_2`, `SCALP_BOOM` a su familia de worker."""
    text = str(value or "").upper().strip()
    if not text:
        return ""
    if text.startswith("SCALP_"):
        text = text[len("SCALP_"):]
    for family in ("VOLATILITY", "FOREX", "BOOM", "CRASH", "STEP", "JUMP", "FLIP", "GOLD", "SYNTHETICS"):
        if text.startswith(family):
            return family
    return text


def _profiles_match(worker, metadata_profile) -> bool:
    wanted = str(worker or "").upper().strip()
    actual = str(metadata_profile or "").upper().strip()
    if not wanted:
        return True
    if wanted == actual:
        return True
    # Un worker de familia entrena con todas sus instancias numeradas.
    return _canonical_profile(wanted) == _canonical_profile(actual) and bool(_canonical_profile(wanted))


def build_training_dataset(
    trades,
    *,
    worker: str | None = None,
    strategy_name: str | None = None,
) -> dict:
    """Convierte el historial persistido en matriz de entrenamiento ordenada por tiempo."""
    if trades is None:
        return {"features": [], "labels": [], "times": [], "rr": [], "rows": 0}

    if isinstance(trades, pd.DataFrame):
        records = trades.to_dict("records")
    else:
        records = list(trades)

    samples = []
    for row in records:
        if not isinstance(row, dict):
            continue
        metadata = _row_metadata(row)
        if worker and not _profiles_match(worker, metadata.get("bot_profile")):
            continue
        if strategy_name and str(metadata.get("strategy_name") or "SMC").upper() != str(strategy_name).upper():
            continue

        label = _trade_label(row)
        if label is None:
            continue

        entry_time = row.get("entry_time")
        try:
            stamp = pd.to_datetime(entry_time, utc=True, errors="raise")
        except Exception:
            continue

        features = extract_meta_features(
            signal=metadata,
            analysis=metadata,
            market={
                "planned_rr": row.get("planned_rr"),
                "risk_percent": row.get("risk_percent"),
                "entry_price": row.get("entry_price"),
            },
            evaluated_at=entry_time,
        )
        try:
            realized = float(row.get("realized_rr") or 0.0)
        except (TypeError, ValueError):
            realized = 0.0

        samples.append((stamp, feature_vector(features), int(label), realized))

    samples.sort(key=lambda item: item[0])
    return {
        "features": [item[1] for item in samples],
        "labels": [item[2] for item in samples],
        "times": [item[0] for item in samples],
        "rr": [item[3] for item in samples],
        "rows": len(samples),
        "feature_names": list(FEATURE_NAMES),
    }


def _average_outcomes(labels, rr_values) -> tuple[float, float]:
    wins = [abs(rr) for rr, label in zip(rr_values, labels) if label == 1 and abs(rr) > 1e-9]
    losses = [abs(rr) for rr, label in zip(rr_values, labels) if label == 0 and abs(rr) > 1e-9]
    average_win = float(np.mean(wins)) if wins else 1.0
    average_loss = float(np.mean(losses)) if losses else 1.0
    return average_win, average_loss


def train_worker_model(
    trades,
    *,
    worker: str = "DEFAULT",
    strategy_name: str | None = None,
    calibrate: bool = True,
    min_samples: int = MIN_TRAINING_SAMPLES,
) -> CalibratedLogisticModel:
    """Entrena el modelo de un worker con su propio historial."""
    dataset = build_training_dataset(trades, worker=worker, strategy_name=strategy_name)
    model = CalibratedLogisticModel(
        worker=str(worker or "DEFAULT"),
        strategy_name=str(strategy_name or "ALL"),
    )
    labels = dataset["labels"]
    if dataset["rows"] < max(2, int(min_samples)) or len(set(labels)) < 2:
        return model

    features = np.asarray(dataset["features"], dtype=float)
    target = np.asarray(labels, dtype=int)

    # Calibración fuera de muestra: último 30% reservado, respetando el orden temporal.
    split = int(len(target) * 0.70)
    split = max(1, min(split, len(target) - 1))

    model.model = LogisticRegressionModel().fit(features[:split], target[:split])
    if calibrate and len(set(target[split:].tolist())) >= 1:
        holdout_probs = model.model.predict_proba(features[split:])
        model.calibrator = ProbabilityCalibrator().fit(holdout_probs, target[split:])

    # El modelo final reaprovecha todo el historial ya calibrado.
    model.model = LogisticRegressionModel().fit(features, target)
    model.average_win_rr, model.average_loss_rr = _average_outcomes(labels, dataset["rr"])
    model.trained_at = datetime.now(timezone.utc).isoformat()
    return model


@dataclass
class TemporalValidationReport:
    """Resultado de la validación walk-forward."""

    folds: int = 0
    samples_evaluated: int = 0
    accuracy: float = 0.0
    brier_score: float = 1.0
    log_loss: float = 0.0
    base_rate: float = 0.0
    lift: float = 0.0
    fold_details: list = field(default_factory=list)
    valid: bool = False
    reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "folds": self.folds,
            "samples_evaluated": self.samples_evaluated,
            "accuracy": self.accuracy,
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "base_rate": self.base_rate,
            "lift": self.lift,
            "fold_details": self.fold_details,
            "valid": self.valid,
            "reason": self.reason,
        }


def temporal_validation(
    trades,
    *,
    worker: str = "DEFAULT",
    strategy_name: str | None = None,
    folds: int = 4,
    min_train_samples: int = 20,
) -> TemporalValidationReport:
    """Walk-forward: entrena con el pasado y evalúa únicamente el futuro inmediato."""
    dataset = build_training_dataset(trades, worker=worker, strategy_name=strategy_name)
    report = TemporalValidationReport()
    total = dataset["rows"]
    if total < max(4, int(min_train_samples) + 2):
        report.reason = "INSUFFICIENT_HISTORY_FOR_TEMPORAL_VALIDATION"
        return report

    features = np.asarray(dataset["features"], dtype=float)
    labels = np.asarray(dataset["labels"], dtype=int)
    folds = max(1, int(folds))

    start = max(int(min_train_samples), total // (folds + 1))
    step = max(1, (total - start) // folds)

    predictions: list[float] = []
    observed: list[int] = []
    for index in range(folds):
        train_end = start + index * step
        test_end = min(total, train_end + step)
        if train_end >= total or train_end < 2 or test_end <= train_end:
            break
        train_labels = labels[:train_end]
        if len(set(train_labels.tolist())) < 2:
            continue

        fold_model = LogisticRegressionModel().fit(features[:train_end], train_labels)
        calibrator = ProbabilityCalibrator()
        # Calibramos con la cola del bloque de entrenamiento, nunca con el test.
        inner = max(2, int(train_end * 0.70))
        if inner < train_end:
            calibrator.fit(
                fold_model.predict_proba(features[inner:train_end]),
                train_labels[inner:],
            )

        fold_probs = [
            float(calibrator.calibrate(value))
            for value in fold_model.predict_proba(features[train_end:test_end])
        ]
        fold_labels = labels[train_end:test_end].tolist()
        predictions.extend(fold_probs)
        observed.extend(fold_labels)
        report.fold_details.append({
            "fold": index + 1,
            "train_samples": int(train_end),
            "test_samples": int(test_end - train_end),
            "test_positive_rate": float(np.mean(fold_labels)) if fold_labels else 0.0,
        })

    if not predictions:
        report.reason = "NO_VALID_TEMPORAL_FOLDS"
        return report

    probs = np.asarray(predictions, dtype=float)
    truth = np.asarray(observed, dtype=float)
    clipped = np.clip(probs, 1e-6, 1 - 1e-6)

    report.folds = len(report.fold_details)
    report.samples_evaluated = int(truth.size)
    report.accuracy = float(np.mean((probs >= 0.5).astype(float) == truth))
    report.brier_score = float(np.mean((probs - truth) ** 2))
    report.log_loss = float(
        -np.mean(truth * np.log(clipped) + (1 - truth) * np.log(1 - clipped))
    )
    report.base_rate = float(truth.mean())
    baseline = max(report.base_rate, 1.0 - report.base_rate)
    report.lift = float(report.accuracy - baseline)
    report.valid = True
    return report
