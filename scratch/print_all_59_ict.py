import pandas as pd

df = pd.read_csv('storage/analysis/ict_5y_m5_refinement_audit_report.csv')
activos = df[df['status'] == 'ACTIVO'].sort_values(['category', 'r_m5'], ascending=[True, False])
print(f"Total activos activos: {len(activos)}\n")

for cat, grp in activos.groupby('category'):
    print(f"### Familia: {cat} ({len(grp)} activos)")
    print("| Instrumento | Trades Base | Trades con M5 | Delta Trades | Win Rate Base | Win Rate con M5 | Delta WR | Retorno Base | Retorno con M5 | Ganancia Extra |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in grp.iterrows():
        sym = r['symbol']
        tb = int(r['trades_base'])
        tm = int(r['trades_m5'])
        dt = int(r['delta_trades'])
        wrb = f"{r['wr_base']:.2f} %"
        wrm = f"{r['wr_m5']:.2f} %"
        dwr = f"{r['delta_wr']:+.2f} pp"
        rb = f"+{r['r_base']:.2f} R"
        rm = f"+{r['r_m5']:.2f} R"
        dr = f"+{r['delta_r']:.2f} R"
        print(f"| **{sym}** | {tb:,} | {tm:,} | **+{dt}** | {wrb} | {wrm} | {dwr} | {rb} | {rm} | **{dr}** |")
    print()
