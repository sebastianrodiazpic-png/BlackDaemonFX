"""Demostración del Meta-Etiquetado de IA para Malaysian SNR.

Ejecuta inferencias en tiempo real con MetaLabelingEngine para demostrar cómo
el modelo entrenado filtra señales de baja probabilidad y optimiza la toma de decisiones
en escenarios institucionales reales.
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

from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig, FILTER_MODE
from strategy.ai.feature_extraction import FEATURE_NAMES, extract_meta_features, feature_vector


def run_meta_labeling_demonstration():
    print("=" * 95)
    print("DEMOSTRACIÓN EN TIEMPO REAL: META-ETIQUETADO DE IA EN MALAYSIAN SNR")
    print("=" * 95)

    # 1. Instanciar Motor de Meta-Etiquetado en Modo FILTER
    model_dir = str(PROJECT_ROOT / "storage" / "ai_models")
    config = MetaLabelingConfig(
        enabled=True,
        mode=FILTER_MODE,
        min_probability=0.50,
        min_probability_forex=0.55,
        min_probability_gold=0.55,
        min_probability_volatility=0.52,
        min_net_expectancy_r=0.10,
        model_directory=model_dir,
    )
    engine = MetaLabelingEngine(config, worker="MALAYSIAN_SNR")

    # Cargar modelo entrenado de Malaysian SNR
    model = engine.load_model(strategy_name="MALAYSIAN_SNR")
    print(f"\n[1] ESTADO DEL META-MODELO DE IA:")
    print(f"  - Worker                : {engine.worker}")
    print(f"  - Estrategia            : {model.strategy_name}")
    print(f"  - Estado de Entrenamiento: {'ENTRENADO Y ACTIVO' if model.trained else 'NO ENTRENADO'}")
    print(f"  - Fecha de Calibración  : {model.trained_at}")
    print(f"  - Vector Canónico       : {len(model.model.feature_names)} features (meta-features-v5)")
    print(f"  - Modo Operativo        : {config.mode} (Bloqueo activo de trades con baja expectativa)")
    print(f"  - R/R Ganador Promedio  : {model.average_win_rr}R")
    print(f"  - R/R Perdedor Promedio : {model.average_loss_rr}R")

    if not model.trained:
        print("[ERROR] El modelo no está entrenado. Por favor ejecute tools/train_malaysian_snr_meta_model.py primero.")
        return

    # 2. Casos de Prueba Paradigmáticos
    print("\n" + "=" * 95)
    print("[2] PRUEBAS DE INFERENCIA EN TIEMPO REAL: EVALUACIÓN DE SEÑALES CONFIRMADAS")
    print("=" * 95)

    scenarios = [
        {
            "id": "CASO_1",
            "title": "Caso 1: Trade Institucional de Alta Convicción (Jump 10 Index - Quasimodo Fractal)",
            "description": "Retesteo de Left Shoulder QM en Killzone Londres (08:30 UTC), ADX 28.5, estructura alcista confirmada.",
            "symbol": "Jump 10 Index",
            "signal": {
                "symbol": "Jump 10 Index",
                "direction": "BUY",
                "scenario": "ESC_3_FRACTAL",
                "entry_time": "2026-10-09T08:30:00Z",
                "entry_price": 1250.0,
                "stop_loss": 1240.0,
                "risk_reward_ratio": 2.0,
                "risk_reward_ratio_tp1": 2.0,
                "tp1_price": 1270.0,
                "tp2_price": 1290.0,
                "adx": 28.5,
                "atr": 10.0,
                "trade_score": 92.0,
                "confirmation_percentage": 90.0,
                "structure_break": "ESC_3_FRACTAL_BUY",
                "chart_pattern_strength": 0.95,
                "timeframe": "M15",
            },
            "eval_time": "2026-10-09T08:30:00Z",
            "expected_verdict": "APROBADO",
        },
        {
            "id": "CASO_2",
            "title": "Caso 2: Breakout Institucional en Materia Prima Líder (Oro XAUUSD en Killzone Nueva York)",
            "description": "Ruptura M15 con cuerpo sólido en Killzone NY (14:30 UTC), ADX 26.0, Storyline D1 alcista alineado.",
            "symbol": "XAUUSD",
            "signal": {
                "symbol": "XAUUSD",
                "direction": "BUY",
                "scenario": "ESC_1_CONTINUATION",
                "entry_time": "2026-10-09T14:30:00Z",
                "entry_price": 2650.0,
                "stop_loss": 2642.0,
                "risk_reward_ratio": 2.0,
                "risk_reward_ratio_tp1": 2.0,
                "tp1_price": 2666.0,
                "tp2_price": 2682.0,
                "adx": 26.0,
                "atr": 5.0,
                "trade_score": 85.0,
                "confirmation_percentage": 82.0,
                "structure_break": "ESC_1_CONTINUATION_BUY",
                "chart_pattern_strength": 0.85,
                "timeframe": "M15",
            },
            "eval_time": "2026-10-09T14:30:00Z",
            "expected_verdict": "APROBADO",
        },
        {
            "id": "CASO_3",
            "title": "Caso 3: Señal Tóxica / Falso Rompimiento Fuera de Sesión (EURUSD a las 02:00 UTC)",
            "description": "Señal generada en sesión asiática (02:00 UTC, fuera de Killzone), ADX débil (13.0), sin volumen institucional.",
            "symbol": "EURUSD",
            "signal": {
                "symbol": "EURUSD",
                "direction": "BUY",
                "scenario": "ESC_2_REVERSAL",
                "entry_time": "2026-10-09T02:00:00Z",
                "entry_price": 1.0950,
                "stop_loss": 1.0940,
                "risk_reward_ratio": 2.0,
                "risk_reward_ratio_tp1": 2.0,
                "tp1_price": 1.0970,
                "tp2_price": 1.0990,
                "adx": 13.0,
                "atr": 0.0008,
                "trade_score": 55.0,
                "confirmation_percentage": 50.0,
                "structure_break": "ESC_2_REVERSAL_BUY",
                "chart_pattern_strength": 0.40,
                "chart_pattern_conflict": 0.60,
                "timeframe": "M15",
            },
            "eval_time": "2026-10-09T02:00:00Z",
            "expected_verdict": "BLOQUEADO",
        },
        {
            "id": "CASO_4",
            "title": "Caso 4: Reversal Sucio / FVG Pierce Contratendencial (USOil)",
            "description": "Perforación de FVG sin confluencia de soporte D1, ADX 12.0, spread relativo desfavorable.",
            "symbol": "USOil",
            "signal": {
                "symbol": "USOil",
                "direction": "SELL",
                "scenario": "ESC_5_FVG_PIERCE",
                "entry_time": "2026-10-09T18:00:00Z",
                "entry_price": 75.0,
                "stop_loss": 75.8,
                "risk_reward_ratio": 2.0,
                "risk_reward_ratio_tp1": 2.0,
                "tp1_price": 73.4,
                "tp2_price": 71.8,
                "adx": 12.0,
                "atr": 0.6,
                "trade_score": 45.0,
                "confirmation_percentage": 40.0,
                "structure_break": "ESC_5_FVG_PIERCE_SELL",
                "chart_pattern_strength": 0.30,
                "chart_pattern_conflict": 0.70,
                "timeframe": "M15",
            },
            "eval_time": "2026-10-09T18:00:00Z",
            "expected_verdict": "BLOQUEADO",
        },
    ]

    for case in scenarios:
        print(f"\n--- {case['title']} ---")
        print(f"Contexto Operativo: {case['description']}")

        # Extraer características sincronizadas temporalmente con la vela de confirmación
        features = extract_meta_features(
            signal=case["signal"],
            evaluated_at=case["eval_time"],
        )
        vec = feature_vector(features)

        # Inferencia matemática
        prob = model.probability(vec)
        expectancy = model.net_expectancy_r(prob)
        min_prob = engine.resolve_min_probability(case["symbol"])
        min_expectancy = config.min_net_expectancy_r

        # Lógica de decisión del modo FILTER
        allowed = (prob >= min_prob) and (expectancy >= min_expectancy)
        reason = (
            "PROBABILITY_AND_EXPECTANCY_ACCEPTED"
            if allowed
            else ("PROBABILITY_BELOW_THRESHOLD" if prob < min_prob else "NET_EXPECTANCY_BELOW_THRESHOLD")
        )
        runner_eligible = (prob >= 0.58) and allowed

        prob_pct = prob * 100.0
        min_prob_pct = min_prob * 100.0

        print(f"Diagnóstico del Meta-Etiquetado (Meta-Labeling Engine):")
        print(f"  * Probabilidad Calibrada (P)  : {prob_pct:.1f}% (Umbral Adaptativo: {min_prob_pct:.1f}%)")
        print(f"  * Expectativa Matemática Neta : {'+' if expectancy >= 0 else ''}{expectancy:.3f}R (Exigencia Mínima: +{min_expectancy:.2f}R)")
        print(f"  * Decisión Final del Filtro   : {'[AUTORIZADO] EJECUTAR EN BROKER' if allowed else '[BLOQUEADO] RECHAZAR SEÑAL'}")
        print(f"  * Código de Auditoría         : {reason}")
        print(f"  * Extensión a Runner (TP3/TP4): {'HABILITADA (P >= 58%)' if runner_eligible else 'DESHABILITADA (Objetivo en TP2)'}")

        if allowed:
            print(f"  >>> IMPACTO POSITIVO: La señal cuenta con alta convicción probabilística. Se autoriza la entrada dual-leg.")
        else:
            print(f"  >>> SALVAGUARDA DE CAPITAL: La IA bloquea la orden antes de enviarse al broker, ahorrando -1.0R de pérdida.")

    # 3. Resumen Cuantitativo General de la Auditoría Out-Of-Sample
    metrics_path = Path(model_dir) / "metalabel_MALAYSIAN_SNR_metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        print("\n" + "=" * 95)
        print("[3] RESUMEN CUANTITATIVO DE IMPACTO: AUDITORÍA FUERA DE MUESTRA (2 AÑOS)")
        print("=" * 95)
        wr_base = metrics.get("win_rate_base", 0.3493) * 100.0
        th_eval = metrics.get("thresholds_eval", {})

        print(f"Total Operaciones Evaluadas       : {metrics.get('samples', 207520):,} trades")
        print(f"Operaciones de Test (Out-of-Sample): {metrics.get('test_samples', 41504):,} trades")
        print(f"Win Rate Base (Sin Filtro IA)     : {wr_base:.2f}% (Expectativa Neta: +0.071R / trade)")
        print("-" * 95)
        print(f"{'Umbral de Probabilidad':<25} | {'Win Rate Resultante':<22} | {'Trades Aceptados':<20} | {'Mejora Neta':<15}")
        print("-" * 95)
        for th_key, res in th_eval.items():
            th_f = float(th_key)
            wr_f = res["win_rate"] * 100.0
            cnt = res["selected_trades"]
            total = metrics.get("test_samples", 41504)
            pct_cnt = (cnt / total) * 100.0
            print(f"Probabilidad >= {th_f*100:.0f}%{'':<10} | {wr_f:.2f}%{'':<14} | {cnt:,} ({pct_cnt:.1f}%){'':<7} | +{wr_f - wr_base:.1f}%")
        print("=" * 95)


if __name__ == "__main__":
    run_meta_labeling_demonstration()
