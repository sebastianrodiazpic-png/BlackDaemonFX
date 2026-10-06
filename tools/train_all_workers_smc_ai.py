"""
Entrenamiento de Modelos de IA de Meta-Etiquetado para todos los Workers:
CRASH, BOOM, VOLATILITY, FLIP, FOREX, GOLD, JUMP, STEP.

Alimenta el entrenamiento con:
1. Registros históricos de trade_journal en la base persistente trading_bot.sqlite3.
2. Dataset de 673 operaciones del Replay Histórico Cuantitativo de 2 años (SMC optimizado).
3. Calibración isotónica (Platt/Bin scaling) y cálculo de R medio ganado/perdido.
4. Exportación a storage/ai_models/ para que los workers en vivo lo carguen automáticamente.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai.feature_extraction import FEATURE_NAMES, feature_vector
from strategy.ai.model import CalibratedLogisticModel, LogisticRegressionModel, ProbabilityCalibrator
from strategy.ai.training import train_worker_model, temporal_validation, MIN_TRAINING_SAMPLES
from database.database import resolve_db_path

WORKERS = [
    "CRASH",
    "BOOM",
    "VOLATILITY",
    "FLIP",
    "FOREX",
    "GOLD",
    "JUMP",
    "STEP",
    "SYNTHETICS",
    "GLOBAL"
]

def load_journal_trades():
    """Carga los trades históricos del trade_journal persistente."""
    db_path = resolve_db_path()
    trades = []
    if not os.path.exists(db_path):
        return trades
        
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, source, instrument, direction, status, result, entry_time, exit_time, realized_rr, net_pnl, details_json, strategy_version FROM trade_journal")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()
        
        for r in rows:
            row_dict = dict(zip(cols, r))
            details = {}
            if row_dict.get("details_json"):
                try:
                    details = json.loads(row_dict["details_json"])
                except Exception:
                    details = {}
            row_dict["details"] = details
            trades.append(row_dict)
        print(f"Cargados {len(trades)} registros de trade_journal desde {db_path}")
    except Exception as e:
        print(f"Aviso al leer trade_journal: {e}")
        
    return trades

def load_replay_dataset():
    """Carga el dataset etiquetado de 2 años de replay."""
    ds_path = Path("storage/analysis/ai_meta_training_dataset_ready.json")
    if not ds_path.exists():
        print("No se encontró storage/analysis/ai_meta_training_dataset_ready.json")
        return []
    with open(ds_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    samples = data.get("samples", [])
    print(f"Cargadas {len(samples)} muestras etiquetadas desde {ds_path}")
    return samples

def map_sample_to_training_row(sample):
    """Mapea una muestra del replay al formato estándar de fila de entrenamiento."""
    cat = str(sample.get("category") or "synthetics").upper()
    worker = "SYNTHETICS"
    if cat == "FOREX": worker = "FOREX"
    elif cat == "GOLD": worker = "GOLD"
    elif cat == "STEP": worker = "STEP"
    elif cat == "JUMP": worker = "JUMP"
    elif cat == "VOLATILITY": worker = "VOLATILITY"
    elif cat == "BOOM": worker = "BOOM"
    elif cat == "CRASH": worker = "CRASH"
    elif cat == "FLIP": worker = "FLIP"

    entry_t = sample.get("entry_time") or datetime.now(timezone.utc).isoformat()
    feats = sample.get("features", {})
    
    # Asegurar que todas las 44 features existan
    complete_feats = {}
    for fn in FEATURE_NAMES:
        complete_feats[fn] = float(feats.get(fn, 0.0))
        
    row = {
        "source": "DEMO",
        "instrument": sample.get("symbol", "UNKNOWN"),
        "status": "CLOSED",
        "entry_time": entry_t,
        "exit_time": entry_t,
        "realized_rr": float(sample.get("realized_r", 0.0)),
        "net_pnl": float(sample.get("realized_r", 0.0)) * 50.0,
        "details_json": {
            "metadata": {
                "bot_profile": worker,
                "strategy_name": "SMC",
                "entry_learning_snapshot": {
                    "schema": "entry-learning-v5",
                    "features": complete_feats,
                    "captured_at": entry_t
                }
            }
        }
    }
    return worker, row

def main():
    print("=" * 80)
    print("INICIANDO ENTRENAMIENTO IA DE META-ETIQUETADO PARA TODOS LOS WORKERS")
    print("Workers: CRASH, BOOM, VOLATILITY, FLIP, FOREX, GOLD, JUMP, STEP")
    print("Estrategia: Smart Money Concepts (SMC)")
    print("=" * 80)
    
    models_dir = Path("storage/ai_models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Cargar datos
    journal_trades = load_journal_trades()
    replay_samples = load_replay_dataset()
    
    # 2. Agrupar trades por worker y crear pool global
    all_combined_trades = list(journal_trades)
    
    for s in replay_samples:
        w, row = map_sample_to_training_row(s)
        all_combined_trades.append(row)
        
    print(f"Total histórico unificado para entrenamiento: {len(all_combined_trades)} operaciones")
    
    training_results = {}
    
    # 3. Entrenar cada worker
    for worker in WORKERS:
        print(f"\n--- Entrenando Modelo IA para Worker: {worker} ---")
        
        # Entrenar modelo SMC
        model_smc = train_worker_model(
            all_combined_trades,
            worker=worker,
            strategy_name="SMC",
            min_samples=8,
            allow_global_pooling=True
        )
        
        # Guardar en storage/ai_models/
        smc_file = models_dir / f"metalabel_{worker}_SMC.json"
        with open(smc_file, "w", encoding="utf-8") as f:
            json.dump(model_smc.to_dict(), f, indent=2)
            
        # También guardar como ALL para compatibilidad global de fallback
        all_file = models_dir / f"metalabel_{worker}_ALL.json"
        with open(all_file, "w", encoding="utf-8") as f:
            json.dump(model_smc.to_dict(), f, indent=2)
            
        # Validación temporal walk-forward
        val_report = temporal_validation(
            all_combined_trades,
            worker=worker,
            strategy_name="SMC",
            min_train_samples=10
        )
        
        metrics_file = models_dir / f"metalabel_{worker}_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump({
                "worker": worker,
                "strategy": "SMC",
                "trained": model_smc.trained,
                "samples": model_smc.model.samples,
                "positive_rate": round(model_smc.model.positive_rate, 4),
                "average_win_rr": round(model_smc.average_win_rr, 2),
                "average_loss_rr": round(model_smc.average_loss_rr, 2),
                "trained_at": model_smc.trained_at,
                "validation": val_report.to_dict()
            }, f, indent=2)
            
        print(f"  [OK] Guardado: {smc_file.name}")
        print(f"  Estado: {'ENTRENADO' if model_smc.trained else 'NO ENTRENADO (Insuficientes muestras)'}")
        print(f"  Muestras: {model_smc.model.samples} | Tasa Base (WinRate): {model_smc.model.positive_rate*100:.1f}%")
        print(f"  R Medio Ganado: +{model_smc.average_win_rr:.2f}R | R Medio Perdido: -{model_smc.average_loss_rr:.2f}R")
        
        training_results[worker] = {
            "trained": model_smc.trained,
            "samples": model_smc.model.samples,
            "win_rate": round(model_smc.model.positive_rate * 100, 1),
            "avg_win_rr": round(model_smc.average_win_rr, 2),
            "avg_loss_rr": round(model_smc.average_loss_rr, 2),
            "lift": round(val_report.lift, 3) if val_report.valid else 0.0
        }
        
    print("\n" + "=" * 80)
    print("RESUMEN DE MODELOS IA ENTRENADOS Y PERSISTIDOS")
    for w, res in training_results.items():
        status = "ACTIVO (ENTRENADO)" if res["trained"] else "EN ESPERA"
        print(f"  {w:12} | {status:20} | Muestras: {res['samples']:4} | WR: {res['win_rate']:5.1f}% | Win/Loss RR: +{res['avg_win_rr']}R / -{res['avg_loss_rr']}R")
    print("=" * 80)

if __name__ == "__main__":
    main()
