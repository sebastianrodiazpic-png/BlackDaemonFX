"""
scratch/update_final_report.py
Genera el reporte final 100% sincronizado con WINNERS_DATA de dashboard/strategy_bases_page.py
"""
import pandas as pd
from pathlib import Path

df = pd.read_csv("storage/analysis/replay_5y_perfect_strategy_bases.csv")

strat_map = {
    "Malaysian SNR": "🇲🇾 Estrategia Malaysian SNR (H1 Break / M15 Retest)",
    "ICT Sabri Malle": "🎯 Estrategia ICT Sabri Malle (FVG, Mitigación & MSS)",
    "Trend Pullback": "📈 Estrategia Trend Pullback (Impulso y Retroceso)",
    "ORB New York": "🗽 Estrategia ORB New York (Apertura NY 50% Midpoint)",
}

SYNTHETICS_38 = [
    "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index", "Crash 1000 Index",
    "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index", "Boom 1000 Index",
    "Step Index", "Step Index 200", "Step Index 400", "Step Index 500",
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
    "Volatility 5 Index", "Volatility 10 Index", "Volatility 15 Index", "Volatility 25 Index",
    "Volatility 50 Index", "Volatility 75 Index", "Volatility 90 Index", "Volatility 100 Index",
    "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
    "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
    "Vol over Boom 550", "Vol over Crash 550", "VolSwitch High Vol Index",
    "High Frequency Vol 50 Index", "High Frequency Vol 100 Index"
]

lines = []
lines.append("# Auditoría y Replay de 5 Años: Baseline Exacto (/Strategy-bases) vs Con Mejoras")
lines.append("**Fuente de Verdad Baseline:** `WINNERS_DATA` extraído directamente de `dashboard/strategy_bases_page.py`.\n")

for strat_key, strat_title in strat_map.items():
    sub_strat = df[df["strategy"] == strat_key]
    lines.append(f"## {strat_title}\n")
    
    # 1. Sintéticos (38 activos)
    sub_synth = sub_strat[sub_strat["symbol"].isin(SYNTHETICS_38)]
    if not sub_synth.empty:
        lines.append("### Índices Sintéticos Deriv (38 activos)\n")
        lines.append("| Instrumento | Trades Antes | WR Antes | DD Antes | PnL Antes ($) | Trades Después | WR Después | DD Después | PnL Después ($) | Δ WR | Δ PnL ($) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for sym in SYNTHETICS_38:
            match = sub_synth[sub_synth["symbol"] == sym]
            if match.empty:
                continue
            r = match.iloc[0]
            ta = int(r["trades_antes"])
            wra = f"{r['wr_antes']:.1f}%" if ta > 0 else "-"
            dda = f"{r['dd_antes_r']:.1f}R" if ta > 0 else "-"
            pnla = f"+${r['pnl_antes']:,.2f}" if ta > 0 else "$0.00"
            td = int(r["trades_despues"])
            wrd = f"{r['wr_despues']:.1f}%" if td > 0 else "-"
            ddd = f"{r['dd_despues_r']:.1f}R" if td > 0 else "-"
            pnld = f"+${r['pnl_despues']:,.2f}" if td > 0 else "$0.00"
            dwr = f"+{r['delta_wr']:.1f} pp" if r["delta_wr"] > 0 else f"{r['delta_wr']:.1f} pp" if ta > 0 else "-"
            dpnl = f"+${r['delta_pnl']:,.2f}" if ta > 0 else "$0.00"
            lines.append(f"| **{sym}** | {ta} | {wra} | {dda} | {pnla} | {td} | {wrd} | {ddd} | {pnld} | {dwr} | {dpnl} |")
        lines.append("\n")
        
    # 2. Otros mercados (35 activos)
    sub_other = sub_strat[~sub_strat["symbol"].isin(SYNTHETICS_38)]
    if not sub_other.empty:
        lines.append("### Mercados Financieros Tradicionales (Forex, Metales, Índices, Cripto, Commodities)\n")
        lines.append("| Instrumento | Trades Antes | WR Antes | DD Antes | PnL Antes ($) | Trades Después | WR Después | DD Después | PnL Después ($) | Δ WR | Δ PnL ($) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, r in sub_other.iterrows():
            sym = r["symbol"]
            ta = int(r["trades_antes"])
            wra = f"{r['wr_antes']:.1f}%" if ta > 0 else "-"
            dda = f"{r['dd_antes_r']:.1f}R" if ta > 0 else "-"
            pnla = f"+${r['pnl_antes']:,.2f}" if ta > 0 else "$0.00"
            td = int(r["trades_despues"])
            wrd = f"{r['wr_despues']:.1f}%" if td > 0 else "-"
            ddd = f"{r['dd_despues_r']:.1f}R" if td > 0 else "-"
            pnld = f"+${r['pnl_despues']:,.2f}" if td > 0 else "$0.00"
            dwr = f"+{r['delta_wr']:.1f} pp" if r["delta_wr"] > 0 else f"{r['delta_wr']:.1f} pp" if ta > 0 else "-"
            dpnl = f"+${r['delta_pnl']:,.2f}" if ta > 0 else "$0.00"
            lines.append(f"| **{sym}** | {ta} | {wra} | {dda} | {pnla} | {td} | {wrd} | {ddd} | {pnld} | {dwr} | {dpnl} |")
        lines.append("\n")

out_text = "\n".join(lines)
Path("storage/analysis/REPORTE_73_ACTIVOS_POR_ESTRATEGIA_5Y.md").write_text(out_text, encoding="utf-8")
print("Reporte actualizado correctamente.")
