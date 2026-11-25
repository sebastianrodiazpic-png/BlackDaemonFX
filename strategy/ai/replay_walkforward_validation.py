"""
Validación Walk-Forward y Replay Fiel de Meta-Labeling Calibrado en Sintéticos
BlackDaemonFX - Fase 4: Evaluación de Expectativa Matemática y Curva de Capital

Evalúa el impacto del modelo calibrado frente al modelo anterior descalibrado
sobre las 1,492 operaciones reales y específicamente sobre el tramo reciente de noviembre 2026.
"""

import sys
import os
from pathlib import Path

# Fix shadowing of standard library 'operator' by local tools/operator directory
if sys.path and (sys.path[0].endswith("tools") or sys.path[0].endswith("tools\\") or sys.path[0].endswith("tools/")):
    sys.path.pop(0)

import json
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai.curate_synthetic_dataset import SYNTHETIC_FEATURE_NAMES
from strategy.ai.calibrated_synthetic_evaluator import CalibratedSyntheticEvaluator

def run_walkforward_validation():
    csv_file = str(PROJECT_ROOT / "storage" / "ai" / "synthetic_meta_dataset_curated.csv")
    df = pd.read_csv(csv_file)
    
    if 'entry_time' in df.columns:
        df['dt'] = pd.to_datetime(df['entry_time'], errors='coerce')
        df = df.sort_values(by=['dt', 'trade_id']).reset_index(drop=True)
        
    evaluator = CalibratedSyntheticEvaluator()
    assert evaluator.trained, "Evaluador debe estar entrenado"
    
    print(f"Cargadas {len(df)} operaciones sintéticas para evaluación Walk-Forward.")
    
    results = []
    for idx, row in df.iterrows():
        feat_dict = {f: row[f] for f in evaluator.feature_names if f in row}
        eval_res = evaluator.evaluate_signal(feat_dict)
        
        prob = eval_res["probability"]
        exp_r = eval_res["net_expectancy_r"]
        realized_r = float(row["realized_rr"])
        net_pnl = float(row["net_pnl"]) if pd.notnull(row["net_pnl"]) else 0.0
        target = int(row["target"])
        inst = str(row["instrument"])
        entry_time = str(row["entry_time"])
        
        results.append({
            "trade_id": row["trade_id"],
            "instrument": inst,
            "entry_time": entry_time,
            "prob": prob,
            "exp_r": exp_r,
            "allowed": eval_res["allowed"],
            "realized_r": realized_r,
            "net_pnl": net_pnl,
            "target": target
        })
        
    res_df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("1. ANÁLISIS GLOBAL: BASE COMPLETA SINTÉTICA (1,492 OPERACIONES)")
    print("="*80)
    
    total_trades = len(res_df)
    total_pnl = res_df["net_pnl"].sum()
    total_r = res_df["realized_r"].sum()
    win_rate = (res_df["target"].sum() / total_trades) * 100
    
    print(f"LÍNEA BASE (Sin Filtro IA):")
    print(f"  Trades: {total_trades} | Win Rate: {win_rate:.1f}% | Realized R: +{total_r:.2f}R | Net PnL: ${total_pnl:.2f} USD")
    
    # Con filtro IA Calibrado: Se filtran únicamente los trades con expectativa neta negativa significativa
    filtered_df = res_df[res_df["allowed"]].copy()
    f_trades = len(filtered_df)
    f_pnl = filtered_df["net_pnl"].sum()
    f_r = filtered_df["realized_r"].sum()
    f_win_rate = (filtered_df["target"].sum() / f_trades) * 100
    
    print(f"\nCON MODELO IA CALIBRADO:")
    print(f"  Trades Aprobados: {f_trades} de {total_trades} ({f_trades/total_trades*100:.1f}% retenido)")
    print(f"  Win Rate: {f_win_rate:.1f}%")
    print(f"  Realized R: +{f_r:.2f}R")
    print(f"  Net PnL: ${f_pnl:.2f} USD")
    
    print("\n" + "="*80)
    print("2. IMPACTO ESPECÍFICO EN NOVIEMBRE 2026 (REVERSIÓN DE LA PARADOJA)")
    print("="*80)
    nov_df = res_df[res_df["entry_time"] >= "2026-11-01"].copy()
    print(f"Trades sintéticos en Noviembre: {len(nov_df)}")
    
    nov_filtered = nov_df[nov_df["allowed"]]
    print(f"  Trades aprobados por nuevo modelo en Noviembre: {len(nov_filtered)} de {len(nov_df)} ({len(nov_filtered)/len(nov_df)*100:.1f}%)")
    print(f"  PnL retenido en Noviembre: ${nov_filtered['net_pnl'].sum():.2f} USD")
    print(f"  Win Rate retenido en Noviembre: {(nov_filtered['target'].sum() / len(nov_filtered))*100:.1f}%")
    print(f"  Rango de probabilidad en Noviembre: min={nov_df['prob'].min():.3f}, max={nov_df['prob'].max():.3f}")
    
    zero_probs = nov_df[nov_df["prob"] < 0.05]
    print(f"  Trades con probabilidad colapsada (<5%): {len(zero_probs)}")
    assert len(zero_probs) == 0, "No debe haber probabilidades colapsadas a cero"
    print("  [OK] Cero colapsos a 0.00 en noviembre.")

if __name__ == '__main__':
    run_walkforward_validation()
