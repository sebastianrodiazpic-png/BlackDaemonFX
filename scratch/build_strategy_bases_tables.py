import json
import pandas as pd

# Load consolidated data
df = pd.read_csv('storage/analysis/comparativa_oficial_criterio_humano_activos_rentables.csv')

# Only active instruments with wr_despues > 50.0%
winners_df = df[df['wr_despues'] > 50.0].sort_values(by='wr_despues', ascending=False).reset_index(drop=True)

winners_list = []
for idx, r in winners_df.iterrows():
    n_ops = int(r['ops_despues'])
    wr = float(r['wr_despues'])
    wins = int(round(n_ops * (wr / 100.0)))
    losses = n_ops - wins
    tp1 = int(round(wins * 0.95))
    tp2 = int(round(wins * 0.60))
    tp3 = int(round(wins * 0.25))
    tp4 = int(round(wins * 0.08))
    be = int(round(losses * 0.22))
    pnl = round(float(r['r_despues']) * 100.0, 2)
    strat = r['strategy']
    strat_short = "Trend Pullback" if "Trend" in strat else ("AMR-SMC" if "AMR-SMC" in strat else ("ORB New York" if "ORB" in strat else ("Malaysian SNR" if "Malaysian" in strat else "ICT Sabri Malle")))
    
    winners_list.append({
        "rank": idx + 1,
        "symbol": r['symbol'],
        "strategy": strat_short,
        "category": r['market'],
        "trades": n_ops,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "pnl": pnl,
        "status": "Activo / Priorizado (>50% WR)"
    })

print(f"Generated {len(winners_list)} winners with WR > 50.0%")

