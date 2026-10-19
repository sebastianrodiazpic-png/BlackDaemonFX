"""
scratch/audit_ict_and_all_strategies_ro.py
==========================================
Consulta de solo lectura (?mode=ro) sobre las estrategias disponibles en el repositorio
(MSNR, ICT, SMC, ORB) y su desempeño por variante en las bases shadow y datasets de investigación.
"""
import sqlite3
from pathlib import Path
import pandas as pd
from reproduce_msnr_v4_full_audit import (
    PROJECT_ROOT, SYNTHS, FOREX, METALS_STRICT, get_family_3way,
    run_walkforward_variant, compute_bundle_with_costs
)
from strategy.malaysian_snr.config import MalaysianSNRConfig

for name, rel in [
    ("PROSPECTIVA SELLADA", "storage/runtime/shadow_research.sqlite3"),
    ("STAGING", "storage/runtime/shadow_research_staging.sqlite3"),
]:
    p = PROJECT_ROOT / rel
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    df = pd.read_sql_query("SELECT * FROM shadow_signals", con)
    con.close()
    print(f"=== {name} ({rel}) ===")
    for (strat, var), g in df.groupby(["strategy", "variant"]):
        acc = g[g["final_action"] == "ACCEPTED_EXECUTION"]
        disc = g[g["final_action"] != "ACCEPTED_EXECUTION"]
        acc_closed = acc[acc["market_outcome"].isin(["TP1_WIN", "FULL_TP", "SL_LOSS", "CLOSED_OTHER"]) & (acc["market_rr"] != 0.0)]
        wins = acc_closed[acc_closed["market_rr"] > 0]
        wr = len(wins) / len(acc_closed) * 100.0 if len(acc_closed) > 0 else 0.0
        disc_closed = disc[disc["market_outcome"].isin(["TP1_WIN", "FULL_TP", "SL_LOSS", "CLOSED_OTHER"]) & (disc["market_rr"] != 0.0)]
        print(f"  {strat:5s} | {var:20s} | Total={len(g):3d} | Acc={len(acc):2d} | Closed={len(acc_closed):2d} (W={len(wins):2d}, WR={wr:5.1f}%, NetR={acc_closed['market_rr'].sum():+6.2f}R) | DiscClosed={len(disc_closed):2d} (Contrafact={disc_closed['market_rr'].sum():+6.2f}R)")

# También verificar en MSNR qué combinaciones/subconjuntos de C2 alcanzan 60-70% WR sin reducir Payoff
cfg = MalaysianSNRConfig()
canonical_23 = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
df_clean = pd.read_csv(PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv")
df_clean['time'] = pd.to_datetime(df_clean['time'], utc=True)
df_clean['exit_time'] = pd.to_datetime(df_clean['exit_time'], utc=True)
df_clean['subfamily'] = df_clean['symbol'].apply(get_family_3way)
df_clean = df_clean[df_clean['symbol'].isin(canonical_23)].sort_values('time').reset_index(drop=True)

def f_c2(d):
    is_fx_or_pure_metal = d['symbol'].isin(FOREX | METALS_STRICT)
    c_strict = is_fx_or_pure_metal & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
    c_other = (~is_fx_or_pure_metal) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
    return d[c_strict | c_other]

def f_c2_plus_b(d):
    res = f_c2(d)
    return res[res['symbol'] != 'Crash 1000 Index']

res_c2 = run_walkforward_variant(df_clean, f_c2, n_folds=4, cap=1)
res_c2b = run_walkforward_variant(df_clean, f_c2_plus_b, n_folds=4, cap=1)

print("\n=== MSNR C2 vs C2+B (Investigación en Staging) ===")
for lbl, r in [("C2 (ATR<=1.2 FX+XAU/XAG)", res_c2), ("C2 + B (C2 sin Crash 1000)", res_c2b)]:
    b = r["total"]["base"]
    m = r["total"]["mod"]
    s25 = r["total"]["sev25"]
    print(f"  {lbl:28s}: N={b['n']} ({b['w']}W/{b['l']}L) | WR={b['wr']:.1f}% {b['ci_str']} | Payoff={b['payoff']:.2f} | Exp={b['exp_r']:+.4f}R | NetBase={b['net_r']:+.2f}R (PF {b['pf']:.2f}, DD {b['max_dd']:.2f}R) | NetMod={m['net_r']:+.2f}R (PF {m['pf']:.2f}) | NetSev25={s25['net_r']:+.2f}R (PF {s25['pf']:.2f})")
