import pandas as pd

p_orig = 'storage/analysis/msnr_faithful_trades.csv'
p_omit = 'scratch/omitted_14_msnr_faithful_trades.csv'

df_orig = pd.read_csv(p_orig)
df_omit = pd.read_csv(p_omit)

print(f"Orig: {len(df_orig)} rows, min: {df_orig['time'].min()}, max: {df_orig['time'].max()}")
print(f"Omit: {len(df_omit)} rows, min: {df_omit['time'].min()}, max: {df_omit['time'].max()}")

# Símbolos en orig
print("Symbols in orig:")
print(df_orig['symbol'].value_counts())

# Símbolos en omit
print("\nSymbols in omit:")
print(df_omit['symbol'].value_counts())
