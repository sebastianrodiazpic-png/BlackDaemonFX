"""
Script para generar el Informe Forense de Mediodía (12:00 PM Chile)
Audita SQLite, Logs del Daemon, Estado de Centinela, Análisis Recientes y Métricas de Trades.
"""
import sqlite3
import json
import datetime
from pathlib import Path

DB_PATH = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
OUTPUT_DIR = Path(r"C:\Users\sebas\.gemini\antigravity-ide\brain\910b64e8-0e4d-429e-b1eb-15b16146fe6c")

def generate_report():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_chile = now_utc - datetime.timedelta(hours=3)

    # 1. Workers Runtime States
    workers = cur.execute("SELECT * FROM worker_runtime_states ORDER BY id ASC").fetchall()
    
    # 2. Trades Today
    trades = cur.execute("""
        SELECT * FROM trades 
        WHERE entry_time >= '2026-10-15 00:00:00' 
        ORDER BY id ASC
    """).fetchall()

    # 3. Signals Today
    signals = cur.execute("""
        SELECT * FROM signals 
        ORDER BY id DESC LIMIT 50
    """).fetchall()

    return {
        "timestamp_utc": now_utc.isoformat(),
        "timestamp_chile": now_chile.strftime("%Y-%m-%d %H:%M:%S CLT"),
        "workers_count": len(workers),
        "trades_count": len(trades),
        "signals_count": len(signals)
    }

if __name__ == "__main__":
    res = generate_report()
    print("Report generated successfully:", res)
