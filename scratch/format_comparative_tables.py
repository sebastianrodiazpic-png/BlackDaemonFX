from pathlib import Path
import pandas as pd

ROOT = Path.cwd()
OUT = ROOT / "storage" / "analysis"

df_ict = pd.read_csv(OUT / "simulacion_ict_mejoras_5y.csv")
df_orb = pd.read_csv(OUT / "simulacion_orb_mejoras_5y.csv")
df_msnr = pd.read_csv(OUT / "simulacion_msnr_mejoras_5y.csv")

def print_md(df, title):
    print(f"\n{title}")
    cols = df.columns.tolist()
    print("| " + " | ".join(cols) + " |")
    print("|" + "|".join(["---"] * len(cols)) + "|")
    for _, row in df.iterrows():
        print("| " + " | ".join(str(row[c]) for c in cols) + " |")

cols = ["symbol", "n_actual", "wr_actual", "r_actual", "n_proyectado", "wr_proyectado", "r_proyectado", "delta_trades", "status_proyectado"]

print_md(df_ict[df_ict["market_type"] == "Sintético"].sort_values(by="r_proyectado", ascending=False)[cols].head(25), "### ICT: SINTÉTICOS DERIV")
print_md(df_ict[df_ict["market_type"] == "Real"].sort_values(by="r_proyectado", ascending=False)[cols].head(25), "### ICT: FOREX Y MERCADOS REALES")
print_md(df_orb.sort_values(by="r_proyectado", ascending=False)[cols], "### ORB: ANÁLISIS DE MEJORAS")
print_md(df_msnr.sort_values(by="r_proyectado", ascending=False)[cols].head(30), "### MALAYSIAN SNR: ANÁLISIS DE MEJORAS")
