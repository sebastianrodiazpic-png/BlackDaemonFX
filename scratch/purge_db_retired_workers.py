import sqlite3
import os
from pathlib import Path

p = Path(os.environ['LOCALAPPDATA']) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
print('Opening database:', p)

conn = sqlite3.connect(p)
cur = conn.cursor()

retired = ('CARRY', 'DRIFT', 'GOLD', 'MSNR', 'NIGHT', 'RSI2', 'FLIP', 'IDX_OPEN', 'V53_PROBE')

# Ver qué filas hay antes
cur.execute("SELECT bot_profile, status, last_event_time FROM worker_runtime_states WHERE bot_profile IN (?, ?, ?, ?, ?, ?, ?, ?, ?)", retired)
rows = cur.fetchall()
print(f"Found {len(rows)} rows to purge:")
for r in rows:
    print("  ", r)

# Eliminar
cur.execute("DELETE FROM worker_runtime_states WHERE bot_profile IN (?, ?, ?, ?, ?, ?, ?, ?, ?)", retired)
conn.commit()
print(f"Purged {cur.rowcount} rows from worker_runtime_states successfully!")

# Verificar restantes
cur.execute("SELECT DISTINCT bot_profile FROM worker_runtime_states")
remaining = [r[0] for r in cur.fetchall()]
print("Remaining distinct bot_profiles in worker_runtime_states:", remaining)

conn.close()
