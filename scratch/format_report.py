"""
scratch/format_report.py
Genera tablas markdown completas por estrategia para los 73 instrumentos.
"""
import pandas as pd
from pathlib import Path

df = pd.read_csv("storage/analysis/replay_5y_strategy_bases_vs_mejoras.csv")

strat_names = {
    "MALAYSIAN_SNR": "🇲🇾 Estrategia Malaysian SNR (H1 Break / M15 Retest)",
    "ICT": "🎯 Estrategia ICT Sabri Malle (FVG, Liquidity & MSS)",
    "TREND_PULLBACK": "📈 Estrategia Trend Pullback (Impulso y Retroceso)",
    "ORB": "🗽 Estrategia ORB New York (Apertura NY 50% Midpoint)",
}

cat_names = {
    "SYNTHETICS": "Índices Sintéticos Deriv (38 activos)",
    "FOREX": "Pares de Divisas Forex (24 pares)",
    "METALS": "Metales Preciosos (3 activos)",
    "CRYPTO": "Criptomonedas (2 activos)",
    "INDICES": "Índices Bursátiles (4 índices)",
    "COMMODITIES": "Commodities / Energías (2 activos)",
}

lines = []
lines.append("# Auditoría y Replay Fiel de 5 Años: Baseline (/Strategy-bases) vs Con Mejoras")
lines.append("Comparativa exhaustiva de los 73 instrumentos disponibles en Deriv, desglosados por estrategia.\n")

for strat_key, strat_title in strat_names.items():
    sub_strat = df[df["strategy"] == strat_key]
    lines.append(f"## {strat_title}\n")
    
    for cat_key, cat_title in cat_names.items():
        sub = sub_strat[sub_strat["category"] == cat_key]
        if sub.empty:
            continue
        lines.append(f"### {cat_title}\n")
        lines.append("| Instrumento | Trades Antes | WR Antes | DD Antes | Trades Después | WR Después | DD Después | Δ WR | Δ Net R |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in sub.iterrows():
            sym = r["symbol"]
            ta = int(r["trades_antes"])
            wra = f"{r['wr_antes']:.1f}%" if ta > 0 else "-"
            dda = f"{r['dd_antes_r']:.1f}R" if ta > 0 else "-"
            td = int(r["trades_despues"])
            wrd = f"{r['wr_despues']:.1f}%" if td > 0 else "-"
            ddd = f"{r['dd_despues_r']:.1f}R" if td > 0 else "-"
            dwr = f"+{r['delta_wr']:.1f} pp" if r["delta_wr"] > 0 else f"{r['delta_wr']:.1f} pp" if ta > 0 else "-"
            dr = f"+{r['delta_r']:+.1f}R" if ta > 0 else "-"
            lines.append(f"| **{sym}** | {ta} | {wra} | {dda} | {td} | {wrd} | {ddd} | {dwr} | {dr} |")
        lines.append("\n")

out_text = "\n".join(lines)
Path("storage/analysis/REPORTE_73_ACTIVOS_POR_ESTRATEGIA_5Y.md").write_text(out_text, encoding="utf-8")
print(f"Reporte generado con {len(lines)} líneas.")
