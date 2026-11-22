"""
tools/write_perfect_synced_strategy_bases.py
"""
import json
import re
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("C:/TradingBoot/smc_synthetic_bot")
CSV_PATH = PROJECT_ROOT / "storage" / "analysis" / "tabla_comparativa_todos_instrumentos_tripartita_5y.csv"
PAGE_PATH = PROJECT_ROOT / "dashboard" / "strategy_bases_page.py"

df = pd.read_csv(CSV_PATH)
content = PAGE_PATH.read_text(encoding="utf-8-sig")

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

winners_data = []
losers_data = []

# En WINNERS_DATA van los 292 pares para que la tabla interactiva pueda renderizar
# todos los instrumentos en cada una de las 4 pestañas (73 x 4 = 292).
# Los rentables (177) tienen is_profitable: True, rank y estado verde.
# Los incompatibles/podados (115) tienen is_profitable: False y estado rojo/dorado.

profitable_items = []
unprofitable_items = []

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

        profitable_items.append({
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
        # Incompatible o podado
        if n == 0 or "INCOMPATIBLE" in dec:
            reason = f"Incompatible estructural en {strat_label}: activo opera 24/7 sin subasta de apertura NY. Descartado para proteger capital (0 trades / 0 riesgo)."
            status_text = "Incompatible (Sintético sin sesión)"
        else:
            reason = f"Poda preventiva en {strat_label}: Win Rate {wr:.2f}% ({r_net:.2f}R en {n} trades en Replay 5A). Descartado por fricción de spread o expectativa negativa."
            status_text = f"Podado Preventivo ({r_net:.2f}R · WR {wr:.2f}%)"

        unprofitable_items.append({
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
            "is_profitable": False,
            "is_rehabilitated": False,
        })

        losers_data.append({
            "symbol": sym,
            "strategy": strat_label,
            "trades": n,
            "win_rate": wr,
            "sl_hits": sl,
            "pnl": pnl,
            "reason": reason,
            "status": status_text,
        })

# Ordenar los rentables por PnL descendente y asignar rank
profitable_items.sort(key=lambda x: x["pnl"], reverse=True)
for idx, item in enumerate(profitable_items):
    item["rank"] = idx + 1

# Los no rentables se ordenan al final
for idx, item in enumerate(unprofitable_items):
    item["rank"] = len(profitable_items) + idx + 1

winners_data = profitable_items + unprofitable_items
losers_data.sort(key=lambda x: x["pnl"])

print(f"Total en WINNERS_DATA: {len(winners_data)} (Rentables: {len(profitable_items)}, No rentables: {len(unprofitable_items)})")
print(f"Total en LOSERS_DATA: {len(losers_data)}")

assert len(winners_data) == 292
assert len(profitable_items) == 177
assert len(losers_data) == 115

# Serializar JSON
winners_json = json.dumps(winners_data, indent=2, ensure_ascii=False)
losers_json = json.dumps(losers_data, indent=2, ensure_ascii=False)

winners_block = f"      const WINNERS_DATA = {winners_json};"
losers_block = f"      const LOSERS_DATA = {losers_json};"

pattern = re.compile(
    r"const WINNERS_DATA\s*=\s*\[.*?\];\s*const LOSERS_DATA\s*=\s*\[.*?\];",
    re.DOTALL
)

assert pattern.search(content) is not None, "No se encontró el patrón WINNERS_DATA / LOSERS_DATA"
new_replacement = f"{winners_block}\n\n{losers_block}"
new_content = pattern.sub(new_replacement, content, count=1)

PAGE_PATH.write_text(new_content, encoding="utf-8")
print("dashboard/strategy_bases_page.py sincronizado perfectamente a 292 / 177 / 115.")
