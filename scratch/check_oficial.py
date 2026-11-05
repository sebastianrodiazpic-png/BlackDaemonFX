import pandas as pd

df = pd.read_csv("storage/analysis/comparativa_oficial_criterio_humano_activos_rentables.csv")
print("Strategies in comparativa_oficial:", df["strategy"].unique())
for st, grp in df.groupby("strategy"):
    gt51 = grp[grp["wr_despues"] > 51.0]
    print(f"\nStrategy {st}: {len(gt51)} / {len(grp)} symbols with wr_despues > 51.0%")
    for _, r in gt51.iterrows():
        print(f"  {r['symbol']} ({r['market']}): WR={r['wr_despues']}%, R={r['r_despues']}")
