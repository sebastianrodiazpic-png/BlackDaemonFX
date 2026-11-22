import pandas as pd

df = pd.read_csv("storage/analysis/replay_5y_perfect_strategy_bases.csv")
msnr = df[df['strategy'] == 'Malaysian SNR']
xau = msnr[msnr['symbol'] == 'XAUUSD']
print(xau[['symbol', 'category', 'trades_antes', 'wr_antes', 'trades_despues', 'wr_despues', 'r_despues', 'pnl_despues']])

print("\n--- Traditional assets in Malaysian SNR ---")
trad = msnr[msnr['category'] != 'SYNTHETICS']
print(trad[['symbol', 'trades_despues', 'wr_despues', 'r_despues']].to_string())
