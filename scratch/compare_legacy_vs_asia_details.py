import pandas as pd
from pathlib import Path

OUT = Path("storage/analysis")

files_legacy = ["msnr_variants_signals_real_win_legacy_A.csv", "msnr_variants_signals_real_win_legacy_B.csv", "msnr_variants_signals_real_win_legacy_D.csv"]
files_asia = ["msnr_variants_signals_real_win_asia_A.csv", "msnr_variants_signals_real_win_asia_B.csv", "msnr_variants_signals_real_win_asia_D.csv"]

def load_group(file_list):
    dfs = []
    for f in file_list:
        p = OUT / f
        if p.exists():
            dfs.append(pd.read_csv(p))
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

df_legacy = load_group(files_legacy)
df_asia = load_group(files_asia)

print(f"Legacy dataset: {len(df_legacy)} signals")
print(f"Asia dataset: {len(df_asia)} signals")

# Compare per symbol
syms = sorted(list(set(df_legacy['symbol']).union(set(df_asia['symbol']))))

rows = []
for s in syms:
    sub_leg = df_legacy[df_legacy['symbol'] == s]
    sub_asi = df_asia[df_asia['symbol'] == s]
    
    n_leg = len(sub_leg)
    w_leg = (sub_leg['rr_live'] > 0).sum() if n_leg > 0 else 0
    wr_leg = (w_leg / n_leg * 100) if n_leg > 0 else 0
    r_leg = sub_leg['rr_live'].sum() if n_leg > 0 else 0
    
    n_asi = len(sub_asi)
    w_asi = (sub_asi['rr_live'] > 0).sum() if n_asi > 0 else 0
    wr_asi = (w_asi / n_asi * 100) if n_asi > 0 else 0
    r_asi = sub_asi['rr_live'].sum() if n_asi > 0 else 0
    
    rows.append({
        'symbol': s,
        'n_legacy': n_leg,
        'wr_legacy': round(wr_leg, 1),
        'r_legacy': round(r_leg, 2),
        'n_asia': n_asi,
        'wr_asia': round(wr_asi, 1),
        'r_asia': round(r_asi, 2),
        'delta_n': n_asi - n_leg,
        'delta_wr': round(wr_asi - wr_leg, 1),
        'delta_r': round(r_asi - r_leg, 2),
    })

res_df = pd.DataFrame(rows)
print("\n--- COMPARATIVA REAL: LEGACY (LONDRES + NY) VS ASIA_TO_NY ---")
print(res_df.to_string())

# Summary totals
tot_leg_n = res_df['n_legacy'].sum()
tot_leg_r = res_df['r_legacy'].sum()
tot_asi_n = res_df['n_asia'].sum()
tot_asi_r = res_df['r_asia'].sum()
print(f"\nTOTAL LEGACY: {tot_leg_n} trades, +{tot_leg_r:.2f}R")
print(f"TOTAL ASIA: {tot_asi_n} trades, +{tot_asi_r:.2f}R")
