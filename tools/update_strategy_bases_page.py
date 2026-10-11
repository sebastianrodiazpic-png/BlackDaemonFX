import json
import re

with open("scratch/msnr_winners_clean.json", "r", encoding="utf-8") as f:
    msnr_winners = json.load(f)

with open("scratch/msnr_losers_clean.json", "r", encoding="utf-8") as f:
    msnr_losers = json.load(f)

with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    content = f.read()

# Other winners
orb_winners = [
    { "symbol": "BTCUSD (ORB)", "strategy": "ORB New York", "category": "Criptomonedas", "trades": 8, "win_rate": 75.0, "tp1": 6, "tp2": 2, "tp3": 0, "tp4": 0, "be": 2, "pnl": 439.00, "status": "Activo / Priorizado (Líder WR 75%)" },
    { "symbol": "US Tech 100 (ORB)", "strategy": "ORB New York", "category": "Índices Bursátiles", "trades": 38, "win_rate": 55.3, "tp1": 21, "tp2": 5, "tp3": 0, "tp4": 0, "be": 11, "pnl": 209.00, "status": "Activo / Priorizado (Nasdaq ORB)" },
    { "symbol": "EURUSD (ORB)", "strategy": "ORB New York", "category": "Forex Core", "trades": 187, "win_rate": 51.9, "tp1": 97, "tp2": 34, "tp3": 0, "tp4": 0, "be": 34, "pnl": 1436.00, "status": "Activo / Priorizado (Forex ORB)" },
    { "symbol": "XAUUSD (Oro ORB)", "strategy": "ORB New York", "category": "Metales", "trades": 130, "win_rate": 50.8, "tp1": 66, "tp2": 16, "tp3": 0, "tp4": 0, "be": 23, "pnl": 310.00, "status": "Activo / Priorizado (Oro ORB)" },
    { "symbol": "XAGUSD (Plata ORB)", "strategy": "ORB New York", "category": "Metales", "trades": 183, "win_rate": 50.3, "tp1": 92, "tp2": 34, "tp3": 0, "tp4": 0, "be": 30, "pnl": 569.00, "status": "Activo / Priorizado (Plata ORB)" },
    { "symbol": "Wall Street 30 (ORB)", "strategy": "ORB New York", "category": "Índices Bursátiles", "trades": 23, "win_rate": 47.8, "tp1": 11, "tp2": 5, "tp3": 0, "tp4": 0, "be": 3, "pnl": 154.00, "status": "Activo / Priorizado (Dow Jones ORB)" },
    { "symbol": "US SP 500 (ORB)", "strategy": "ORB New York", "category": "Índices Bursátiles", "trades": 42, "win_rate": 42.9, "tp1": 18, "tp2": 7, "tp3": 0, "tp4": 0, "be": 4, "pnl": 85.00, "status": "Activo / Priorizado (S&P 500 ORB)" }
]

