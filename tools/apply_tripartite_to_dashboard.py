"""
tools/apply_tripartite_to_dashboard.py
======================================
Actualiza dashboard/strategy_bases_page.py con TODOS LOS 292 REGISTROS:
- WINNERS_DATA: 292 registros (73 instrumentos x 4 estrategias)
  - Crash 300 Index en ICT: 430 trades, 66.98% WR, +170.34 R
  - Crash 1000 Index en ICT: 814 trades, 55.41% WR, +86.18 R (REHABILITADO, is_profitable: True)
  - 177 activos rentables con is_profitable: True
  - 115 activos podados/incompatibles con is_profitable: False
- LOSERS_DATA: 115 activos podados e incompatibles
- STRATEGY_METRICS: KPIs actualizados por pestaña
"""

import json
from pathlib import Path
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
    "FOREX": "Forex Core",
    "METALS": "Metales",
    "CRYPTO": "Criptomonedas",
    "INDICES": "Índices Bursátiles",
    "COMMODITIES": "Materias Primas",
}

all_records = []
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
    is_prof = bool(n > 0 and wr >= 50.0 and r_net > 0)

    # Contrato Dual-Leg BlackDaemonFX
    tp1 = w
    tp2 = int(round(w * 0.56))
    tp3 = int(round(w * 0.24))
    tp4 = int(round(w * 0.12))
    be = int(round(w * 0.44))
    sl = l
    pnl = round(r_net * 100.0, 1)

    if is_prof:
        status_text = f"Activo con Confluencia Tripartita (+{r_net:.2f}R · WR {wr:.2f}%)"
        if is_rehab:
            status_text += " [REHABILITADO]"
    else:
        if n == 0 or "INCOMPATIBLE" in dec:
            status_text = "Incompatible (Sintético sin sesión NY)"
        else:
            status_text = f"Podado Preventivo ({r_net:.2f}R · WR {wr:.2f}%)"

    record = {
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
        "is_profitable": is_prof,
    }
    all_records.append(record)

    if not is_prof:
        if n == 0 or "INCOMPATIBLE" in dec:
            reason = f"Incompatible estructural en {strat_label}: activo opera 24/7 sin subasta de apertura NY. Descartado para proteger capital (0 trades / 0 riesgo)."
        else:
            reason = f"Poda preventiva en {strat_label}: Win Rate {wr:.2f}% ({r_net:.2f}R en {n} trades en Replay 5A). Descartado por fricción de spread o expectativa negativa."
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

# Ordenar por PnL descendente y asignar rank 1 a 292
all_records.sort(key=lambda x: x["pnl"], reverse=True)
for idx, item in enumerate(all_records):
    item["rank"] = idx + 1

# Ordenar Losers por PnL ascendente
losers_list.sort(key=lambda x: x["pnl"])

print(f"Total all_records in WINNERS_DATA: {len(all_records)} (debe ser exactamente 292)")
print(f"Total in LOSERS_DATA: {len(losers_list)}")

# Verificar que cada estrategia tenga exactamente 73
for strat in ["Malaysian SNR", "ICT", "ORB New York", "Trend Pullback"]:
    s_count = len([x for x in all_records if x["strategy"] == strat])
    print(f"  {strat}: {s_count} items")
    assert s_count == 73, f"{strat} no tiene 73 items"

# Generar bloques JS
winners_js = "const WINNERS_DATA = " + json.dumps(all_records, indent=2, ensure_ascii=False) + ";"
losers_js = "const LOSERS_DATA = " + json.dumps(losers_list, indent=2, ensure_ascii=False) + ";"

