import pandas as pd

df = pd.read_csv('storage/analysis/msnr_5y_strict_comparison_report.csv')
cat_df = pd.read_csv('storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv')
cat_map = dict(zip(cat_df['symbol'], cat_df['category']))

df['real_category'] = df['symbol'].map(cat_map).fillna(df['category'])

# Sort by real_category and r_optimizado descending
cat_order = ['SYNTHETICS', 'FOREX', 'INDICES', 'METALS', 'COMMODITIES', 'CRYPTO']
df['cat_rank'] = df['real_category'].map(lambda x: cat_order.index(x) if x in cat_order else 99)
df = df.sort_values(by=['cat_rank', 'r_optimizado'], ascending=[True, False]).reset_index(drop=True)

print(f"Total rows: {len(df)}")
for cat, g in df.groupby('real_category', sort=False):
    print(f"\n### {cat} ({len(g)} activos)")
    t_b = g['trades_base'].sum()
    t_o = g['trades_optimizado'].sum()
    d_t = g['delta_trades'].sum()
    wr_b = (g['trades_base'] * g['wr_base'] / 100).sum() / t_b * 100
    wr_o = (g['trades_optimizado'] * g['wr_optimizado'] / 100).sum() / t_o * 100
    r_b = g['r_base'].sum()
    r_o = g['r_optimizado'].sum()
    d_r = g['delta_r'].sum()
    print(f"Subtotal: Base {t_b} trades, {wr_b:.2f}% WR, +{r_b:,.2f}R -> Opt {t_o} trades, {wr_o:.2f}% WR, +{r_o:,.2f}R (Delta: +{d_t} trades, {d_r:+,.2f}R)")
