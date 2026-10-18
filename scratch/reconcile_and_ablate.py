import pandas as pd
import numpy as np

# 1. ICT Ablation: Pre-market lock (hours 7, 8 NY)
df_ict = pd.read_csv('storage/analysis/ict_faithful_trades.csv')
total_ict_r = df_ict['rr'].sum()
premarket_mask = df_ict['ny_hour'].isin([7, 8])
premarket_r = df_ict[premarket_mask]['rr'].sum()
locked_r = df_ict[~premarket_mask]['rr'].sum()

print("=================================================================")
print("1. ICT FAITHFUL: PREMARKET ABLATION & SESSIONS")
print("=================================================================")
print(f"Total Trades: {len(df_ict)}, Net R: {total_ict_r:.2f}R, Expectancy: {df_ict['rr'].mean():.4f}R")
print(f"Premarket Window (07:00-09:00 NY): {premarket_mask.sum()} trades ({premarket_mask.sum()/len(df_ict)*100:.1f}%), Net R: {premarket_r:.2f}R")
print(f"Without Premarket (Filtered): {(~premarket_mask).sum()} trades, Net R: {locked_r:.2f}R, Expectancy: {df_ict[~premarket_mask]['rr'].mean():.4f}R")

print("\nPerformance by NY Hour:")
hour_grp = df_ict.groupby('ny_hour')['rr'].agg(trades='count', win_rate=lambda x: (x > 0).mean(), net_r='sum', mean_r='mean')
print(hour_grp.to_string())

# 2. MSNR Reconciled: v20 vs v21 on all catalog vs live allowlist
df_msnr = pd.read_csv('storage/analysis/msnr_v21_two_years_20261011/trades.csv')
print("\n=================================================================")
print("2. MALAYSIAN SNR: RECONCILIATION OF SAMPLE SIZES (2036 vs 5016)")
print("=================================================================")
print(f"Total Rows in trades.csv: {len(df_msnr)}")
for ver, group in df_msnr.groupby('version'):
    net_r = group['rr'].sum()
    wr = (group['rr'] > 0).mean()
    mean_r = group['rr'].mean()
    print(f"  Version: {ver:30s} | Trades: {len(group):4d} | WinRate: {wr*100:5.2f}% | Net R: {net_r:7.2f}R | Mean R: {mean_r:7.4f}R")

print("\nBreakdown of current version (v21) by Catalog vs Live Allowlist:")
v21 = df_msnr[df_msnr['version'] == 'msnr-v2.1-persistent-retest']
for is_live, group in v21.groupby('live_allowlist'):
    label = "Live Enabled (19 Symbols)" if is_live else "Other Catalog (41 Symbols)"
    net_r = group['rr'].sum()
    wr = (group['rr'] > 0).mean()
    mean_r = group['rr'].mean()
    print(f"  {label:30s} | Trades: {len(group):4d} | WinRate: {wr*100:5.2f}% | Net R: {net_r:7.2f}R | Mean R: {mean_r:7.4f}R")

# 3. ORB Reconciled: Variants in trades.csv vs Enabled symbols
df_orb = pd.read_csv('storage/analysis/orb_nunez_2y/trades.csv')
print("\n=================================================================")
print("3. NEW YORK ORB: RECONCILIATION OF SAMPLE SIZES (424 vs 2934)")
print("=================================================================")
print(f"Total Rows in trades.csv: {len(df_orb)}")
for var, group in df_orb.groupby('variant'):
    net_r = group['leg1_r'].sum() + group['leg2_r'].sum()
    wr = ((group['leg1_r'] + group['leg2_r']) > 0).mean()
    print(f"  Variant: {var:15s} | Trades: {len(group):4d} | WinRate: {wr*100:5.2f}% | Net R: {net_r:7.2f}R")

print("\nBreakdown of CURRENT Variant by Symbol:")
orb_curr = df_orb[df_orb['variant'] == 'CURRENT'].copy()
orb_curr['total_r'] = orb_curr['leg1_r'] + orb_curr['leg2_r']
enabled_syms = ['Wall Street 30', 'US Tech 100', 'XAUUSD', 'BTCUSD']
orb_curr['is_enabled'] = orb_curr['symbol'].isin(enabled_syms)

sym_grp = orb_curr.groupby(['symbol', 'is_enabled'])['total_r'].agg(trades='count', win_rate=lambda x: (x > 0).mean(), net_r='sum', mean_r='mean')
print(sym_grp.to_string())

enabled_only = orb_curr[orb_curr['is_enabled']]
other_syms = orb_curr[~orb_curr['is_enabled']]
print(f"\n  Enabled 4 Symbols: {len(enabled_only)} trades | Net R: {enabled_only['total_r'].sum():.2f}R | Mean R: {enabled_only['total_r'].mean():.4f}R")
print(f"  Other Symbols (XAGUSD, US500): {len(other_syms)} trades | Net R: {other_syms['total_r'].sum():.2f}R | Mean R: {other_syms['total_r'].mean():.4f}R")
