import sqlite3
from pathlib import Path

# Shadow
conn_s = sqlite3.connect('storage/runtime/shadow_research.sqlite3')
cur_s = conn_s.cursor()
cur_s.execute('SELECT id, timestamp, variant, symbol, direction, simulated_outcome, simulated_rr FROM shadow_signals WHERE symbol="US SP 500"')
for r in cur_s.fetchall():
    print('Shadow:', r)
conn_s.close()

# Live
p = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn_l = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
cur_l = conn_l.cursor()
cur_l.execute('SELECT id, instrument, direction, entry_time, exit_time, result, realized_rr FROM trades WHERE instrument="US SP 500"')
for r in cur_l.fetchall():
    print('Live:', r)
conn_l.close()
