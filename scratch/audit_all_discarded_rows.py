import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=====================================================================")
print("AUDITORÍA DE TODAS LAS FILAS CON FINAL_ACTION == 'DISCARDED_BY_FILTER'")
print("=====================================================================")

cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, rejection_reason,
           final_action, simulated_outcome, simulated_rr
    FROM shadow_signals
    WHERE final_action = 'DISCARDED_BY_FILTER'
    ORDER BY id ASC
""")
discarded_rows = [dict(r) for r in cur.fetchall()]
conn.close()

df_disc = pd.DataFrame(discarded_rows)
print(f"Total filas descartadas: {len(df_disc)}")

inconsistent = df_disc[(df_disc['simulated_rr'] != 0.0) | (df_disc['simulated_outcome'].isin(['SL_LOSS', 'TP1_WIN']))]
print(f"Filas descartadas con simulated_rr != 0.0 o outcome in ['SL_LOSS', 'TP1_WIN']: {len(inconsistent)}")
if not inconsistent.empty:
    print(inconsistent.to_string())
