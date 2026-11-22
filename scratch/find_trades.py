import glob
import os
import sqlite3
import pandas as pd

tickets = ["47916250", "47916321", "47916580"]

print("=== BUSCANDO TICKETS EN BASES DE DATOS ===")
all_dbs = ["storage/trading_bot.sqlite3"] + glob.glob("storage/**/*.sqlite3", recursive=True)

# Also check %LOCALAPPDATA%/BlackDaemonFx/trading_bot.sqlite3 if accessible
appdata = os.path.expandvars(r"%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3")
if os.path.exists(appdata):
    all_dbs.append(appdata)

for db in all_dbs:
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in ["trades", "signals", "daemon_audit_events", "trade_visual_audits"]:
            if t in tables:
                for tk in tickets:
                    # search text columns
                    q = f"SELECT * FROM {t} WHERE CAST(id AS TEXT) LIKE '%{tk}%' OR CAST(ticket AS TEXT) LIKE '%{tk}%' LIMIT 5"
                    try:
                        df = pd.read_sql_query(q, conn)
                        if len(df) > 0:
                            print(f"\n[ENCONTRADO] Tabla {t} en {db} para ticket {tk}:")
                            print(df.to_dict(orient="records"))
                    except Exception:
                        pass
    except Exception:
        pass

print("\n=== BUSCANDO EN LOGS DE BOT ===")
log_dir = "storage/logs"
if os.path.exists(log_dir):
    for root, dirs, files in os.walk(log_dir):
        for f in files:
            if f.endswith(".log") or f.endswith(".jsonl"):
                p = os.path.join(root, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        for line in fp:
                            for tk in tickets:
                                if tk in line:
                                    print(f"Log {p}: {line.strip()[:150]}")
                except Exception:
                    pass
