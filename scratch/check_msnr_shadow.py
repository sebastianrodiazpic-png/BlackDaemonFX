import sqlite3
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cur = con.cursor()

print("--- MSNR Rows in shadow_signals ---")
rows = cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, 
           stop_loss, take_profit_1, mechanical_decision, rejection_reason, 
           final_action, market_outcome, market_rr, contrafactual_note
    FROM shadow_signals
    WHERE strategy = 'MSNR'
    ORDER BY id;
""").fetchall()

for r in rows:
    print(r)

con.close()
