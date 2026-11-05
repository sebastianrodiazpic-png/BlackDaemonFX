"""Replay integral de todas las estrategias con y sin Criterio Humano.

Genera la comparación exacta de:
- % Ganancias Antes vs % Ganancias Después
- % Pérdidas Antes vs % Pérdidas Después
- Retorno Neto R Antes vs Después
- Desglose detallado por Activo y por Estrategia.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd


def get_realized_r(df: pd.DataFrame) -> pd.Series:
    """Extrae el retorno en R según la estructura del dataset."""
    if "rr" in df.columns:
        return df["rr"].astype(float)
    elif "asym_realized_rr" in df.columns:
        return df["asym_realized_rr"].astype(float)
    elif "be_realized_rr" in df.columns:
        return df["be_realized_rr"].astype(float)
    elif "trade1_realized_r" in df.columns:
        pata1 = df["trade1_realized_r"].astype(float)
        pata2 = df.get("trade2_3r_realized_r", pata1).astype(float)
        return (pata1 * 0.5) + (pata2 * 0.5)
    return pd.Series(0.0, index=df.index)


def get_human_criteria_veto_mask(df: pd.DataFrame, strategy_name: str) -> pd.Series:
    """Aplica las reglas exactas de admisibilidad del HumanCriteriaEngine."""
    # 1. Filtro de Fango / Choppiness (ADX < 18 en sintéticos)
    fango = (df["adx"].astype(float) < 18.0) if "adx" in df.columns else pd.Series(False, index=df.index)

    # 2. Filtro Anti-Agotamiento Clímax (body_ratio > 0.85)
    climax = (df["body_ratio"].astype(float) > 0.85) if "body_ratio" in df.columns else pd.Series(False, index=df.index)

    # 3. Fricción excesiva de spread vs riesgo (> 15% del SL)
    if "spread_price" in df.columns and "risk_price" in df.columns:
        spread = (df["spread_price"].astype(float) / df["risk_price"].astype(float).replace(0, 1e-9)) > 0.15
    elif "spread_ratio" in df.columns:
        spread = df["spread_ratio"].astype(float) > 0.15
    else:
        spread = pd.Series(False, index=df.index)

    # 4. ORB New York: Retest de baja calidad
    orb_low = pd.Series(False, index=df.index)
    if "retest_quality" in df.columns:
        orb_low = df["retest_quality"].astype(str).str.upper().str.contains("LOW")

    return fango | climax | spread | orb_low


def evaluate_strategy_assets(df: pd.DataFrame, strategy_name: str) -> list[dict]:
    """Evalúa activo por activo dentro de la estrategia."""
    r_series = get_realized_r(df)
    df_eval = df.copy()
    df_eval["r_realized"] = r_series
    df_eval["is_vetoed"] = get_human_criteria_veto_mask(df, strategy_name)

    results = []

    for sym, group in df_eval.groupby("symbol"):
        n_total_antes = len(group)
        if n_total_antes == 0:
            continue

        r_antes = group["r_realized"]
        wins_antes = int((r_antes > 0).sum())
        losses_antes = int((r_antes < 0).sum())
        be_antes = int((r_antes == 0).sum())

        pct_win_antes = round((wins_antes / n_total_antes) * 100.0, 1)
        pct_loss_antes = round((losses_antes / n_total_antes) * 100.0, 1)
        r_neto_antes = round(float(r_antes.sum()), 2)

        # Después de aplicar el filtro de criterio humano
        approved_group = group[~group["is_vetoed"]]
        n_total_despues = len(approved_group)

        if n_total_despues > 0:
            r_despues = approved_group["r_realized"]
            wins_despues = int((r_despues > 0).sum())
            losses_despues = int((r_despues < 0).sum())

            pct_win_despues = round((wins_despues / n_total_despues) * 100.0, 1)
            pct_loss_despues = round((losses_despues / n_total_despues) * 100.0, 1)
            r_neto_despues = round(float(r_despues.sum()), 2)
        else:
            wins_despues = 0
            losses_despues = 0
            pct_win_despues = 0.0
            pct_loss_despues = 0.0
            r_neto_despues = 0.0

        n_vetados = n_total_antes - n_total_despues
        perdidas_evitadas = losses_antes - losses_despues
        ganancias_filtradas = wins_antes - wins_despues

        delta_pct_win = round(pct_win_despues - pct_win_antes, 1)
        delta_pct_loss = round(pct_loss_despues - pct_loss_antes, 1)
        delta_r = round(r_neto_despues - r_neto_antes, 2)

        results.append({
            "strategy": strategy_name,
            "symbol": sym,
            "n_antes": n_total_antes,
            "n_despues": n_total_despues,
            "n_vetados": n_vetados,
            "pct_win_antes": pct_win_antes,
            "pct_win_despues": pct_win_despues,
            "delta_pct_win": delta_pct_win,
            "pct_loss_antes": pct_loss_antes,
            "pct_loss_despues": pct_loss_despues,
            "delta_pct_loss": delta_pct_loss,
            "r_antes": r_neto_antes,
            "r_despues": r_neto_despues,
            "delta_r": delta_r,
            "perdidas_evitadas": perdidas_evitadas,
            "ganancias_filtradas": ganancias_filtradas,
        })

    return results


def main():
    datasets = {
        "ICT Sabri Malle": "storage/analysis/ict_faithful_365d_v2_trades.csv",
        "Malaysian SNR v3.2": "storage/analysis/msnr_faithful_trades.csv",
        "Trend Pullback": "storage/analysis/volatility_workers_2y_smc_trades.csv",
        "AMR-SMC (Step & Jump)": "storage/analysis/step_jump_workers_2y_smc_trades.csv",
        "ORB New York": "storage/analysis/replay_orb_12m_trades.csv",
    }

    all_results = []

    for strat, path_str in datasets.items():
        p = Path(path_str)
        if not p.exists():
            continue
        df = pd.read_csv(p)
        res = evaluate_strategy_assets(df, strat)
        all_results.extend(res)

    df_out = pd.DataFrame(all_results)
    out_csv = Path("storage/analysis/replay_human_criteria_comparison_by_asset.csv")
    df_out.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Reporte completo por activo guardado en: {out_csv}")

    # Mostrar resumen por estrategia
    print("\n" + "=" * 90)
    print("RESUMEN CONSOLIDADO POR ESTRATEGIA (ANTES VS DESPUÉS DE CRITERIO HUMANO)")
    print("=" * 90)

    for strat, grp in df_out.groupby("strategy"):
        tot_antes = grp["n_antes"].sum()
        tot_desp = grp["n_despues"].sum()
        tot_vetados = grp["n_vetados"].sum()
        tot_losses_evitadas = grp["perdidas_evitadas"].sum()
        tot_wins_filt = grp["ganancias_filtradas"].sum()

        r_antes_tot = round(grp["r_antes"].sum(), 2)
        r_desp_tot = round(grp["r_despues"].sum(), 2)
        delta_r_tot = round(r_desp_tot - r_antes_tot, 2)

        # Promedios ponderados de Win Rate y Loss Rate
        tot_wins_ant = int(round((grp["pct_win_antes"] * grp["n_antes"] / 100.0).sum()))
        tot_loss_ant = int(round((grp["pct_loss_antes"] * grp["n_antes"] / 100.0).sum()))
        wr_ant = round((tot_wins_ant / tot_antes) * 100.0, 1)
        lr_ant = round((tot_loss_ant / tot_antes) * 100.0, 1)

        tot_wins_des = int(round((grp["pct_win_despues"] * grp["n_despues"] / 100.0).sum()))
        tot_loss_des = int(round((grp["pct_loss_despues"] * grp["n_despues"] / 100.0).sum()))
        wr_des = round((tot_wins_des / tot_desp) * 100.0, 1) if tot_desp > 0 else 0.0
        lr_des = round((tot_loss_des / tot_desp) * 100.0, 1) if tot_desp > 0 else 0.0

        print(f"\n>>> Estrategia: {strat}")
        print(f"    Operaciones: {tot_antes} -> {tot_desp} (Vetadas: {tot_vetados} | Pérdidas Evitadas: {tot_losses_evitadas})")
        print(f"    % Ganancias: {wr_ant}% -> {wr_des}% ({'+' if wr_des>=wr_ant else ''}{round(wr_des-wr_ant, 1)}%)")
        print(f"    % Pérdidas : {lr_ant}% -> {lr_des}% ({'-' if lr_des<lr_ant else '+'}{round(abs(lr_des-lr_ant), 1)}%)")
        print(f"    Retorno R  : {r_antes_tot} R -> {r_desp_tot} R ({'+' if delta_r_tot>=0 else ''}{delta_r_tot} R)")


if __name__ == "__main__":
    main()