ict_winners = [
    { "symbol": "XAGUSD (Plata ICT)", "strategy": "ICT Sabri Malle", "category": "Metales", "trades": 40, "win_rate": 52.5, "tp1": 21, "tp2": 17, "tp3": 17, "tp4": 17, "be": 4, "pnl": 3805.73, "status": "Activo / Priorizado (#1 ICT +38.1R)" },
    { "symbol": "BTCUSD (ICT)", "strategy": "ICT Sabri Malle", "category": "Criptomonedas", "trades": 50, "win_rate": 48.0, "tp1": 24, "tp2": 14, "tp3": 14, "tp4": 14, "be": 10, "pnl": 2808.11, "status": "Activo / Priorizado (#2 ICT +28.1R)" },
    { "symbol": "Step Index (ICT)", "strategy": "ICT Sabri Malle", "category": "Sintéticos Step", "trades": 24, "win_rate": 54.2, "tp1": 13, "tp2": 10, "tp3": 10, "tp4": 10, "be": 1, "pnl": 2717.45, "status": "Activo / Priorizado (#3 ICT +27.2R)" },
    { "symbol": "Volatility 75 Index (ICT)", "strategy": "ICT Sabri Malle", "category": "Sintéticos Vol", "trades": 22, "win_rate": 54.5, "tp1": 12, "tp2": 9, "tp3": 9, "tp4": 9, "be": 3, "pnl": 2000.00, "status": "Activo / Priorizado (+20.0R)" },
    { "symbol": "Volatility 100 Index (ICT)", "strategy": "ICT Sabri Malle", "category": "Sintéticos Vol", "trades": 15, "win_rate": 66.7, "tp1": 10, "tp2": 5, "tp3": 5, "tp4": 5, "be": 2, "pnl": 1928.39, "status": "Activo / Priorizado (+19.3R)" },
    { "symbol": "Boom 1000 Index (ICT)", "strategy": "ICT Sabri Malle", "category": "Boom (Compras)", "trades": 29, "win_rate": 48.3, "tp1": 14, "tp2": 10, "tp3": 10, "tp4": 10, "be": 4, "pnl": 1900.00, "status": "Activo / Priorizado (+19.0R)" },
    { "symbol": "Crash 1000 Index (ICT)", "strategy": "ICT Sabri Malle", "category": "Crash (Ventas)", "trades": 17, "win_rate": 52.9, "tp1": 9, "tp2": 8, "tp3": 8, "tp4": 8, "be": 1, "pnl": 1792.67, "status": "Activo / Priorizado (+17.9R)" },
    { "symbol": "USDCAD (ICT Forex)", "strategy": "ICT Sabri Malle", "category": "Forex Core", "trades": 16, "win_rate": 62.5, "tp1": 10, "tp2": 4, "tp3": 4, "tp4": 4, "be": 6, "pnl": 1200.00, "status": "Activo / Priorizado (#1 Forex ICT +12.0R)" },
    { "symbol": "Wall Street 30 (ICT)", "strategy": "ICT Sabri Malle", "category": "Índices Bursátiles", "trades": 14, "win_rate": 64.3, "tp1": 9, "tp2": 4, "tp3": 4, "tp4": 4, "be": 5, "pnl": 1200.00, "status": "Activo / Priorizado (+12.0R)" },
    { "symbol": "EURUSD (ICT v2 Killzones)", "strategy": "ICT Sabri Malle", "category": "Forex Core", "trades": 89, "win_rate": 50.6, "tp1": 45, "tp2": 24, "tp3": 24, "tp4": 24, "be": 18, "pnl": 5100.00, "status": "Activo / Top Performer Forex (PF 2.24)" },
    { "symbol": "GBPUSD (ICT v2 Killzones)", "strategy": "ICT Sabri Malle", "category": "Forex Core", "trades": 87, "win_rate": 49.4, "tp1": 43, "tp2": 21, "tp3": 21, "tp4": 21, "be": 17, "pnl": 3654.80, "status": "Activo / Rehabilitado (+36.5% PnL / PF 1.88)" },
    { "symbol": "XAUUSD (Oro ICT)", "strategy": "ICT Sabri Malle", "category": "Metales", "trades": 62, "win_rate": 41.9, "tp1": 26, "tp2": 12, "tp3": 12, "tp4": 12, "be": 11, "pnl": 1900.00, "status": "Activo / M15/M5 FVG CE (PF 1.58)" },
    { "symbol": "US Tech 100 (ICT)", "strategy": "ICT Sabri Malle", "category": "Índices Bursátiles", "trades": 6, "win_rate": 50.0, "tp1": 3, "tp2": 3, "tp3": 3, "tp4": 3, "be": 0, "pnl": 600.00, "status": "Activo / Priorizado (+6.0R)" },
    { "symbol": "USDCHF (ICT Forex)", "strategy": "ICT Sabri Malle", "category": "Forex Core", "trades": 21, "win_rate": 42.9, "tp1": 9, "tp2": 3, "tp3": 3, "tp4": 3, "be": 6, "pnl": 300.00, "status": "Activo / Priorizado (+3.0R)" },
    { "symbol": "AUDUSD (ICT Forex)", "strategy": "ICT Sabri Malle", "category": "Forex Core", "trades": 14, "win_rate": 42.9, "tp1": 6, "tp2": 2, "tp3": 2, "tp4": 2, "be": 4, "pnl": 200.00, "status": "Activo / Priorizado (+2.0R)" },
    { "symbol": "US SP 500 (ICT)", "strategy": "ICT Sabri Malle", "category": "Índices Bursátiles", "trades": 15, "win_rate": 40.0, "tp1": 6, "tp2": 2, "tp3": 2, "tp4": 2, "be": 4, "pnl": 100.00, "status": "Activo / Priorizado (+1.0R)" }
]

