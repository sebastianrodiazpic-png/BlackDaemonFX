import sqlite3
import pandas as pd

db_path = "file:///C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3?mode=ro"
try:
    conn = sqlite3.connect(db_path, uri=True)
    print("Conexión a SQLite exitosa.")

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tablas disponibles:", tables)

    # 1. Operaciones abiertas
    open_trades = pd.read_sql_query("SELECT * FROM trades WHERE status = 'OPEN'", conn)
    print(f"\n--- POSICIONES ABIERTAS: {len(open_trades)} ---")
    if not open_trades.empty:
        cols = [c for c in ['id', 'instrument', 'direction', 'entry_price', 'stop_loss', 'take_profit', 'entry_time', 'source'] if c in open_trades.columns]
        print(open_trades[cols].to_string())

    # 2. Últimas operaciones
    recent = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC LIMIT 15", conn)
    print(f"\n--- ÚLTIMAS 15 OPERACIONES EN TRADES ---")
    recent_cols = [c for c in ['id', 'instrument', 'direction', 'status', 'entry_time', 'close_time', 'pnl', 'exit_reason', 'strategy_name'] if c in recent.columns]
    print(recent[recent_cols].to_string())

    # 3. Eventos de auditoría o rechazos
    for t in ['audit_events', 'events', 'bot_events', 'logs']:
        if t in tables:
            print(f"\n--- ÚLTIMOS REGISTROS EN {t} ---")
            ev = pd.read_sql_query(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 15", conn)
            print(ev.to_string())

except Exception as e:
    print("Error consultando SQLite:", e)
