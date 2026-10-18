import sqlite3
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cur = con.cursor()

print("--- Distinct Strategy and Variant ---")
rows = cur.execute("SELECT strategy, variant, COUNT(*), MIN(timestamp), MAX(timestamp) FROM shadow_signals GROUP BY strategy, variant;").fetchall()
for r in rows:
    print(r)

print("\n--- Distinct Rejection Reasons ---")
reasons = cur.execute("SELECT rejection_reason, COUNT(*) FROM shadow_signals GROUP BY rejection_reason;").fetchall()
for r in reasons:
    print(r)

print("\n--- Distinct Final Action and Market Outcome ---")
outcomes = cur.execute("SELECT final_action, market_outcome, COUNT(*) FROM shadow_signals GROUP BY final_action, market_outcome;").fetchall()
for o in outcomes:
    print(o)

con.close()
