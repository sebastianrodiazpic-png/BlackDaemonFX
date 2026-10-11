import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Total señales y si alguna fue de Malaysian SNR
cursor.execute("SELECT count(*) as cnt FROM signals")
total_sig = cursor.fetchone()["cnt"]
print(f"Total señales históricas registradas: {total_sig}")

cursor.execute("""
    SELECT * FROM signals 
    WHERE details_json LIKE '%MALAYSIAN%' 
       OR details_json LIKE '%msnr%'
""")
msnr_signals = cursor.fetchall()
print(f"Señales de Malaysian SNR: {len(msnr_signals)}")
for s in msnr_signals:
    print(dict(s))

# 2. Total trades y si alguno fue de Malaysian SNR (magic 26082031)
cursor.execute("SELECT count(*) as cnt FROM trades")
total_trades = cursor.fetchone()["cnt"]
print(f"\nTotal trades en tabla 'trades': {total_trades}")

cursor.execute("SELECT * FROM trades WHERE magic = 26082031 OR strategy LIKE '%MALAYSIAN%'")
msnr_trades = cursor.fetchall()
print(f"Trades de Malaysian SNR: {len(msnr_trades)}")
for t in msnr_trades:
    print(dict(t))

# 3. Trade journal
cursor.execute("SELECT count(*) as cnt FROM trade_journal")
print(f"\nTotal en 'trade_journal': {cursor.fetchone()['cnt']}")
cursor.execute("SELECT * FROM trade_journal WHERE magic = 26082031 OR strategy LIKE '%MALAYSIAN%'")
tj_trades = cursor.fetchall()
print(f"Trades en journal de Malaysian SNR: {len(tj_trades)}")

# 4. Revisar si alguna vez hubo una señal confirmada en daemon_audit_events
cursor.execute("""
    SELECT count(*) as cnt FROM daemon_audit_events 
    WHERE action IN ('MALAYSIAN_SNR_CONFIRMED', 'ORDER_OPENED') 
       OR event_type LIKE '%SIGNAL%'
""")
print(f"\nAudit events con señal confirmada o apertura: {cursor.fetchone()['cnt']}")

cursor.execute("""
    SELECT * FROM daemon_audit_events 
    WHERE action IN ('MALAYSIAN_SNR_CONFIRMED', 'ORDER_OPENED') 
       OR event_type = 'ORDER_OPENED'
    ORDER BY id DESC LIMIT 10
""")
for e in cursor.fetchall():
    d = dict(e)
    print(f"[{d.get('created_at')}] Event: {d.get('event_type')} | Daemon: {d.get('source')} | Sym: {d.get('instrument')} | Act: {d.get('action')} | Reason: {d.get('reason')}")

conn.close()
