"""
scratch/extract_dashboard_data.py
Extrae con precisión milimétrica los arrays JSON WINNERS_DATA y LOSERS_DATA
directamente de dashboard/strategy_bases_page.py
"""
import json
import re
from pathlib import Path
import pandas as pd

page_path = Path("dashboard/strategy_bases_page.py")
content = page_path.read_text(encoding="utf-8-sig")

# Extraer WINNERS_DATA
m_win = re.search(r"const WINNERS_DATA = (\[.*?\]);", content, re.DOTALL)
if not m_win:
    print("ERROR: No se encontró WINNERS_DATA")
    exit(1)

winners = json.loads(m_win.group(1))
print(f"WINNERS_DATA extraído: {len(winners)} registros")

# Extraer LOSERS_DATA si existe
m_los = re.search(r"const LOSERS_DATA = (\[.*?\]);", content, re.DOTALL)
losers = []
if m_los:
    losers = json.loads(m_los.group(1))
    print(f"LOSERS_DATA extraído: {len(losers)} registros")

# Unir ambos
all_records = winners + losers
print(f"Total registros en /Strategy-bases: {len(all_records)}")

df = pd.DataFrame(all_records)
df.to_csv("storage/analysis/exact_strategy_bases_data.csv", index=False)
print("Guardado en storage/analysis/exact_strategy_bases_data.csv")

# Verificar Crash 300 Index
c300 = df[df["symbol"] == "Crash 300 Index"]
print("\n--- CRASH 300 INDEX EN DASHBOARD ---")
print(c300[["symbol", "strategy", "trades", "win_rate", "tp1", "tp2", "pnl"]])

# Verificar Boom 1000 Index
b1k = df[df["symbol"] == "Boom 1000 Index"]
print("\n--- BOOM 1000 INDEX EN DASHBOARD ---")
print(b1k[["symbol", "strategy", "trades", "win_rate", "tp1", "tp2", "pnl"]])
