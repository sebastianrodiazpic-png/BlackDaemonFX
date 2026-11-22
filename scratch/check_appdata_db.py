import sqlite3

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in main DB:", tables)
for t in tables:
    cnt = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"  {t}: {cnt} rows")
    if 'instrument' in cols:
        step_cnt = conn.execute(f"SELECT instrument, count(*) FROM {t} WHERE instrument LIKE '%Step%' GROUP BY instrument").fetchall()
        print(f"    Step rows in {t} (by instrument): {step_cnt}")
    if 'symbol' in cols:
        step_cnt = conn.execute(f"SELECT symbol, count(*) FROM {t} WHERE symbol LIKE '%Step%' GROUP BY symbol").fetchall()
        print(f"    Step rows in {t} (by symbol): {step_cnt}")

# Let's also check recent trades and signals for Step
print("\n--- Recent signals for Step Index 400 or 500 ---")
for t in ['signals', 'daemon_audit_events']:
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()]
    sym_col = 'instrument' if 'instrument' in cols else ('symbol' if 'symbol' in cols else None)
    if sym_col:
        rows = conn.execute(f"SELECT * FROM {t} WHERE {sym_col} LIKE '%Step%' ORDER BY id DESC LIMIT 10").fetchall()
        print(f"{t} (Step):", len(rows))
        for r in rows:
            print(" ", r)

# Let's check instrument_selection_profile_preferences
print("\n--- instrument_selection_profile_preferences ---")
for r in conn.execute("SELECT * FROM instrument_selection_profile_preferences").fetchall():
    print(" ", r)

conn.close()
