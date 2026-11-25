import os
import sys
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai.curate_synthetic_dataset import SYNTHETIC_FEATURE_NAMES, EXCLUDED_TOXIC_SYMBOLS
from strategy.ai.calibrated_synthetic_evaluator import CalibratedSyntheticEvaluator
from strategy.ai.model import ProbabilityCalibrator

def test_curated_synthetic_dataset():
    dataset_path = PROJECT_ROOT / "storage" / "ai" / "synthetic_meta_dataset_curated.csv"
    assert dataset_path.exists(), "El dataset curado de sintéticos debe existir"
    
    import pandas as pd
    df = pd.read_csv(dataset_path)
    assert len(df) >= 1000, f"Debe contener al menos 1000 operaciones curadas (encontradas {len(df)})"
    
    insts = set(df['instrument'].unique())
    found_toxic = insts.intersection(EXCLUDED_TOXIC_SYMBOLS)
    assert not found_toxic, f"No debe contener activos tóxicos excluidos: {found_toxic}"
    
    for col in [f for f in SYNTHETIC_FEATURE_NAMES if f != 'structure_aligned']:
        assert col in df.columns, f"Columna {col} requerida en el dataset"
    assert 'target' in df.columns
    assert 'realized_rr' in df.columns

def test_calibrated_model_file():
    model_path = PROJECT_ROOT / "storage" / "ai_models" / "metalabel_SYNTHETICS_CALIBRATED.json"
    assert model_path.exists(), "El archivo de modelo calibrado debe existir"
    
    with open(model_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data.get("trained") is True
    assert "model_str" in data and len(data["model_str"]) > 100
    assert "calibrator" in data
    cal_data = data["calibrator"]
    assert cal_data.get("method") == "PLATT"
    assert cal_data.get("platt_coef", 0.0) > 0.0, "El coeficiente de Platt debe ser estrictamente positivo (monótono)"
    assert "metrics_out_of_fold" in data
    assert data["metrics_out_of_fold"]["ece_percent"] < 5.0, "ECE out-of-fold debe ser inferior al 5%"

def test_calibrated_synthetic_evaluator():
    evaluator = CalibratedSyntheticEvaluator()
    assert evaluator.trained is True, "El evaluador debe cargar el modelo exitosamente"
    
    # Setup A+ de alta calidad
    setup_elite = {
        "trade_score": 0.95,
        "confirmation_percentage": 0.95,
        "confirmations_ratio": 1.0,
        "adx": 32.0,
        "adx_normalized": 0.64,
        "atr_ratio": 0.025,
        "spread_ratio": 0.0003,
        "spread_to_sl_ratio": 0.015,
        "planned_rr": 2.0,
        "direction_buy": 1.0,
        "human_criteria_score": 95.0,
        "is_boom": 0.0,
        "is_crash": 1.0,
        "is_volatility": 0.0,
        "is_step": 0.0,
        "is_jump": 0.0
    }
    
    res_elite = evaluator.evaluate_signal(setup_elite)
    assert res_elite["trained"] is True
    assert 0.35 <= res_elite["probability"] <= 0.75
    assert res_elite["probability"] > 0.45, "Un setup elite debe tener probabilidad superior a 45%"
    assert res_elite["allowed"] is True
    
    # Setup degradado con fricción alta
    setup_degraded = {
        "trade_score": 0.40,
        "confirmation_percentage": 0.50,
        "confirmations_ratio": 0.5,
        "adx": 12.0,
        "adx_normalized": 0.24,
        "atr_ratio": 0.01,
        "spread_ratio": 0.005,
        "spread_to_sl_ratio": 0.15,
        "planned_rr": 1.0,
        "direction_buy": 0.0,
        "human_criteria_score": 45.0,
        "is_boom": 0.0,
        "is_crash": 0.0,
        "is_volatility": 1.0,
        "is_step": 0.0,
        "is_jump": 0.0
    }
    
    res_degraded = evaluator.evaluate_signal(setup_degraded)
    assert res_degraded["trained"] is True
    assert 0.35 <= res_degraded["probability"] <= 0.75
    assert res_degraded["probability"] > 0.05, "El calibrador Platt previene el colapso absoluto a 0.00"

def test_probability_calibrator_platt():
    # Test del calibrador Platt dentro de ProbabilityCalibrator
    calibrator = ProbabilityCalibrator(
        method="PLATT",
        platt_coef=0.3897,
        platt_intercept=0.0737,
        trained=True
    )
    # Para probabilidad bruta baja
    p_low = calibrator.calibrate(0.10)
    assert 0.05 <= p_low <= 0.50
    assert p_low > 0.01, "No debe colapsar a 0"
    
    # Para probabilidad bruta alta
    p_high = calibrator.calibrate(0.90)
    assert 0.50 <= p_high <= 0.95
    
    # Monotonicidad
    assert p_high > p_low, "La calibración debe ser monótona"

def test_gbdt_model_online_calibration_update():
    from strategy.ai.gbdt_model import CalibratedGBDTModel
    model_path = PROJECT_ROOT / "storage" / "ai_models" / "metalabel_SYNTHETICS_CALIBRATED.json"
    with open(model_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    model = CalibratedGBDTModel.from_dict(data)
    assert model.trained is True
    
    vec = [0.8] * len(model.feature_names)
    prob_initial = model.probability(vec)
    initial_intercept = model.calibrator.platt_intercept
    
    # Simular cierre de trade ganador
    updated = model.update_one(vec, label=1, realized_rr=1.5, learning_rate=0.05)
    assert updated is True
    
    # El intercept debe haber subido ligeramente por el acierto
    assert model.calibrator.platt_intercept >= initial_intercept
    assert model.average_win_rr > 0.5