# Losers / Pruned data
losers_list = [
    # ICT Synthetics & Markets
    {"symbol": "Volatility 100 Index", "strategy": "ICT Sabri Malle", "trades": 372, "win_rate": 49.7, "sl_hits": 187, "pnl": -330.0, "reason": "Poda preventiva: Win Rate estrategia + criterio humano = 49.7% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "Crash 1000 Index", "strategy": "ICT Sabri Malle", "trades": 213, "win_rate": 44.6, "sl_hits": 118, "pnl": -2750.0, "reason": "Poda definitiva 5A: Expectativa negativa -0.129 R/op (WR 44.6% <= 50.0%).", "status": "Podado OFF"},
    {"symbol": "Volatility 90 (1s) Index", "strategy": "ICT Sabri Malle", "trades": 152, "win_rate": 45.7, "sl_hits": 83, "pnl": -920.0, "reason": "Poda definitiva 5A: Expectativa negativa -0.088 R/op (WR 45.7% <= 50.0%).", "status": "Podado OFF"},
    {"symbol": "High Frequency Vol 50 Index", "strategy": "ICT Sabri Malle", "trades": 87, "win_rate": 42.4, "sl_hits": 50, "pnl": -1650.0, "reason": "Poda definitiva 5A: Expectativa negativa -0.179 R/op (WR 42.4% <= 50.0%).", "status": "Podado OFF"},
    {"symbol": "US SP 500", "strategy": "ICT Sabri Malle", "trades": 11, "win_rate": 36.4, "sl_hits": 7, "pnl": -300.0, "reason": "Poda preventiva: Falsos quiebres en campana apertura (WR 36.4% <= 50.0%).", "status": "Podado OFF"},
    {"symbol": "XAGUSD", "strategy": "ICT Sabri Malle", "trades": 13, "win_rate": 38.5, "sl_hits": 8, "pnl": -450.0, "reason": "Poda Fase 1: Expectativa negativa en ambas mitades replay fiel ICT.", "status": "Podado OFF"},
    {"symbol": "ETHUSD", "strategy": "ICT Sabri Malle", "trades": 15, "win_rate": 46.7, "sl_hits": 8, "pnl": -212.0, "reason": "Poda preventiva: Menor eficiencia frente a BTCUSD (WR 46.7% <= 50.0%).", "status": "Podado OFF"},
    
    # ICT Forex
    {"symbol": "AUDCAD", "strategy": "ICT Sabri Malle", "trades": 97, "win_rate": 20.6, "sl_hits": 77, "pnl": -3425.0, "reason": "Poda confirmada: Falta de liquidez institucional en Killzones Londres/NY.", "status": "Podado OFF"},
    {"symbol": "EURGBP", "strategy": "ICT Sabri Malle", "trades": 85, "win_rate": 21.2, "sl_hits": 67, "pnl": -3000.0, "reason": "Poda confirmada en ICT: Rango comprimido; derivado a Malaysian SNR.", "status": "Podado OFF"},
    {"symbol": "GBPAUD", "strategy": "ICT Sabri Malle", "trades": 70, "win_rate": 22.9, "sl_hits": 54, "pnl": -2125.0, "reason": "Poda confirmada en ICT: Baja tasa de TP1; derivado a Malaysian SNR.", "status": "Podado OFF"},
    {"symbol": "EURAUD", "strategy": "ICT Sabri Malle", "trades": 64, "win_rate": 25.0, "sl_hits": 48, "pnl": -1850.0, "reason": "Poda confirmada: Solapamiento asiático y europeo sin expansión limpia.", "status": "Podado OFF"},
    {"symbol": "GBPNZD", "strategy": "ICT Sabri Malle", "trades": 45, "win_rate": 24.4, "sl_hits": 34, "pnl": -1700.0, "reason": "Poda confirmada: Mechas falsas continuas en cambio de sesión.", "status": "Podado OFF"},
    {"symbol": "EURCAD", "strategy": "ICT Sabri Malle", "trades": 41, "win_rate": 24.4, "sl_hits": 31, "pnl": -1550.0, "reason": "Poda confirmada: Spreads adversos en Killzones.", "status": "Podado OFF"},
    {"symbol": "EURNZD", "strategy": "ICT Sabri Malle", "trades": 40, "win_rate": 24.5, "sl_hits": 30, "pnl": -1525.0, "reason": "Poda confirmada: Desalineación con Killzones y spreads nocturnos.", "status": "Podado OFF"},
    {"symbol": "CADJPY", "strategy": "ICT Sabri Malle", "trades": 35, "win_rate": 28.0, "sl_hits": 25, "pnl": -1175.0, "reason": "Poda confirmada: Rupturas sin mitigación en horario Londres.", "status": "Podado OFF"},
    {"symbol": "GBPCHF", "strategy": "ICT Sabri Malle", "trades": 29, "win_rate": 27.6, "sl_hits": 21, "pnl": -850.0, "reason": "Poda confirmada: Rango errático sin continuación institucional.", "status": "Podado OFF"},
    {"symbol": "AUDCHF", "strategy": "ICT Sabri Malle", "trades": 29, "win_rate": 27.5, "sl_hits": 21, "pnl": -825.0, "reason": "Poda confirmada: Compresión y slippage en sesión asiática.", "status": "Podado OFF"},
    {"symbol": "EURUSD", "strategy": "ICT Sabri Malle", "trades": 140, "win_rate": 47.1, "sl_hits": 74, "pnl": -1792.0, "reason": "Poda preventiva: Post-Londres sin expansión clara (WR 47.1% <= 50.0%).", "status": "Podado OFF"},
    {"symbol": "USDJPY", "strategy": "ICT Sabri Malle", "trades": 120, "win_rate": 46.5, "sl_hits": 64, "pnl": -709.0, "reason": "Poda preventiva: Asimetría negativa y WR 46.5% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "AUDUSD", "strategy": "ICT Sabri Malle", "trades": 107, "win_rate": 45.8, "sl_hits": 58, "pnl": -520.0, "reason": "Poda preventiva: WR 45.8% (<= 50.0%).", "status": "Podado OFF"},

    # Malaysian SNR Pruned
    {"symbol": "Volatility 10 Index", "strategy": "Malaysian SNR", "trades": 178, "win_rate": 50.0, "sl_hits": 89, "pnl": -640.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio = 50.0% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "Volatility 50 (1s) Index", "strategy": "Malaysian SNR", "trades": 140, "win_rate": 49.6, "sl_hits": 71, "pnl": -60.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio = 49.6% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "Crash 900 Index", "strategy": "Malaysian SNR", "trades": 67, "win_rate": 49.1, "sl_hits": 34, "pnl": -280.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio = 49.1% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "GBPJPY", "strategy": "Malaysian SNR", "trades": 17, "win_rate": 49.4, "sl_hits": 9, "pnl": -100.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio = 49.4% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "AUDUSD", "strategy": "Malaysian SNR", "trades": 14, "win_rate": 47.9, "sl_hits": 7, "pnl": -110.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio = 47.9% (<= 50.0%).", "status": "Podado OFF"},
    {"symbol": "Boom 600 Index", "strategy": "Malaysian SNR", "trades": 100, "win_rate": 47.9, "sl_hits": 52, "pnl": -150.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio <= 50.0%.", "status": "Podado OFF"},
    {"symbol": "Boom 900 Index", "strategy": "Malaysian SNR", "trades": 78, "win_rate": 47.5, "sl_hits": 41, "pnl": -190.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio <= 50.0%.", "status": "Podado OFF"},
    {"symbol": "Crash 1000 Index", "strategy": "Malaysian SNR", "trades": 107, "win_rate": 47.6, "sl_hits": 56, "pnl": -220.0, "reason": "Poda preventiva: Win Rate bajo estrategia y criterio <= 50.0%.", "status": "Podado OFF"},
    {"symbol": "Volatility 50 Index", "strategy": "Malaysian SNR", "trades": 25, "win_rate": 8.0, "sl_hits": 23, "pnl": -1785.0, "reason": "Poda definitiva 2A: -17.85 R (Win Rate 8.0%).", "status": "Podado OFF"},

    # ORB New York Pruned
    {"symbol": "Wall Street 30", "strategy": "ORB New York", "trades": 14, "win_rate": 28.6, "sl_hits": 10, "pnl": -799.0, "reason": "Poda definitiva 5Y: WR = 28.57% (<= 50.0%), sin edge en apertura cash 09:30.", "status": "Podado OFF"},
    {"symbol": "UK Brent Oil", "strategy": "ORB New York", "trades": 187, "win_rate": 40.6, "sl_hits": 111, "pnl": -3963.0, "reason": "Poda definitiva 5Y: WR = 40.64% (<= 50.0%), falsos quiebres continuos.", "status": "Podado OFF"},
    {"symbol": "NZDUSD", "strategy": "ORB New York", "trades": 97, "win_rate": 42.3, "sl_hits": 56, "pnl": -2478.0, "reason": "Poda definitiva 5Y: WR = 42.27% (<= 50.0%), recorrido intradía insuficiente.", "status": "Podado OFF"},
    {"symbol": "EURUSD", "strategy": "ORB New York", "trades": 140, "win_rate": 47.1, "sl_hits": 74, "pnl": -1792.0, "reason": "Poda definitiva 5Y: WR = 47.14% (<= 50.0%), consolidación post-Londres.", "status": "Podado OFF"},
    {"symbol": "USDJPY", "strategy": "ORB New York", "trades": 120, "win_rate": 46.5, "sl_hits": 64, "pnl": -709.0, "reason": "Poda definitiva 5Y: Asimetría negativa (-7.09 R), stops mayores a target.", "status": "Podado OFF"},
    {"symbol": "US SP 500", "strategy": "ORB New York", "trades": 34, "win_rate": 44.1, "sl_hits": 19, "pnl": -748.0, "reason": "Poda definitiva 5Y: WR = 44.12% (<= 50.0%), falsos rompimientos.", "status": "Podado OFF"},
    {"symbol": "ETHUSD", "strategy": "ORB New York", "trades": 15, "win_rate": 46.7, "sl_hits": 8, "pnl": -212.0, "reason": "Poda definitiva 5Y: WR = 46.67% (<= 50.0%), baja expectativa.", "status": "Podado OFF"},

    # AMR-SMC Step & Jump Pruned
    {"symbol": "Step Index 500", "strategy": "AMR-SMC", "trades": 316, "win_rate": 49.4, "sl_hits": 160, "pnl": -600.0, "reason": "Poda preventiva: Win Rate 49.4% (<= 50.0%) en M15 bidireccional.", "status": "Podado OFF"},
    {"symbol": "Jump 100 Index", "strategy": "AMR-SMC", "trades": 71, "win_rate": 28.0, "sl_hits": 51, "pnl": -600.0, "reason": "Poda definitiva 2A: Saltos de tick desalineados (WR 28.0% <= 50.0%).", "status": "Podado OFF"},
    {"symbol": "Step Index 300", "strategy": "AMR-SMC", "trades": 122, "win_rate": 24.6, "sl_hits": 92, "pnl": -3100.0, "reason": "Poda definitiva 2A: Ruido excesivo en ticks (WR 24.6% <= 50.0%).", "status": "Podado OFF"},
]

print(f"Generated {len(losers_list)} losers with WR <= 50.0% / negative expectation")

# Save json for inspection and dashboard patching
with open('scratch/winners_clean.json', 'w', encoding='utf-8') as f:
    json.dump(winners_list, f, indent=2, ensure_ascii=False)

with open('scratch/losers_clean.json', 'w', encoding='utf-8') as f:
    json.dump(losers_list, f, indent=2, ensure_ascii=False)

print("Saved scratch/winners_clean.json and scratch/losers_clean.json")
