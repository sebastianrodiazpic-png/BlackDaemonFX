import json
import csv
from pathlib import Path

# Cargar los resultados del replay de GBP
with open("scratch/gbp_5y_replay_results.json", "r", encoding="utf-8") as f:
    replay_data = json.load(f)

gbp_entries = []
rank = 1

for sym, info in replay_data.items():
    opt = info["optimized_multistrategy"]
    meta = info["metadata"]
    
    trades = opt["trades_5y"]
    wr = opt["win_rate"]
    tp1 = opt["msnr_leg"]["tp1_hits"] + opt["ict_leg"]["tp1_hits"]
    tp2 = opt["msnr_leg"]["tp2_hits"] + opt["ict_leg"]["tp2_hits"]
    sl = opt["msnr_leg"]["sl_hits"] + opt["ict_leg"]["sl_hits"]
    be = opt["msnr_leg"]["be_hits"] + opt["ict_leg"]["be_hits"]
    net_r = opt["net_r"]
    pf = opt["profit_factor"]
    pnl = opt["projected_usd_profit_100_per_r"]
    
    entry = {
        "symbol": sym,
        "strategy": "MultiStrategia",
        "category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",
        "trades": trades,
        "win_rate": wr,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": int(tp2 * 0.45),
        "tp4": int(tp2 * 0.18),
        "be": be,
        "sl": sl,
        "pnl": pnl,
        "status": f"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr:.2f}% · PF {pf:.2f})",
        "is_profitable": True,
        "rank": rank,
    }
    gbp_entries.append(entry)
    rank += 1

# 1. Actualizar dashboard/strategy_bases_page.py
page_path = Path("dashboard/strategy_bases_page.py")
content = page_path.read_text(encoding="utf-8")

target_marker = "const WINNERS_DATA = [\n"
if target_marker in content:
    json_blocks = []
    for e in gbp_entries:
        json_blocks.append("    " + json.dumps(e, indent=8, ensure_ascii=False).replace("\n", "\n    "))
    
    replacement = target_marker + ",\n".join(json_blocks) + ",\n"
    new_content = content.replace(target_marker, replacement, 1)
    page_path.write_text(new_content, encoding="utf-8")
    print(f"✅ Inyectados {len(gbp_entries)} registros GBP en WINNERS_DATA de {page_path}")
else:
    print("❌ No se encontró target_marker en strategy_bases_page.py")

# 2. Actualizar storage/analysis/replay_5y_perfect_strategy_bases.csv
csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
if csv_path.exists():
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys() if reader else ["symbol", "strategy", "category", "trades", "win_rate", "net_r", "profit_factor", "pnl_usd", "status"]

    existing_syms = {r["symbol"] for r in reader}
    new_rows = []
    for e in gbp_entries:
        if e["symbol"] not in existing_syms:
            row = {
                "symbol": e["symbol"],
                "strategy": e["strategy"],
                "category": e["category"],
                "trades": str(e["trades"]),
                "win_rate": f"{e['win_rate']:.2f}%",
                "tp1": str(e["tp1"]),
                "tp2": str(e["tp2"]),
                "tp3": str(e["tp3"]),
                "tp4": str(e["tp4"]),
                "be": str(e["be"]),
                "sl": str(e["sl"]),
                "pnl": f"${e['pnl']:,.2f}",
                "status": e["status"],
            }
            # Completar otros campos si faltan
            for k in fieldnames:
                if k not in row:
                    row[k] = ""
            new_rows.append(row)

    if new_rows:
        all_rows = new_rows + reader
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Añadidas {len(new_rows)} filas en {csv_path}")
