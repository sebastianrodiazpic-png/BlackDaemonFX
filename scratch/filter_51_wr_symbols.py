import pandas as pd
df = pd.read_csv('storage/analysis/deriv_synthetics_5y_test_evaluation.csv')
eligible = df[(df['v3_wr'] > 51.0) & (df['v3_r'] > 0)].sort_values('v3_wr', ascending=False)
print(f"Eligible symbols (> 51% WR and Net R > 0): {len(eligible)}")
for _, r in eligible.iterrows():
    print(r['symbol'].ljust(30), f"WR: {r['v3_wr']:.2f}%", f"Net R: {r['v3_r']:.2f} R")
print("\nTuple:")
print(repr(tuple(eligible['symbol'].tolist())))
