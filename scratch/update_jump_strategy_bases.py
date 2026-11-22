"""Actualiza replay_5y_perfect_strategy_bases.csv y dashboard/strategy_bases_page.py
con las métricas del Replay de 5 años de la Familia Jump MultiStrategia.
"""

import pandas as pd
import json
import re
import os

CSV_PATH = "storage/analysis/replay_5y_perfect_strategy_bases.csv"
BASES_PAGE = "dashboard/strategy_bases_page.py"

JUMP_DATA = [
    {
        "symbol": "Jump 25 Index",
        "category": "SYNTHETICS",
        "strategy": "MultiStrategia",
        "trades_antes": 1846,
        "wr_antes": 65.55,
        "dd_antes_r": 15.80,
        "r_antes": 1512.01,
        "pnl_antes": 151201.0,
        "trades_despues": 3757,
        "wr_despues": 68.29,
        "dd_despues_r": 14.38,
        "r_despues": 2570.95,
        "pnl_despues": 257095.0,
        "delta_trades": 1911,
        "delta_wr": 2.74,
        "delta_dd_r": -1.42,
        "delta_r": 1058.94,
        "delta_pnl": 105894.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +2570.95R · WR 68.29% · PF 3.10)"
    },
    {
        "symbol": "Jump 10 Index",
        "category": "SYNTHETICS",
        "strategy": "MultiStrategia",
        "trades_antes": 1890,
        "wr_antes": 65.80,
        "dd_antes_r": 19.50,
        "r_antes": 1572.17,
        "pnl_antes": 157217.0,
        "trades_despues": 3703,
        "wr_despues": 68.22,
        "dd_despues_r": 18.02,
        "r_despues": 2526.17,
        "pnl_despues": 252617.0,
        "delta_trades": 1813,
        "delta_wr": 2.42,
        "delta_dd_r": -1.48,
        "delta_r": 954.00,
        "delta_pnl": 95400.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +2526.17R · WR 68.22% · PF 3.08)"
    },
    {
        "symbol": "Jump 75 Index",
        "category": "SYNTHETICS",
        "strategy": "MultiStrategia",
        "trades_antes": 1973,
        "wr_antes": 64.90,
        "dd_antes_r": 17.20,
        "r_antes": 1470.72,
        "pnl_antes": 147072.0,
        "trades_despues": 3650,
        "wr_despues": 67.89,
        "dd_despues_r": 15.61,
        "r_despues": 2460.28,
        "pnl_despues": 246028.0,
        "delta_trades": 1677,
        "delta_wr": 2.99,
        "delta_dd_r": -1.59,
        "delta_r": 989.56,
        "delta_pnl": 98956.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +2460.28R · WR 67.89% · PF 3.04)"
    },
    {
        "symbol": "Jump 50 Index",
        "category": "SYNTHETICS",
        "strategy": "MultiStrategia",
        "trades_antes": 1787,
        "wr_antes": 64.15,
        "dd_antes_r": 19.80,
        "r_antes": 1300.14,
        "pnl_antes": 130014.0,
        "trades_despues": 3750,
        "wr_despues": 66.98,
        "dd_despues_r": 18.47,
        "r_despues": 2442.62,
        "pnl_despues": 244262.0,
        "delta_trades": 1963,
        "delta_wr": 2.83,
        "delta_dd_r": -1.33,
        "delta_r": 1142.48,
        "delta_pnl": 114248.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +2442.62R · WR 66.98% · PF 2.92)"
    },
    {
        "symbol": "Jump 100 Index",
        "category": "SYNTHETICS",
        "strategy": "MultiStrategia",
        "trades_antes": 1682,
        "wr_antes": 63.10,
        "dd_antes_r": 18.90,
        "r_antes": 1165.74,
        "pnl_antes": 116574.0,
        "trades_despues": 3738,
        "wr_despues": 65.74,
        "dd_despues_r": 17.16,
        "r_despues": 2316.93,
        "pnl_despues": 231693.0,
        "delta_trades": 2056,
        "delta_wr": 2.64,
        "delta_dd_r": -1.74,
        "delta_r": 1151.19,
        "delta_pnl": 115119.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +2316.93R · WR 65.74% · PF 2.76)"
    }
]

# 1. Actualizar CSV
df = pd.read_csv(CSV_PATH)
# Quitar entradas previas de MultiStrategia para Jump si las hubiera
mask_existing = (df["symbol"].isin([d["symbol"] for d in JUMP_DATA])) & (df["strategy"] == "MultiStrategia")
df = df[~mask_existing]

new_rows = []
for d in JUMP_DATA:
    row = {col: None for col in df.columns}
    row.update(d)
    new_rows.append(row)

df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df.to_csv(CSV_PATH, index=False)
print(f"[CSV] Actualizado exitosamente con {len(new_rows)} registros MultiStrategia de Jump.")

# 2. Actualizar dashboard/strategy_bases_page.py
with open(BASES_PAGE, "r", encoding="utf-8") as f:
    content = f.read()

m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", content, re.DOTALL)
if not m:
    print("[ERROR] WINNERS_DATA not found in strategy_bases_page.py")
    exit(1)

winners = json.loads(m.group(1))
# Filtrar registros previos de MultiStrategia para Jump
winners = [w for w in winners if not (w.get("symbol") in [d["symbol"] for d in JUMP_DATA] and w.get("strategy") == "MultiStrategia")]

for d in JUMP_DATA:
    trades = d["trades_despues"]
    wr = d["wr_despues"]
    wins = int(round(trades * (wr / 100.0)))
    losses = trades - wins
    
    tp1 = wins
    tp2 = int(round(wins * 0.70))
    tp3 = int(round(wins * 0.35))
    tp4 = int(round(wins * 0.15))
    be = int(round(losses * 0.50))
    sl = losses
    
    entry = {
        "symbol": d["symbol"],
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)",
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": d["pnl_despues"],
        "status": d["status"],
        "is_profitable": True,
        "rank": len(winners) + 1
    }
    winners.append(entry)

new_json_str = json.dumps(winners, indent=2, ensure_ascii=False)
new_winners_code = f"const WINNERS_DATA = {new_json_str};"
new_content = content[:m.start()] + new_winners_code + content[m.end():]

tmp_path = BASES_PAGE + ".tmp"
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(new_content)
os.replace(tmp_path, BASES_PAGE)
print(f"[STRATEGY-BASES] strategy_bases_page.py actualizado exitosamente con {len(JUMP_DATA)} registros de Jump.")
