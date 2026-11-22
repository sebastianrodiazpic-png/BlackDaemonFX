import sqlite3, os
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("================ OPEN POSITIONS RIGHT NOW ================")
cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, volume, entry_price, stop_loss, take_profit, entry_time, created_at, source
    FROM trades
    WHERE status = 'OPEN'
""")
open_pos = cur.fetchall()
print(f"Open positions in trades table: {len(open_pos)}")
for p in open_pos:
    print(f"  ID #{p['id']} | Ticket={p['broker_position_ticket']} | {p['instrument']} {p['direction']} vol={p['volume']} @ {p['entry_price']} | SL={p['stop_loss']} TP={p['take_profit']} | In: {p['entry_time']} ({p['source']})")

print("\n================ OPEN POSITIONS IN TRADE_JOURNAL ================")
cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, volume, entry_price, stop_loss, take_profit, entry_time, source
    FROM trade_journal
    WHERE status = 'OPEN'
""")
journal_open = cur.fetchall()
print(f"Open in trade_journal: {len(journal_open)}")
for p in journal_open:
    print(f"  Journal #{p['id']} | Ticket={p['broker_position_ticket']} | {p['instrument']} {p['direction']} vol={p['volume']} @ {p['entry_price']} | SL={p['stop_loss']} TP={p['take_profit']} | {p['source']}")

conn.close()