gold_winners = [
    { "symbol": "XAGUSD (Plata Cuartos)", "strategy": "Gold Quarters", "category": "Metales", "trades": 170, "win_rate": 41.8, "tp1": 71, "tp2": 34, "tp3": 0, "tp4": 0, "be": 32, "pnl": 986.12, "status": "Activo / Priorizado (+9.86% Retorno)" },
    { "symbol": "XAUUSD (Oro Cuartos)", "strategy": "Gold Quarters", "category": "Metales", "trades": 656, "win_rate": 41.3, "tp1": 271, "tp2": 131, "tp3": 0, "tp4": 0, "be": 124, "pnl": 252.76, "status": "Activo / Priorizado (Nivel Cuartos $25/$50)" }
]

other_losers = [
    { "symbol": "US Oil (Petróleo WTI ORB)", "strategy": "ORB New York", "trades": 245, "win_rate": 42.4, "sl_hits": 141, "pnl": -4286.88, "reason": "Deslizamiento severo en sesión NY cash y spread adverso (-42.87R). Podado en ORB." },
    { "symbol": "UK Brent Oil", "strategy": "ORB New York", "trades": 282, "win_rate": 45.4, "sl_hits": 154, "pnl": -4223.33, "reason": "Falsas rupturas en los primeros 15 min de sesión NY cash (-42.23R). Podado en ORB." },
    { "symbol": "Jump 50 Index (ICT)", "strategy": "ICT Sabri Malle", "trades": 20, "win_rate": 15.0, "sl_hits": 17, "pnl": -958.95, "reason": "Ruido lateral severo y gaps adversos en temporalidades H1 (-9.6R). Podado en ICT." },
    { "symbol": "USDJPY (ICT)", "strategy": "ICT Sabri Malle", "trades": 11, "win_rate": 18.2, "sl_hits": 9, "pnl": -700.00, "reason": "Ausencia de expansión hacia TP2 y dilatación de spread (-7.0R). Podado en ICT." },
    { "symbol": "GBPUSD (ICT v1 sin Killzones)", "strategy": "ICT Sabri Malle", "trades": 15, "win_rate": 21.0, "sl_hits": 12, "pnl": -500.00, "reason": "Superado: La versión v1 sin Killzones fallaba por operar fuera de sesión. Con la v2 (Killzones Londres/NY) se rehabilitó con 49.4% WR y +$3,654.80 USD." }
]

# Build total WINNERS_DATA with updated sequential rank
all_winners = []
curr_rank = 1
for w in msnr_winners:
    w['rank'] = curr_rank
    all_winners.append(w)
    curr_rank += 1

for w in orb_winners:
    w['rank'] = curr_rank
    all_winners.append(w)
    curr_rank += 1

for w in ict_winners:
    w['rank'] = curr_rank
    all_winners.append(w)
    curr_rank += 1

for w in gold_winners:
    w['rank'] = curr_rank
    all_winners.append(w)
    curr_rank += 1

# Total LOSERS_DATA
all_losers = msnr_losers + other_losers

