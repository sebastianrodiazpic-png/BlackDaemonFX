import sqlite3
import pandas as pd
import sys

for s in [sys.stdout, sys.stderr]:
    try: s.reconfigure(encoding="utf-8")
    except: pass

paths = [
    "storage/trading_bot.sqlite3",
    "storage/trades.db",
    "storage/trading_system.db",
    "storage/database.sqlite"
]

for p in paths:
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"\n=== Base: {p} ===")
        print("Tablas:", tables)
        for t in ["trades", "positions", "audit_events", "events"]:
            if t in tables:
                cnt = conn.execute(f"SELECT COUNT() FROM {t}").fetchone()[0]
                print(f"  Tabla {t}: {cnt} registros")
                if t == "trades":
                    df = pd.read_sql_query(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 5", conn)
                    cols = [c for c in ['id', 'instrument', 'direction', 'status', 'entry_time', 'close_time', 'pnl', 'exit_reason', 'strategy_name'] if c in df.columns]
                    print(df[cols].to_string())
                    open_trades = pd.read_sql_query(f"SELECT * FROM {t} WHERE status = 'OPEN'", conn)
                    print(f"  Trades OPEN ({len(open_trades)}):")
                    if not open_trades.empty:
                        print(open_trades[cols].to_string())
                elif t in ["audit_events", "events"]:
                    df_ev = pd.read_sql_query(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 5", conn)
                    print(df_ev.to_string())
    except Exception as e:
        print(f"Error en {p}: {e}")
