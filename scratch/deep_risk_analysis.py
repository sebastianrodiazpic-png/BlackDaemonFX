import pandas as pd
import numpy as np

path = 'storage/exports/deriv_demo_trading_report.xlsx'
df = pd.read_excel(path, sheet_name="Trades")

# Filter closed trades
df_closed = df[df['status'].astype(str).str.upper() == 'CLOSED'].copy()
print(f"Total Closed Trades: {len(df_closed)}")

# 1. Overall stats
print("\n--- 1. OVERALL STATS ---")
print("Net PnL Sum:", df_closed['net_pnl'].sum())
print("Realized RR Mean:", df_closed['realized_rr'].mean())
print("Realized RR Median:", df_closed['realized_rr'].median())
print("Win rate (PnL > 0):", (df_closed['net_pnl'] > 0).mean() * 100)
print("Win rate (RR > 0.25):", (df_closed['realized_rr'] > 0.25).mean() * 100)
print("Loss rate (RR < -0.25):", (df_closed['realized_rr'] < -0.25).mean() * 100)
print("BE rate (-0.25 <= RR <= 0.25):", ((df_closed['realized_rr'] >= -0.25) & (df_closed['realized_rr'] <= 0.25)).mean() * 100)

# 2. Risk slippage & Tail losses
print("\n--- 2. RISK DISCIPLINE & SL SLIPPAGE ---")
print("Trades with realized_rr < -1.05R:", (df_closed['realized_rr'] < -1.05).sum())
print("Worst 5 losses (RR):", df_closed['realized_rr'].sort_values().head(5).tolist())
print("Average loss when losing (RR < -0.25):", df_closed[df_closed['realized_rr'] < -0.25]['realized_rr'].mean())
print("Average win when winning (RR > 0.25):", df_closed[df_closed['realized_rr'] > 0.25]['realized_rr'].mean())

# 3. MFE vs Realized RR: Are we leaving money on the table or getting choked by BE?
print("\n--- 3. MFE (Maximum Favorable Excursion) vs REALIZED RR ---")
if 'mfe_max_rr' in df_closed.columns and df_closed['mfe_max_rr'].notna().sum() > 50:
    mfe = df_closed['mfe_max_rr'].dropna()
    print("MFE Mean:", mfe.mean())
    print("MFE Median:", mfe.median())
    print("Trades with MFE >= 1.0R:", (df_closed['mfe_max_rr'] >= 1.0).sum(), f"({(df_closed['mfe_max_rr'] >= 1.0).mean()*100:.1f}%)")
    print("Trades with MFE >= 2.0R:", (df_closed['mfe_max_rr'] >= 2.0).sum(), f"({(df_closed['mfe_max_rr'] >= 2.0).mean()*100:.1f}%)")
    print("Trades with MFE >= 3.0R:", (df_closed['mfe_max_rr'] >= 3.0).sum(), f"({(df_closed['mfe_max_rr'] >= 3.0).mean()*100:.1f}%)")
    
    # What happened to trades with MFE >= 1.0R?
    mfe_ge_1 = df_closed[df_closed['mfe_max_rr'] >= 1.0]
    print("\nFor trades that reached MFE >= 1.0R:")
    print("  Realized RR Mean:", mfe_ge_1['realized_rr'].mean())
    print("  Ended up closing <= 0.35R:", (mfe_ge_1['realized_rr'] <= 0.35).sum(), f"({(mfe_ge_1['realized_rr'] <= 0.35).mean()*100:.1f}%)")
    print("  Ended up closing NEGATIVE (< 0):", (mfe_ge_1['realized_rr'] < 0).sum(), f"({(mfe_ge_1['realized_rr'] < 0).mean()*100:.1f}%)")
else:
    print("mfe_max_rr not sufficiently populated or not available")

# 4. Pierna 1 vs Pierna 2 performance
print("\n--- 4. PERFORMANCE BY PIERNA (LEG) ---")
if 'pierna_operacion' in df_closed.columns:
    print(df_closed.groupby('pierna_operacion')[['realized_rr', 'net_pnl']].agg(['count', 'mean', 'sum']))

# 5. Top and bottom instruments by Net PnL and Realized RR
print("\n--- 5. TOP & BOTTOM INSTRUMENTS ---")
inst = df_closed.groupby('instrument')[['realized_rr', 'net_pnl']].agg(
    trades=('realized_rr', 'count'),
    mean_rr=('realized_rr', 'mean'),
    sum_rr=('realized_rr', 'sum'),
    sum_pnl=('net_pnl', 'sum'),
    winrate=('realized_rr', lambda x: (x > 0.25).mean() * 100)
).sort_values(by='sum_pnl', ascending=False)
print("Top 5 profitable:")
print(inst.head(5))
print("\nBottom 5 losing:")
print(inst.tail(5))

# 6. Exit classification breakdown
print("\n--- 6. EXIT CLASSIFICATION BREAKDOWN ---")
if 'clasificacion_cierre_es' in df_closed.columns:
    print(df_closed['clasificacion_cierre_es'].value_counts())

# 7. Runner exit reasons
print("\n--- 7. RUNNER EXIT REASONS ---")
if 'motivo_salida_runner' in df_closed.columns:
    print(df_closed['motivo_salida_runner'].value_counts())
