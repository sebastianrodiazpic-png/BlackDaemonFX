import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.simulate_msnr_improvements import load_all_msnr_signals, compute_metrics

df = load_all_msnr_signals()
if "spread_sl" in df.columns:
    df = df[df["spread_sl"] <= 0.05].copy()

metric_col = "rr_live" if "rr_live" in df.columns else "rr"

active_step = ["Step Index 500", "Step Index 200", "Step Index 400"]
df_active = df[df["symbol"].isin(active_step)].copy()
df_adx25 = df_active[df_active["adx"] >= 25.0] if "adx" in df_active.columns else df_active

# 1. Active Step SELL-Only
df_sell_only = df_adx25[df_adx25["direction"] == "SELL"]
m_sell = compute_metrics(df_sell_only[metric_col])

# 2. Active Step Bidireccional
m_bidi = compute_metrics(df_adx25[metric_col])

# 3. Active Step con Step 500 y 200 Bidireccionales, y Step 400 SELL-only
df_opt = df_adx25[~((df_adx25["symbol"] == "Step Index 400") & (df_adx25["direction"] == "BUY"))]
m_opt = compute_metrics(df_opt[metric_col])

print("COMPILACIÓN DE LOS STEP ACTIVOS (Step 500, Step 200, Step 400):")
print(f"1. SELL-ONLY ANTERIOR:   n={m_sell['n']}  WR={m_sell['win_rate']}%  R={m_sell['total_r']:+.2f} R  PF={m_sell['pf']}")
print(f"2. BIDIRECCIONAL TOTAL:  n={m_bidi['n']}  WR={m_bidi['win_rate']}%  R={m_bidi['total_r']:+.2f} R  PF={m_bidi['pf']}")
print(f"3. BIDIRECCIONAL ÓPTIMO (Step 500/200 Bidi + Step 400 Sell): n={m_opt['n']}  WR={m_opt['win_rate']}%  R={m_opt['total_r']:+.2f} R  PF={m_opt['pf']}")
print(f"DELTA BIDIRECCIONAL TOTAL vs SELL-ONLY:  +{m_bidi['n'] - m_sell['n']} trades | {m_bidi['total_r'] - m_sell['total_r']:+.2f} R de ganancia neta!")
