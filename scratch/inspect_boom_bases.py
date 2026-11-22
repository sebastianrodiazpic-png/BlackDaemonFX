import pandas as pd

df = pd.read_csv('storage/analysis/replay_5y_perfect_strategy_bases.csv')
boom_rows = df[df['symbol'].str.contains('Boom', case=False, na=False) & df['strategy'].isin(['Malaysian SNR', 'ICT Sabri Malle'])]

print("=== DATOS EXISTENTES EN STRATEGY BASES (BOOM) ===")
for idx, r in boom_rows.iterrows():
    print(f"{r['symbol']} | {r['strategy']} | Trades: {r['trades_despues']} | WR: {r['wr_despues']}% | R: {r['r_despues']} R | MaxDD: {r.get('max_dd_despues_r', 'N/A')}")
