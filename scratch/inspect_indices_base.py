import pandas as pd
df = pd.read_csv('storage/analysis/replay_5y_perfect_strategy_bases.csv')
idx_syms = ['Wall Street 30', 'US Tech 100', 'US SP 500', 'Germany 40']
for s in idx_syms:
    sub = df[(df['symbol'] == s) & (df['strategy'] == 'Malaysian SNR')]
    for _, r in sub.iterrows():
        print(f"{s}: trades={r['trades_despues']}, wr={r['wr_despues']}%, r={r['r_despues']}, pnl=${r['pnl_despues']}")
