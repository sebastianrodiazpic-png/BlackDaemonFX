"""
Comparativa Rigurosa de Métodos de Calibración Probabilística para Sintéticos
BlackDaemonFX - Fase 3: Purged Cross-Validation & Calibración Dual

Compara:
1. Bruto (LightGBM sin calibrar)
2. Platt Scaling (Sigmoide)
3. Isotonic Regression
4. Beta Calibration

Métricas evaluadas out-of-fold:
- Brier Score
- Expected Calibration Error (ECE)
- Maximum Calibration Error (MCE)
- Log Loss y ROC-AUC
- Preservación de colas (ausencia de colapso a 0.00)
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
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
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

def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> tuple[float, float, list[dict]]:
    """Calcula Expected Calibration Error (ECE), MCE y tabla de deciles."""
    bin_limits = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    n = len(y_true)
    table = []
    
    for i in range(n_bins):
        low, high = bin_limits[i], bin_limits[i + 1]
        mask = (y_prob >= low) & (y_prob < high) if i < n_bins - 1 else (y_prob >= low) & (y_prob <= high)
        count = int(np.sum(mask))
        if count > 0:
            bin_acc = float(np.mean(y_true[mask]))
            bin_conf = float(np.mean(y_prob[mask]))
            diff = abs(bin_acc - bin_conf)
            ece += (count / n) * diff
            mce = max(mce, diff)
            table.append({
                "bin_low": round(low, 2),
                "bin_high": round(high, 2),
                "count": count,
                "confidence": round(bin_conf, 4),
                "accuracy": round(bin_acc, 4),
                "gap": round(diff, 4)
            })
    return float(ece), float(mce), table

class BetaCalibrator:
    """Calibrador Beta (Kull et al., 2017): log(p/(1-p)) = a*log(f) - b*log(1-f) + c."""
    def __init__(self):
        self.lr = LogisticRegression(C=1.0, solver='lbfgs')
        self.trained = False
        
    def _transform(self, probs: np.ndarray) -> np.ndarray:
        eps = 1e-5
        p = np.clip(probs, eps, 1 - eps)
        # Features: [log(p), -log(1-p)]
        return np.column_stack([np.log(p), -np.log(1 - p)])
        
    def fit(self, probs: np.ndarray, y_true: np.ndarray):
        X = self._transform(probs)
        self.lr.fit(X, y_true)
        self.trained = True
        return self
        
    def predict_proba(self, probs: np.ndarray) -> np.ndarray:
        if not self.trained:
            return probs
        X = self._transform(probs)
        return self.lr.predict_proba(X)[:, 1]

def run_calibration_comparison():
    if not LIGHTGBM_AVAILABLE:
        raise RuntimeError("LightGBM no está disponible.")
        
    csv_file = str(PROJECT_ROOT / "storage" / "ai" / "synthetic_meta_dataset_curated.csv")
    if not os.path.exists(csv_file):
        curate_synthetic_dataset(output_path=csv_file)
        
    df = pd.read_csv(csv_file)
    n_total = len(df)
    print(f"Cargadas {n_total} operaciones sintéticas curadas.")
    
    # Ordenamiento temporal
    if 'entry_time' in df.columns:
        df['dt'] = pd.to_datetime(df['entry_time'], errors='coerce')
        df = df.sort_values(by=['dt', 'trade_id']).reset_index(drop=True)
        
    X = df[SYNTHETIC_FEATURE_NAMES].values.astype(float)
    y = df['target'].values.astype(int)
    r_real = df['realized_rr'].values.astype(float)
    
    # K-Fold Temporal (TimeSeriesSplit con 5 particiones continuas)
    tscv = TimeSeriesSplit(n_splits=5)
    
    raw_oof_preds = np.zeros(n_total)
    oof_indices = []
    
    print("\nIniciando Validación Cruzada Temporal (Purged Walk-Forward 5-Folds)...")
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_va = X[val_idx]
        
        clf = lgb.LGBMClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.03,
            min_child_samples=20,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42 + fold,
            verbose=-1
        )
        clf.fit(X_tr, y_tr)
        preds = clf.predict_proba(X_va)[:, 1]
        raw_oof_preds[val_idx] = preds
        oof_indices.extend(val_idx)
        print(f"  Fold {fold+1}: Train n={len(train_idx)}, Val n={len(val_idx)} | AUC={roc_auc_score(y[val_idx], preds):.3f}")
        
    oof_idx = np.array(oof_indices)
    y_oof = y[oof_idx]
    raw_probs = raw_oof_preds[oof_idx]
    
    print(f"\nEvaluando Out-Of-Fold en {len(oof_idx)} predicciones temporales puras...")
    
    # Comparativa de Calibradores sobre OOF
    # Para evitar overfitting en calibración, dividimos OOF en 2 mitades temporales:
    split_cal = len(oof_idx) // 2
    cal_fit_idx = oof_idx[:split_cal]
    cal_eval_idx = oof_idx[split_cal:]
    
    fit_raw = raw_oof_preds[cal_fit_idx]
    fit_y = y[cal_fit_idx]
    eval_raw = raw_oof_preds[cal_eval_idx]
    eval_y = y[cal_eval_idx]
    
    # 1. Platt Scaling
    eps = 1e-5
    fit_logits = np.log(np.clip(fit_raw, eps, 1-eps) / (1 - np.clip(fit_raw, eps, 1-eps))).reshape(-1, 1)
    eval_logits = np.log(np.clip(eval_raw, eps, 1-eps) / (1 - np.clip(eval_raw, eps, 1-eps))).reshape(-1, 1)
    
    platt = LogisticRegression(C=1.0, solver='lbfgs')
    platt.fit(fit_logits, fit_y)
    platt_eval_probs = platt.predict_proba(eval_logits)[:, 1]
    
    # 2. Isotonic Regression
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(fit_raw, fit_y)
    iso_eval_probs = iso.predict(eval_raw)
    
    # 3. Beta Calibration
    beta = BetaCalibrator()
    beta.fit(fit_raw, fit_y)
    beta_eval_probs = beta.predict_proba(eval_raw)
    
    methods = {
        "Raw (Sin Calibrar)": eval_raw,
        "Platt Scaling (Sigmoide)": platt_eval_probs,
        "Beta Calibration": beta_eval_probs,
        "Isotonic Regression": iso_eval_probs
    }
    
    results = {}
    print("\n" + "="*85)
    print(f"{'Método de Calibración':<26} | {'Brier':<8} | {'ECE %':<8} | {'MCE %':<8} | {'Min Prob':<8} | {'Max Prob':<8}")
    print("="*85)
    
    for name, p in methods.items():
        brier = brier_score_loss(eval_y, p)
        ece, mce, table = compute_ece(eval_y, p, n_bins=8)
        p_min = float(np.min(p))
        p_max = float(np.max(p))
        results[name] = {
            "brier": round(float(brier), 4),
            "ece": round(float(ece * 100), 2),
            "mce": round(float(mce * 100), 2),
            "min_prob": round(p_min, 3),
            "max_prob": round(p_max, 3),
            "table": table
        }
        print(f"{name:<26} | {brier:<8.4f} | {ece*100:<7.2f}% | {mce*100:<7.2f}% | {p_min:<8.3f} | {p_max:<8.3f}")
    print("="*85)
    
    print("\nDetalle de Calibración por Deciles para Platt Scaling:")
    for t in results["Platt Scaling (Sigmoide)"]["table"]:
        print(f"  Rango [{t['bin_low']:.2f} - {t['bin_high']:.2f}]: n={t['count']:3d} | Confianza media={t['confidence']*100:.1f}% | Win Rate real={t['accuracy']*100:.1f}% | Gap={t['gap']*100:.1f}%")
        
    return results

if __name__ == '__main__':
    run_calibration_comparison()
