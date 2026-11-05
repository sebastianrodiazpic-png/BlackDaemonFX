import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.simulate_msnr_improvements import compute_metrics

ict_fpath = ROOT / "storage" / "analysis" / "ict_5y_signals_complete.csv"
df_ict = pd.read_csv(ict_fpath)

# Órdenes ejecutadas
df_fill = df_ict[df_ict["lim_fill"] == "LIMITE"].copy()
if "spread" in df_fill.columns and "stop_loss" in df_fill.columns and "close" in df_fill.columns:
    sl_dist = (df_fill["close"] - df_fill["stop_loss"]).abs()
    df_fill = df_fill[(df_fill["spread"] / sl_dist.replace(0, 1e-9)) <= 0.025].copy()
if "adx_h1" in df_fill.columns:
    df_fill = df_fill[df_fill["adx_h1"] >= 20.0].copy()

r_col = "lim_rr"
jump_syms = ["Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index"]
step_syms = ["Step Index", "Step Index 200", "Step Index 500"]

print("=" * 115)
print("ICT SABRI MALLE (5Y REPLAY FIEL): COMPARATIVA COMPRAS vs VENTAS vs BIDIRECCIONAL")
print("=" * 115)
for s in jump_syms + step_syms:
    df_s = df_fill[df_fill["symbol"] == s]
    if len(df_s) == 0: continue
    m_buy = compute_metrics(df_s[df_s["direction"] == "BUY"][r_col])
    m_sell = compute_metrics(df_s[df_s["direction"] == "SELL"][r_col])
    m_all = compute_metrics(df_s[r_col])
    b_str = f"BUY:  n={m_buy['n']:<3} WR={m_buy['win_rate']:>5.1f}% R={m_buy['total_r']:>+6.1f} (r/op={m_buy['r_op']:>+5.3f})"
    s_str = f"SELL: n={m_sell['n']:<3} WR={m_sell['win_rate']:>5.1f}% R={m_sell['total_r']:>+6.1f} (r/op={m_sell['r_op']:>+5.3f})"
    tot_str = f"BIDI: n={m_all['n']:<3} WR={m_all['win_rate']:>5.1f}% R={m_all['total_r']:>+6.1f} (PF={m_all['pf']})"
    print(f"{s:<18} | {b_str} | {s_str} | {tot_str}")
print("=" * 115)