# Generate JS code for WINNERS_DATA
winners_lines = ["      const WINNERS_DATA = ["]
winners_lines.append("        // MALAYSIAN SNR INSTITUCIONAL - REPLAY 2 AÑOS AUDITADO (60 ACTIVOS EVALUADOS: 23 ACTIVOS RENTABLES)")
for w in msnr_winners:
    winners_lines.append(f"        {{ rank: {w['rank']}, symbol: \"{w['symbol']}\", strategy: \"{w['strategy']}\", category: \"{w['category']}\", trades: {w['trades']}, win_rate: {w['win_rate']}, tp1: {w['tp1']}, tp2: {w['tp2']}, tp3: {w['tp3']}, tp4: {w['tp4']}, be: {w['be']}, pnl: {w['pnl']}, status: \"{w['status']}\" }},")

winners_lines.append("        // ORB NEW YORK - UNIVERSO AUDITADO")
for w in orb_winners:
    winners_lines.append(f"        {{ rank: {w['rank']}, symbol: \"{w['symbol']}\", strategy: \"{w['strategy']}\", category: \"{w['category']}\", trades: {w['trades']}, win_rate: {w['win_rate']}, tp1: {w['tp1']}, tp2: {w['tp2']}, tp3: {w['tp3']}, tp4: {w['tp4']}, be: {w['be']}, pnl: {w['pnl']}, status: \"{w['status']}\" }},")

winners_lines.append("        // ICT SABRI MALLE - UNIVERSO COMPLETO AUDITADO (2 AÑOS: +196.9 R / +$19,690 USD)")
for w in ict_winners:
    winners_lines.append(f"        {{ rank: {w['rank']}, symbol: \"{w['symbol']}\", strategy: \"{w['strategy']}\", category: \"{w['category']}\", trades: {w['trades']}, win_rate: {w['win_rate']}, tp1: {w['tp1']}, tp2: {w['tp2']}, tp3: {w['tp3']}, tp4: {w['tp4']}, be: {w['be']}, pnl: {w['pnl']}, status: \"{w['status']}\" }},")

winners_lines.append("        // GOLD QUARTERS (ESTRATEGIA DE CUARTOS - WORKER GOLD)")
for idx, w in enumerate(gold_winners):
    comma = "," if idx < len(gold_winners) - 1 else ""
    winners_lines.append(f"        {{ rank: {w['rank']}, symbol: \"{w['symbol']}\", strategy: \"{w['strategy']}\", category: \"{w['category']}\", trades: {w['trades']}, win_rate: {w['win_rate']}, tp1: {w['tp1']}, tp2: {w['tp2']}, tp3: {w['tp3']}, tp4: {w['tp4']}, be: {w['be']}, pnl: {w['pnl']}, status: \"{w['status']}\" }}{comma}")
winners_lines.append("      ];")
winners_block = "\n".join(winners_lines)

# Generate JS code for LOSERS_DATA
losers_lines = ["      const LOSERS_DATA = ["]
losers_lines.append("        // MALAYSIAN SNR - 37 ACTIVOS PODADOS (REPLAY 2 AÑOS / EXPECTATIVA NEGATIVA)")
for l in msnr_losers:
    losers_lines.append(f"        {{ symbol: \"{l['symbol']}\", strategy: \"{l['strategy']}\", trades: {l['trades']}, win_rate: {l['win_rate']}, sl_hits: {l['sl_hits']}, pnl: {l['pnl']}, reason: \"{l['reason']}\" }},")

losers_lines.append("        // OTRAS ESTRATEGIAS PODADAS")
for idx, l in enumerate(other_losers):
    comma = "," if idx < len(other_losers) - 1 else ""
    losers_lines.append(f"        {{ symbol: \"{l['symbol']}\", strategy: \"{l['strategy']}\", trades: {l['trades']}, win_rate: {l['win_rate']}, sl_hits: {l['sl_hits']}, pnl: {l['pnl']}, reason: \"{l['reason']}\" }}{comma}")
losers_lines.append("      ];")
losers_block = "\n".join(losers_lines)

