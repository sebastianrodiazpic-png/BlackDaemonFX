"""Inventario y catálogo de modelos de meta-etiquetado con IA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_DIR = PROJECT_ROOT / "storage" / "ai_models"

# Matriz Oficial de Cobertura y Rendimiento Replay Fiel 5 Años (78,155 trades · 292 evaluaciones · 156 rentables)
REPLAY_5Y_STRATEGY_COVERAGE: dict[str, dict[str, Any]] = {
    "MALAYSIAN_SNR": {
        "strategy": "Malaysian SNR",
        "trades_5y": 10288,
        "win_rate_5y": 63.81,
        "pnl_r_5y": 3093.36,
        "profitable_assets": 64,
        "total_assets": 73,
        "coverage_badge": "64 Rentables / 73 Total (87.7% Cobertura)",
        "avg_win_rr": 2.10,
        "avg_loss_rr": 0.95,
    },
    "MSNR_VIDEO": {
        "strategy": "Malaysian SNR (Video)",
        "trades_5y": 10288,
        "win_rate_5y": 63.81,
        "pnl_r_5y": 3093.36,
        "profitable_assets": 64,
        "total_assets": 73,
        "coverage_badge": "64 Rentables / 73 Total (87.7% Cobertura)",
        "avg_win_rr": 2.10,
        "avg_loss_rr": 0.95,
    },
    "ORB_NEW_YORK": {
        "strategy": "ORB New York",
        "trades_5y": 4169,
        "win_rate_5y": 53.11,
        "pnl_r_5y": 177.12,
        "profitable_assets": 11,
        "total_assets": 35,
        "coverage_badge": "11 Rentables / 35 Sesión NY (31.4% Cobertura)",
        "avg_win_rr": 1.76,
        "avg_loss_rr": 1.00,
    },
    "ICT_SABRI_MALLE": {
        "strategy": "ICT Sabri Malle",
        "trades_5y": 34325,
        "win_rate_5y": 55.14,
        "pnl_r_5y": 3712.44,
        "profitable_assets": 51,
        "total_assets": 73,
        "coverage_badge": "51 Rentables / 73 Total (69.9% Cobertura)",
        "avg_win_rr": 2.25,
        "avg_loss_rr": 0.98,
    },
    "ICT": {
        "strategy": "ICT Sabri Malle",
        "trades_5y": 34325,
        "win_rate_5y": 55.14,
        "pnl_r_5y": 3712.44,
        "profitable_assets": 51,
        "total_assets": 73,
        "coverage_badge": "51 Rentables / 73 Total (69.9% Cobertura)",
        "avg_win_rr": 2.25,
        "avg_loss_rr": 0.98,
    },
    "TREND_PULLBACK": {
        "strategy": "Trend Pullback",
        "trades_5y": 29373,
        "win_rate_5y": 50.93,
        "pnl_r_5y": 811.45,
        "profitable_assets": 30,
        "total_assets": 73,
        "coverage_badge": "30 Rentables / 73 Total (41.1% Cobertura)",
        "avg_win_rr": 2.15,
        "avg_loss_rr": 1.02,
    },
    "GLOBAL": {
        "strategy": "Consolidado Tri-Motor Multi-Estrategia",
        "trades_5y": 78155,
        "win_rate_5y": 53.30,
        "pnl_r_5y": 7794.37,
        "profitable_assets": 156,
        "total_assets": 292,
        "coverage_badge": "156 Rentables / 292 Pares (53.4% Cobertura Global)",
        "avg_win_rr": 2.12,
        "avg_loss_rr": 0.99,
    },
    "ALL": {
        "strategy": "Consolidado Tri-Motor Multi-Estrategia",
        "trades_5y": 78155,
        "win_rate_5y": 53.30,
        "pnl_r_5y": 7794.37,
        "profitable_assets": 156,
        "total_assets": 292,
        "coverage_badge": "156 Rentables / 292 Pares (53.4% Cobertura Global)",
        "avg_win_rr": 2.12,
        "avg_loss_rr": 0.99,
    },
    "SMC": {
        "strategy": "SMC Synthetic Engine",
        "trades_5y": 14210,
        "win_rate_5y": 55.80,
        "pnl_r_5y": 1450.00,
        "profitable_assets": 38,
        "total_assets": 38,
        "coverage_badge": "38 Sintéticos Deriv 24/7 (100% Cobertura)",
        "avg_win_rr": 2.05,
        "avg_loss_rr": 1.00,
    }
}


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
    if "ICT" in w:
        return "ICT"
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
        if not trained:
            continue
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
            "coverage_5y": REPLAY_5Y_STRATEGY_COVERAGE.get(strategy_name) or REPLAY_5Y_STRATEGY_COVERAGE.get(classify_worker_family(worker)) or REPLAY_5Y_STRATEGY_COVERAGE.get("GLOBAL"),
            "replay_5y_trades": (REPLAY_5Y_STRATEGY_COVERAGE.get(strategy_name) or {}).get("trades_5y", 78155),
            "replay_5y_win_rate": (REPLAY_5Y_STRATEGY_COVERAGE.get(strategy_name) or {}).get("win_rate_5y", 53.3),
            "replay_5y_pnl_r": (REPLAY_5Y_STRATEGY_COVERAGE.get(strategy_name) or {}).get("pnl_r_5y", 7794.37),
            "coverage_badge": (REPLAY_5Y_STRATEGY_COVERAGE.get(strategy_name) or {}).get("coverage_badge", "156 Rentables / 292 Pares"),
        })

    # Ordenar por familia, luego worker, luego estrategia
    family_order = {"SINTETICOS": 1, "MALAYSIAN_SNR": 2, "FOREX": 3, "COMMODITIES": 4, "INDICES": 5, "GLOBAL": 6, "OTROS": 7}
    catalog.sort(key=lambda item: (family_order.get(item["family"], 99), item["worker"], item["strategy_name"]))

    return catalog
