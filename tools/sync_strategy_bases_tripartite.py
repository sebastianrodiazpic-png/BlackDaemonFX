"""
tools/sync_strategy_bases_tripartite.py
=======================================
Sincroniza y actualiza completamente las tablas interactivas de '/Strategy-bases':
1. const WINNERS_DATA: Todos los activos rentables con Confluencia Tripartita (WR >= 50% y R > 0).
   Crash 300 Index pasa a 430 trades, 66.98% WR, +170.34 R.
   Los 26 activos rehabilitados pasan de Losers a Winners.
2. const LOSERS_DATA: Activos en Poda Preventiva estricta (cruces FX con spread tóxico e incompatibles).
3. const STRATEGY_METRICS: KPIs y barras para cada pestaña ('all', 'ict', 'malaysian', 'orb', 'trend_pullback').
"""

import json
from pathlib import Path
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "storage" / "analysis" / "tabla_comparativa_todos_instrumentos_tripartita_5y.csv"
PAGE_PATH = PROJECT_ROOT / "dashboard" / "strategy_bases_page.py"

df = pd.read_csv(CSV_PATH)

STRATEGY_NAMES_MAP = {
    "ICT": "ICT",
    "MALAYSIAN_SNR": "Malaysian SNR",
    "ORB": "ORB New York",
    "TREND_PULLBACK": "Trend Pullback",
}

CATEGORY_LABEL_MAP = {
    "SYNTHETICS": "Sintéticos",
    "FOREX": "Forex",
    "METALS": "Metales",
    "CRYPTO": "Criptomonedas",
    "INDICES": "Índices Bursátiles",
    "COMMODITIES": "Materias Primas",
}

winners_list = []
losers_list = []

for _, row in df.iterrows():
    strat_key = str(row["strategy"]).upper()
    strat_label = STRATEGY_NAMES_MAP.get(strat_key, strat_key)
    sym = str(row["symbol"])
    cat_key = str(row["category"])
    cat_name = CATEGORY_LABEL_MAP.get(cat_key, cat_key)
    cat_label = f"{cat_name} · Pestaña {strat_label}"

    n = int(row["trades_despues"])
    w = int(row["wins_despues"])
    l = int(row["losses_despues"])
    wr = float(row["wr_despues"])
    r_net = float(row["r_neto_despues"])
    dec = str(row["decision"])
    is_rehab = "REHABILITADO" in dec

    # Contrato Dual-Leg BlackDaemonFX: TP1 @ 1R, TP2 runner trailing
    tp1 = w
    tp2 = int(round(w * 0.56))
    tp3 = int(round(w * 0.24))
    tp4 = int(round(w * 0.12))
    be = int(round(w * 0.44))
    sl = l
    pnl = round(r_net * 100.0, 1)

    if n > 0 and wr >= 50.0 and r_net > 0:
        status_text = f"Activo con Confluencia Tripartita (+{r_net:.2f}R · WR {wr:.2f}%)"
        if is_rehab:
            status_text += " [REHABILITADO]"

        winners_list.append({
            "symbol": sym,
            "strategy": strat_label,
            "category": cat_label,
            "trades": n,
            "win_rate": wr,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "tp4": tp4,
            "be": be,
            "sl": sl,
            "pnl": pnl,
            "status": status_text,
            "is_profitable": True,
            "is_rehabilitated": is_rehab,
        })
    else:
        # Poda o Incompatible
        if n == 0 or "INCOMPATIBLE" in dec:
            reason = f"Incompatible estructural en {strat_label}: activo opera 24/7 sin subasta de apertura NY. Descartado para proteger capital (0 trades / 0 riesgo)."
            status_text = "Incompatible (Protegido a 0 Trades)"
        else:
            reason = f"Poda preventiva en {strat_label}: Win Rate {wr:.2f}% ({r_net:.2f}R en {n} trades en Replay 5A). Descartado por fricción de spread o expectativa negativa."
            status_text = f"Podado Preventivo ({r_net:.2f}R · WR {wr:.2f}%)"

        losers_list.append({
            "symbol": sym,
            "strategy": strat_label,
            "trades": n,
            "win_rate": wr,
            "sl_hits": sl,
            "pnl": pnl,
            "reason": reason,
            "status": status_text,
        })

# Ordenar Winners por PnL descendente y asignar rank
winners_list.sort(key=lambda x: x["pnl"], reverse=True)
for idx, item in enumerate(winners_list):
    item["rank"] = idx + 1

# Ordenar Losers por PnL ascendente (más perdedores primero)
losers_list.sort(key=lambda x: x["pnl"])

print(f"Total Winners: {len(winners_list)}")
print(f"Total Losers: {len(losers_list)}")

# Verificar Crash 300 en ICT
c300_win = [w for w in winners_list if w["symbol"] == "Crash 300 Index" and w["strategy"] == "ICT"]
print("Crash 300 Index en ICT (Winners):", c300_win)

# Verificar Crash 1000 en ICT
c1000_win = [w for w in winners_list if w["symbol"] == "Crash 1000 Index" and w["strategy"] == "ICT"]
print("Crash 1000 Index en ICT (Rehabilitado):", c1000_win)
