import pandas as pd

df = pd.read_csv('storage/analysis/comparativa_oficial_criterio_humano_activos_rentables.csv')
msnr = df[(df['strategy'] == 'Malaysian SNR v3.2') & (df['wr_despues'] > 50.0)].sort_values(by='wr_despues', ascending=False)
print(f"Total MSNR > 50%: {len(msnr)}")
for _, r in msnr.iterrows():
    print(f"{r['symbol']} | Antes: {r['wr_antes']}% | Despues: {r['wr_despues']}% | R: {r['r_despues']}")
