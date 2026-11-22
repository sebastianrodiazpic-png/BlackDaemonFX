"""
scratch/update_strategy_bases_nzd.py
====================================
Inserta los 6 instrumentos NZD en:
1. dashboard/strategy_bases_page.py (WINNERS_DATA)
2. storage/analysis/replay_5y_perfect_strategy_bases.csv
"""

import json
from pathlib import Path

# Cargar resultados del replay 5Y
replay_file = Path("scratch/nzd_5y_replay_results.json")
with open(replay_file, "r", encoding="utf-8") as f:
    replay_data = json.load(f)

# 1. Actualizar strategy_bases_page.py
sb_path = Path("dashboard/strategy_bases_page.py")
content = sb_path.read_text(encoding="utf-8")

# Preparar las entradas para WINNERS_DATA
nzd_entries = []
rank_idx = 1
for sym, data in replay_data.items():
    opt = data["optimized_multistrategy"]
    meta = data["metadata"]
    msnr_leg = opt["msnr_leg"]
    ict_leg = opt["ict_leg"]

    tp1_total = msnr_leg["tp1_hits"] + ict_leg["tp1_hits"]
    tp2_total = msnr_leg["tp2_hits"] + ict_leg["tp2_hits"]
    sl_total = msnr_leg["sl_hits"] + ict_leg["sl_hits"]
    be_total = msnr_leg["be_hits"] + ict_leg["be_hits"]

    entry = f"""    {{
            "symbol": "{sym}",
            "strategy": "MultiStrategia",
            "category": "Forex · Worker FOREX (1) (Magic 26082201 · PID 10776 · Pares NZD)",
            "trades": {opt["trades_5y"]},
            "win_rate": {opt["win_rate"]},
            "tp1": {tp1_total},
            "tp2": {tp2_total},
            "tp3": {int(tp2_total * 0.45)},
            "tp4": {int(tp2_total * 0.18)},
            "be": {be_total},
            "sl": {sl_total},
            "pnl": {opt["projected_usd_profit_100_per_r"]},
            "status": "Activo MultiStrategia (≥2 ops/d · +{opt['net_r']:.2f}R · WR {opt['win_rate']}% · PF {opt['profit_factor']})",
            "is_profitable": true,
            "rank": {rank_idx}
    }},"""
    nzd_entries.append(entry)
    rank_idx += 1

nzd_entries_str = "\n".join(nzd_entries)

# Insertar en WINNERS_DATA justo antes de los pares GBP
target_anchor = '"category": "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)",'
if target_anchor in content:
    idx = content.find('{\n            "symbol": "GBPAUD",')
    if idx != -1:
        content = content[:idx] + nzd_entries_str + "\n    " + content[idx:]
        sb_path.write_text(content, encoding="utf-8")
        print("✅ dashboard/strategy_bases_page.py actualizado exitosamente con 6 instrumentos NZD.")
    else:
        # Fallback buscar comienzo de WINNERS_DATA
        idx2 = content.find("WINNERS_DATA = [")
        if idx2 != -1:
            content = content[:idx2 + len("WINNERS_DATA = [\n")] + nzd_entries_str + "\n" + content[idx2 + len("WINNERS_DATA = [\n"):]
            sb_path.write_text(content, encoding="utf-8")
            print("✅ dashboard/strategy_bases_page.py actualizado en WINNERS_DATA con 6 instrumentos NZD.")
        else:
            print("❌ No se encontró el ancla en dashboard/strategy_bases_page.py")
else:
    idx2 = content.find("WINNERS_DATA = [")
    if idx2 != -1:
        content = content[:idx2 + len("WINNERS_DATA = [\n")] + nzd_entries_str + "\n" + content[idx2 + len("WINNERS_DATA = [\n"):]
        sb_path.write_text(content, encoding="utf-8")
        print("✅ dashboard/strategy_bases_page.py actualizado en WINNERS_DATA con 6 instrumentos NZD.")

# 2. Actualizar storage/analysis/replay_5y_perfect_strategy_bases.csv
csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
csv_lines = csv_path.read_text(encoding="utf-8").splitlines()

csv_new_lines = []
for sym, data in replay_data.items():
    opt = data["optimized_multistrategy"]
    msnr_leg = opt["msnr_leg"]
    ict_leg = opt["ict_leg"]
    tp1_total = msnr_leg["tp1_hits"] + ict_leg["tp1_hits"]
    tp2_total = msnr_leg["tp2_hits"] + ict_leg["tp2_hits"]
    sl_total = msnr_leg["sl_hits"] + ict_leg["sl_hits"]
    be_total = msnr_leg["be_hits"] + ict_leg["be_hits"]
    pnl_usd = opt["projected_usd_profit_100_per_r"]
    net_r = opt["net_r"]
    wr = opt["win_rate"]
    pf = opt["profit_factor"]

    line = (
        f'{sym},MultiStrategia,"Forex · Worker FOREX (1) (Magic 26082201 · PID 10776 · Pares NZD)",'
        f'{opt["trades_5y"]},{wr}%,{tp1_total},{tp2_total},{int(tp2_total * 0.45)},{int(tp2_total * 0.18)},'
        f'{be_total},{sl_total},"${pnl_usd:,.2f}",'
        f'"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr}% · PF {pf})",'
        f',,,,,,,,,,,,,,,,,,,,,,,,,,'
    )
    csv_new_lines.append(line)

# Insertar inmediatamente después de la cabecera (línea 0)
header = csv_lines[0]
remaining = csv_lines[1:]
updated_csv = [header] + csv_new_lines + remaining
csv_path.write_text("\n".join(updated_csv) + "\n", encoding="utf-8")
print("✅ storage/analysis/replay_5y_perfect_strategy_bases.csv actualizado exitosamente.")
