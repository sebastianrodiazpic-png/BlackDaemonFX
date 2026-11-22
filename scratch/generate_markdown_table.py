import pandas as pd

df = pd.read_csv('storage/analysis/msnr_5y_strict_comparison_report.csv')
cat_df = pd.read_csv('storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv')
cat_map = dict(zip(cat_df['symbol'], cat_df['category']))

df['real_category'] = df['symbol'].map(cat_map).fillna(df['category'])
cat_order = ['SYNTHETICS', 'FOREX', 'INDICES', 'METALS', 'COMMODITIES', 'CRYPTO']
df['cat_rank'] = df['real_category'].map(lambda x: cat_order.index(x) if x in cat_order else 99)
df = df.sort_values(by=['cat_rank', 'r_optimizado'], ascending=[True, False]).reset_index(drop=True)

with open('scratch/all_73_markdown_table.md', 'w', encoding='utf-8') as f:
    f.write("| # | Instrumento | Categoría | Trades Base | Trades con Buffer | Delta Trades | Win Rate Base | Win Rate con Buffer | Delta WR | Retorno Base | Retorno con Buffer | Ganancia Extra | Cumple Piso WR |\n")
    f.write("| :-: | :--- | :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :--- |\n")
    for i, r in df.iterrows():
        delta_t_str = f"+{r['delta_trades']}" if r['delta_trades'] > 0 else "0"
        delta_wr_str = f"{r['delta_wr_pp']:+.2f} pp" if r['delta_trades'] > 0 else "0.00 pp"
        delta_r_str = f"+{r['delta_r']:.2f} R" if r['delta_r'] > 0 else "0.00 R"
        f.write(f"| {i+1} | **{r['symbol']}** | {r['real_category']} | {r['trades_base']} | {r['trades_optimizado']} | {delta_t_str} | {r['wr_base']:.2f}% | {r['wr_optimizado']:.2f}% | {delta_wr_str} | +{r['r_base']:.2f} R | +{r['r_optimizado']:.2f} R | {delta_r_str} | {r['cumple_piso_wr']} |\n")

print("Generated scratch/all_73_markdown_table.md successfully!")
