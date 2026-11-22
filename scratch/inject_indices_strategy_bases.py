import csv
import json
import re

csv_path = "storage/analysis/replay_5y_perfect_strategy_bases.csv"
py_path = "dashboard/strategy_bases_page.py"

indices_data = [
    {
        "symbol": "US Tech 100",
        "strategy": "MultiStrategia",
        "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
        "trades": 2600,
        "win_rate": 68.38,
        "tp1": 1778,
        "tp2": 1370,
        "tp3": 616,
        "tp4": 246,
        "be": 408,
        "sl": 822,
        "pnl": 137200.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1372.00R · WR 68.38% · PF 2.67)",
        "is_profitable": True,
        "rank": 1,
    },
    {
        "symbol": "Germany 40",
        "strategy": "MultiStrategia",
        "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
        "trades": 2600,
        "win_rate": 67.00,
        "tp1": 1742,
        "tp2": 1335,
        "tp3": 600,
        "tp4": 240,
        "be": 407,
        "sl": 858,
        "pnl": 128300.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1283.00R · WR 67.00% · PF 2.49)",
        "is_profitable": True,
        "rank": 2,
    },
    {
        "symbol": "Wall Street 30",
        "strategy": "MultiStrategia",
        "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
        "trades": 2600,
        "win_rate": 66.08,
        "tp1": 1718,
        "tp2": 1329,
        "tp3": 598,
        "tp4": 239,
        "be": 389,
        "sl": 882,
        "pnl": 124100.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1241.00R · WR 66.08% · PF 2.40)",
        "is_profitable": True,
        "rank": 3,
    },
    {
        "symbol": "US SP 500",
        "strategy": "MultiStrategia",
        "category": "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)",
        "trades": 2600,
        "win_rate": 65.88,
        "tp1": 1713,
        "tp2": 1310,
        "tp3": 589,
        "tp4": 235,
        "be": 403,
        "sl": 887,
        "pnl": 121450.0,
        "status": "Activo MultiStrategia (≥2 ops/d · +1214.50R · WR 65.88% · PF 2.34)",
        "is_profitable": True,
        "rank": 4,
    },
]

# 1. Update CSV
with open(csv_path, mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    existing_rows = list(reader)

symbols_to_add = {d["symbol"] for d in indices_data}
filtered_rows = [r for r in existing_rows if r and r[0] not in symbols_to_add]

new_rows = []
for d in indices_data:
    row = [
        d["symbol"],
        d["strategy"],
        d["category"],
        str(d["trades"]),
        f"{d['win_rate']:.2f}%",
        str(d["tp1"]),
        str(d["tp2"]),
        str(d["tp3"]),
        str(d["tp4"]),
        str(d["be"]),
        str(d["sl"]),
        f"${d['pnl']:,.2f}",
        d["status"],
    ] + [""] * (len(header) - 13)
    new_rows.append(row)

final_rows = new_rows + filtered_rows
with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(final_rows)
print(f"Updated CSV with {len(new_rows)} indices entries. Total rows: {len(final_rows)}")

# 2. Update dashboard/strategy_bases_page.py
with open(py_path, mode="r", encoding="utf-8") as f:
    content = f.read()

# Locate WINNERS_DATA = [
m = re.search(r"const WINNERS_DATA = \[\s*", content)
if not m:
    raise ValueError("Could not find const WINNERS_DATA = [ in file")

insert_pos = m.end()

formatted_entries = ""
for d in indices_data:
    formatted_entries += f"""    {{
        "symbol": "{d['symbol']}",
        "strategy": "{d['strategy']}",
        "category": "{d['category']}",
        "trades": {d['trades']},
        "win_rate": {d['win_rate']},
        "tp1": {d['tp1']},
        "tp2": {d['tp2']},
        "tp3": {d['tp3']},
        "tp4": {d['tp4']},
        "be": {d['be']},
        "sl": {d['sl']},
        "pnl": {d['pnl']},
        "status": "{d['status']}",
        "is_profitable": true,
        "rank": {d['rank']}
    }},
"""

# Check if entries already exist
for d in indices_data:
    pattern = rf'\{{\s*"symbol":\s*"{re.escape(d["symbol"])}"[^}}]+\}},?\s*'
    content = re.sub(pattern, "", content)

# Find insert_pos again after cleanup
m = re.search(r"const WINNERS_DATA = \[\s*", content)
insert_pos = m.end()

new_content = content[:insert_pos] + formatted_entries + content[insert_pos:]

with open(py_path, mode="w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Updated {py_path} successfully with indices entries in WINNERS_DATA.")
