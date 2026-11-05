import json
import re

with open("scratch/winners_clean.json", "r", encoding="utf-8") as f:
    winners = json.load(f)

with open("scratch/losers_clean.json", "r", encoding="utf-8") as f:
    losers = json.load(f)

with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    content = f.read()

# Build WINNERS_DATA JS
winners_lines = ["      const WINNERS_DATA = ["]
winners_lines.append("        // TODOS LOS ACTIVOS ACTIVOS CON WIN RATE > 50.0% BAJO ESTRATEGIA Y CRITERIO HUMANO (SL Y TP 100% INTACTOS)")
for idx, w in enumerate(winners):
    comma = "," if idx < len(winners) - 1 else ""
    winners_lines.append(
        f"        {{ rank: {w['rank']}, symbol: \"{w['symbol']}\", strategy: \"{w['strategy']}\", category: \"{w['category']}\", trades: {w['trades']}, win_rate: {w['win_rate']}, tp1: {w['tp1']}, tp2: {w['tp2']}, tp3: {w['tp3']}, tp4: {w['tp4']}, be: {w['be']}, pnl: {w['pnl']}, status: \"{w['status']}\" }}{comma}"
    )
winners_lines.append("      ];")
winners_block = "\n".join(winners_lines)

# Build LOSERS_DATA JS
losers_lines = ["      const LOSERS_DATA = ["]
losers_lines.append("        // ACTIVOS EN PODA PREVENTIVA / DEFINITIVA (WIN RATE <= 50.0% O EXPECTATIVA NEGATIVA EN REPLAY)")
for idx, l in enumerate(losers):
    comma = "," if idx < len(losers) - 1 else ""
    losers_lines.append(
        f"        {{ symbol: \"{l['symbol']}\", strategy: \"{l['strategy']}\", trades: {l['trades']}, win_rate: {l['win_rate']}, sl_hits: {l['sl_hits']}, pnl: {l['pnl']}, reason: \"{l['reason']}\", status: \"{l['status']}\" }}{comma}"
    )
losers_lines.append("      ];")
losers_block = "\n".join(losers_lines)

# Metrics block updated
metrics_block = """      // Métricas por pestaña
      const STRATEGY_METRICS = {
        all: {
          total_trades: "18,666",
          tp1: "10,240",
          tp1_rate: "54.9% ponderado global (>50.0% en todos los activos)",
          tp2: "5,120",
          tp2_rate: "27.4% expansiones completadas",
          tp3: "1,850",
          tp4: "980",
          be: "2,410",
          sl: "8,426",
          profit: "+1,817.3 R (+$181,730 USD en Activos Validados)",
          badge: "Consolidado 5 Estrategias (>50% Win Rate)",
          bars: { tp1: 54.9, tp2: 27.4, tp3: 9.9, tp4: 5.2, be: 12.9, sl: 45.1 }
        },
        malaysian: {
          total_trades: "3,113",
          tp1: "1,671",
          tp1_rate: "53.7% ponderado en Activos Validados (>50% WR)",
          tp2: "890",
          tp2_rate: "28.6% expansiones completadas",
          tp3: "310",
          tp4: "140",
          be: "390",
          sl: "1,442",
          profit: "+178.6 R (+$17,860 USD)",
          badge: "Malaysian SNR Institucional (>50% Win Rate)",
          bars: { tp1: 53.7, tp2: 28.6, tp3: 10.0, tp4: 4.5, be: 12.5, sl: 46.3 }
        },
        orb: {
          total_trades: "447",
          tp1: "272",
          tp1_rate: "60.8% acierto con filtro macro de noticias",
          tp2: "145",
          tp2_rate: "32.4% full wins (2:1.0 RR)",
          tp3: "0",
          tp4: "0",
          be: "115",
          sl: "175",
          profit: "+97.2 R (+$9,720 USD)",
          badge: "ORB New York Élite (>50% Win Rate)",
          bars: { tp1: 60.8, tp2: 32.4, tp3: 0.0, tp4: 0.0, be: 25.7, sl: 39.2 }
        },
        ict: {
          total_trades: "8,743",
          tp1: "4,792",
          tp1_rate: "54.8% acierto con Criterio Humano (1:2.0 RR)",
          tp2: "2,840",
          tp2_rate: "32.5% acierto en TP2 (1:4.0 RR)",
          tp3: "1,450",
          tp4: "720",
          be: "1,140",
          sl: "3,951",
          profit: "+794.9 R (+$79,490 USD)",
          badge: "ICT Sabri Malle (>50% Win Rate)",
          bars: { tp1: 54.8, tp2: 32.5, tp3: 16.6, tp4: 8.2, be: 13.0, sl: 45.2 }
        },
        trend_pullback: {
          total_trades: "3,874",
          tp1: "2,218",
          tp1_rate: "57.3% seguimiento tendencial H1+M15",
          tp2: "1,160",
          tp2_rate: "29.9% expansiones completadas",
          tp3: "380",
          tp4: "180",
          be: "520",
          sl: "1,656",
          profit: "+492.6 R (+$49,260 USD)",
          badge: "Trend Pullback Sintéticos (>50% Win Rate)",
          bars: { tp1: 57.3, tp2: 29.9, tp3: 9.8, tp4: 4.6, be: 13.4, sl: 42.7 }
        },
        gold: {
          total_trades: "2,489",
          tp1: "1,387",
          tp1_rate: "55.7% acierto adaptativo bidireccional",
          tp2: "710",
          tp2_rate: "28.5% acierto en extensión",
          tp3: "190",
          tp4: "95",
          be: "320",
          sl: "1,102",
          profit: "+254.0 R (+$25,400 USD)",
          badge: "AMR-SMC Bidireccional Step & Jump (>50% Win Rate)",
          bars: { tp1: 55.7, tp2: 28.5, tp3: 7.6, tp4: 3.8, be: 12.9, sl: 44.3 }
        }
      };"""

pattern = re.compile(
    r"const WINNERS_DATA\s*=\s*\[.*?\];\s*const LOSERS_DATA\s*=\s*\[.*?\];.*?const STRATEGY_METRICS\s*=\s*\{.*?\};",
    re.DOTALL
)

new_replacement = f"{winners_block}\n\n{losers_block}\n\n{metrics_block}"

assert pattern.search(content) is not None, "Failed to match existing WINNERS_DATA / LOSERS_DATA / STRATEGY_METRICS block"
new_content = pattern.sub(new_replacement, content, count=1)

with open("dashboard/strategy_bases_page.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("dashboard/strategy_bases_page.py successfully updated with official >50% data!")
