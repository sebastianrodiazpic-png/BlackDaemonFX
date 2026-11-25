import sqlite3
import pandas as pd

db_path = "file:storage/live_trading_bot.sqlite3?mode=ro"
conn = sqlite3.connect(db_path, uri=True)

df = pd.read_sql_query("SELECT * FROM trades", conn)
closed = df[df['status'].isin(['CLOSED', 'closed']) | df['exit_time'].notnull()].copy()
closed['entry_time'] = pd.to_datetime(closed['entry_time'])
closed['exit_time'] = pd.to_datetime(closed['exit_time'])

recent = closed[closed['entry_time'] >= '2026-11-01'].copy()
print(f"Trades desde el 1 de Noviembre 2026: {len(recent)}")

if len(recent) > 0:
    wins = recent[recent['net_pnl'] > 0]
    losses = recent[recent['net_pnl'] < 0]
    wr = len(wins) / len(recent) * 100
    print(f"Noviembre PnL: ${recent['net_pnl'].sum():,.2f}")
    print(f"Noviembre WR: {wr:.2f}% | Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"Noviembre Realized R sum: {recent['realized_rr'].sum():.2f} R")
    
    print("\n--- Rendimiento por instrumento en Noviembre ---")
    inst_nov = recent.groupby('instrument').agg(
        n=('id', 'count'),
        net_pnl=('net_pnl', 'sum'),
        wr=('net_pnl', lambda x: (x > 0).mean() * 100),
        sum_r=('realized_rr', 'sum'),
        avg_r=('realized_rr', 'mean')
    ).sort_values('net_pnl')
    print(inst_nov.to_string())

last_7d = closed[closed['entry_time'] >= '2026-11-16'].copy()
print(f"\nTrades en los últimos 7 días (desde 16-nov): {len(last_7d)}")
if len(last_7d) > 0:
    print(f"Últimos 7 días PnL: ${last_7d['net_pnl'].sum():,.2f}")
    print(f"Últimos 7 días WR: {(last_7d['net_pnl'] > 0).mean()*100:.2f}%")
    print("\nTrades por instrumento en los últimos 7 días:")
    print(last_7d.groupby('instrument').agg(
        n=('id', 'count'),
        net_pnl=('net_pnl', 'sum'),
        wr=('net_pnl', lambda x: (x > 0).mean() * 100),
        sum_r=('realized_rr', 'sum')
    ).sort_values('net_pnl').to_string())

conn.close()
