import sqlite3
import os
import json

db_path = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
print("Connecting to:", db_path)
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("\n--- TRADES BY DATE (entry_time) ---")
q1 = """
SELECT substr(entry_time, 1, 10) as dt, source, count(*), round(sum(net_pnl), 2), 
       round(sum(case when net_pnl > 0 then 1.0 else 0.0 end)/count(*)*100, 1) as wr
FROM trades
WHERE entry_time >= '2026-10-01'
GROUP BY dt, source
ORDER BY dt, source;
"""
for row in c.execute(q1).fetchall():
    print(row)

print("\n--- OCT 4 TO OCT 10 BY INSTRUMENT ---")
q2 = """
SELECT instrument, count(*), round(sum(net_pnl), 2), 
       round(sum(case when net_pnl > 0 then 1.0 else 0.0 end)/count(*)*100, 1) as wr,
       round(avg(realized_rr), 2) as avg_rr
FROM trades
WHERE entry_time >= '2026-10-04' AND entry_time <= '2026-10-10 23:59:59'
GROUP BY instrument
ORDER BY count(*) DESC;
"""
for row in c.execute(q2).fetchall():
    print(row)

print("\n--- OCT 4 TO OCT 10 BY SETUP REASON ---")
q3 = """
SELECT setup_reason, count(*), round(sum(net_pnl), 2),
       round(sum(case when net_pnl > 0 then 1.0 else 0.0 end)/count(*)*100, 1) as wr
FROM trades
WHERE entry_time >= '2026-10-04' AND entry_time <= '2026-10-10 23:59:59'
GROUP BY setup_reason
ORDER BY count(*) DESC;
"""
for row in c.execute(q3).fetchall():
    print(row)

print("\n--- OCT 11 TO OCT 13 TRADES ---")
q4 = """
SELECT id, instrument, entry_time, exit_time, direction, net_pnl, exit_reason, setup_reason, details_json
FROM trades
WHERE entry_time >= '2026-10-11'
ORDER BY id DESC;
"""
for row in c.execute(q4).fetchall():
    print(row[:8])
    if row[8]:
        try:
            d = json.loads(row[8])
            print("   details:", {k: d[k] for k in list(d.keys())[:5]})
        except Exception:
            pass