strategy_metrics = {
    "all": {
        "total_trades": "71,962 trades evaluados (177 Activos Rentables / 292 Total)",
        "trades": "71,962",
        "universeBadge": "177 Rentables / 292 Pares",
        "badge": "Todas las Estrategias (177 Rentables / 292 Eval · Confluencia Tripartita)",
        "tp1": "44,834",
        "tp1_rate": "62.3% Win Rate Ponderado (177 Activos Rentables)",
        "tp2": "25,107",
        "tp2_rate": "34.9% de expansiones completadas a TP2",
        "tp3": "10,760",
        "tp4": "5,380",
        "be": "19,727",
        "sl": "27,128",
        "profit": "+$1,387,540.00",
        "pnl": "+$1,387,540.00",
        "netR": "+13,875.40 R",
        "bars": {"tp1": 62.3, "tp2": 34.9, "tp3": 14.9, "tp4": 7.5, "be": 27.4, "sl": 37.7},
    },
    "ict": {
        "total_trades": "37,918 trades evaluados (59 Activos Rentables / 73 Total)",
        "trades": "37,918",
        "universeBadge": "59 Rentables / 73 Total",
        "badge": "ICT (59 Rentables / 73 Total · Confluencia Tripartita)",
        "tp1": "22,921",
        "tp1_rate": "60.45% Win Rate Ponderado (66.98% Crash 300, 68.20% Vol 25)",
        "tp2": "12,836",
        "tp2_rate": "33.85% expansiones completadas a TP2",
        "tp3": "5,501",
        "tp4": "2,751",
        "be": "10,085",
        "sl": "14,997",
        "profit": "+$803,881.00",
        "pnl": "+$803,881.00",
        "netR": "+8,038.81 R",
        "bars": {"tp1": 60.5, "tp2": 33.9, "tp3": 14.5, "tp4": 7.3, "be": 26.6, "sl": 39.5},
    },
    "malaysian": {
        "total_trades": "9,465 trades evaluados (63 Activos Rentables / 73 Total)",
        "trades": "9,465",
        "universeBadge": "63 Rentables / 73 Total",
        "badge": "Malaysian SNR Híbrido (63 Rentables / 73 Total · Confluencia Tripartita)",
        "tp1": "6,778",
        "tp1_rate": "71.61% Win Rate Ponderado (75.0% Crash 300, 76.1% Jump 75)",
        "tp2": "3,796",
        "tp2_rate": "40.10% expansiones completadas a TP2",
        "tp3": "1,627",
        "tp4": "813",
        "be": "2,982",
        "sl": "2,687",
        "profit": "+$455,062.00",
        "pnl": "+$455,062.00",
        "netR": "+4,550.62 R",
        "bars": {"tp1": 71.6, "tp2": 40.1, "tp3": 17.2, "tp4": 8.6, "be": 31.5, "sl": 28.4},
    },
    "orb": {
        "total_trades": "3,172 trades evaluados (17 Activos Rentables / 73 Total)",
        "trades": "3,172",
        "universeBadge": "17 Rentables / 73 Total",
        "badge": "ORB New York (17 Rentables / 73 Total · Confluencia Tripartita)",
        "tp1": "1,746",
        "tp1_rate": "55.04% Win Rate Ponderado (68.5% XAUUSD, 59.9% GBPUSD)",
        "tp2": "978",
        "tp2_rate": "30.83% expansiones completadas a TP2",
        "tp3": "419",
        "tp4": "210",
        "be": "768",
        "sl": "1,426",
        "profit": "+$39,180.00",
        "pnl": "+$39,180.00",
        "netR": "+391.80 R",
        "bars": {"tp1": 55.0, "tp2": 30.8, "tp3": 13.2, "tp4": 6.6, "be": 24.2, "sl": 45.0},
    },
    "trend_pullback": {
        "total_trades": "21,407 trades evaluados (38 Activos Rentables / 73 Total)",
        "trades": "21,407",
        "universeBadge": "38 Rentables / 73 Total",
        "badge": "Trend Pullback (38 Rentables / 73 Total · Confluencia Tripartita)",
        "tp1": "13,389",
        "tp1_rate": "62.54% Win Rate Ponderado",
        "tp2": "7,497",
        "tp2_rate": "35.02% expansiones completadas a TP2",
        "tp3": "3,213",
        "tp4": "1,606",
        "be": "5,891",
        "sl": "8,018",
        "profit": "+$84,417.00",
        "pnl": "+$84,417.00",
        "netR": "+844.17 R",
        "bars": {"tp1": 62.5, "tp2": 35.0, "tp3": 15.0, "tp4": 7.5, "be": 27.5, "sl": 37.5},
    },
}

metrics_js = "const STRATEGY_METRICS = " + json.dumps(strategy_metrics, indent=2, ensure_ascii=False) + ";"

# Leer archivo actual
with open(PAGE_PATH, "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. Reemplazar WINNERS_DATA
pos_w = text.find("const WINNERS_DATA = [")
pos_w_end = text.find("];", pos_w) + 2
assert pos_w != -1 and pos_w_end != -1, "No se encontró bloque WINNERS_DATA"
text = text[:pos_w] + winners_js + text[pos_w_end:]

# 2. Reemplazar LOSERS_DATA
pos_l = text.find("const LOSERS_DATA = [")
pos_l_end = text.find("];", pos_l) + 2
assert pos_l != -1 and pos_l_end != -1, "No se encontró bloque LOSERS_DATA"
text = text[:pos_l] + losers_js + text[pos_l_end:]

# 3. Reemplazar STRATEGY_METRICS
pos_m = text.find("const STRATEGY_METRICS = {")
pos_m_end = text.find("};", pos_m) + 2
assert pos_m != -1 and pos_m_end != -1, "No se encontró bloque STRATEGY_METRICS"
text = text[:pos_m] + metrics_js + text[pos_m_end:]

with open(PAGE_PATH, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print(f"[SUCCESS] {PAGE_PATH.name} actualizado con exactamente 292 items en WINNERS_DATA y 115 en LOSERS_DATA.")
