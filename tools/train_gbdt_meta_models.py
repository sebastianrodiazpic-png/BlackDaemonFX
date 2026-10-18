"""Entrenamiento de Meta-Modelos GBDT (LightGBM) desde Replays y Journal.

Permite entrenar la Capa 2 (Micro / Puntería Quirúrgica) con árboles de decisión
ensamblados y calibración de probabilidad isotónica.

Uso:
    python tools/train_gbdt_meta_models.py --worker FOREX
    python tools/train_gbdt_meta_models.py --worker MALAYSIAN_SNR
    python tools/train_gbdt_meta_models.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai import (
    FEATURE_NAMES,
    CalibratedGBDTModel,
    MetaLabelingConfig,
    MetaLabelingEngine,
    train_worker_gbdt_model,
)
from strategy.ai.training import build_training_dataset
from tools.train_180d_meta_models import build_unified_trade_records


def train_gbdt_for_worker(worker: str, records: list[dict], models_dir: Path | None = None) -> dict:
    models_path = models_dir or (PROJECT_ROOT / "storage" / "ai_models")
    models_path.mkdir(parents=True, exist_ok=True)

    engine = MetaLabelingEngine(
        MetaLabelingConfig(
            enabled=True,
            model_directory=str(models_path),
            min_training_samples=15,
            model_type="LIGHTGBM",
        ),
        worker=worker,
    )

    dataset = build_training_dataset(records, worker=worker)
    total_rows = dataset["rows"]
    wins = sum(dataset["labels"]) if total_rows > 0 else 0
    win_rate = round(wins / total_rows * 100, 1) if total_rows > 0 else 0.0

    print(f"\n--- Entrenando GBDT para Worker: {worker} ---")
    print(f"Muestras disponibles: {total_rows} (Aciertos: {wins}, WR Base: {win_rate}%)")

    model = train_worker_gbdt_model(
        records,
        worker=worker,
        min_samples=15,
        allow_global_pooling=True,
        n_estimators=80,
        max_depth=4,
        learning_rate=0.03,
    )
    model.worker = worker
    model.strategy_name = "ALL"

    if model.trained:
        saved_path = engine.save_model(model)
        print(f"Modelo GBDT guardado en: {saved_path}")

        # Mostrar Top 5 características más influyentes
        top_features = sorted(model.feature_importances.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 características predictivas:")
        for name, importance in top_features:
            print(f"  - {name}: {importance * 100:.2f}%")

        return {
            "worker": worker,
            "trained": True,
            "samples": model.samples,
            "win_rate": win_rate,
            "path": saved_path,
            "top_features": top_features,
        }
    else:
        print(f"Advertencia: Muestras insuficientes para entrenar GBDT en {worker}.")
        return {
            "worker": worker,
            "trained": False,
            "samples": total_rows,
            "win_rate": win_rate,
        }


def main():
    parser = argparse.ArgumentParser(description="Entrenar meta-modelos GBDT (LightGBM)")
    parser.add_argument("--worker", type=str, default="FOREX", help="Nombre del worker a entrenar")
    parser.add_argument("--all", action="store_true", help="Entrenar todos los workers principales")
    args = parser.parse_args()

    print("Cargando registros unificados de operaciones (DB + Replays)...")
    records = build_unified_trade_records()

    if args.all:
        workers = ["FOREX", "GOLD", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "GLOBAL"]
        for w in workers:
            train_gbdt_for_worker(w, records)
    else:
        train_gbdt_for_worker(args.worker, records)


if __name__ == "__main__":
    main()
