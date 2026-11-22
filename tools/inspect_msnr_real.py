import pandas as pd

df = pd.read_csv('storage/analysis/replay_5y_perfect_strategy_bases.csv')
msnr_real = df[(df['strategy'] == 'Malaysian SNR') & (df['category'] != 'SYNTHETICS')].copy()

print(f"Total activos mercados reales MSNR: {len(msnr_real)}")
tot_trades = msnr_real['trades_despues'].sum()
print(f"Total trades en 5 años: {tot_trades}")
print(f"Media de trades por activo en 5 años: {tot_trades / len(msnr_real):.1f} trades")
print(f"Media mensual por activo: {(tot_trades / len(msnr_real)) / 60.0:.2f} trades/mes (1 trade cada {(60.0 * len(msnr_real)) / tot_trades:.1f} meses)")
print("\nDesglose completo:")
print(msnr_real[['symbol', 'trades_despues', 'wr_despues', 'r_despues', 'pnl_despues']].sort_values(by='trades_despues').to_string())
