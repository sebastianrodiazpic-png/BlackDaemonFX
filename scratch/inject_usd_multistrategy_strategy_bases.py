"""
scratch/inject_usd_multistrategy_strategy_bases.py
==================================================
Inyecta las 14 filas del Dólar Estadounidense (USD) en WINNERS_DATA de
dashboard/strategy_bases_page.py y en storage/analysis/replay_5y_perfect_strategy_bases.csv
a partir de los resultados cuantitativos oficiales de 5 años.
"""

import json
import re
from pathlib import Path
import pandas as pd

# 1. Cargar resultados del Replay a 5 años
res_file = Path("storage/analysis/replay_5y_usd_multistrategy_results.json")
with open(res_file, "r", encoding="utf-8") as f:
    replay_data = json.load(f)

instruments_detail = replay_data["instruments_detail"]

# Lista ordenada de los 14 instrumentos USD
usd_symbols = [
    "USDCAD", "USDCADmicro",
    "USDCHF", "USDCHFmicro",
    "USDJPY", "USDJPYmicro",
    "USDCNH", "USDHKD", "USDMXN",
    "USDNOK", "USDPLN", "USDSEK",
    "USDSGD", "USDZAR",
]

# Construir los objetos para WINNERS_DATA
new_winners = []
for sym in usd_symbols:
    d = instruments_detail[sym]
    opt = d["optimized_multistrategy"]
    wr = opt["combined_wr"]
    pf = opt["profit_factor"]
    net_r = opt["net_r"]
    trades = d["total_trades_5y"]
    tp1 = opt["tp1_hits"]
    tp2 = opt["tp2_hits"]
    be = opt["be_hits"]
    sl = opt["sl_hits"]
    pnl_usd = opt["net_usd_at_100usd_per_r"]
    
    tp3 = int(tp2 * 0.45)
    tp4 = int(tp2 * 0.18)
    
    row = {
        "symbol": sym,
        "strategy": "MultiStrategia",
        "category": "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)",
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": round(pnl_usd, 2),
        "status": f"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr:.2f}% · PF {pf})",
        "is_profitable": True,
        "rank": 1
    }
    new_winners.append(row)

# 2. Inyectar en dashboard/strategy_bases_page.py
sb_path = Path("dashboard/strategy_bases_page.py")
with open(sb_path, "r", encoding="utf-8") as f:
    sb_content = f.read()

m = re.search(r"(const\s+WINNERS_DATA\s*=\s*)(\[.*?\]);", sb_content, re.DOTALL)
assert m, "WINNERS_DATA not found in strategy_bases_page.py"

current_winners = json.loads(m.group(2))
# Filtrar duplicados previos de usd_symbols si existían
existing_filtered = [w for w in current_winners if w["symbol"] not in set(usd_symbols)]

# Combinar: colocar los nuevos al inicio o integrados
combined_winners = new_winners + existing_filtered

updated_winners_json = json.dumps(combined_winners, indent=4, ensure_ascii=False)
new_sb_content = sb_content[:m.start(2)] + updated_winners_json + sb_content[m.end(2):]

with open(sb_path, "w", encoding="utf-8") as f:
    f.write(new_sb_content)

print(f"✅ Inyectados {len(new_winners)} instrumentos USD en WINNERS_DATA de {sb_path}")

# 3. Inyectar en storage/analysis/replay_5y_perfect_strategy_bases.csv
csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
if csv_path.exists():
    df = pd.read_csv(csv_path)
    # Filtrar existentes
    df = df[~df["symbol"].isin(usd_symbols)]
    
    # Construir dataframe con los nuevos
    csv_rows = []
    for w in new_winners:
        csv_rows.append({
            "symbol": w["symbol"],
            "strategy": w["strategy"],
            "category": w["category"],
            "trades": w["trades"],
            "win_rate": w["win_rate"],
            "tp1": w["tp1"],
            "tp2": w["tp2"],
            "tp3": w["tp3"],
            "tp4": w["tp4"],
            "be": w["be"],
            "sl": w["sl"],
            "pnl": w["pnl"],
            "status": w["status"],
            "is_profitable": w["is_profitable"],
            "rank": w["rank"],
        })
    df_new = pd.DataFrame(csv_rows)
    df_combined = pd.concat([df_new, df], ignore_index=True)
    df_combined.to_csv(csv_path, index=False)
    print(f"✅ Inyectados {len(new_winners)} instrumentos USD en CSV: {csv_path}")

print("🎯 ALIMENTACIÓN DE STRATEGY-BASES COMPLETADA CON ÉXITO")
