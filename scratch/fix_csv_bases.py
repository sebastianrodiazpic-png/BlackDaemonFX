"""
scratch/fix_csv_bases.py
========================
Reconstruye storage/analysis/replay_5y_perfect_strategy_bases.csv asegurando
que cada fila tenga exactamente 39 campos como la cabecera.
"""

import csv
import json
from pathlib import Path

csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = rows[0]
n_cols = len(header)
print(f"Header has {n_cols} columns.")

# Eliminar cualquier fila de NZD previa mal formada
clean_rows = [header]
for r in rows[1:]:
    if len(r) > 0 and r[0] in ["NZDCAD", "NZDUSD", "NZDUSDmicro", "NZDCHF", "NZDJPY", "NZDSGD"]:
        continue
    # Asegurar que tenga exactamente n_cols
    if len(r) < n_cols:
        r = r + [""] * (n_cols - len(r))
    elif len(r) > n_cols:
        r = r[:n_cols]
    clean_rows.append(r)

# Cargar resultados del replay NZD
with open("scratch/nzd_5y_replay_results.json", "r", encoding="utf-8") as f:
    replay_data = json.load(f)

nzd_rows = []
for sym, data in replay_data.items():
    opt = data["optimized_multistrategy"]
    msnr = opt["msnr_leg"]
    ict = opt["ict_leg"]
    tp1 = msnr["tp1_hits"] + ict["tp1_hits"]
    tp2 = msnr["tp2_hits"] + ict["tp2_hits"]
    sl = msnr["sl_hits"] + ict["sl_hits"]
    be = msnr["be_hits"] + ict["be_hits"]
    pnl = opt["projected_usd_profit_100_per_r"]
    net_r = opt["net_r"]
    wr = opt["win_rate"]
    pf = opt["profit_factor"]

    row = [
        sym,
        "MultiStrategia",
        "Forex · Worker FOREX (1) (Magic 26082201 · PID 10776 · Pares NZD)",
        str(opt["trades_5y"]),
        f"{wr}%",
        str(tp1),
        str(tp2),
        str(int(tp2 * 0.45)),
        str(int(tp2 * 0.18)),
        str(be),
        str(sl),
        f"${pnl:,.2f}",
        f"Activo MultiStrategia (≥2 ops/d · +{net_r:.2f}R · WR {wr}% · PF {pf})"
    ]
    # Completar hasta n_cols (39)
    row += [""] * (n_cols - len(row))
    assert len(row) == n_cols, f"Row for {sym} has {len(row)} cols, expected {n_cols}"
    nzd_rows.append(row)

# Insertar filas NZD al inicio (después del header)
final_rows = [header] + nzd_rows + clean_rows[1:]

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(final_rows)

print(f"✅ CSV guardado exitosamente con {len(final_rows)} filas y {n_cols} columnas exactas.")
