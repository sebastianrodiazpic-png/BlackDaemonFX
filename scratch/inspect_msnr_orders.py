import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== TRADES DE MALAYSIAN SNR ===")
cursor.execute("""
    SELECT id, instrument, direction, status, entry_time, exit_time, net_pnl, setup_reason, execution_key, details_json
    FROM trades 
    WHERE setup_reason LIKE '%MALAYSIAN%' 
       OR details_json LIKE '%MALAYSIAN%'
       OR execution_key LIKE '%26082031%'
       OR details_json LIKE '%26082031%'
""")
trades = cursor.fetchall()
print(f"Total trades encontrados para Malaysian SNR: {len(trades)}")
for t in trades:
    d = dict(t)
    print(f"[{d.get('id')}] {d.get('instrument')} {d.get('direction')} | Status: {d.get('status')} | Entry: {d.get('entry_time')} | PnL: {d.get('net_pnl')} | Reason: {d.get('setup_reason')}")

print("\n=== TRADE JOURNAL DE MALAYSIAN SNR ===")
cursor.execute("""
    SELECT id, instrument, direction, status, entry_time, net_pnl, execution_key, details_json
    FROM trade_journal 
    WHERE details_json LIKE '%MALAYSIAN%'
       OR execution_key LIKE '%26082031%'
       OR details_json LIKE '%26082031%'
""")
journal = cursor.fetchall()
print(f"Total journal encontrados para Malaysian SNR: {len(journal)}")
for j in journal:
    d = dict(j)
    print(f"[{d.get('id')}] {d.get('instrument')} {d.get('direction')} | Status: {d.get('status')} | Entry: {d.get('entry_time')} | PnL: {d.get('net_pnl')}")

print("\n=== RESUMEN DE TODAS LAS ESTRATEGIAS EN TRADES ===")
cursor.execute("SELECT DISTINCT setup_reason FROM trades")
reasons = cursor.fetchall()
for r in reasons:
    print("Setup reason en DB:", r["setup_reason"])

conn.close()
