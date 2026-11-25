"""
Pipeline de Entrenamiento y Calibración de GBDT para Meta-Labeling en Sintéticos
BlackDaemonFX - Fases 2, 3 y 4: Modelo LightGBM con Calibración Sigmoide / Platt Scaling

Entrena un modelo LightGBM regularizado sobre operaciones sintéticas curadas,
aplica calibración paramétrica Platt monótona para erradicar colapsos a 0.00,
y serializa el modelo compatible con CalibratedGBDTModel y ProbabilityCalibrator.
"""

import sys
import os
from pathlib import Path

# Fix shadowing of standard library 'operator' by local tools/operator directory
if sys.path and (sys.path[0].endswith("tools") or sys.path[0].endswith("tools\\") or sys.path[0].endswith("tools/")):
    sys.path.pop(0)

import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
from sklearn.model_selection import TimeSeriesSplit

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai.curate_synthetic_dataset import SYNTHETIC_FEATURE_NAMES, curate_synthetic_dataset

def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calcula el Expected Calibration Error (ECE)."""
    bin_limits = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        low, high = bin_limits[i], bin_limits[i + 1]
        mask = (y_prob >= low) & (y_prob < high) if i < n_bins - 1 else (y_prob >= low) & (y_prob <= high)
        if np.sum(mask) > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / n) * abs(bin_acc - bin_conf)
    return float(ece)

def train_calibrated_synthetic_gbdt(
    csv_path: str | None = None,
    output_model_path: str | None = None
) -> dict:
    if not LIGHTGBM_AVAILABLE:
        raise RuntimeError("LightGBM no está disponible en este entorno.")
        
    csv_file = csv_path or str(PROJECT_ROOT / "storage" / "ai" / "synthetic_meta_dataset_curated.csv")
    if not os.path.exists(csv_file):
        print(f"Dataset curado no encontrado. Generando desde SQLite...")
        curate_synthetic_dataset(output_path=csv_file)
        
    df = pd.read_csv(csv_file)
    n_total = len(df)
    print(f"Dataset cargado: {n_total} registros sintéticos.")
    
    # Ordenar temporalmente por fecha
    if 'entry_time' in df.columns:
        df['dt'] = pd.to_datetime(df['entry_time'], errors='coerce')
        df = df.sort_values(by=['dt', 'trade_id']).reset_index(drop=True)
        
    # Excluir features con varianza cero
    feature_names = [f for f in SYNTHETIC_FEATURE_NAMES if f != 'structure_aligned']
    
    X = df[feature_names].values.astype(float)
    y = df['target'].values.astype(int)
    r_real = df['realized_rr'].values.astype(float)
    
    win_mask = y == 1
    avg_win_r = float(np.mean(r_real[win_mask])) if np.sum(win_mask) > 0 else 1.04
    avg_loss_r = float(abs(np.mean(r_real[~win_mask]))) if np.sum(~win_mask) > 0 else 0.92
    avg_win_r = max(0.5, avg_win_r)
    avg_loss_r = max(0.5, avg_loss_r)
    print(f"Métricas realizadas históricas: Avg Win = +{avg_win_r:.2f}R | Avg Loss = -{avg_loss_r:.2f}R")
    
    # K-Fold Temporal Walk-Forward (5 Folds) para estimar calibración out-of-fold monótona
    tscv = TimeSeriesSplit(n_splits=5)
    oof_preds = np.zeros(n_total)
    val_indices = []
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        clf_fold = lgb.LGBMClassifier(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.03,
            min_child_samples=25,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42 + fold,
            verbose=-1
        )
        clf_fold.fit(X[train_idx], y[train_idx])
        oof_preds[val_idx] = clf_fold.predict_proba(X[val_idx])[:, 1]
        val_indices.extend(val_idx)
        
    val_idx_arr = np.array(val_indices)
    oof_y = y[val_idx_arr]
    oof_probs = oof_preds[val_idx_arr]
    
    # Ajuste monótono seguro de Platt Scaling:
    # log(p / (1-p)) = A * logit + B, donde A >= 0.5 (fuerza monotonicidad positiva)
    eps = 1e-5
    clipped_oof = np.clip(oof_probs, eps, 1 - eps)
    oof_logits = np.log(clipped_oof / (1 - clipped_oof))
    
    # Ajuste por mínimos cuadrados de regresión logística regularizada con límite A > 0
    from scipy.optimize import minimize
    def neg_log_likelihood(params):
        a, b = params
        cal_logits = a * oof_logits + b
        p = 1.0 / (1.0 + np.exp(-cal_logits))
        p = np.clip(p, eps, 1 - eps)
        # NLL binaria con regularización L2 en a y b
        loss = -np.mean(oof_y * np.log(p) + (1 - oof_y) * np.log(1 - p))
        reg = 0.01 * ((a - 1.0)**2 + b**2)
        return loss + reg

    res = minimize(neg_log_likelihood, x0=[1.0, 0.0], bounds=[(0.2, 3.0), (-2.0, 2.0)])
    platt_coef, platt_intercept = float(res.x[0]), float(res.x[1])
    print(f"Platt Scaling regularizado y monótono: Coef={platt_coef:.4f}, Intercept={platt_intercept:.4f}")
    
    # Entrenar modelo final sobre el dataset completo
    final_clf = lgb.LGBMClassifier(
        n_estimators=70,
        max_depth=3,
        learning_rate=0.03,
        min_child_samples=25,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        verbose=-1
    )
    final_clf.fit(X, y)
    booster = final_clf.booster_
    
    # Métricas out-of-fold calibradas
    cal_oof_logits = platt_coef * oof_logits + platt_intercept
    cal_oof_probs = 1.0 / (1.0 + np.exp(-cal_oof_logits))
    cal_oof_probs = np.clip(cal_oof_probs, 0.05, 0.95)
    
    brier = brier_score_loss(oof_y, cal_oof_probs)
    ece = calculate_ece(oof_y, cal_oof_probs)
    auc = roc_auc_score(oof_y, cal_oof_probs)
    
    print(f"\nMÉTRICAS OUT-OF-FOLD (Validación Temporal 5-Folds):")
    print(f"  Brier Score: {brier:.4f}")
    print(f"  ECE %: {ece * 100:.2f}%")
    print(f"  ROC-AUC: {auc:.4f}")
    print(f"  Rango calibrado: min={cal_oof_probs.min():.3f}, max={cal_oof_probs.max():.3f}")
    
    raw_importances = booster.feature_importance(importance_type="gain")
    total_gain = float(np.sum(raw_importances)) if np.sum(raw_importances) > 1e-12 else 1.0
    feat_importances = {
        name: round(float(raw_importances[i]) / total_gain, 4)
        for i, name in enumerate(feature_names)
    }
    
    # Payload serializado compatible tanto con CalibratedGBDTModel como ProbabilityCalibrator
    model_payload = {
        "worker": "SYNTHETICS",
        "strategy_name": "ALL",
        "model_type": "LIGHTGBM",
        "feature_names": feature_names,
        "model_str": booster.model_to_string(),
        "calibrator": {
            "method": "PLATT",
            "platt_coef": platt_coef,
            "platt_intercept": platt_intercept,
            "trained": True,
            "bin_edges": [],
            "bin_values": []
        },
        "trained": True,
        "samples": n_total,
        "positive_rate": float(np.mean(y)),
        "average_win_rr": avg_win_r,
        "average_loss_rr": avg_loss_r,
        "metrics_out_of_fold": {
            "auc": round(float(auc), 4),
            "brier_score": round(float(brier), 4),
            "ece_percent": round(float(ece * 100), 2)
        },
        "feature_importances": feat_importances,
        "trained_at": datetime.now(timezone.utc).isoformat()
    }
    
    out_path = output_model_path or str(PROJECT_ROOT / "storage" / "ai_models" / "metalabel_SYNTHETICS_CALIBRATED.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model_payload, f, indent=2, ensure_ascii=False)
        
    print(f"Modelo serializado exitosamente en: {out_path}")
    return model_payload

if __name__ == '__main__':
    train_calibrated_synthetic_gbdt()
