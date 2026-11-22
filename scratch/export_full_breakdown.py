import pandas as pd

df = pd.read_csv('storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv')

# Format table generator
def format_category_table(cat_name):
    cat_df = df[df['category'] == cat_name]
    lines = []
    lines.append(f"### {cat_name} ({cat_df['symbol'].nunique()} Activos)")
    lines.append("")
    lines.append("| Instrumento | Estrategia | Trades Antes | Trades Desp. | Δ Trades | WR Antes | WR Desp. | Δ WR | PnL Antes (R) | PnL Desp. (R) | Δ PnL (R) | Estado / Decisión |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
    
    # Sort by symbol, then strategy order: ICT, Trend Pullback, Malaysian SNR, ORB
    strat_order = {'ICT': 1, 'TREND_PULLBACK': 2, 'MALAYSIAN_SNR': 3, 'ORB': 4}
    cat_df = cat_df.copy()
    cat_df['strat_rank'] = cat_df['strategy'].map(strat_order)
    cat_df = cat_df.sort_values(by=['symbol', 'strat_rank'])
    
    current_sym = None
    for _, r in cat_df.iterrows():
        sym_display = f"**{r['symbol']}**" if r['symbol'] != current_sym else '↳'
        current_sym = r['symbol']
        strat_display = r['strategy'].replace('_', ' ')
        sign_delta_trades = f"{int(r['delta_trades']):+d}" if r['delta_trades'] != 0 else "0"
        sign_delta_wr = f"{r['delta_wr_pp']:+.2f} pp" if r['delta_wr_pp'] != 0 else "0.00 pp"
        sign_pnl_antes = f"{r['r_neto_antes']:+.2f} R"
        sign_pnl_desp = f"{r['r_neto_despues']:+.2f} R"
        sign_delta_pnl = f"{r['delta_r']:+.2f} R"
        
        lines.append(f"| {sym_display} | {strat_display} | {int(r['trades_antes']):,} | {int(r['trades_despues']):,} | {sign_delta_trades} | {r['wr_antes']:.2f}% | {r['wr_despues']:.2f}% | {sign_delta_wr} | {sign_pnl_antes} | {sign_pnl_desp} | {sign_delta_pnl} | {r['decision']} |")
    return "\n".join(lines)

with open('scratch/full_breakdown_markdown.md', 'w', encoding='utf-8') as f:
    for cat in ['SYNTHETICS', 'FOREX', 'METALS', 'CRYPTO', 'INDICES', 'COMMODITIES']:
        f.write(format_category_table(cat))
        f.write("\n\n")

print("SUCCESS: written scratch/full_breakdown_markdown.md")
