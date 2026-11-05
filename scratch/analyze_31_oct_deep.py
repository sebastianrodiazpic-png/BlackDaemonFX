import sqlite3
import pandas as pd
import json

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)

query = """
SELECT id, external_ticket, instrument, direction, status, result, 
       entry_time, exit_time, entry_price, exit_price, stop_loss, take_profit,
       realized_rr, exit_reason, net_pnl, setup_reason, details_json, created_at
FROM trades 
WHERE created_at LIKE '2026-10-31%' OR exit_time LIKE '2026-10-31%'
ORDER BY id ASC
"""

df = pd.read_sql_query(query, conn)
print(f"Total trades on 2026-10-31: {len(df)}")
print(f"Total net PnL: ${df['net_pnl'].sum():.2f}")
print(f"Total realized RR: {df['realized_rr'].sum():.2f} R")

# Wins vs losses
wins = df[df['net_pnl'] > 0]
losses = df[df['net_pnl'] < 0]
be = df[df['net_pnl'] == 0]
open_t = df[df['status'] == 'OPEN']

print(f"Wins: {len(wins)} (${wins['net_pnl'].sum():.2f})")
print(f"Losses: {len(losses)} (${losses['net_pnl'].sum():.2f})")
print(f"BE: {len(be)}")
print(f"Open: {len(open_t)}")
if len(wins) + len(losses) > 0:
    print(f"Win Rate: {len(wins) / (len(wins) + len(losses)) * 100:.1f}%")

print("\n=== BREAKDOWN BY INSTRUMENT ===")
inst_summary = df.groupby('instrument').agg(
    trades=('id', 'count'),
    net_pnl=('net_pnl', 'sum'),
    realized_rr=('realized_rr', 'sum'),
    wins=('net_pnl', lambda x: (x > 0).sum()),
    losses=('net_pnl', lambda x: (x < 0).sum())
).reset_index()
inst_summary['wr'] = inst_summary['wins'] / (inst_summary['wins'] + inst_summary['losses']) * 100
inst_summary = inst_summary.sort_values(by='net_pnl', ascending=True)
print(inst_summary.to_string())

print("\n=== DETAILED TRADE LIST ===")
for _, r in df.iterrows():
    strat = "Unknown"
    details = {}
    try:
        details = json.loads(r['details_json'] or '{}')
        strat = details.get('strategy') or details.get('source') or details.get('worker') or r['setup_reason']
    except Exception:
        pass
    print(f"ID {r['id']} | {r['instrument']} {r['direction']} | PnL: ${r['net_pnl']} ({r['realized_rr']}R) | Result: {r['result']} | Exit: {r['exit_reason']} | Entry: {r['entry_time']} -> Exit: {r['exit_time']} | Setup: {strat}")

conn.close()
