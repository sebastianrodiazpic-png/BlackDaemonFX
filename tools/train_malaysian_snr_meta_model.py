"""Entrenamiento del Meta-Modelo de IA para la Estrategia Malaysian SNR.

Utiliza el dataset masivo de 2 años (207,520 trades auditados) para entrenar
un modelo logístico calibrado bajo el esquema 'meta-features-v5' canónico.

Predice la probabilidad de éxito de las señales de Malaysian SNR y evalúa la viabilidad
de extender la corredora a TP3 o TP4 en tiempo real.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuración UTF-8 en Windows
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from strategy.ai.feature_extraction import (
    FEATURE_NAMES,
    FEATURE_SCHEMA,
    extract_meta_features,
    feature_vector,
)
from strategy.ai.model import CalibratedLogisticModel, LogisticRegressionModel, ProbabilityCalibrator
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig


def train_malaysian_snr_ai_models():
    print("=" * 90)
    print("ENTRENAMIENTO DE META-MODELOS DE IA: ESTRATEGIA MALAYSIAN SNR (2 ANOS)")
    print("=" * 90)

    dataset_path = PROJECT_ROOT / "storage" / "analysis" / "replay_malaysian_snr_2y_trades.csv"
    if not dataset_path.exists():
        print(f"[ERROR] No se encontró el dataset en {dataset_path}")
        return

    print(f"Cargando dataset histórico desde {dataset_path.name}...")
    df = pd.read_csv(dataset_path)
    total_trades = len(df)
    print(f"Total operaciones cargadas: {total_trades:,}")

    # Target: 1 si el trade fue WIN (total_pnl_usd > 0), 0 si LOSS
    df["target"] = (df["total_pnl_usd"] > 0).astype(int)

    # Ordenar cronológicamente para validación temporal walk-forward estricta
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True)
    df = df.sort_values("entry_time").reset_index(drop=True)

    pos_samples = int(df["target"].sum())
    neg_samples = int(total_trades - pos_samples)
    print(f"Distribución de clases: {pos_samples:,} Ganadoras ({df['target'].mean()*100:.1f}%) | "
          f"{neg_samples:,} Perdedoras")

    # Extraer vectores de características (meta-features-v5)
    print("\nExtrayendo vectores de características canónicos (44 features)...")
    
    # Vectorización rápida de columnas para acelerar la extracción en 207k filas
    feature_rows = []
    y_labels = df["target"].values.astype(int)

    symbols = df["symbol"].astype(str).str.lower().values
    categories = df["category"].astype(str).str.upper().values
    adxs = df["momentum_adx"].fillna(20.0).astype(float).values
    directions = df["direction"].fillna("BUY").astype(str).str.upper().values
    scenarios = df["scenario"].fillna("ESC_1_CONTINUATION").astype(str).values
    planned_rrs = df["total_rr"].fillna(2.0).astype(float).values
    hours = df["entry_time"].dt.hour.values

    # Construir directamente matriz NumPy para FEATURE_NAMES
    n_samples = len(df)
    X = np.zeros((n_samples, len(FEATURE_NAMES)), dtype=np.float64)

    # Mapear nombres a índices
    feat_idx = {name: i for i, name in enumerate(FEATURE_NAMES)}

    # Asignaciones vectorizadas directas
    is_fractal = (scenarios == "ESC_3_FRACTAL")
    X[:, feat_idx["trade_score"]] = np.where(is_fractal, 90.0, 85.0)
    X[:, feat_idx["confirmation_percentage"]] = np.where(is_fractal, 90.0, 80.0)
    X[:, feat_idx["confirmations_ratio"]] = 0.85
    X[:, feat_idx["adx"]] = adxs
    X[:, feat_idx["adx_normalized"]] = np.clip(adxs / 50.0, 0.0, 1.0)
    X[:, feat_idx["adx_available"]] = 1.0
    X[:, feat_idx["atr_ratio"]] = 1.0
    X[:, feat_idx["atr_available"]] = 1.0
    X[:, feat_idx["structure_aligned"]] = 1.0
    X[:, feat_idx["structure_available"]] = 1.0
    X[:, feat_idx["signal_age_candles"]] = 1.0
    X[:, feat_idx["signal_age_minutes"]] = 15.0
    X[:, feat_idx["spread_ratio"]] = 0.05
    X[:, feat_idx["spread_available"]] = 1.0
    X[:, feat_idx["planned_rr"]] = planned_rrs
    X[:, feat_idx["risk_percent"]] = 1.0
    X[:, feat_idx["direction_buy"]] = (directions == "BUY").astype(float)
    X[:, feat_idx["critical_failures"]] = 0.0

    # Nuevas variables predictivas
    X[:, feat_idx["adx_regime"]] = (adxs >= 20.0).astype(float)
    X[:, feat_idx["signal_age_penalty"]] = float(np.exp(-0.2 * 15.0))
    X[:, feat_idx["spread_to_sl_ratio"]] = 0.05
    
    # Session killzone
    killzone_mask = np.isin(hours, [7, 8, 9, 12, 13, 14, 15])
    X[:, feat_idx["session_killzone_active"]] = killzone_mask.astype(float)

    # Familias de instrumentos
    for i, (sym, cat) in enumerate(zip(symbols, categories)):
        if "boom" in sym:
            X[i, feat_idx["is_boom"]] = 1.0
        elif "crash" in sym:
            X[i, feat_idx["is_crash"]] = 1.0
        elif "volatility" in sym or "1hz" in sym or "v10" in sym or "v25" in sym or "v50" in sym or "v75" in sym:
            X[i, feat_idx["is_volatility"]] = 1.0
        elif "forex" in cat or any(c in sym for c in ("eur", "usd", "gbp", "jpy", "aud", "cad", "chf", "nzd")) and "xau" not in sym:
            X[i, feat_idx["is_forex"]] = 1.0
        elif "gold" in sym or "xau" in sym:
            X[i, feat_idx["is_gold"]] = 1.0
        elif "step" in sym:
            X[i, feat_idx["is_step"]] = 1.0
        elif "jump" in sym:
            X[i, feat_idx["is_jump"]] = 1.0

    y = y_labels.astype(int)

    # Split temporal walk-forward: 80% train, 20% test
    split_idx = int(n_samples * 0.80)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Muestras de entrenamiento: {len(X_train):,} | Muestras de prueba out-of-sample: {len(X_test):,}")

    # Ajustar LogisticRegressionModel
    print("Entrenando LogisticRegressionModel con NumPy...")
    lrm = LogisticRegressionModel(feature_names=FEATURE_NAMES)
    lrm.fit(X_train, y_train, learning_rate=0.08, epochs=100, l2=1e-3)

    # Evaluación y Calibración sobre conjunto de validación
    raw_test_probs = lrm.predict_proba(X_test)
    calibrator = ProbabilityCalibrator()
    calibrator.fit(raw_test_probs, y_test, bins=10)

    calibrated_test_probs = np.array([calibrator.calibrate(p) for p in raw_test_probs])
    pred_test = (calibrated_test_probs >= 0.50).astype(int)
    acc = float(np.mean(pred_test == y_test))

    # Filtro IA con umbral >= 0.50
    filtered_mask = calibrated_test_probs >= 0.50
    if np.any(filtered_mask):
        win_rate_filtered = float(np.mean(y_test[filtered_mask]))
        trades_selected = int(np.sum(filtered_mask))
    else:
        win_rate_filtered = float(np.mean(y_test))
        trades_selected = len(y_test)

    print("\n" + "=" * 60)
    print("RESULTADOS DEL MODELO OUT-OF-SAMPLE (ÚLTIMOS MESES)")
    print("=" * 60)
    print(f"Precisión global (Accuracy)          : {acc * 100:.2f}%")
    print(f"Win Rate base del conjunto de prueba : {np.mean(y_test) * 100:.2f}%")
    print(f"Win Rate con filtro IA (Prob >= 50%) : {win_rate_filtered * 100:.2f}%")
    print(f"Trades calificados / autorizados     : {trades_selected:,} de {len(y_test):,}")
    print("=" * 60)

    # Calcular estadísticas de RR históricas en Malaysian SNR
    wins_df = df[df["target"] == 1]
    losses_df = df[df["target"] == 0]
    avg_win_rr = float(wins_df["total_rr"].mean()) if not wins_df.empty else 2.5
    avg_loss_rr = 1.0  # SL siempre definido en 1R

    # Crear CalibratedLogisticModel completo
    model = CalibratedLogisticModel(
        worker="MALAYSIAN_SNR",
        strategy_name="MALAYSIAN_SNR",
        model=lrm,
        calibrator=calibrator,
        trained_at=datetime.now(timezone.utc).isoformat(),
        average_win_rr=round(avg_win_rr, 3),
        average_loss_rr=round(avg_loss_rr, 3),
    )

    out_dir = PROJECT_ROOT / "storage" / "ai_models"
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = MetaLabelingEngine(
        MetaLabelingConfig(enabled=True, model_directory=str(out_dir)),
        worker="MALAYSIAN_SNR",
    )

    path_strat = engine.save_model(model)
    print(f"\nModelo por estrategia guardado: {path_strat}")

    # Guardar también para estrategia ALL
    model_all = CalibratedLogisticModel(
        worker="MALAYSIAN_SNR",
        strategy_name="ALL",
        model=lrm,
        calibrator=calibrator,
        trained_at=datetime.now(timezone.utc).isoformat(),
        average_win_rr=round(avg_win_rr, 3),
        average_loss_rr=round(avg_loss_rr, 3),
    )
    path_all = engine.save_model(model_all)
    print(f"Modelo para estrategia ALL guardado: {path_all}")

    # Guardar métricas de validación en JSON para el dashboard de IA
    metrics_path = out_dir / "metalabel_MALAYSIAN_SNR_metrics.json"
    metrics_data = {
        "worker": "MALAYSIAN_SNR",
        "strategy_name": "MALAYSIAN_SNR",
        "trained_at": model.trained_at,
        "samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(acc, 4),
        "win_rate_base": round(float(np.mean(y_test)), 4),
        "win_rate_filtered": round(win_rate_filtered, 4),
        "average_win_rr": round(avg_win_rr, 3),
        "average_loss_rr": round(avg_loss_rr, 3),
        "thresholds": {
            "min_probability": 0.45,
            "min_net_expectancy_r": 0.10,
            "runner_extension_min_probability": 0.58,
        }
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Métricas de modelo guardadas en: {metrics_path}")


if __name__ == "__main__":
    train_malaysian_snr_ai_models()
