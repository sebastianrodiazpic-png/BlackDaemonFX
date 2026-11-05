"""Replay cuantitativo y comparativa del Criterio Humano Especializado en Sintéticos.

Evalúa todas las operaciones de activos sintéticos en todas las estrategias disponibles:
- ICT Sabri Malle (37 sintéticos)
- Malaysian SNR (Sintéticos)
- Step & Jump AMR-SMC (10 sintéticos)
- Volatility SMC (36 sintéticos)

Calcula:
- Trades Antes vs Después
- Win Rate (%) Antes vs Después
- Loss Rate (%) Antes vs Después
- Retorno Neto R Antes vs Después
- Pérdidas Tóxicas Evitadas
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np
import pandas as pd

from strategy.human_criteria.human_criteria_engine import classify_symbol_category


def get_realized_r(df: pd.DataFrame) -> pd.Series:
    """Extrae el retorno en R de cada operación."""
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


def evaluate_synthetic_human_criteria(df: pd.DataFrame) -> pd.Series:
    """Aplica las reglas del Criterio Humano Especializado en Sintéticos.

    1. Cero puntos macro de regalo (weight_macro_news = 0.0).
    2. Veto o penalización severa por Asimetría de Spike en Boom/Crash:
       - Compra en Crash (BUY en Crash): penalización -20 pts.
       - Venta en Boom (SELL en Boom): penalización -20 pts.
    3. Veto por Fango / Choppiness tóxico (ADX < 18).
    4. Veto por Clímax Parabólico (Body ratio > 0.85).
    5. Veto por Fricción de Spread excesivo (> 15% del SL).
    6. Exigencia de Umbral Mínimo Adaptativo en Sintéticos: Score >= 75.0.
    """
    syms = df["symbol"].astype(str)
    dirs = df["direction"].astype(str).str.upper() if "direction" in df.columns else pd.Series("BUY", index=df.index)

    # 1. Asimetría de Spikes (Boom & Crash Hazard)
    is_crash_buy = syms.str.upper().str.contains("CRASH") & (dirs == "BUY")
    is_boom_sell = syms.str.upper().str.contains("BOOM") & (dirs == "SELL")
    spike_penalty = np.where(is_crash_buy | is_boom_sell, 20.0, 0.0)

    # 2. Régimen de Volatilidad / Choppiness (ADX)
    if "adx" in df.columns:
        adx_val = df["adx"].astype(float).fillna(22.0)
        is_choppy = adx_val < 18.0
        score_regime = np.where(adx_val >= 25.0, 25.0, np.where(adx_val >= 18.0, 18.0, 0.0))
    else:
        is_choppy = pd.Series(False, index=df.index)
        score_regime = 20.0

    # 3. Calidad de Acción del Precio / Clímax (Body Ratio)
    if "body_ratio" in df.columns:
        b_ratio = df["body_ratio"].astype(float).fillna(0.55)
        is_climax = b_ratio > 0.85
        score_candle = np.where(
            (b_ratio >= 0.25) & (b_ratio <= 0.75),
            25.0,
            np.where(b_ratio <= 0.85, 15.0, 0.0),
        )
    else:
        is_climax = pd.Series(False, index=df.index)
        score_candle = 20.0

    # 4. Fricción de Spread vs SL
    if "spread_price" in df.columns and "risk_price" in df.columns:
        spread_ratio = (df["spread_price"].astype(float) / df["risk_price"].astype(float).replace(0, 1e-9))
        is_spread_toxic = spread_ratio > 0.15
        score_spread = np.where(spread_ratio <= 0.03, 10.0, np.where(spread_ratio <= 0.08, 7.5, np.where(spread_ratio <= 0.15, 5.0, 0.0)))
    elif "spread_ratio" in df.columns:
        spread_ratio = df["spread_ratio"].astype(float).fillna(0.02)
        is_spread_toxic = spread_ratio > 0.15
        score_spread = np.where(spread_ratio <= 0.03, 10.0, np.where(spread_ratio <= 0.08, 7.5, np.where(spread_ratio <= 0.15, 5.0, 0.0)))
    else:
        is_spread_toxic = pd.Series(False, index=df.index)
        score_spread = 8.0

    # 5. Tendencia H1 y Racha (Base 30 pts trend + 8 pts streak)
    score_htf = 30.0
    score_streak = 8.0  # Línea base neutra saludable

    # Puntuación total sintética (máx 100)
    total_score = score_htf + score_regime + score_candle + score_streak + score_spread - spike_penalty

    # Umbral de corte institucional para sintéticos
    min_threshold = 75.0
    score_insufficient = total_score < min_threshold

    veto_mask = is_choppy | is_climax | is_spread_toxic | score_insufficient
    return pd.Series(veto_mask, index=df.index)


def evaluate_dataset(df: pd.DataFrame, strategy_name: str) -> list[dict]:
    """Evalúa activo por activo las operaciones de una estrategia en sintéticos."""
    # Filtrar estrictamente activos sintéticos
    is_synth = df["symbol"].astype(str).apply(classify_symbol_category) == "SYNTHETIC"
    synth_df = df[is_synth].copy()
    if len(synth_df) == 0:
        return []

    r_series = get_realized_r(synth_df)
    synth_df["r_realized"] = r_series
    synth_df["is_vetoed"] = evaluate_synthetic_human_criteria(synth_df)

    results = []
    for sym, group in synth_df.groupby("symbol"):
        n_antes = len(group)
        if n_antes == 0:
            continue

        r_antes = group["r_realized"]
        wins_ant = int((r_antes > 0).sum())
        loss_ant = int((r_antes < 0).sum())
        wr_ant = round((wins_ant / n_antes) * 100.0, 1)
        lr_ant = round((loss_ant / n_antes) * 100.0, 1)
        r_tot_ant = round(float(r_antes.sum()), 2)

        approved = group[~group["is_vetoed"]]
        n_desp = len(approved)

        if n_desp > 0:
            r_desp = approved["r_realized"]
            wins_desp = int((r_desp > 0).sum())
            loss_desp = int((r_desp < 0).sum())
            wr_desp = round((wins_desp / n_desp) * 100.0, 1)
            lr_desp = round((loss_desp / n_desp) * 100.0, 1)
            r_tot_desp = round(float(r_desp.sum()), 2)
        else:
            wins_desp = 0
            loss_desp = 0
            wr_desp = 0.0
            lr_desp = 0.0
            r_tot_desp = 0.0

        n_vetados = n_antes - n_desp
        perdidas_evitadas = loss_ant - loss_desp
        ganancias_filtradas = wins_ant - wins_desp
        delta_wr = round(wr_desp - wr_ant, 1)
        delta_lr = round(lr_desp - lr_ant, 1)
        delta_r = round(r_tot_desp - r_tot_ant, 2)

        results.append({
            "strategy": strategy_name,
            "symbol": sym,
            "n_antes": n_antes,
            "n_despues": n_desp,
            "n_vetados": n_vetados,
            "pct_win_antes": wr_ant,
            "pct_win_despues": wr_desp,
            "delta_pct_win": delta_wr,
            "pct_loss_antes": lr_ant,
            "pct_loss_despues": lr_desp,
            "delta_pct_loss": delta_lr,
            "r_antes": r_tot_ant,
            "r_despues": r_tot_desp,
            "delta_r": delta_r,
            "perdidas_evitadas": perdidas_evitadas,
            "ganancias_filtradas": ganancias_filtradas,
        })

    return results


def main():
    datasets = {
        "ICT Sabri Malle (SMC)": "storage/analysis/ict_faithful_365d_v2_trades.csv",
        "Malaysian SNR v3.2": "storage/analysis/msnr_faithful_trades.csv",
        "AMR-SMC (Step & Jump)": "storage/analysis/step_jump_workers_2y_smc_trades.csv",
        "Volatility SMC": "storage/analysis/volatility_workers_2y_smc_trades.csv",
    }

    all_results = []
    for name, path_str in datasets.items():
        p = Path(path_str)
        if not p.exists():
            continue
        df = pd.read_csv(p)
        res = evaluate_dataset(df, name)
        all_results.extend(res)

    out_df = pd.DataFrame(all_results)
    out_path = Path("storage/analysis/replay_synthetics_human_criteria_comparison.csv")
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Reporte detallado guardado en: {out_path}")

    # Resumen por Estrategia
    print("\n" + "=" * 95)
    print("RESUMEN GLOBAL DE SINTÉTICOS POR ESTRATEGIA (ANTES VS DESPUÉS DE CRITERIO HUMANO)")
    print("=" * 95)

    tot_n_ant = out_df["n_antes"].sum()
    tot_n_des = out_df["n_despues"].sum()
    tot_vetados = out_df["n_vetados"].sum()
    tot_losses_evitadas = out_df["perdidas_evitadas"].sum()
    tot_wins_filt = out_df["ganancias_filtradas"].sum()
    tot_r_ant = round(out_df["r_antes"].sum(), 2)
    tot_r_des = round(out_df["r_despues"].sum(), 2)
    tot_delta_r = round(tot_r_des - tot_r_ant, 2)

    for strat, grp in out_df.groupby("strategy"):
        s_n_ant = grp["n_antes"].sum()
        s_n_des = grp["n_despues"].sum()
        s_vet = grp["n_vetados"].sum()
        s_losses_ev = grp["perdidas_evitadas"].sum()
        s_r_ant = round(grp["r_antes"].sum(), 2)
        s_r_des = round(grp["r_despues"].sum(), 2)
        s_delta_r = round(s_r_des - s_r_ant, 2)

        w_ant = int(round((grp["pct_win_antes"] * grp["n_antes"] / 100.0).sum()))
        l_ant = int(round((grp["pct_loss_antes"] * grp["n_antes"] / 100.0).sum()))
        wr_ant = round((w_ant / s_n_ant) * 100.0, 1)
        lr_ant = round((l_ant / s_n_ant) * 100.0, 1)

        w_des = int(round((grp["pct_win_despues"] * grp["n_despues"] / 100.0).sum()))
        l_des = int(round((grp["pct_loss_despues"] * grp["n_despues"] / 100.0).sum()))
        wr_des = round((w_des / s_n_des) * 100.0, 1) if s_n_des > 0 else 0.0
        lr_des = round((l_des / s_n_des) * 100.0, 1) if s_n_des > 0 else 0.0

        print(f"\n>>> Estrategia: {strat}")
        print(f"    Operaciones: {s_n_ant} -> {s_n_des} (Vetadas: {s_vet} | Pérdidas Evitadas: {s_losses_ev})")
        print(f"    % Ganancias: {wr_ant}% -> {wr_des}% ({'+' if wr_des >= wr_ant else ''}{round(wr_des - wr_ant, 1)}%)")
        print(f"    % Pérdidas : {lr_ant}% -> {lr_des}% ({'-' if lr_des < lr_ant else '+'}{round(abs(lr_des - lr_ant), 1)}%)")
        print(f"    Retorno R  : {s_r_ant} R -> {s_r_des} R ({'+' if s_delta_r >= 0 else ''}{s_delta_r} R)")

    # Global
    global_w_ant = int(round((out_df["pct_win_antes"] * out_df["n_antes"] / 100.0).sum()))
    global_l_ant = int(round((out_df["pct_loss_antes"] * out_df["n_antes"] / 100.0).sum()))
    global_wr_ant = round((global_w_ant / tot_n_ant) * 100.0, 1)
    global_lr_ant = round((global_l_ant / tot_n_ant) * 100.0, 1)

    global_w_des = int(round((out_df["pct_win_despues"] * out_df["n_despues"] / 100.0).sum()))
    global_l_des = int(round((out_df["pct_loss_despues"] * out_df["n_despues"] / 100.0).sum()))
    global_wr_des = round((global_w_des / tot_n_des) * 100.0, 1)
    global_lr_des = round((global_l_des / tot_n_des) * 100.0, 1)

    print("\n" + "=" * 95)
    print("TOTAL GLOBAL CONSOLIDADO (TODOS LOS ACTIVOS SINTÉTICOS):")
    print(f"  Total Operaciones : {tot_n_ant} -> {tot_n_des} (Vetadas: {tot_vetados} | Pérdidas Evitadas: {tot_losses_evitadas})")
    print(f"  Win Rate Global   : {global_wr_ant}% -> {global_wr_des}% ({'+' if global_wr_des >= global_wr_ant else ''}{round(global_wr_des - global_wr_ant, 1)}%)")
    print(f"  Loss Rate Global  : {global_lr_ant}% -> {global_lr_des}% ({'-' if global_lr_des < global_lr_ant else '+'}{round(abs(global_lr_des - global_lr_ant), 1)}%)")
    print(f"  Retorno Neto Total: {tot_r_ant} R -> {tot_r_des} R ({'+' if tot_delta_r >= 0 else ''}{tot_delta_r} R)")
    print("=" * 95)


if __name__ == "__main__":
    main()
