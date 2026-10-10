"""Entrenamiento de modelos de Meta-Etiquetado IA a partir del Replay de 2 años
de la estrategia ICT (Sabri Malle).
Genera y actualiza los modelos para GLOBAL, BOOM, CRASH, VOLATILITY, STEP, JUMP, GOLD y FOREX.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, ".")
import json
from pathlib import Path
import numpy as np
import pandas as pd

from strategy.ai.feature_extraction import FEATURE_NAMES, feature_vector
from strategy.ai.model import CalibratedLogisticModel, LogisticRegressionModel, ProbabilityCalibrator

REPLAY_CSV = Path("storage/meta_labeling_ict_sabri_malle_trades.csv")
MODELS_DIR = Path("storage/ai_models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Mapeo de asset_class / symbol a worker
WORKER_MAP = {
    "forex": "FOREX",
    "synthetic": {
        "Boom_1000_Index": "BOOM",
        "Crash_1000_Index": "CRASH",
        "Step_Index": "STEP",
        "Jump_50_Index": "JUMP",
        "Volatility_75_Index": "VOLATILITY",
        "Volatility_100_Index": "VOLATILITY",
    },
    "metal": "GOLD",
    "commodity": "GLOBAL",
    "crypto": "GLOBAL",
    "index": "GLOBAL",
}

def get_worker_for_trade(symbol: str, asset_class: str) -> str:
    mapping = WORKER_MAP.get(asset_class)
    if isinstance(mapping, dict):
        return mapping.get(symbol, "SYNTHETICS")
    elif isinstance(mapping, str):
        return mapping
    return "GLOBAL"

def convert_trade_to_feature_dict(row: dict) -> dict:
    """Mapea las columnas del trade de replay al vector de características FEATURE_NAMES."""
    symbol = str(row["symbol"])
    asset_class = str(row["asset_class"])
    direction = str(row["direction"]).upper()
    
    # Derivados
    range_atr = float(row.get("range_atr_ratio", 3.0))
    sweep_ratio = float(row.get("sweep_depth_ratio", 0.05))
    spread_risk = float(row.get("spread_to_risk", 0.01))
    
    # 45 features en FEATURE_NAMES
    features = {name: 0.0 for name in FEATURE_NAMES}
    
    # Puntuaciones base y confirmación
    features["trade_score"] = 85.0
    features["confirmation_percentage"] = 80.0
    features["confirmations_ratio"] = 0.85
    features["adx"] = 28.0
    features["adx_normalized"] = 0.56
    features["atr_ratio"] = range_atr
    features["structure_aligned"] = 1.0
    features["chart_pattern_strength"] = 0.80
    features["chart_pattern_conflict"] = 0.0
    features["chart_pattern_strength_delta"] = 0.80
    features["signal_age_candles"] = 1.0
    features["signal_age_minutes"] = 5.0
    features["spread_ratio"] = spread_risk
    features["planned_rr"] = 2.0
    features["risk_percent"] = 1.0
    features["divergence_confirmed"] = 1.0
    features["harmonic_confirmed"] = 0.0
    features["h1_doji_confirmed"] = 1.0
    features["exhaustion_reversal_confirmed"] = 0.0
    features["direction_buy"] = 1.0 if direction == "BUY" else 0.0
    features["adx_regime"] = 1.0
    features["spread_to_sl_ratio"] = spread_risk
    features["session_killzone_active"] = 1.0 if (8 <= int(row.get("hour_utc", 0)) <= 17) else 0.0
    
    # Flags de activo
    features["is_boom"] = 1.0 if "boom" in symbol.lower() else 0.0
    features["is_crash"] = 1.0 if "crash" in symbol.lower() else 0.0
    features["is_volatility"] = 1.0 if "volatility" in symbol.lower() else 0.0
    features["is_forex"] = 1.0 if asset_class == "forex" else 0.0
    features["is_gold"] = 1.0 if ("xau" in symbol.lower() or "xag" in symbol.lower()) else 0.0
    features["is_step"] = 1.0 if "step" in symbol.lower() else 0.0
    features["is_jump"] = 1.0 if "jump" in symbol.lower() else 0.0

    return features

def train_and_save_all_models():
    print("=" * 80)
    print("ENTRENANDO MODELOS DE META-ETIQUETADO IA CON DATASET ICT 2Y...")
    print("=" * 80)
    
    df = pd.read_csv(REPLAY_CSV)
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True)
    df = df.sort_values("entry_time").reset_index(drop=True)
    
    records = df.to_dict("records")
    
    # Preparar muestras
    all_samples = []
    for r in records:
        worker = get_worker_for_trade(r["symbol"], r["asset_class"])
        feat_dict = convert_trade_to_feature_dict(r)
        vec = feature_vector(feat_dict)
        label = int(r["meta_label_win_rr4"]) # 1 si ganancia, 0 si pérdida
        realized_rr = float(r["r_net_rr4"])
        all_samples.append({
            "worker": worker,
            "asset_class": r["asset_class"],
            "features": vec,
            "label": label,
            "rr": realized_rr,
            "entry_time": r["entry_time"],
        })
        
    workers = ["GLOBAL", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "GOLD", "FOREX"]
    
    for worker in workers:
        if worker == "GLOBAL":
            worker_samples = all_samples
        else:
            worker_samples = [s for s in all_samples if s["worker"] == worker]
            # Si el worker tiene pocos datos específicos, enriquecer con GLOBAL para transfer learning
            if len(worker_samples) < 55:
                # Combinar muestras del worker con muestras globales para transfer learning
                needed = 55 - len(worker_samples) + 10
                worker_samples = worker_samples + [s for s in all_samples if s["worker"] != worker][:needed]

        X = np.array([s["features"] for s in worker_samples], dtype=float)
        y = np.array([s["label"] for s in worker_samples], dtype=int)
        rr_vals = [s["rr"] for s in worker_samples]
        
        n_samples = len(y)
        win_rate = float(np.mean(y)) * 100.0
        
        # Train / Test split temporal (70 / 30)
        split_idx = max(1, int(n_samples * 0.70))
        
        model = CalibratedLogisticModel(worker=worker, strategy_name="SMC")
        model.model = LogisticRegressionModel(feature_names=FEATURE_NAMES).fit(X[:split_idx], y[:split_idx])
        
        if len(set(y[split_idx:].tolist())) >= 2:
            holdout_probs = model.model.predict_proba(X[split_idx:])
            model.calibrator = ProbabilityCalibrator().fit(holdout_probs, y[split_idx:])
            
        # Refit final con todas las muestras
        model.model = LogisticRegressionModel(feature_names=FEATURE_NAMES).fit(X, y)
        
        wins = [abs(rr) for rr, l in zip(rr_vals, y) if l == 1 and abs(rr) > 1e-9]
        losses = [abs(rr) for rr, l in zip(rr_vals, y) if l == 0 and abs(rr) > 1e-9]
        model.average_win_rr = float(np.mean(wins)) if wins else 2.5
        model.average_loss_rr = float(np.mean(losses)) if losses else 1.0
        model.trained_at = pd.Timestamp.now(tz="UTC").isoformat()
        
        # Guardar tanto en SMC como en ALL
        for strat in ("SMC", "ALL"):
            model.strategy_name = strat
            path = MODELS_DIR / f"metalabel_{worker}_{strat}.json"
            model_dict = model.to_dict()
            model_dict["feature_schema"] = "meta-features-v5"
            path.write_text(json.dumps(model_dict, indent=2, ensure_ascii=False), encoding="utf-8")
            
        print(f"[+] Modelo entrenado: {worker:<12} | Muestras: {n_samples:>3} | WR Base: {win_rate:>5.1f}% | Avg Win: +{model.average_win_rr:.2f}R | Avg Loss: -{model.average_loss_rr:.2f}R -> Guardado en {MODELS_DIR}")

    print("=" * 80)
    print("TODOS LOS MODELOS DE META-ETIQUETADO IA HAN SIDO CALIBRADOS Y GUARDADOS.")
    print("=" * 80)

if __name__ == "__main__":
    train_and_save_all_models()
