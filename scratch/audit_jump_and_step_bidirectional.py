import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.simulate_msnr_improvements import load_all_msnr_signals, compute_metrics

# -------------------------------------------------------------
# 1. Malaysian SNR Analysis
# -------------------------------------------------------------
df_msnr = load_all_msnr_signals()
if "spread_sl" in df_msnr.columns:
    df_msnr = df_msnr[df_msnr["spread_sl"] <= 0.05].copy()

metric_col = "rr_live" if "rr_live" in df_msnr.columns else "rr"

jump_syms = ["Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"]
step_syms = ["Step Index", "Step Index 200", "Step Index 400", "Step Index 500"]

print("=" * 105)
print("1. MALAYSIAN SNR: AUDITORÍA BIDIRECCIONAL COMPLETA (JUMP & STEP)")
print("=" * 105)

print(f"{'GRUPO / ACTIVO':<20} | {'COMPRAS (BUY)':<26} | {'VENTAS (SELL)':<26} | {'TOTAL BIDIRECCIONAL':<26}")
print("-" * 105)

# JUMP en MSNR
for s in jump_syms:
    df_s = df_msnr[df_msnr["symbol"] == s]
    if len(df_s) == 0: continue
    m_buy = compute_metrics(df_s[df_s["direction"] == "BUY"][metric_col])
    m_sell = compute_metrics(df_s[df_s["direction"] == "SELL"][metric_col])
    m_all = compute_metrics(df_s[metric_col])
    b_str = f"n={m_buy['n']:<3} WR={m_buy['win_rate']:>5.1f}% R={m_buy['total_r']:>+6.1f}"
    s_str = f"n={m_sell['n']:<3} WR={m_sell['win_rate']:>5.1f}% R={m_sell['total_r']:>+6.1f}"
    tot_str = f"n={m_all['n']:<3} WR={m_all['win_rate']:>5.1f}% R={m_all['total_r']:>+6.1f}"
    print(f"{s:<20} | {b_str:<26} | {s_str:<26} | {tot_str:<26}")

# STEP en MSNR (con ADX >= 25)
print("-" * 105)
for s in step_syms:
    df_s = df_msnr[df_msnr["symbol"] == s]
    if len(df_s) == 0: continue
    df_s_adx = df_s[df_s["adx"] >= 25.0] if "adx" in df_s.columns else df_s
    m_buy = compute_metrics(df_s_adx[df_s_adx["direction"] == "BUY"][metric_col])
    m_sell = compute_metrics(df_s_adx[df_s_adx["direction"] == "SELL"][metric_col])
    m_all = compute_metrics(df_s_adx[metric_col])
    b_str = f"n={m_buy['n']:<3} WR={m_buy['win_rate']:>5.1f}% R={m_buy['total_r']:>+6.1f}"
    s_str = f"n={m_sell['n']:<3} WR={m_sell['win_rate']:>5.1f}% R={m_sell['total_r']:>+6.1f}"
    tot_str = f"n={m_all['n']:<3} WR={m_all['win_rate']:>5.1f}% R={m_all['total_r']:>+6.1f}"
    print(f"{s:<20} | {b_str:<26} | {s_str:<26} | {tot_str:<26}")

# -------------------------------------------------------------
# 2. ICT Sabri Malle 5Y Analysis
# -------------------------------------------------------------
ict_fpath = ROOT / "storage" / "analysis" / "ict_5y_signals_complete.csv"
if ict_fpath.exists():
    print("\n" + "=" * 105)
    print("2. ICT SABRI MALLE (REPLAY FIEL 5 AÑOS): AUDITORÍA BIDIRECCIONAL (JUMP & STEP)")
    print("=" * 105)
    df_ict = pd.read_csv(ict_fpath)
    r_col = "lim_rr"
    if "spread" in df_ict.columns and "stop_loss" in df_ict.columns and "close" in df_ict.columns:
        # spread / sl <= 0.025
        sl_dist = (df_ict["close"] - df_ict["stop_loss"]).abs()
        df_ict = df_ict[(df_ict["spread"] / sl_dist.replace(0, 1e-9)) <= 0.025].copy()
    if "adx_h1" in df_ict.columns:
        df_ict = df_ict[df_ict["adx_h1"] >= 20.0].copy()

    print(f"{'GRUPO / ACTIVO':<20} | {'COMPRAS (BUY)':<26} | {'VENTAS (SELL)':<26} | {'TOTAL BIDIRECCIONAL':<26}")
    print("-" * 105)
    for s in jump_syms:
        df_s = df_ict[df_ict["symbol"] == s]
        if len(df_s) == 0: continue
        m_buy = compute_metrics(df_s[df_s["direction"] == "BUY"][r_col])
        m_sell = compute_metrics(df_s[df_s["direction"] == "SELL"][r_col])
        m_all = compute_metrics(df_s[r_col])
        b_str = f"n={m_buy['n']:<3} WR={m_buy['win_rate']:>5.1f}% R={m_buy['total_r']:>+6.1f}"
        s_str = f"n={m_sell['n']:<3} WR={m_sell['win_rate']:>5.1f}% R={m_sell['total_r']:>+6.1f}"
        tot_str = f"n={m_all['n']:<3} WR={m_all['win_rate']:>5.1f}% R={m_all['total_r']:>+6.1f}"
        print(f"{s:<20} | {b_str:<26} | {s_str:<26} | {tot_str:<26}")

    print("-" * 105)
    for s in step_syms:
        df_s = df_ict[df_ict["symbol"] == s]
        if len(df_s) == 0: continue
        m_buy = compute_metrics(df_s[df_s["direction"] == "BUY"][r_col])
        m_sell = compute_metrics(df_s[df_s["direction"] == "SELL"][r_col])
        m_all = compute_metrics(df_s[r_col])
        b_str = f"n={m_buy['n']:<3} WR={m_buy['win_rate']:>5.1f}% R={m_buy['total_r']:>+6.1f}"
        s_str = f"n={m_sell['n']:<3} WR={m_sell['win_rate']:>5.1f}% R={m_sell['total_r']:>+6.1f}"
        tot_str = f"n={m_all['n']:<3} WR={m_all['win_rate']:>5.1f}% R={m_all['total_r']:>+6.1f}"
        print(f"{s:<20} | {b_str:<26} | {s_str:<26} | {tot_str:<26}")
print("=" * 105)
