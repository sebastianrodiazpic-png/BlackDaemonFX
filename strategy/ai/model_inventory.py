"""Inventario y catálogo de modelos de meta-etiquetado con IA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_DIR = PROJECT_ROOT / "storage" / "ai_models"


def classify_worker_family(worker: str) -> str:
    """Clasifica el worker en una familia operativa."""
    w = str(worker or "").upper()
    if any(k in w for k in ("BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP", "SYNTHETICS")):
        return "SINTETICOS"
    if "FOREX" in w:
        return "FOREX"
    if "GOLD" in w or "XAU" in w or "METAL" in w:
        return "COMMODITIES"
    if "ORB" in w or "INDEX" in w or "INDICES" in w:
        return "INDICES"
    if "MALAYSIAN" in w or "SNR" in w:
        return "MALAYSIAN_SNR"
    if "GLOBAL" in w:
        return "GLOBAL"
    return "OTROS"


def scan_trained_models_catalog(directory: str | Path | None = None) -> list[dict[str, Any]]:
    """Escanea el directorio de modelos de IA y genera el catálogo estructurado.

    Extrae para cada fichero `metalabel_*.json` las métricas de entrenamiento,
    muestras evaluadas, tasas de acierto, calibración walk-forward y frescura.
    """
    target_dir = Path(directory or DEFAULT_MODELS_DIR)
    if not target_dir.exists() or not target_dir.is_dir():
        return []

    catalog: list[dict[str, Any]] = []

    for path in sorted(target_dir.glob("metalabel_*.json")):
        if path.name.endswith("_metrics.json"):
            continue

        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue

        if not isinstance(content, dict):
            continue

        worker = str(content.get("worker") or path.stem.replace("metalabel_", "").split("_")[0]).upper()
        strategy_name = str(content.get("strategy_name") or "ALL").upper()
        model_obj = content.get("model") if isinstance(content.get("model"), dict) else {}
        calibrator_obj = content.get("calibrator") if isinstance(content.get("calibrator"), dict) else {}

        # Intentar cargar archivo complementario de métricas si existe
        metrics_candidates = [
            target_dir / f"metalabel_{worker}_{strategy_name}_metrics.json",
            target_dir / f"metalabel_{worker}_metrics.json",
        ]
        metrics_extra: dict[str, Any] = {}
        for mc in metrics_candidates:
            if mc.exists():
                try:
                    metrics_extra = json.loads(mc.read_text(encoding="utf-8")) or {}
                    break
                except Exception:
                    pass

        trained = bool(model_obj.get("trained") or content.get("trained"))
        samples = (
            model_obj.get("samples")
            or metrics_extra.get("samples")
            or metrics_extra.get("train_samples")
            or 0
        )
        positive_rate = (
            model_obj.get("positive_rate")
            or metrics_extra.get("win_rate_base")
            or 0.0
        )
        avg_win_rr = content.get("average_win_rr") or metrics_extra.get("average_win_rr") or 0.0
        avg_loss_rr = content.get("average_loss_rr") or metrics_extra.get("average_loss_rr") or 1.0
        trained_at = content.get("trained_at") or metrics_extra.get("trained_at")
        calibrated = bool(calibrator_obj.get("trained"))
        feature_names = model_obj.get("feature_names") or []
        features_count = len(feature_names) if isinstance(feature_names, list) else 0

        catalog.append({
            "filename": path.name,
            "worker": worker,
            "strategy_name": strategy_name,
            "family": classify_worker_family(worker),
            "trained": trained,
            "samples": int(samples) if samples is not None else 0,
            "positive_rate": round(float(positive_rate), 4) if positive_rate is not None else 0.0,
            "average_win_rr": round(float(avg_win_rr), 2) if avg_win_rr is not None else 0.0,
            "average_loss_rr": round(float(avg_loss_rr), 2) if avg_loss_rr is not None else 1.0,
            "calibrated": calibrated,
            "trained_at": trained_at,
            "feature_schema": content.get("feature_schema", "meta-features-v5"),
            "features_count": features_count,
            "accuracy": metrics_extra.get("accuracy"),
            "status": "MODELO ENTRENADO Y ACTIVO" if trained else "EN PREPARACIÓN",
        })

    # Ordenar por familia, luego worker, luego estrategia
    family_order = {"SINTETICOS": 1, "MALAYSIAN_SNR": 2, "FOREX": 3, "COMMODITIES": 4, "INDICES": 5, "GLOBAL": 6, "OTROS": 7}
    catalog.sort(key=lambda item: (family_order.get(item["family"], 99), item["worker"], item["strategy_name"]))

    return catalog
