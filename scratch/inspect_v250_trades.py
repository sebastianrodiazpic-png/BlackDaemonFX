import pandas as pd

df = pd.read_csv('scratch/omitted_14_msnr_faithful_trades.csv')
v250 = df[df['symbol'] == 'Volatility 250 (1s) Index']
print(v250.iloc[0])
