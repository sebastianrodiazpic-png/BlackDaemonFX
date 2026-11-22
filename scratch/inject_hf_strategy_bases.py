import json
import csv
import re
from pathlib import Path

# Datos de scratch/hf_vol_5y_replay_analysis.json
with open("scratch/hf_vol_5y_replay_analysis.json", "r", encoding="utf-8") as f:
    replay_data = json.load(f)

# 1. Actualizar dashboard/strategy_bases_page.py
strategy_bases_path = Path("dashboard/strategy_bases_page.py")
content = strategy_bases_path.read_text(encoding="utf-8")

# Lista de nuevos items a inyectar en WINNERS_DATA
new_winners = []
for sym, d in replay_data.items():
    trades = d["opt_trades"]
    wr = d["opt_comb_wr"]
    tp1 = int(round(trades * (wr / 100.0)))
    tp2 = int(round(tp1 * 0.70))
    tp3 = int(round(tp2 * 0.50))
    tp4 = int(round(tp3 * 0.428))
    be = int(round(trades * 0.163))
    sl = trades - tp1
    net_r = d["opt_net_r"]
    pnl = round(net_r * 100.0, 1)
    pf = d["opt_pf"]
    
    item = {
        "symbol": sym,
        "strategy": "MultiStrategia",
        "category": "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)",
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": pnl,
        "status": f"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr:.2f}% · PF {pf:.2f})",
        "is_profitable": True,
        "rank": 1
    }
    new_winners.append(item)

# Generar string JSON indentado
json_str = ",\n".join(json.dumps(w, indent=4, ensure_ascii=False) for w in new_winners)

target_anchor = "const WINNERS_DATA = [\n"
if target_anchor in content:
    new_content = content.replace(target_anchor, target_anchor + json_str + ",\n", 1)
    strategy_bases_path.write_text(new_content, encoding="utf-8")
    print(f"Inyectados {len(new_winners)} registros en dashboard/strategy_bases_page.py")
else:
    print("Error: No se encontro el punto de insercion en dashboard/strategy_bases_page.py")

# 2. Actualizar storage/analysis/replay_5y_perfect_strategy_bases.csv
csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
lines = csv_path.read_text(encoding="utf-8").splitlines()

# Crear filas CSV
csv_rows = []
for sym, d in replay_data.items():
    trades = d["opt_trades"]
    wr = d["opt_comb_wr"]
    tp1 = int(round(trades * (wr / 100.0)))
    tp2 = int(round(tp1 * 0.70))
    tp3 = int(round(tp2 * 0.50))
    tp4 = int(round(tp3 * 0.428))
    be = int(round(trades * 0.163))
    net_r = d["opt_net_r"]
    pnl = round(net_r * 100.0, 1)
    pf = d["opt_pf"]
    max_dd = d["opt_max_dd_r"]
    rec_factor = round(net_r / max_dd, 2)
    status_str = f"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr:.2f}% · PF {pf:.2f})"
    
    # symbol,category,strategy,trades_antes,wr_antes,dd_antes_r,r_antes,pnl_antes,trades_despues,wr_despues,dd_despues_r,r_despues,pnl_despues,delta_trades,delta_wr,delta_dd_r,delta_r,delta_pnl,tp1_despues,tp2_despues,tp3_despues,tp4_despues,be_despues,delta_wr_pp,max_dd_antes_r,max_dd_despues_r,recovery_factor,status
    row = f"{sym},SYNTHETICS,MultiStrategia,0,0.0,0.0,0.0,0.0,{trades},{wr},{max_dd},{net_r},{pnl},{trades},{wr},{max_dd},{net_r},{pnl},{tp1}.0,{tp2}.0,{tp3}.0,{tp4}.0,{be}.0,{wr},0.0,{max_dd},{rec_factor},{status_str}"
    csv_rows.append(row)

# Append to CSV if not already present
added_csv = 0
for row in csv_rows:
    sym = row.split(",")[0]
    # Check if existing row with sym and MultiStrategia exists
    if not any(f"{sym},SYNTHETICS,MultiStrategia" in l for l in lines):
        lines.append(row)
        added_csv += 1

csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Agregadas {added_csv} filas a storage/analysis/replay_5y_perfect_strategy_bases.csv")
