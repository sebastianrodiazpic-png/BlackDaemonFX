import pandas as pd
df = pd.read_csv("storage/analysis/comparativa_oficial_criterio_humano_activos_rentables.csv")
ict_synths = df[(df["strategy"] == "ICT Sabri Malle") & (df["wr_despues"] > 51.0)]
# filter to synthetics
synths = ict_synths[ict_synths["symbol"].str.contains("Index|Vol", case=False)]
print(f"ICT Synthetics with WR > 51% (count = {len(synths)}):")
for _, r in synths.sort_values(by="wr_despues", ascending=False).iterrows():
    print(f"  {r['symbol']}: WR={r['wr_despues']}%, R={r['r_despues']}")
