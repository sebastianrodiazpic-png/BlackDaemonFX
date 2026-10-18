import sqlite3
import json
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
jsonl_path = Path("storage/runtime/shadow_events.jsonl")

print("=== 1. CONSISTENCIA DB vs JSONL ===")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get DB count
cur.execute("SELECT count(*) FROM shadow_signals")
db_count = cur.fetchone()[0]

# Get table columns
cur.execute("PRAGMA table_info(shadow_signals)")
columns = [row[1] for row in cur.fetchall()]
print(f"Columnas en shadow_signals: {columns}")
print(f"Total registros en SQLite: {db_count}")

# Read jsonl
jsonl_events = []
if jsonl_path.exists():
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                jsonl_events.append(json.loads(line))
print(f"Total eventos en JSONL: {len(jsonl_events)}")

# Check action counts in DB
cur.execute("SELECT final_action, count(*) FROM shadow_signals GROUP BY final_action")
actions_db = dict(cur.fetchall())
print(f"final_action en DB: {actions_db}")

# Check action counts in JSONL
actions_jsonl = {}
for e in jsonl_events:
    act = e.get("final_action") or e.get("action") or "UNKNOWN"
    actions_jsonl[act] = actions_jsonl.get(act, 0) + 1
print(f"final_action en JSONL: {actions_jsonl}")

print("\n=== 2. VERIFICACIÓN DE SEÑALES DESCARTADAS (AVOIDED vs MARKET) ===")
cur.execute("""
    SELECT count(*), simulated_outcome, simulated_rr
    FROM shadow_signals
    WHERE final_action = 'DISCARDED_BY_FILTER'
    GROUP BY simulated_outcome, simulated_rr
""")
discarded_stats = cur.fetchall()
print("Estadísticas de señales DESCARTADAS en DB:")
for r in discarded_stats:
    print(f"  Count: {r[0]} | simulated_outcome: {r[1]} | simulated_rr: {r[2]}")

# Check simulated_outcome for ACCEPTED
cur.execute("""
    SELECT count(*), simulated_outcome, round(sum(simulated_rr), 4)
    FROM shadow_signals
    WHERE final_action = 'ACCEPTED_EXECUTION'
    GROUP BY simulated_outcome
""")
accepted_stats = cur.fetchall()
print("\nEstadísticas de señales ACEPTADAS en DB:")
for r in accepted_stats:
    print(f"  Count: {r[0]} | simulated_outcome: {r[1]} | sum_simulated_rr: {r[2]}")

# Detailed breakdown of discarded signals that have counterfactual market results
cur.execute("""
    SELECT 
        id, symbol, strategy, variant, rejection_reason, 
        final_action, simulated_outcome, simulated_rr, market_outcome, market_rr, contrafactual_note
    FROM shadow_signals
    WHERE final_action = 'DISCARDED_BY_FILTER'
""")
discarded_rows = cur.fetchall()
print(f"\nTotal descartadas: {len(discarded_rows)}")
avoided_losses = [r for r in discarded_rows if r[8] == 'LOSS']
avoided_wins = [r for r in discarded_rows if r[8] == 'WIN']
pending_or_open_discarded = [r for r in discarded_rows if r[8] is None or r[8] in ('OPEN', 'PENDING')]
print(f"  Descartadas con market_outcome == 'LOSS' (pérdidas contrafactuales evitadas): {len(avoided_losses)}")
for al in avoided_losses:
    print(f"    ID: {al[0]}, {al[1]}, {al[3]}, Razón: {al[4]}, market_rr: {al[9]}, note: {al[10]}")
print(f"  Descartadas con market_outcome == 'WIN' (ganancias contrafactuales perdidas): {len(avoided_wins)}")
for aw in avoided_wins:
    print(f"    ID: {aw[0]}, {aw[1]}, {aw[3]}, Razón: {aw[4]}, market_rr: {aw[9]}, note: {aw[10]}")
print(f"  Descartadas con market_outcome OPEN/PENDING/None: {len(pending_or_open_discarded)}")

print("\n=== 3. DETALLE DE COHORTE Y MARCADORES TEMPORALES ===")
cur.execute("SELECT min(timestamp), max(timestamp) FROM shadow_signals")
min_ts, max_ts = cur.fetchone()
print(f"Rango temporal en DB: {min_ts} a {max_ts}")

cur.execute("""
    SELECT strategy, variant, count(*), 
           sum(CASE WHEN final_action = 'ACCEPTED_EXECUTION' THEN 1 ELSE 0 END) as accepted,
           sum(CASE WHEN final_action = 'DISCARDED_BY_FILTER' THEN 1 ELSE 0 END) as discarded
    FROM shadow_signals
    GROUP BY strategy, variant
""")
for sv in cur.fetchall():
    print(f"  {sv[0]} | {sv[1]} | Total: {sv[2]} | Aceptadas: {sv[3]} | Descartadas: {sv[4]}")

conn.close()
