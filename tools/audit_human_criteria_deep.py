from __future__ import annotations

import sys
if sys.path and ("tools" in sys.path[0] or sys.path[0].endswith("tools")):
    sys.path.pop(0)

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


def run_threshold_audit():
    datasets = {
        "ICT": "storage/analysis/ict_faithful_365d_v2_trades.csv",
        "Malaysian SNR v3.2": "storage/analysis/msnr_faithful_trades.csv",
        "AMR-SMC (Step & Jump)": "storage/analysis/step_jump_workers_2y_smc_trades.csv",
        "Trend Pullback": "storage/analysis/volatility_workers_2y_smc_trades.csv",
        "ORB New York": "storage/analysis/replay_orb_12m_trades.csv",
    }

    print("=" * 90)
    print("AUDITORÍA CUANTITATIVA PROFUNDA DE FILTROS Y UMBRALES DE CRITERIO HUMANO")
    print("=" * 90)

    summary_records = []

    for strat_name, path_str in datasets.items():
        p = Path(path_str)
        if not p.exists():
            continue
        df = pd.read_csv(p)
        r_all = get_realized_r(df)
        df["r_realized"] = r_all
        n_total = len(df)
        r_base = float(r_all.sum())
        wr_base = float((r_all > 0).mean() * 100.0)

        print(f"\n>>> Estrategia: {strat_name} (N = {n_total:,} trades, R Base = {r_base:+.2f} R, WR = {wr_base:.1f}%)")

        # 1. Auditoría de cada filtro aislado
        filters = {}

        # Filtro A: ADX / Fango
        if "adx" in df.columns:
            for adx_th in [15.0, 18.0, 20.0, 25.0]:
                mask_veto = df["adx"].astype(float) < adx_th
                n_veto = int(mask_veto.sum())
                r_veto = float(df.loc[mask_veto, "r_realized"].sum()) if n_veto > 0 else 0.0
                r_pass = float(df.loc[~mask_veto, "r_realized"].sum()) if n_veto < n_total else 0.0
                wr_pass = float((df.loc[~mask_veto, "r_realized"] > 0).mean() * 100.0) if n_veto < n_total else 0.0
                filters[f"ADX < {adx_th}"] = {
                    "vetados": n_veto,
                    "r_vetado": r_veto,
                    "r_aprobado": r_pass,
                    "delta_r": r_pass - r_base,
                    "wr_aprobado": wr_pass,
                }

        # Filtro B: Body Ratio / Clímax
        if "body_ratio" in df.columns:
            for br_th in [0.75, 0.80, 0.85, 0.90]:
                mask_veto = df["body_ratio"].astype(float) > br_th
                n_veto = int(mask_veto.sum())
                r_veto = float(df.loc[mask_veto, "r_realized"].sum()) if n_veto > 0 else 0.0
                r_pass = float(df.loc[~mask_veto, "r_realized"].sum()) if n_veto < n_total else 0.0
                wr_pass = float((df.loc[~mask_veto, "r_realized"] > 0).mean() * 100.0) if n_veto < n_total else 0.0
                filters[f"BodyRatio > {br_th}"] = {
                    "vetados": n_veto,
                    "r_vetado": r_veto,
                    "r_aprobado": r_pass,
                    "delta_r": r_pass - r_base,
                    "wr_aprobado": wr_pass,
                }

        # Filtro C: Fricción Spread / Slippage
        if "spread_price" in df.columns and "risk_price" in df.columns:
            spread_ratio = df["spread_price"].astype(float) / df["risk_price"].astype(float).replace(0, 1e-9)
        elif "spread_ratio" in df.columns:
            spread_ratio = df["spread_ratio"].astype(float)
        elif "spread_sl" in df.columns:
            spread_ratio = df["spread_sl"].astype(float)
        else:
            spread_ratio = None

        if spread_ratio is not None:
            for sp_th in [0.08, 0.10, 0.12, 0.15, 0.20]:
                mask_veto = spread_ratio > sp_th
                n_veto = int(mask_veto.sum())
                r_veto = float(df.loc[mask_veto, "r_realized"].sum()) if n_veto > 0 else 0.0
                r_pass = float(df.loc[~mask_veto, "r_realized"].sum()) if n_veto < n_total else 0.0
                wr_pass = float((df.loc[~mask_veto, "r_realized"] > 0).mean() * 100.0) if n_veto < n_total else 0.0
                filters[f"Spread/SL > {int(sp_th*100)}%"] = {
                    "vetados": n_veto,
                    "r_vetado": r_veto,
                    "r_aprobado": r_pass,
                    "delta_r": r_pass - r_base,
                    "wr_aprobado": wr_pass,
                }

        for f_name, stats in filters.items():
            sign = "+" if stats["delta_r"] >= 0 else ""
            status = "ALFA POSITIVO" if stats["delta_r"] > 0 else "FALSO NEGATIVO"
            print(f"  [{status:14s}] {f_name:20s}: Vetados {stats['vetados']:5d} ({stats['vetados']/n_total*100:4.1f}%) | "
                  f"R Vetado: {stats['r_vetado']:+7.2f} R | R Aprobado: {stats['r_aprobado']:+7.2f} R (Delta: {sign}{stats['delta_r']:+.2f} R) | WR: {stats['wr_aprobado']:.1f}%")
            summary_records.append({
                "strategy": strat_name,
                "filter": f_name,
                "vetados": stats["vetados"],
                "r_vetado": stats["r_vetado"],
                "delta_r": stats["delta_r"],
                "wr_aprobado": stats["wr_aprobado"],
            })

    # Guardar resumen
    df_res = pd.DataFrame(summary_records)
    df_res.to_csv("storage/analysis/human_criteria_isolated_filters_audit.csv", index=False)
    print("\nReporte detallado guardado en storage/analysis/human_criteria_isolated_filters_audit.csv")


if __name__ == "__main__":
    run_threshold_audit()
