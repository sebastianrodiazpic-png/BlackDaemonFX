from __future__ import annotations

import sys
if sys.path and ("tools" in sys.path[0] or sys.path[0].endswith("tools")):
    sys.path.pop(0)

from pathlib import Path
import numpy as np
import pandas as pd


def audit_combined_system():
    # 1. Dataset ICT con variantes de salida (18,331 trades)
    df_y0 = pd.read_csv("storage/analysis/ict_exit_variants_y0.csv")
    df_y1 = pd.read_csv("storage/analysis/ict_exit_variants_y1.csv")
    df_ict = pd.concat([df_y0, df_y1], ignore_index=True)

    # 2. Dataset ICT fiel con características de vela
    df_ict_feat = pd.read_csv("storage/analysis/ict_faithful_365d_v2_trades.csv")
    
    print("=" * 90)
    print("SIMULACIÓN DE IMPACTO SISTÉMICO: CRITERIO HUMANO OPTIMIZADO + PATA 2 PROGRESIVA")
    print("=" * 90)

    # Cruzar datos de ICT: Pata 2 Progresiva (tp1_1.0_r3_out) con Filtro Clímax
    # En df_ict, tenemos 'tp1_1.0_r3' (pata 2 extendida a 3R con lock 1R)
    # y en df_ict_feat tenemos body_ratio
    
    print(f"Total trades ICT analizados: {len(df_ict):,}")
    
    # Calcular R progresivo de Pata 2 en df_ict:
    # Si outcome de tp1_1.0_r3 es TP3: +2.0R combinado (0.5 * 1.0 + 0.5 * 3.0)
    # Si es TP1+BE / TP1: +1.0R combinado (0.5 * 1.0 + 0.5 * 1.0 gracias al lock a 1.0R al tocar 2R) o +0.5R si no tocó 2R
    # Base actual:
    r_pata2_base = df_ict["tp1_1.0_r2"].astype(float)
    r_pata2_prog = df_ict["tp1_1.0_r3"].astype(float)

    # Filtros de Criterio Humano a evaluar:
    # 1. Sin filtro
    # 2. Filtro Actual (ADX < 18 en sintéticos genéricos + Clímax 0.85)
    # 3. Filtro Calibrado (Clímax optimizado 0.80 + Exención inteligente de ADX para activos de salto discreto como Step/Jump)

    # Revisar correlación en df_ict_feat
    # En df_ict_feat, rr_r3 es el retorno a 3R
    n_feat = len(df_ict_feat)
    r_feat_base = df_ict_feat["rr"].astype(float)
    r_feat_r3 = df_ict_feat["rr_r3"].astype(float)

    print(f"\n--- Estrategia ICT (N = {n_feat:,} trades) ---")
    print(f"  1. Base sin filtros (TP2 2R Fijo): {r_feat_base.sum():+.2f} R")
    print(f"  2. Con Pata 2 Progresiva (3R):      {r_feat_r3.sum():+.2f} R (Delta: {r_feat_r3.sum() - r_feat_base.sum():+.2f} R)")

    for br_th in [0.85, 0.80, 0.75]:
        mask_pass = df_ict_feat["body_ratio"].astype(float) <= br_th
        r_f_base = df_ict_feat.loc[mask_pass, "rr"].astype(float).sum()
        r_f_r3 = df_ict_feat.loc[mask_pass, "rr_r3"].astype(float).sum()
        trades_pass = int(mask_pass.sum())
        print(f"  3. Pata 2 Progresiva + Filtro Clímax (Body <= {br_th}):")
        print(f"     Trades Aprobados: {trades_pass:,} ({trades_pass/n_feat*100:.1f}%) | R Neto: {r_f_r3:+.2f} R (Mejora total: {r_f_r3 - r_feat_base.sum():+.2f} R)")

    # 4. Malaysian SNR
    df_msnr = pd.read_csv("storage/analysis/msnr_faithful_trades.csv")
    r_msnr_base = df_msnr["rr"].astype(float)
    n_msnr = len(df_msnr)
    print(f"\n--- Estrategia Malaysian SNR v3.2 (N = {n_msnr:,} trades) ---")
    print(f"  Base sin filtros: {r_msnr_base.sum():+.2f} R")
    
    # Filtro actual MSNR: ADX < 18 o Climax > 0.85
    veto_msnr_act = (df_msnr["adx"] < 18.0) | (df_msnr["body_ratio"] > 0.85)
    r_msnr_act = df_msnr.loc[~veto_msnr_act, "rr"].sum()
    print(f"  Con Criterio Humano Actual (ADX<18 | Climax>0.85): {r_msnr_act:+.2f} R (Delta: {r_msnr_act - r_msnr_base.sum():+.2f} R)")

    # Filtro optimizado MSNR: Climax > 0.75 + ADX < 18
    veto_msnr_opt = (df_msnr["adx"] < 18.0) | (df_msnr["body_ratio"] > 0.75)
    r_msnr_opt = df_msnr.loc[~veto_msnr_opt, "rr"].sum()
    print(f"  Con Criterio Humano Optimizado (ADX<18 | Climax>0.75): {r_msnr_opt:+.2f} R (Delta: {r_msnr_opt - r_msnr_base.sum():+.2f} R)")

    # 5. AMR-SMC Step & Jump
    df_sj = pd.read_csv("storage/analysis/step_jump_workers_2y_smc_trades.csv")
    r_sj_pata1 = df_sj["trade1_realized_r"].astype(float)
    r_sj_pata2 = df_sj["trade2_3r_realized_r"].astype(float)
    r_sj_base = (r_sj_pata1 * 0.5) + (r_sj_pata2 * 0.5)
    n_sj = len(df_sj)
    print(f"\n--- Estrategia AMR-SMC Step & Jump (N = {n_sj:,} trades) ---")
    print(f"  Base sin filtros: {r_sj_base.sum():+.2f} R")
    
    # Filtro previo con falso negativo de ADX:
    veto_sj_prev = (df_sj["adx"] < 18.0) | (df_sj["body_ratio"] > 0.85)
    r_sj_prev = r_sj_base[~veto_sj_prev].sum()
    print(f"  Con Filtro Antiguo (ADX<18 causaba Falso Negativo): {r_sj_prev:+.2f} R (Delta: {r_sj_prev - r_sj_base.sum():+.2f} R)")

    # Filtro corregido: Eximir ADX en Step/Jump y afilar Clímax (Body > 0.80)
    veto_sj_opt = (df_sj["body_ratio"] > 0.80)
    r_sj_opt = r_sj_base[~veto_sj_opt].sum()
    print(f"  Con Filtro Corregido (Exención ADX en Step + Climax>0.80): {r_sj_opt:+.2f} R (Delta: {r_sj_opt - r_sj_base.sum():+.2f} R)")


if __name__ == "__main__":
    audit_combined_system()
