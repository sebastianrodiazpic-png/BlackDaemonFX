"""tools/audit_pata2_conversion.py - Auditoría Cuantitativa de Pata 2 y Conversión a TP2/TP3/TP4.

Calcula con rigor estadístico y microestructura:
1. Tasa de conversión de Pata 1 (TP1) y tasa de fallo directo a Stop Loss.
2. Tasa de conversión de Pata 2:
   - Proporción que muere en BE plano (TP1+BE).
   - Proporción que convierte a TP2 (2R).
   - Proporción que extiende a TP3 (3R).
3. Expectativa matemática E(R) por operación y por segmento (Año 0 y Año 1).
4. Tasa de ganancia efectiva (Win Rate de trades con R > 0).
5. Impacto de optimizar los umbrales de TP1 y los locks progresivos del Runner.
"""

from __future__ import annotations

import sys
if sys.path and ("tools" in sys.path[0] or sys.path[0].endswith("tools")):
    sys.path.pop(0)
from pathlib import Path

import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / "storage" / "analysis"


def audit_exit_dataset(file_path: Path):
    if not file_path.exists():
        print(f"Archivo no encontrado: {file_path}")
        return None

    df = pd.read_csv(file_path)
    total_trades = len(df)
    print(f"\n{'='*80}")
    print(f"AUDITORÍA DE DATASET: {file_path.name} ({total_trades} trades evaluados)")
    print(f"{'='*80}")

    variants = [
        ("tp1_1.0_r2", "Gestión Actual (TP1 1.0R + Runner 2.0R)"),
        ("tp1_0.8_r2", "TP1 Temprano (TP1 0.8R + Runner 2.0R)"),
        ("tp1_0.6_r2", "TP1 Rápido (TP1 0.6R + Runner 2.0R)"),
        ("tp1_1.2_r2", "TP1 Amplio (TP1 1.2R + Runner 2.0R)"),
        ("tp1_1.0_r3", "Runner Largo (TP1 1.0R + Runner 3.0R)"),
        ("tp1_0.8_r3", "Híbrido (TP1 0.8R + Runner 3.0R)"),
        ("tp1_1.0_r1.5", "Salida Conservadora (TP1 1.0R + Runner 1.5R)"),
        ("tp1_0.8_r1.5", "Defensiva (TP1 0.8R + Runner 1.5R)"),
    ]

    results = []

    for key, label in variants:
        out_col = f"{key}_out"
        r_col = key

        if out_col not in df.columns or r_col not in df.columns:
            continue

        outcomes = df[out_col].value_counts()
        n_sl = outcomes.get("SL", 0)
        n_be = outcomes.get("TP1+BE", 0)
        n_tp2 = outcomes.get("TP2", 0)
        n_tp3 = outcomes.get("TP3", 0)

        # Trades que superaron TP1
        reached_tp1 = n_be + n_tp2 + n_tp3
        pct_reached_tp1 = (reached_tp1 / total_trades) * 100.0 if total_trades else 0.0

        # Tasa de conversión de Pata 2 dado que tocó TP1
        conv_be = (n_be / reached_tp1) * 100.0 if reached_tp1 else 0.0
        conv_tp2 = (n_tp2 / reached_tp1) * 100.0 if reached_tp1 else 0.0
        conv_tp3 = (n_tp3 / reached_tp1) * 100.0 if reached_tp1 else 0.0

        r_values = df[r_col].dropna()
        total_r = float(r_values.sum())
        exp_r = float(r_values.mean())
        win_rate = (len(r_values[r_values > 0]) / total_trades) * 100.0 if total_trades else 0.0
        profit_factor = (
            abs(r_values[r_values > 0].sum() / r_values[r_values < 0].sum())
            if len(r_values[r_values < 0]) and r_values[r_values < 0].sum() != 0
            else float("nan")
        )

        results.append({
            "key": key,
            "label": label,
            "total_trades": total_trades,
            "n_sl": int(n_sl),
            "n_be": int(n_be),
            "n_tp2": int(n_tp2),
            "n_tp3": int(n_tp3),
            "reached_tp1_pct": pct_reached_tp1,
            "conv_be_pct": conv_be,
            "conv_tp2_pct": conv_tp2,
            "conv_tp3_pct": conv_tp3,
            "win_rate": win_rate,
            "total_r": total_r,
            "exp_r": exp_r,
            "profit_factor": profit_factor,
        })

    # Imprimir tabla comparativa
    print(f"{'VARIANTE':<40} | {'WR %':<7} | {'TP1 %':<7} | {'P2->BE':<8} | {'P2->TP2/3':<10} | {'E[R]':<8} | {'TOT R':<9} | {'PF':<6}")
    print("-" * 105)
    for r in results:
        runner_conv = r["conv_tp2_pct"] + r["conv_tp3_pct"]
        print(f"{r['label']:<40} | {r['win_rate']:>5.1f}% | {r['reached_tp1_pct']:>5.1f}% | {r['conv_be_pct']:>6.1f}% | {runner_conv:>8.1f}% | {r['exp_r']:>6.3f}R | {r['total_r']:>7.1f}R | {r['profit_factor']:>5.2f}")

    return results


def run_full_pata2_audit():
    y0_file = ANALYSIS_DIR / "ict_exit_variants_y0.csv"
    y1_file = ANALYSIS_DIR / "ict_exit_variants_y1.csv"

    res_y0 = audit_exit_dataset(y0_file)
    res_y1 = audit_exit_dataset(y1_file)

    if res_y0 and res_y1:
        print(f"\n{'='*80}")
        print("CONSOLIDADO MULTIANUAL (Y0 + Y1) - CONSISTENCIA TEMPORAL")
        print(f"{'='*80}")
        print(f"{'VARIANTE':<40} | {'E[R] Y0':<9} | {'E[R] Y1':<9} | {'E[R] GLOBAL':<11} | {'TOT R GLOBAL':<12} | {'ESTADO':<10}")
        print("-" * 100)

        for i in range(len(res_y0)):
            r0 = res_y0[i]
            r1 = res_y1[i]
            tot_trades = r0["total_trades"] + r1["total_trades"]
            tot_r = r0["total_r"] + r1["total_r"]
            exp_global = tot_r / tot_trades if tot_trades else 0.0
            both_pos = r0["exp_r"] > 0 and r1["exp_r"] > 0
            status = "🟢 POSITIVO" if both_pos else "🔴 DESIGUAL"

            print(f"{r0['label']:<40} | {r0['exp_r']:>7.3f}R | {r1['exp_r']:>7.3f}R | {exp_global:>9.3f}R | {tot_r:>10.1f}R | {status}")


if __name__ == "__main__":
    run_full_pata2_audit()
