import sqlite3
import json
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=====================================================================")
print("AUDITORÍA FORENSE DEL EVENTO ICT #10 (US SP 500 SELL - 13:45 UTC)")
print("=====================================================================")

cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, 
           mechanical_decision, rejection_reason, ai_probability, final_action, 
           market_outcome, market_rr, simulated_outcome, simulated_rr, contrafactual_note
    FROM shadow_signals
    WHERE symbol = 'US SP 500' AND timestamp = '2026-10-15T13:45:00+00:00'
    ORDER BY id ASC
""")
rows = [dict(r) for r in cur.fetchall()]
conn.close()

for r in rows:
    print(f"ID #{r['id']} | Variante: {r['variant']:18s} | Acción: {r['final_action']:20s} | "
          f"Mercado: {r['market_outcome']} ({r['market_rr']:+.4f}R) | "
          f"Simulado: {r['simulated_outcome']} ({r['simulated_rr']:+.4f}R) | "
          f"Contrafactual: {str(r['contrafactual_note'])}")
