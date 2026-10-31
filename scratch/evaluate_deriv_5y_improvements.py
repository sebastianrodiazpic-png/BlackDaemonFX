"""Evaluación multianual de 5 años en Deriv (Sintéticos): Comparación V1 vs V2 vs V3 Mejorada.
Evalúa los 37 activos sintéticos de Deriv, analizando si mantenemos o aumentamos la cantidad de trades,
el Win Rate (efectividad) y el retorno acumulado (R total).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis"

def main():
    csv_path = OUT / "ict_5y_signals_h1_enriched.csv"
    if not csv_path.exists():
        print(f"Error: No existe {csv_path}")
        return

    df = pd.read_csv(csv_path, low_memory=False)
    # Filtrar solo sintéticos
    syn = df[df["synthetic"] == True].copy()
    syn["t"] = pd.to_datetime(syn["time"], utc=True)

    # Cargar factores de spread reales
    try:
        from tools.analyze_ict_5y_audit import load_real_tick_spreads
        synth_factors, _ = load_real_tick_spreads()
    except Exception:
        synth_factors = {}

    real_sp = []
    for s, sp in zip(syn["symbol"], syn["spread"]):
        real_sp.append(float(sp) * synth_factors.get(str(s), 1.0))
    syn["real_spread"] = real_sp
    syn["extra_spread"] = np.maximum(0.0, syn["real_spread"] - syn["spread"])

    syn["lim_risk_price"] = (syn["limit"] - syn["stop_loss"]).abs()
    syn["spread_sl_lim"] = syn["real_spread"] / syn["lim_risk_price"].replace(0, np.nan)
    syn["lim_rr_real"] = syn["lim_rr"] - (syn["extra_spread"] / syn["lim_risk_price"].replace(0, np.nan))

    sign = np.where(syn["direction"] == "BUY", 1.0, -1.0)
    syn["signed_pullback_r"] = sign * (syn["close"] - syn["limit"]) / syn["lim_risk_price"].replace(0, np.nan)

    # V1: condición original de entrada limitada con tope spread/sl <= 2%
    v1_mask = syn["lim_rr_real"].notna() & (syn["spread_sl_lim"] <= 0.02)

    # V2 (Activa): 6 mejoras
    m1_ok = (syn["sl_atr_h1"].isna()) | (syn["sl_atr_h1"] >= 1.0)
    m2_ok = syn["signed_pullback_r"].isna() | (syn["signed_pullback_r"] <= 0.35)
    m4_dir_ok = ~(
        (syn["symbol"].isin(["Jump 50 Index", "Jump 75 Index"]) & (syn["direction"] != "BUY"))
        | ((syn["symbol"] == "Step Index") & (syn["direction"] != "SELL"))
    )
    m5_adx_ok = syn["adx_h1"].isna() | (syn["adx_h1"] >= 20.0)
    v2_mask = v1_mask & m1_ok & m2_ok & m4_dir_ok & m5_adx_ok

    # V3 (Mejoras Propuestas: Entrada escalonada mitigación 25% FVG + Asimetría direccional afinada)
    # Relajamos pullback a <= 0.45 R para capturar rebotes tempranos de alta confluencia
    m2_v3 = syn["signed_pullback_r"].isna() | (syn["signed_pullback_r"] <= 0.45)
    
    # Asimetría direccional afinada en Step 500 (solo SELL) y Jump 50/75 (solo BUY)
    dir_v3 = ~(
        (syn["symbol"].isin(["Jump 50 Index", "Jump 75 Index"]) & (syn["direction"] != "BUY"))
        | (syn["symbol"].isin(["Step Index", "Step Index 500"]) & (syn["direction"] != "SELL"))
    )
    v3_mask = v1_mask & m1_ok & m2_v3 & dir_v3 & m5_adx_ok

    bad_assets = ["Crash 1000 Index", "Volatility 90 (1s) Index", "High Frequency Vol 50 Index"]

    results = []
    for sym, grp in syn.groupby("symbol"):
        # V1
        g_v1 = grp[v1_mask.loc[grp.index]]
        n_v1 = len(g_v1)
        wr_v1 = (g_v1["lim_rr_real"] > 0).mean() * 100 if n_v1 > 0 else 0.0
        tot_r_v1 = g_v1["lim_rr_real"].sum() if n_v1 > 0 else 0.0

        # V2
        g_v2 = grp[v2_mask.loc[grp.index]]
        n_v2 = len(g_v2)
        wr_v2 = (g_v2["lim_rr_real"] > 0).mean() * 100 if n_v2 > 0 else 0.0
        tot_r_v2 = g_v2["lim_rr_real"].sum() if n_v2 > 0 else 0.0

        # V3
        g_v3 = grp[v3_mask.loc[grp.index]]
        n_v3 = len(g_v3)
        wr_v3 = (g_v3["lim_rr_real"] > 0).mean() * 100 if n_v3 > 0 else 0.0
        tot_r_v3 = g_v3["lim_rr_real"].sum() if n_v3 > 0 else 0.0

        family = "VOLATILITY"
        s_up = sym.upper()
        if "BOOM" in s_up: family = "BOOM"
        elif "CRASH" in s_up: family = "CRASH"
        elif "STEP" in s_up: family = "STEP"
        elif "JUMP" in s_up: family = "JUMP"

        delta_n = n_v3 - n_v2
        delta_r = tot_r_v3 - tot_r_v2

        status = "ACTIVO RENTABLE" if wr_v3 >= 48.0 and tot_r_v3 > 0 else ("PODA DEFINITIVA" if sym in bad_assets else "PODA PREVENTIVA")

        results.append({
            "symbol": sym,
            "family": family,
            "v1_trades": n_v1,
            "v1_wr": round(wr_v1, 1),
            "v1_r": round(tot_r_v1, 1),
            "v2_trades": n_v2,
            "v2_wr": round(wr_v2, 1),
            "v2_r": round(tot_r_v2, 1),
            "v3_trades": n_v3,
            "v3_wr": round(wr_v3, 1),
            "v3_r": round(tot_r_v3, 1),
            "delta_trades": delta_n,
            "delta_r": round(delta_r, 1),
            "status": status,
        })

    res_df = pd.DataFrame(results).sort_values("v3_r", ascending=False)
    res_df.to_csv(OUT / "deriv_synthetics_5y_test_evaluation.csv", index=False)
    print("Evaluación completada. Guardado en storage/analysis/deriv_synthetics_5y_test_evaluation.csv")
    print(f"Total activos evaluados: {len(res_df)}")
    print(f"Total trades V2: {res_df['v2_trades'].sum()} | WR V2 Prom: {res_df['v2_wr'].mean():.1f}% | R Total V2: {res_df['v2_r'].sum():.1f} R")
    print(f"Total trades V3: {res_df['v3_trades'].sum()} | WR V3 Prom: {res_df['v3_wr'].mean():.1f}% | R Total V3: {res_df['v3_r'].sum():.1f} R")
    print(f"Delta Trades: +{res_df['delta_trades'].sum()} trades | Delta R: +{res_df['delta_r'].sum():.1f} R")

if __name__ == "__main__":
    main()
