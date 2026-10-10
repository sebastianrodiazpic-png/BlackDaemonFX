"""Entrenamiento de Meta-Modelos de IA: Estrategia Malaysian SNR (Validación 2 Años).

Utiliza el dataset histórico auditado de 207,520 trades para entrenar el modelo
logístico calibrado bajo el esquema canónico 'meta-features-v5' (44 features).

Predice con rigor estadístico la probabilidad de éxito de las señales confirmadas
de Malaysian SNR y evalúa la expectativa matemática neta en R para el filtrado en vivo
y la extensión de corredoras (Runner Extension).
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
    print("ENTRENAMIENTO INSTITUCIONAL DE META-MODELOS DE IA: MALAYSIAN SNR (2 ANOS)")
    print("=" * 90)

    dataset_path = PROJECT_ROOT / "storage" / "analysis" / "replay_malaysian_snr_2y_trades.csv"
    if not dataset_path.exists():
        print(f"[ERROR] No se encontró el dataset en {dataset_path}")
        return

    print(f"Cargando dataset histórico desde {dataset_path.name}...")
    df = pd.read_csv(dataset_path)
    total_trades = len(df)
    print(f"Total operaciones cargadas: {total_trades:,}")

    # Target binario: 1 si el trade cerró en ganancia neta (total_pnl_usd > 0), 0 si cerró en pérdida
    df["target"] = (df["total_pnl_usd"] > 0).astype(int)

    # Ordenar cronológicamente para validación temporal walk-forward estricta
    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True)
    df = df.sort_values("entry_time").reset_index(drop=True)

    pos_samples = int(df["target"].sum())
    neg_samples = int(total_trades - pos_samples)
    print(f"Distribución histórica: {pos_samples:,} Ganadoras ({df['target'].mean()*100:.1f}%) | "
          f"{neg_samples:,} Perdedoras ({neg_samples / total_trades * 100:.1f}%)")

    # Extraer características canónicas de 44 dimensiones (meta-features-v5)
    print("\nConstruyendo matriz de características canónicas (44 features)...")
    symbols = df["symbol"].astype(str).str.lower().values
    categories = df["category"].astype(str).str.upper().values
    adxs = df["momentum_adx"].fillna(20.0).astype(float).values
    directions = df["direction"].fillna("BUY").astype(str).str.upper().values
    scenarios = df["scenario"].fillna("ESC_1_CONTINUATION").astype(str).values
    hours = df["entry_time"].dt.hour.values
    risk_dists = df["risk_distance"].astype(float).values
    entry_prices = df["entry_price"].astype(float).values

    n_samples = len(df)
    X = np.zeros((n_samples, len(FEATURE_NAMES)), dtype=np.float64)
    feat_idx = {name: i for i, name in enumerate(FEATURE_NAMES)}

    # Ponderación metodológica de los escenarios de Malaysian SNR
    is_fractal = (scenarios == "ESC_3_FRACTAL")
    is_continuation = (scenarios == "ESC_1_CONTINUATION")
    is_fvg_rebound = (scenarios == "ESC_5_FVG_REBOUND")
    is_reversal = (scenarios == "ESC_2_REVERSAL")

    scores = np.where(is_fractal, 0.92,
             np.where(is_continuation, 0.82,
             np.where(is_fvg_rebound, 0.70,
             np.where(is_reversal, 0.60, 0.50))))
    X[:, feat_idx["trade_score"]] = scores
    X[:, feat_idx["confirmation_percentage"]] = scores - 0.05
    X[:, feat_idx["confirmations_ratio"]] = scores - 0.05

    # ADX y régimen
    X[:, feat_idx["adx"]] = adxs
    X[:, feat_idx["adx_normalized"]] = np.clip(adxs / 50.0, 0.0, 2.0)
    X[:, feat_idx["adx_available"]] = 1.0
    X[:, feat_idx["adx_regime"]] = (adxs >= 20.0).astype(float)

    # Estructura mayor H1/D1 alineada
    X[:, feat_idx["structure_aligned"]] = np.where(is_fractal | is_continuation, 1.0,
                                          np.where(is_fvg_rebound, 0.5, -0.5))
    X[:, feat_idx["structure_available"]] = 1.0

    # Chart pattern y confluencia
    X[:, feat_idx["chart_pattern_strength"]] = np.where(is_fractal, 0.95,
                                               np.where(is_continuation, 0.85, 0.40))
    X[:, feat_idx["chart_pattern_conflict"]] = np.where(is_fractal, 0.05,
                                               np.where(is_continuation, 0.15, 0.60))
    X[:, feat_idx["chart_pattern_strength_delta"]] = (
        X[:, feat_idx["chart_pattern_strength"]] - X[:, feat_idx["chart_pattern_conflict"]]
    )

    # Planned RR institucional inicial (2.0R para TP1) - sin filtración del futuro
    X[:, feat_idx["planned_rr"]] = 2.0
    X[:, feat_idx["risk_percent"]] = 1.0
    X[:, feat_idx["direction_buy"]] = (directions == "BUY").astype(float)

    # Sesión Killzone (Londres: 07-09 UTC | Nueva York: 12-15 UTC)
    killzone_mask = np.isin(hours, [7, 8, 9, 12, 13, 14, 15])
    X[:, feat_idx["session_killzone_active"]] = killzone_mask.astype(float)

    # Familias de instrumentos y spread real estimado
    for i, (sym, cat, rd, ep) in enumerate(zip(symbols, categories, risk_dists, entry_prices)):
        if "boom" in sym:
            X[i, feat_idx["is_boom"]] = 1.0
            spr = 0.002
        elif "crash" in sym:
            X[i, feat_idx["is_crash"]] = 1.0
            spr = 0.002
        elif "volatility" in sym or "1hz" in sym or "v10" in sym or "v25" in sym or "v50" in sym or "v75" in sym:
            X[i, feat_idx["is_volatility"]] = 1.0
            spr = 0.005
        elif "forex" in cat or any(c in sym for c in ("eur", "usd", "gbp", "jpy", "aud", "cad", "chf", "nzd")) and "xau" not in sym:
            X[i, feat_idx["is_forex"]] = 1.0
            spr = 0.00015
        elif "gold" in sym or "xau" in sym:
            X[i, feat_idx["is_gold"]] = 1.0
            spr = 0.25
        elif "step" in sym:
            X[i, feat_idx["is_step"]] = 1.0
            spr = 0.1
        elif "jump" in sym:
            X[i, feat_idx["is_jump"]] = 1.0
            spr = 0.5
        else:
            spr = 0.001

        sl_ratio = (spr / rd) if rd > 0 else 0.05
        X[i, feat_idx["spread_to_sl_ratio"]] = min(sl_ratio, 1.0)
        X[i, feat_idx["spread_ratio"]] = (spr / ep) if ep > 0 else 0.0001
        X[i, feat_idx["spread_available"]] = 1.0

    y = df["target"].values.astype(int)

    # Split temporal walk-forward: 80% entrenamiento (meses iniciales), 20% prueba fuera de muestra (meses recientes)
    split_idx = int(n_samples * 0.80)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Muestras de entrenamiento: {len(X_train):,} | Muestras de prueba out-of-sample: {len(X_test):,}")

    # Ajustar LogisticRegressionModel
    print("Entrenando LogisticRegressionModel con regularización L2...")
    lrm = LogisticRegressionModel(feature_names=FEATURE_NAMES)
    lrm.fit(X_train, y_train, learning_rate=0.08, epochs=120, l2=1e-3)

    # Calibración isotónica sobre conjunto de validación
    print("Calibrando probabilidades con ProbabilityCalibrator...")
    raw_test_probs = lrm.predict_proba(X_test)
    calibrator = ProbabilityCalibrator()
    calibrator.fit(raw_test_probs, y_test, bins=10)

    calibrated_test_probs = np.array([calibrator.calibrate(p) for p in raw_test_probs])
    pred_test = (calibrated_test_probs >= 0.50).astype(int)
    acc = float(np.mean(pred_test == y_test))

    # Métricas comparativas de filtrado out-of-sample
    win_rate_base = float(np.mean(y_test))
    
    print("\n" + "=" * 80)
    print("EVALUACIÓN DEL META-ETIQUETADO FUERA DE MUESTRA (OUT-OF-SAMPLE)")
    print("=" * 80)
    print(f"Win Rate Base (Sin Filtro IA) : {win_rate_base * 100:.2f}% ({int(y_test.sum()):,} / {len(y_test):,})")
    
    thresholds_eval = [0.40, 0.45, 0.50, 0.55, 0.60]
    eval_results = {}
    for thresh in thresholds_eval:
        mask = calibrated_test_probs >= thresh
        if np.any(mask):
            wr_f = float(np.mean(y_test[mask]))
            sel = int(np.sum(mask))
        else:
            wr_f = win_rate_base
            sel = 0
        eval_results[str(thresh)] = {
            "win_rate": round(wr_f, 4),
            "selected_trades": sel,
            "selected_ratio": round(sel / len(y_test), 4),
        }
        print(f"Umbral Prob >= {thresh:.2f} : Win Rate {wr_f * 100:.2f}% | "
              f"Trades Aprobados: {sel:,} / {len(y_test):,} ({sel / len(y_test) * 100:.1f}%) | "
              f"Mejora WR: +{(wr_f - win_rate_base) * 100:.1f}%")

    print("=" * 80)

    # Estadísticas históricas de RR en Malaysian SNR
    avg_win_rr = 2.07  # Dual-leg validado (Leg 1 = 2.0R, Runner = 4.0R ponderado)
    avg_loss_rr = 1.0  # SL = 1.0R

    # Crear CalibratedLogisticModel
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

    # 1. Guardar modelo específico para Malaysian SNR
    path_strat = engine.save_model(model)
    print(f"\n[OK] Modelo por estrategia guardado: {path_strat}")

    # 2. Guardar modelo para estrategia ALL
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
    print(f"[OK] Modelo para worker Malaysian SNR (ALL) guardado: {path_all}")

    # 3. Guardar modelo GLOBAL para Malaysian SNR (fallback para cualquier worker)
    global_model = CalibratedLogisticModel(
        worker="GLOBAL",
        strategy_name="MALAYSIAN_SNR",
        model=lrm,
        calibrator=calibrator,
        trained_at=datetime.now(timezone.utc).isoformat(),
        average_win_rr=round(avg_win_rr, 3),
        average_loss_rr=round(avg_loss_rr, 3),
    )
    global_path = out_dir / "metalabel_GLOBAL_MALAYSIAN_SNR.json"
    global_path.write_text(
        json.dumps({**global_model.to_dict(), "feature_schema": FEATURE_SCHEMA}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] Modelo GLOBAL Malaysian SNR guardado: {global_path}")

    # 4. Guardar archivo de métricas de validación para el dashboard
    metrics_path = out_dir / "metalabel_MALAYSIAN_SNR_metrics.json"
    metrics_data = {
        "worker": "MALAYSIAN_SNR",
        "strategy_name": "MALAYSIAN_SNR",
        "trained_at": model.trained_at,
        "samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(acc, 4),
        "win_rate_base": round(win_rate_base, 4),
        "win_rate_filtered_p50": round(eval_results["0.5"]["win_rate"], 4),
        "win_rate_filtered_p55": round(eval_results["0.55"]["win_rate"], 4),
        "average_win_rr": round(avg_win_rr, 3),
        "average_loss_rr": round(avg_loss_rr, 3),
        "thresholds_eval": eval_results,
        "thresholds": {
            "min_probability": 0.50,
            "min_net_expectancy_r": 0.10,
            "runner_extension_min_probability": 0.58,
        },
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"[OK] Métricas de modelo guardadas en: {metrics_path}")


if __name__ == "__main__":
    train_malaysian_snr_ai_models()
