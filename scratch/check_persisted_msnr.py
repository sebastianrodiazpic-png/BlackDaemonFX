import sqlite3
import os
import json

db_path = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

for t in ['system_settings', 'strategy_settings', 'configurations', 'runtime_settings']:
    if t in tables:
        print(f"\n--- TABLE {t} ---")
        c.execute(f"SELECT * FROM {t};")
        for row in c.fetchall():
            k = row[0] if len(row) > 1 else 'row'
            v = row[1] if len(row) > 1 else str(row)
            try:
                parsed = json.loads(v)
                print(f"{k}: (json with {len(parsed)} keys)")
                if 'asset_modes' in parsed:
                    print("  asset_modes:", parsed.get('asset_modes'))
                if 'breaker_pair_mode' in parsed:
                    print("  breaker_pair_mode:", parsed.get('breaker_pair_mode'))
                if 'retest_pinbar_mode' in parsed:
                    print("  retest_pinbar_mode:", parsed.get('retest_pinbar_mode'))
                if 'continuation_mode' in parsed:
                    print("  continuation_mode:", parsed.get('continuation_mode'))
                if 'retest_window_minutes' in parsed:
                    print("  retest_window_minutes:", parsed.get('retest_window_minutes'))
                if 'session_policy' in parsed:
                    print("  session_policy:", parsed.get('session_policy'))
            except Exception:
                print(f"{k}: {str(v)[:100]}")
