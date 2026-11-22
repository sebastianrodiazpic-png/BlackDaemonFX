import sqlite3, os
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("================ 1. TRADES PERFORMANCE BY SOURCE ================")
cur.execute("""
    SELECT 
        COALESCE(source, 'UNKNOWN') as source,
        COUNT(*) as total_trades,
        SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_trades,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN result = 'BE' OR result = 'BREAK_EVEN' THEN 1 ELSE 0 END) as be,
        ROUND(AVG(realized_rr), 3) as avg_rr,
        ROUND(SUM(realized_rr), 2) as total_rr,
        ROUND(SUM(net_pnl), 2) as total_pnl
    FROM trades
    GROUP BY source
""")
for r in cur.fetchall():
    tot = (r['wins'] or 0) + (r['losses'] or 0)
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"Source: {r['source']} | Total: {r['total_trades']} (Open: {r['open_trades']}) | W/L/BE: {r['wins']}/{r['losses']}/{r['be']} (WR: {wr:.1f}%) | Total R: {r['total_rr']} | Total PnL: ${r['total_pnl']}")

print("\n================ 2. PERFORMANCE BY STRATEGY (PARSED FROM DETAILS/TICKET) ================")
cur.execute("""
    SELECT 
        CASE 
            WHEN execution_key LIKE '%MSNR%' OR setup_reason LIKE '%MSNR%' THEN 'MALAYSIAN_SNR'
            WHEN execution_key LIKE '%ICT%' OR setup_reason LIKE '%ICT%' THEN 'ICT'
            WHEN execution_key LIKE '%ORB%' OR setup_reason LIKE '%ORB%' THEN 'ORB'
            WHEN execution_key LIKE '%CARRY%' THEN 'CARRY'
            WHEN execution_key LIKE '%RSI2%' THEN 'RSI2'
            WHEN execution_key LIKE '%TREND%' THEN 'TREND_PULLBACK'
            ELSE 'OTHER/MANUAL'
        END as strat,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN result IN ('BE', 'BREAK_EVEN') THEN 1 ELSE 0 END) as be,
        ROUND(SUM(realized_rr), 2) as sum_r,
        ROUND(SUM(net_pnl), 2) as sum_pnl
    FROM trades
    WHERE status = 'CLOSED'
    GROUP BY strat
""")
for r in cur.fetchall():
    tot = (r['wins'] or 0) + (r['losses'] or 0)
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"Strat: {r['strat']:16} | Total: {r['total']:4} | W/L/BE: {r['wins']}/{r['losses']}/{r['be']} | WR: {wr:5.1f}% | Net R: {r['sum_r']:+7.2f}R | PnL: ${r['sum_pnl']:+8.2f}")

print("\n================ 3. TOP & FLOPPING INSTRUMENTS ================")
cur.execute("""
    SELECT 
        instrument,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(realized_rr), 2) as sum_r,
        ROUND(SUM(net_pnl), 2) as sum_pnl
    FROM trades
    WHERE status = 'CLOSED'
    GROUP BY instrument
    HAVING total >= 8
    ORDER BY sum_r DESC
""")
rows = cur.fetchall()
print("Top 10 Instruments:")
for r in rows[:10]:
    tot = (r['wins'] or 0) + (r['losses'] or 0)
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"  {r['instrument']:25} | N={r['total']:3} | WR={wr:5.1f}% | Net R={r['sum_r']:+6.2f}R | PnL=${r['sum_pnl']:+8.2f}")

print("\nFlop 10 Instruments:")
for r in rows[-10:]:
    tot = (r['wins'] or 0) + (r['losses'] or 0)
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"  {r['instrument']:25} | N={r['total']:3} | WR={wr:5.1f}% | Net R={r['sum_r']:+6.2f}R | PnL=${r['sum_pnl']:+8.2f}")

print("\n================ 4. RECENT AUDIT EVENTS (LAST 5,000 ROWS) ================")
cur.execute("SELECT MAX(id) FROM daemon_audit_events")
max_id = cur.fetchone()[0] or 0
cur.execute(f"""
    SELECT action, reason, COUNT(*) as cnt
    FROM daemon_audit_events
    WHERE id >= {max_id - 5000}
    GROUP BY action, reason
    ORDER BY cnt DESC
    LIMIT 25
""")
for r in cur.fetchall():
    print(f"  [{r['cnt']:4}x] act={r['action']} | reas={r['reason']}")

print("\n================ 5. OPEN POSITIONS RIGHT NOW ================")
cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, volume, entry_price, stop_loss, take_profit, opened_at, created_at
    FROM trades
    WHERE status = 'OPEN'
""")
open_pos = cur.fetchall()
print(f"Open positions in trades table: {len(open_pos)}")
for p in open_pos:
    print(f"  Ticket={p['broker_position_ticket']} | {p['instrument']} {p['direction']} vol={p['volume']} @ {p['entry_price']} | SL={p['stop_loss']} TP={p['take_profit']}")

conn.close()
