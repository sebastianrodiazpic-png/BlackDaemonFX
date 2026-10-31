import pandas as pd
df = pd.read_csv('storage/analysis/deriv_synthetics_5y_test_evaluation.csv')
for i, r in df.iterrows():
    sym = r['symbol'].ljust(30)
    fam = str(r['family']).ljust(12)
    trades = str(r['v3_trades']).ljust(5)
    wr = f"{r['v3_wr']:.1f}%".ljust(7)
    r_val = f"{r['v3_r']:.2f} R".ljust(11)
    status = r['status']
    print(f"{sym} | {fam} | {trades} | {wr} | {r_val} | {status}")
print("\n--- TOTALS ---")
print(f"Total V3 Trades: {df['v3_trades'].sum()}")
print(f"Total V3 R: {df['v3_r'].sum():.2f} R")
print(f"Average Win Rate: {df['v3_wr'].mean():.2f}%")
print(f"Profitable Assets: {(df['v3_r'] > 0).sum()} / {len(df)}")
