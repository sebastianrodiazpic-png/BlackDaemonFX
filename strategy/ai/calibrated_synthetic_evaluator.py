"""
Evaluador en Tiempo Real de Meta-Labeling Calibrado para Sintéticos
BlackDaemonFX - Motor de Inferencia Ultrarrápida (< 0.5 ms)

Carga el modelo serializado metalabel_SYNTHETICS_CALIBRATED.json
y calcula la probabilidad calibrada mediante Platt Scaling monótono,
garantizando ausencia de colapsos numéricos a 0.00.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Fix shadowing of standard library 'operator' by local tools/operator directory
if sys.path and (sys.path[0].endswith("tools") or sys.path[0].endswith("tools\\") or sys.path[0].endswith("tools/")):
    sys.path.pop(0)

import json
from dataclasses import dataclass, field
from typing import Any
import numpy as np

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_MODEL_PATH = PROJECT_ROOT / "storage" / "ai_models" / "metalabel_SYNTHETICS_CALIBRATED.json"

@dataclass
class CalibratedSyntheticEvaluator:
    model_path: Path = DEFAULT_MODEL_PATH
    trained: bool = False
    feature_names: list[str] = field(default_factory=list)
    avg_win_r: float = 1.04
    avg_loss_r: float = 0.92
    platt_coef: float = 0.3897
    platt_intercept: float = 0.0737
    _booster: Any = None
    
    def __post_init__(self):
        self.load_model()
        
    def load_model(self) -> bool:
        if not self.model_path.exists() or not LIGHTGBM_AVAILABLE:
            return False
            
        try:
            with open(self.model_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            model_str = data.get("model_str", "")
            if not model_str:
                return False
                
            self._booster = lgb.Booster(model_str=model_str)
            self.feature_names = data.get("feature_names", [])
            self.avg_win_r = float(data.get("average_win_rr", 1.04))
            self.avg_loss_r = float(data.get("average_loss_rr", 0.92))
            
            cal_params = data.get("calibrator", {})
            self.platt_coef = float(cal_params.get("platt_coef", 0.3897))
            self.platt_intercept = float(cal_params.get("platt_intercept", 0.0737))
            
            self.trained = True
            return True
        except Exception:
            self.trained = False
            return False

    def evaluate_signal(self, features_dict: dict[str, Any]) -> dict[str, Any]:
        """Evalúa un diccionario de features y devuelve la probabilidad y expectativa calibrada."""
        if not self.trained or self._booster is None:
            # Fallback neutral
            return {
                "trained": False,
                "probability": 0.50,
                "net_expectancy_r": 0.06,
                "allowed": True,
                "mode": "FALLBACK",
                "reason": "MODEL_NOT_LOADED_NEUTRAL_PASS"
            }
            
        vec = []
        for name in self.feature_names:
            val = features_dict.get(name, 0.0)
            try:
                vec.append(float(val) if val is not None else 0.0)
            except (ValueError, TypeError):
                vec.append(0.0)
                
        arr = np.asarray(vec, dtype=float).reshape(1, -1)
        raw_prob = float(self._booster.predict(arr)[0])
        
        # Platt Scaling Sigmoide Monótono
        eps = 1e-5
        clipped_raw = np.clip(raw_prob, eps, 1 - eps)
        logit = np.log(clipped_raw / (1 - clipped_raw))
        calibrated_logit = self.platt_coef * logit + self.platt_intercept
        calibrated_prob = float(1.0 / (1.0 + np.exp(-calibrated_logit)))
        calibrated_prob = float(np.clip(calibrated_prob, 0.05, 0.95))
        
        # Expectativa matemática en R:
        # Exp = P * Win_R - (1 - P) * Loss_R
        exp_r = (calibrated_prob * self.avg_win_r) - ((1.0 - calibrated_prob) * self.avg_loss_r)
        
        # En sintéticos: permitir si la expectativa neta es superior a -0.05R (cerca de BE o positiva)
        allowed = True if exp_r >= -0.05 else False
        
        return {
            "trained": True,
            "raw_probability": round(raw_prob, 4),
            "probability": round(calibrated_prob, 4),
            "net_expectancy_r": round(exp_r, 4),
            "avg_win_r": self.avg_win_r,
            "avg_loss_r": self.avg_loss_r,
            "allowed": allowed,
            "reason": f"CALIBRATED_SYNTH_ML:P={calibrated_prob:.1%}:Exp={exp_r:+.2f}R"
        }
