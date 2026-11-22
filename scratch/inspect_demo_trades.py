import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

q = """
SELECT id, instrument, source, direction, result, planned_rr, realized_rr, net_pnl, entry_time, exit_time, exit_reason, setup_reason, details_json
FROM trades
WHERE (entry_time LIKE '2026-11-19%' OR exit_time LIKE '2026-11-19%') AND source = 'DEMO'
ORDER BY entry_time ASC
"""
df_demo = pd.read_sql_query(q, conn)
print(f"Total DEMO bot trades hoy: {len(df_demo)}")
print("PNL Total DEMO:", round(float(df_demo['net_pnl'].sum()), 2))
print("R Total DEMO:", round(float(df_demo['realized_rr'].sum()), 2))

print("\nDetalle cronológico de cada trade del BOT (DEMO):")
for idx, r in df_demo.iterrows():
    rr = float(r['realized_rr']) if pd.notnull(r['realized_rr']) else 0.0
    print(f"#{r['id']:4d} | {r['instrument']:28s} | {r['direction']:4s} | PNL: ${r['net_pnl']:+7.2f} | R: {rr:+5.2f}R | Exit: {str(r['exit_reason']):10s} | Setup: {str(r['setup_reason'])[:40]} | Hora Ent: {str(r['entry_time'])[:19]}")
