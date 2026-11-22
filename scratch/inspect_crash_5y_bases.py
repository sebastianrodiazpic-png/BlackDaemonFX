import pandas as pd

df = pd.read_csv("storage/analysis/replay_5y_perfect_strategy_bases.csv")

crash_targets = [
    "Crash 1000 Index",
    "Crash 300 Index",
    "Crash 500 Index",
    "Crash 600 Index",
    "Crash 900 Index",
    "Volatility Crash 400 Index",
    "Volatility Crash 550 Index",
    "Volatility Crash 750 Index",
    "Vol over Crash 550"
]

print("--- DATOS DE 5 AÑOS EN replay_5y_perfect_strategy_bases.csv ---")
crash_rows = df[df['symbol'].isin(crash_targets) | df['symbol'].str.contains("Crash", case=False, na=False)]
print(crash_rows[['strategy', 'symbol', 'trades_despues', 'wr_despues', 'r_despues', 'pnl_despues']].to_string())