# Generate updated STRATEGY_METRICS
metrics_block = """      // Métricas por pestaña
      const STRATEGY_METRICS = {
        all: {
          total_trades: "2,287",
          tp1: "1,054",
          tp1_rate: "46.1% global / 53.6% en Activos Core",
          tp2: "535",
          tp2_rate: "23.4% de expansiones completadas",
          tp3: "180",
          tp4: "129",
          be: "458",
          sl: "1,223",
          profit: "+$33,998",
          badge: "Consolidado 4 Estrategias",
          bars: { tp1: 46.1, tp2: 23.4, tp3: 7.9, tp4: 5.6, be: 20.0, sl: 53.5 }
        },
        malaysian: {
          total_trades: "357 activos / 987 evaluados",
          tp1: "156",
          tp1_rate: "43.7% ponderado en 23 Activos Validados",
          tp2: "88",
          tp2_rate: "24.6% expansiones completadas",
          tp3: "44",
          tp4: "22",
          be: "36",
          sl: "201",
          profit: "+81.55 R (+$8,155 USD en Activos Validados)",
          badge: "Malaysian SNR Augmented v2 (60 Activos Replay: 23 Activos / 37 Podados)",
          bars: { tp1: 43.7, tp2: 24.6, tp3: 12.3, tp4: 6.2, be: 10.1, sl: 56.3 }
        },
        orb: {
          total_trades: "878",
          tp1: "446",
          tp1_rate: "50.8% acierto en rango 1:1.0",
          tp2: "209",
          tp2_rate: "23.8% full wins (2:1.0 RR)",
          tp3: "0",
          tp4: "0",
          be: "231",
          sl: "429",
          profit: "+$5,900 (+29.9% s/Oil)",
          badge: "ORB New York",
          bars: { tp1: 50.8, tp2: 23.8, tp3: 0.0, tp4: 0.0, be: 26.3, sl: 48.9 }
        },
        ict: {
          total_trades: "396",
          tp1: "181",
          tp1_rate: "45.7% acierto en TP1 (1:2.0 RR)",
          tp2: "107",
          tp2_rate: "27.0% acierto en TP2 (1:4.0 RR)",
          tp3: "136",
          tp4: "107",
          be: "67",
          sl: "208",
          profit: "+196.9 R (+$19,690 USD)",
          badge: "ICT Sabri Malle (AMD & FVG)",
          bars: { tp1: 45.7, tp2: 34.3, tp3: 34.3, tp4: 27.0, be: 16.9, sl: 52.5 }
        },
        gold: {
          total_trades: "656",
          tp1: "271",
          tp1_rate: "41.3% acierto en primer cuarto",
          tp2: "131",
          tp2_rate: "19.9% acierto en extensión",
          tp3: "0",
          tp4: "0",
          be: "124",
          sl: "385",
          profit: "+$252.76 USD",
          badge: "Gold Quarters (Cuartos XAUUSD)",
          bars: { tp1: 41.3, tp2: 19.9, tp3: 0.0, tp4: 0.0, be: 18.9, sl: 58.7 }
        }
      };"""

# Replace in content using regex pattern matching the datasets and metrics block
pattern = re.compile(
    r"      const WINNERS_DATA = \[.*?\];\s*const LOSERS_DATA = \[.*?\];\s*// Métricas por pestaña\s*const STRATEGY_METRICS = \{.*?\};",
    re.DOTALL
)

new_replacement = f"{winners_block}\n\n{losers_block}\n\n{metrics_block}"

assert pattern.search(content) is not None, "Failed to match existing WINNERS_DATA / LOSERS_DATA block!"
new_content = pattern.sub(new_replacement, content, count=1)

# Also update section 5 file description
old_sec5 = "• <strong>Malaysian SNR 2 Años:</strong> <code>storage/analysis/replay_malaysian_snr_2y_summary.csv</code> (60 activos, 207,520 trades)."
new_sec5 = "• <strong>Malaysian SNR 2 Años:</strong> <code>storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv</code> (60 activos auditados bar-a-bar: 23 validados / 37 podados)."
new_content = new_content.replace(old_sec5, new_sec5)

with open("dashboard/strategy_bases_page.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("dashboard/strategy_bases_page.py successfully updated!")
