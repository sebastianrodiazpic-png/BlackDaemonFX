import pandas as pd
from pathlib import Path

csv_path = Path("storage/analysis/tabla_comparativa_todos_instrumentos_tripartita_5y.csv")
df = pd.read_csv(csv_path)

out_file = Path("storage/analysis/tablas_completas_markdown.md")

with open(out_file, "w", encoding="utf-8") as f:
    for strat in ["ICT", "MALAYSIAN_SNR", "ORB"]:
        sub = df[df["strategy"] == strat]
        f.write(f"\n### ESTRATEGIA: {strat} (TODOS LOS 73 INSTRUMENTOS)\n\n")
        f.write("| # | Símbolo | Categoría | Trades Ant | Trades Desp | WR Ant | WR Desp | $\\Delta$ WR | R Ant | R Desp | $\\Delta$ R | Estado Ant (/Strategy-bases) | Estado Desp (Tripartita) |\n")
        f.write("|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|---|\n")
        idx = 1
        for _, r in sub.iterrows():
            sym = r["symbol"]
            cat = r["category"]
            ta, td = r["trades_antes"], r["trades_despues"]
            wra, wrd = r["wr_antes"], r["wr_despues"]
            ra, rd = r["r_neto_antes"], r["r_neto_despues"]
            dwr = f"+{r['delta_wr_pp']:.2f}%" if r["delta_wr_pp"] >= 0 else f"{r['delta_wr_pp']:.2f}%"
            dr = f"+{r['delta_r']:.2f}R" if r["delta_r"] >= 0 else f"{r['delta_r']:.2f}R"
            sa, sd = r["status_antes"], r["status_despues"]
            f.write(f"| {idx} | **{sym}** | {cat} | {ta} | {td} | {wra:.2f}% | **{wrd:.2f}%** | {dwr} | {ra:.2f}R | **{rd:.2f}R** | {dr} | {sa} | {sd} |\n")
            idx += 1

print(f"Exportado correctamente a {out_file.name}")
