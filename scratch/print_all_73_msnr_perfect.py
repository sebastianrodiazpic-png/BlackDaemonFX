import pandas as pd

df = pd.read_csv('storage/analysis/replay_5y_perfect_strategy_bases.csv')
msnr = df[df['strategy'] == 'Malaysian SNR'].copy()
msnr = msnr.sort_values(by=['category', 'pnl_despues'], ascending=[True, False])

print(f"Total rows: {len(msnr)}")
print(f"Trades antes: {msnr['trades_antes'].sum()} -> Trades despues: {msnr['trades_despues'].sum()}")
print(f"PnL antes: ${msnr['pnl_antes'].sum():,.2f} -> PnL despues: ${msnr['pnl_despues'].sum():,.2f}")

for idx, r in msnr.iterrows():
    print(f"{r['symbol']:25} | {r['category']:10} | Base Trades: {r['trades_despues']:4} | WR: {r['wr_despues']:5.2f}% | R: +{r['r_despues']:8.2f}R | PnL: ${r['pnl_despues']:10,.2f}")
