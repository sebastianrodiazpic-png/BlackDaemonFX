import sqlite3
import json
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
if not db_path.exists():
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("==================================================")
print("AUDITORÍA FORENSE DEL RUNNER EN MODO SOMBRA")
print("==================================================")

cur.execute("SELECT count(*) FROM shadow_signals")
print(f"Total registros en shadow_signals: {cur.fetchone()[0]}")

cur.execute("SELECT count(*) FROM shadow_session_summary")
print(f"Total registros en shadow_session_summary: {cur.fetchone()[0]}")

print("\n--- DISTRIBUCIÓN POR ESTRATEGIA Y VARIANTE ---")
cur.execute("""
    SELECT strategy, variant, 
           COUNT(*) as total,
           SUM(CASE WHEN final_action = 'ACCEPTED_EXECUTION' THEN 1 ELSE 0 END) as accepted,
           SUM(CASE WHEN final_action = 'DISCARDED_BY_FILTER' THEN 1 ELSE 0 END) as discarded,
           SUM(CASE WHEN simulated_outcome IS NOT NULL AND simulated_outcome != 'PENDING' THEN 1 ELSE 0 END) as sim_done,
           ROUND(AVG(ai_probability), 4) as avg_ai_prob
    FROM shadow_signals
    GROUP BY strategy, variant
    ORDER BY strategy, variant
""")
for row in cur.fetchall():
    print(dict(row))

print("\n--- MOTIVOS DE RECHAZO (DISCARDED) ---")
cur.execute("""
    SELECT strategy, variant, rejection_reason, COUNT(*) as count
    FROM shadow_signals
    WHERE rejection_reason IS NOT NULL AND rejection_reason != ''
    GROUP BY strategy, variant, rejection_reason
    ORDER BY strategy, count DESC
""")
for row in cur.fetchall():
    print(dict(row))

print("\n--- DISTRIBUCIÓN POR ACTIVO / SÍMBOLO ---")
cur.execute("""
    SELECT symbol, strategy,
           COUNT(*) as total_signals,
           SUM(CASE WHEN final_action = 'ACCEPTED_EXECUTION' THEN 1 ELSE 0 END) as accepted,
           SUM(CASE WHEN final_action = 'DISCARDED_BY_FILTER' THEN 1 ELSE 0 END) as discarded,
           ROUND(AVG(simulated_rr), 4) as avg_rr,
           ROUND(SUM(simulated_rr), 4) as sum_rr
    FROM shadow_signals
    GROUP BY symbol, strategy
    ORDER BY strategy, total_signals DESC
""")
for row in cur.fetchall():
    print(dict(row))

print("\n--- RESULTADOS SIMULADOS DE OPERACIONES ACEPTADAS ---")
cur.execute("""
    SELECT strategy, variant, simulated_outcome, 
           COUNT(*) as count,
           ROUND(AVG(simulated_rr), 4) as avg_rr,
           ROUND(SUM(simulated_rr), 4) as sum_rr
    FROM shadow_signals
    WHERE final_action = 'ACCEPTED_EXECUTION'
    GROUP BY strategy, variant, simulated_outcome
    ORDER BY strategy, variant, simulated_outcome
""")
for row in cur.fetchall():
    print(dict(row))

print("\n--- MUESTRA DE LAS ÚLTIMAS 10 SEÑALES REGISTRADAS ---")
cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, 
           mechanical_decision, rejection_reason, ai_probability, final_action, simulated_outcome, simulated_rr
    FROM shadow_signals
    ORDER BY id DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(dict(row))
