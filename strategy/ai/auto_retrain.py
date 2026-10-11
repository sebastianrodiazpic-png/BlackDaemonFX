"""Servicio de re-entrenamiento automatizado de Meta-Modelos de IA (auto_retrain.py).

Diseñado para ejecutarse periódicamente (ej. semanalmente vía cron o Windows Task Scheduler).
Adapta los modelos probabilísticos de clasificación (regresión logística calibrada y Online SGD)
a las variaciones recientes de volatilidad y evita el fenómeno de 'Data Drift' / 'Concept Drift'.

Flujo de trabajo:
1. Extrae las operaciones cerradas del historial en `database.repository.TradingRepository`.
2. Filtra por ventana temporal reciente (ej. últimos 30 días) o histórico completo.
3. Para cada perfil operativo (BOOM, CRASH, VOLATILITY, STEP, JUMP, FLIP, GOLD, FOREX, ORB, GLOBAL):
   a) Realiza validación temporal estricta (Walk-Forward).
   b) Ajusta los pesos de las 20 características SMC y re-calibra la curva isotónica.
   c) Si el modelo supera los criterios de viabilidad, lo persiste en `storage/ai_models/`.
   d) Guarda las métricas de validación y registra el evento de auditoría en la base de datos.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.repository import TradingRepository
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig
from strategy.ai.training import (
    train_worker_model,
    temporal_validation,
    MIN_TRAINING_SAMPLES,
)

logger = logging.getLogger("strategy.ai.auto_retrain")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AutoRetrain] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DEFAULT_WORKERS = [
    "GLOBAL",
    "BOOM",
    "CRASH",
    "VOLATILITY",
    "STEP",
    "JUMP",
    "FLIP",
    "GOLD",
    "FOREX",
    "ORB",
]


class MetaModelAutoRetrainer:
    """Orquestador de re-entrenamiento sistemático de meta-modelos."""

    def __init__(
        self,
        repository: TradingRepository | None = None,
        lookback_days: int = 45,
        min_samples: int = MIN_TRAINING_SAMPLES,
        workers: List[str] | None = None,
    ):
        self.repo = repository or TradingRepository()
        self.lookback_days = lookback_days
        self.min_samples = min_samples
        self.workers = workers or DEFAULT_WORKERS
        self.output_audit_dir = PROJECT_ROOT / "storage" / "learning_audit"
        self.output_audit_dir.mkdir(parents=True, exist_ok=True)

    def load_eligible_trades(self) -> pd.DataFrame:
        """Carga operaciones cerradas dentro de la ventana de análisis."""
        df = self.repo.account_trade_history_dataframe()
        if df.empty:
            logger.warning("No hay operaciones en el historial para re-entrenar.")
            return df

        # Filtrar operaciones cerradas
        closed = df[df["status"].astype(str).str.upper() == "CLOSED"].copy()

        # Filtrar por ventana temporal si está configurada
        if self.lookback_days and self.lookback_days > 0 and "exit_time" in closed.columns:
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
                closed["exit_time_dt"] = pd.to_datetime(closed["exit_time"], utc=True, errors="coerce")
                recent = closed[closed["exit_time_dt"] >= cutoff]
                if len(recent) >= self.min_samples:
                    logger.info(
                        "Filtradas %d operaciones recientes de los últimos %d días (de %d totales cerradas).",
                        len(recent),
                        self.lookback_days,
                        len(closed),
                    )
                    return recent
                else:
                    logger.info(
                        "Menos de %d operaciones en ventana de %d días (%d encontradas). Usando histórico completo (%d).",
                        self.min_samples,
                        self.lookback_days,
                        len(recent),
                        len(closed),
                    )
            except Exception as exc:
                logger.warning("Error al filtrar por fecha: %s. Usando histórico completo.", exc)

        return closed

    def run(self) -> Dict[str, Any]:
        """Ejecuta el ciclo de re-entrenamiento para todos los perfiles configurados."""
        trades_df = self.load_eligible_trades()
        if trades_df.empty:
            return {"status": "skipped", "reason": "NO_TRADES"}

        results = {}
        successful_retrains = 0

        for worker in self.workers:
            logger.info("--- Evaluando re-entrenamiento para worker: %s ---", worker)
            engine = MetaLabelingEngine(worker=worker)

            # 1. Validación Temporal (Walk-Forward)
            val_report = temporal_validation(
                trades_df,
                worker=worker,
                strategy_name="ALL",
                folds=4,
                min_train_samples=self.min_samples,
            )

            # 2. Ajuste y Calibración del Modelo
            model = train_worker_model(
                trades_df,
                worker=worker,
                strategy_name="ALL",
                calibrate=True,
                min_samples=self.min_samples,
                allow_global_pooling=True,
            )

            worker_summary = {
                "worker": worker,
                "trained": model.trained,
                "samples": model.samples,
                "trained_at": model.trained_at,
                "temporal_valid": val_report.valid,
                "accuracy": round(val_report.accuracy, 4) if val_report.valid else None,
                "brier_score": round(val_report.brier_score, 4) if val_report.valid else None,
                "lift": round(val_report.lift, 4) if val_report.valid else None,
                "reason": val_report.reason if not val_report.valid else "OK",
            }

            if model.trained:
                saved_path = engine.save_model(model)
                successful_retrains += 1
                worker_summary["saved_path"] = str(saved_path)

                # Persistir métricas detalladas
                metrics_path = Path(saved_path).with_name(
                    Path(saved_path).stem + "_metrics.json"
                )
                metrics_payload = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "worker": worker,
                    "validation": val_report.to_dict(),
                    "samples": model.samples,
                    "average_win_rr": model.average_win_rr,
                    "average_loss_rr": model.average_loss_rr,
                }
                metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

                # Registrar auditoría en la BD
                self.repo.save_audit_event(
                    "AI_META_MODEL_RETRAINED",
                    source="AUTO_RETRAIN",
                    action="MODEL_UPDATED",
                    reason=f"{worker}: accuracy={val_report.accuracy:.2f}, brier={val_report.brier_score:.3f}, samples={model.samples}",
                    payload={
                        "worker": worker,
                        "accuracy": val_report.accuracy,
                        "brier_score": val_report.brier_score,
                        "samples": model.samples,
                    },
                )
                logger.info(
                    "Modelo %s re-entrenado con éxito: samples=%d, acc=%.2f, brier=%.3f",
                    worker,
                    model.samples,
                    val_report.accuracy,
                    val_report.brier_score,
                )
            else:
                logger.info("Modelo %s no re-entrenado (%s).", worker, worker_summary["reason"])

            results[worker] = worker_summary

        # Guardar reporte de auditoría de la sesión
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        audit_file = self.output_audit_dir / f"retrain_session_{now_str}.json"
        session_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lookback_days": self.lookback_days,
            "total_trades_evaluated": len(trades_df),
            "successful_retrains": successful_retrains,
            "results": results,
        }
        audit_file.write_text(json.dumps(session_report, indent=2), encoding="utf-8")
        logger.info(
            "Sesión de re-entrenamiento completada. %d modelos actualizados. Informe: %s",
            successful_retrains,
            audit_file.name,
        )
        return session_report


def main():
    parser = argparse.ArgumentParser(description="Re-entrenamiento Automatizado de Meta-Modelos")
    parser.add_argument("--lookback-days", type=int, default=45, help="Días históricos a evaluar (0 = todo)")
    parser.add_argument("--min-samples", type=int, default=MIN_TRAINING_SAMPLES, help="Mínimo de muestras por perfil")
    parser.add_argument("--workers", type=str, default=None, help="Lista de workers separados por coma")
    args = parser.parse_args()

    workers = [w.strip() for w in args.workers.split(",")] if args.workers else None
    retrainer = MetaModelAutoRetrainer(
        lookback_days=args.lookback_days,
        min_samples=args.min_samples,
        workers=workers,
    )
    report = retrainer.run()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
