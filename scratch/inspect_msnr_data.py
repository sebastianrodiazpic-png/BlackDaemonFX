import pandas as pd
import json
import re

# 1. Load storage CSV
df = pd.read_csv('storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv')
msnr = df[df['strategy'] == 'MALAYSIAN_SNR'].copy()
print(f"Total MSNR rows in storage CSV: {len(msnr)}")
print(f"Total trades: {msnr['trades_despues'].sum()}")
print(f"Wins: {msnr['wins_despues'].sum()}")
print(f"Losses: {msnr['losses_despues'].sum()}")
print(f"Win Rate global: {msnr['wins_despues'].sum() / msnr['trades_despues'].sum() * 100:.2f}%")
print(f"Retorno R neto: {msnr['r_neto_despues'].sum():.2f} R")

# 2. Check by categories
print("\n=== RESUMEN POR CATEGORÍAS ===")
cat_summary = msnr.groupby('category').agg(
    activos=('symbol', 'count'),
    trades=('trades_despues', 'sum'),
    wins=('wins_despues', 'sum'),
    losses=('losses_despues', 'sum'),
    retorno_r=('r_neto_despues', 'sum')
)
cat_summary['win_rate'] = (cat_summary['wins'] / cat_summary['trades']) * 100
cat_summary = cat_summary.sort_values(by='retorno_r', ascending=False)
print(cat_summary.to_string())

# 3. Check Rentables vs Podados
print("\n=== RENTABLES VS PODADOS ===")
print(msnr['decision'].value_counts())

# 4. Check all 73 instruments sorted by category and retorno_r
print("\n=== TODOS LOS 73 INSTRUMENTOS DE MALAYSIAN SNR ===")
msnr_sorted = msnr.sort_values(by=['category', 'r_neto_despues'], ascending=[True, False])
for _, row in msnr_sorted.iterrows():
    print(f"{row['category']:12} | {row['symbol']:25} | Trades: {row['trades_despues']:4} | Wins: {row['wins_despues']:4} | Losses: {row['losses_despues']:4} | WR: {row['wr_despues']:5.2f}% | R: {row['r_neto_despues']:+8.2f}R | {row['decision']}")
