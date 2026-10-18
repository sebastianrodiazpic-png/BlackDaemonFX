import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from scratch.test_subfamily_and_filter_improvements import evaluate_variant, eval_friction, compute_detailed_kpis

df = pd.read_csv('scratch/msnr_complete_23_faithful_trades_clean.csv')
df['time'] = pd.to_datetime(df['time'], utc=True)
df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
df = df.sort_values('time').reset_index(drop=True)

def f_v4(d):
    return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

res_v4 = evaluate_variant(df, f_v4, cap=1)
tdf = res_v4['trades']

print(f"Total trades: {len(tdf)}")
print(f"{'Instrumento':26s} | {'N':2s} | {'Base Net R':11s} | {'Base PF':7s} | {'Mod Net R':10s} | {'Mod PF':7s} | {'Sev Net R':10s} | {'Sev PF':7s}")
print("-" * 95)
for sym in sorted(tdf['symbol'].unique()):
    sub = tdf[tdf['symbol'] == sym]
    k_base = compute_detailed_kpis(sub['rr'], sym)
    k_mod = eval_friction(sub['rr'], 0.05, 0.15)
    k_sev = eval_friction(sub['rr'], 0.10, 0.25)
    print(f"{sym:26s} | {len(sub):2d} | {k_base['net_r']:+10.2f}R | {k_base['pf']:7.2f} | {k_mod['net_r']:+9.2f}R | {k_mod['pf']:7.2f} | {k_sev['net_r']:+9.2f}R | {k_sev['pf']:7.2f}")

k_tot_base = compute_detailed_kpis(tdf['rr'], "Total")
k_tot_mod = eval_friction(tdf['rr'], 0.05, 0.15)
k_tot_sev = eval_friction(tdf['rr'], 0.10, 0.25)
print("-" * 95)
print(f"{'TOTAL CARTERA':26s} | {len(tdf):2d} | {k_tot_base['net_r']:+10.2f}R | {k_tot_base['pf']:7.2f} | {k_tot_mod['net_r']:+9.2f}R | {k_tot_mod['pf']:7.2f} | {k_tot_sev['net_r']:+9.2f}R | {k_tot_sev['pf']:7.2f}")
