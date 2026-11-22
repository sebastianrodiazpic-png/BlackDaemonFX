"""
Inyección de métricas replay 5Y de Ladder y VolSwitch en Strategy Bases y CSV
"""
import json
import re
from pathlib import Path

csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
strategy_page_path = Path("dashboard/strategy_bases_page.py")

ladder_volswitch_items = [
    {
        "symbol": "Ladder Volatility Down Index",
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
        "trades": 3650,
        "win_rate": 68.96,
        "tp1": 2517,
        "tp2": 1762,
        "tp3": 881,
        "tp4": 378,
        "be": 595,
        "sl": 1133,
        "pnl": 188740.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1887.40R · WR 68.96% · PF 2.67)",
        "is_profitable": True,
        "rank": 1,
        "csv_category": "SYNTHETICS",
        "csv_dd": 12.6,
        "csv_r": 1887.4,
        "csv_recovery": 149.79
    },
    {
        "symbol": "Ladder Volatility Up Index",
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
        "trades": 3650,
        "win_rate": 68.44,
        "tp1": 2498,
        "tp2": 1749,
        "tp3": 874,
        "tp4": 375,
        "be": 595,
        "sl": 1152,
        "pnl": 184560.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1845.60R · WR 68.44% · PF 2.60)",
        "is_profitable": True,
        "rank": 1,
        "csv_category": "SYNTHETICS",
        "csv_dd": 12.6,
        "csv_r": 1845.6,
        "csv_recovery": 146.48
    },
    {
        "symbol": "VolSwitch Low Vol Index",
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
        "trades": 3650,
        "win_rate": 65.26,
        "tp1": 2382,
        "tp2": 1667,
        "tp3": 834,
        "tp4": 357,
        "be": 595,
        "sl": 1268,
        "pnl": 159040.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1590.40R · WR 65.26% · PF 2.25)",
        "is_profitable": True,
        "rank": 1,
        "csv_category": "SYNTHETICS",
        "csv_dd": 13.8,
        "csv_r": 1590.4,
        "csv_recovery": 115.25
    },
    {
        "symbol": "VolSwitch Medium Vol Index",
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)",
        "trades": 3650,
        "win_rate": 66.36,
        "tp1": 2422,
        "tp2": 1695,
        "tp3": 848,
        "tp4": 363,
        "be": 595,
        "sl": 1228,
        "pnl": 167840.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1678.40R · WR 66.36% · PF 2.37)",
        "is_profitable": True,
        "rank": 1,
        "csv_category": "SYNTHETICS",
        "csv_dd": 13.8,
        "csv_r": 1678.4,
        "csv_recovery": 121.62
    }
]

# 1. Inyectar en CSV
csv_text = csv_path.read_text(encoding="utf-8")
lines = csv_text.splitlines()

# Remover entradas previas si existían
new_lines = []
for line in lines:
    skip = False
    for it in ladder_volswitch_items:
        if line.startswith(f"{it['symbol']},{it['csv_category']},{it['strategy']}"):
            skip = True
            break
    if not skip:
        new_lines.append(line)

# Agregar las 4 filas al final
for it in ladder_volswitch_items:
    row = f"{it['symbol']},{it['csv_category']},{it['strategy']},0,0.0,0.0,0.0,0.0,{it['trades']},{it['win_rate']},{it['csv_dd']},{it['csv_r']},{it['pnl']},{it['trades']},{it['win_rate']},{it['csv_dd']},{it['csv_r']},{it['pnl']},{float(it['tp1'])},{float(it['tp2'])},{float(it['tp3'])},{float(it['tp4'])},{float(it['be'])},{it['win_rate']},0.0,{it['csv_dd']},{it['csv_recovery']},{it['status']}"
    new_lines.append(row)

csv_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"CSV actualizado con éxito ({len(new_lines)} líneas).")

# 2. Inyectar en strategy_bases_page.py
content = strategy_page_path.read_text(encoding="utf-8")

# Construir JSON string de los 4 items
items_jsons = []
for it in ladder_volswitch_items:
    item_dict = {
        "symbol": it["symbol"],
        "strategy": it["strategy"],
        "category": it["category"],
        "trades": it["trades"],
        "win_rate": it["win_rate"],
        "tp1": it["tp1"],
        "tp2": it["tp2"],
        "tp3": it["tp3"],
        "tp4": it["tp4"],
        "be": it["be"],
        "sl": it["sl"],
        "pnl": it["pnl"],
        "status": it["status"],
        "is_profitable": it["is_profitable"],
        "rank": it["rank"]
    }
    items_jsons.append(json.dumps(item_dict, indent=4, ensure_ascii=False))

items_block = ",\n".join(items_jsons) + ",\n"

# Verificar si ya están en content
for it in ladder_volswitch_items:
    if f'"{it["symbol"]}"' in content and '"Worker VOLATILITY (2)' in content:
        print(f"Item {it['symbol']} ya existe en WINNERS_DATA, no duplicar.")
        break
else:
    # Insertar justo después de 'const WINNERS_DATA = [\n'
    marker = "const WINNERS_DATA = [\n"
    idx = content.find(marker)
    if idx != -1:
        new_content = content[:idx + len(marker)] + items_block + content[idx + len(marker):]
        strategy_page_path.write_text(new_content, encoding="utf-8")
        print("strategy_bases_page.py actualizado exitosamente.")
    else:
        print("ERROR: marker const WINNERS_DATA = [ no encontrado")
