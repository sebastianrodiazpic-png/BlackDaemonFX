import sqlite3
import os
import glob
import datetime

dbs = ['storage/database.sqlite', 'storage/trades.db', 'storage/trading_system.db', 'storage/trading_bot.db', 'storage/database/trading.db']
for db in dbs:
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"\n=== DB {db}: tables={tables} ===")
        for t in tables:
            try:
                cur.execute(f"SELECT count(*) FROM {t};")
                cnt = cur.fetchone()[0]
                print(f"   Table {t}: {cnt} rows")
            except Exception as e:
                pass
        conn.close()

# Inspeccionar los logs de bots: cuántos ciclos llevan y qué motivos de no-entrada dan
print("\n=== BOT LOGS RECENT CYCLES ===")
bots = ['jump', 'boom', 'crash', 'step', 'malaysian_snr', 'ict', 'orb', 'volatility_1']
for b in bots:
    log_p = f"storage/logs/bots/{b}.log"
    if os.path.exists(log_p):
        size = os.path.getsize(log_p)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(log_p)).strftime('%Y-%m-%d %H:%M:%S')
        with open(log_p, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        print(f"\nBot {b.upper()}: size={size} bytes, modified={mtime}, lines={len(lines)}")
        # Buscar palabras clave en las últimas 50 líneas
        for l in lines[-15:]:
            print("  ", l.strip())
