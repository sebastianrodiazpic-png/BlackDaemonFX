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

# Filtrar activos de la familia Step
step_symbols = ["Step Index", "Step Index 200", "Step Index 400", "Step Index 500"]
df_step = df[df["symbol"].isin(step_symbols)].copy()

print("=" * 95)
print("AUDITORÍA DE RENTABILIDAD: FAMILIA STEP EN MALAYSIAN SNR (SELL-ONLY vs BIDIRECCIONAL)")
print("=" * 95)

results = []

for sym in step_symbols:
    df_sym = df_step[df_step["symbol"] == sym].copy()
    
    # 1. Compras solas
    buys = df_sym[df_sym["direction"] == "BUY"]
    m_buy = compute_metrics(buys[metric_col])
    
    # 2. Compras con filtro ADX >= 25
    buys_adx25 = buys[buys["adx"] >= 25.0] if "adx" in buys.columns else buys
    m_buy_adx25 = compute_metrics(buys_adx25[metric_col])
    
    # 3. Ventas solas
    sells = df_sym[df_sym["direction"] == "SELL"]
    m_sell = compute_metrics(sells[metric_col])
    
    # 4. Ventas con filtro ADX >= 25
    sells_adx25 = sells[sells["adx"] >= 25.0] if "adx" in sells.columns else sells
    m_sell_adx25 = compute_metrics(sells_adx25[metric_col])
    
    # 5. Modo Anterior (SELL-Only con ADX >= 25)
    m_prev = m_sell_adx25
    
    # 6. Modo Nuevo Bidireccional (BUY + SELL con ADX >= 25)
    bidi_adx25 = df_sym[df_sym["adx"] >= 25.0] if "adx" in df_sym.columns else df_sym
    m_bidi = compute_metrics(bidi_adx25[metric_col])
    
    results.append({
        "symbol": sym,
        "n_buy": m_buy_adx25["n"], "wr_buy": m_buy_adx25["win_rate"], "r_buy": m_buy_adx25["total_r"], "rop_buy": m_buy_adx25["r_op"],
        "n_sell": m_sell_adx25["n"], "wr_sell": m_sell_adx25["win_rate"], "r_sell": m_sell_adx25["total_r"], "rop_sell": m_sell_adx25["r_op"],
        "n_prev": m_prev["n"], "wr_prev": m_prev["win_rate"], "r_prev": m_prev["total_r"],
        "n_bidi": m_bidi["n"], "wr_bidi": m_bidi["win_rate"], "r_bidi": m_bidi["total_r"],
        "delta_r": m_bidi["total_r"] - m_prev["total_r"],
        "delta_trades": m_bidi["n"] - m_prev["n"]
    })

print(f"{'ACTIVO':<18} | {'COMPRAS (BUY ADX>=25)':<22} | {'VENTAS (SELL ADX>=25)':<22} | {'SELL-ONLY (PREV)':<16} | {'BIDIRECCIONAL (NUEVO)':<18} | {'DELTA R'}")
print("-" * 125)
for r in results:
    buy_str = f"n={r['n_buy']:<3} WR={r['wr_buy']:>5.1f}% R={r['r_buy']:>+5.1f}"
    sell_str = f"n={r['n_sell']:<3} WR={r['wr_sell']:>5.1f}% R={r['r_sell']:>+5.1f}"
    prev_str = f"n={r['n_prev']:<3} R={r['r_prev']:>+5.1f}"
    bidi_str = f"n={r['n_bidi']:<3} WR={r['wr_bidi']:>5.1f}% R={r['r_bidi']:>+5.1f}"
    delta_str = f"{r['delta_r']:>+6.2f} R (+{r['delta_trades']} ops)"
    print(f"{r['symbol']:<18} | {buy_str:<22} | {sell_str:<22} | {prev_str:<16} | {bidi_str:<18} | {delta_str}")

# Total Familia Step
step_all_prev = df_step[(df_step["direction"] == "SELL") & (df_step["adx"] >= 25.0)]
m_tot_prev = compute_metrics(step_all_prev[metric_col])

step_all_bidi = df_step[df_step["adx"] >= 25.0]
m_tot_bidi = compute_metrics(step_all_bidi[metric_col])

print("-" * 125)
print(f"{'TOTAL FAMILIA STEP':<18} | SELL-ONLY: n={m_tot_prev['n']} WR={m_tot_prev['win_rate']}% R={m_tot_prev['total_r']:+.2f}  --->  BIDIRECCIONAL: n={m_tot_bidi['n']} WR={m_tot_bidi['win_rate']}% R={m_tot_bidi['total_r']:+.2f} (PF: {m_tot_bidi['pf']})")
print(f"IMPACTO NETO EN STEP:  +{m_tot_bidi['n'] - m_tot_prev['n']} operaciones | Delta R: {m_tot_bidi['total_r'] - m_tot_prev['total_r']:+.2f} R")
print("=" * 125)
