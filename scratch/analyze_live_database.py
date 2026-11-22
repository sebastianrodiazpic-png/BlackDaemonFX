import sqlite3, os, json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
print(f"Connecting RO to {db_path}...")
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("\n================ 1. RECENT AUDIT EVENTS (LAST 2,000) ================")
cur.execute("""
    SELECT event_type, action, reason, instrument, COUNT(*) as cnt
    FROM daemon_audit_events
    WHERE id >= (SELECT MAX(id) - 2000 FROM daemon_audit_events)
    GROUP BY event_type, action, reason
    ORDER BY cnt DESC
    LIMIT 30
""")
for r in cur.fetchall():
    print(f"[{r['cnt']:4}x] {r['event_type']} | act={r['action']} | reas={r['reason']}")

print("\n================ 2. SPECIFIC REJECTION REASONS IN AUDIT EVENTS ================")
cur.execute("""
    SELECT action, reason, instrument, COUNT(*) as cnt
    FROM daemon_audit_events
    WHERE action LIKE '%BLOCK%' OR action LIKE '%REJECT%' OR action LIKE '%VETO%' OR action LIKE '%GUARD%' OR reason LIKE '%BLOCK%' OR reason LIKE '%REJECT%'
    GROUP BY action, reason, instrument
    ORDER BY cnt DESC
    LIMIT 30
""")
for r in cur.fetchall():
    print(f"[{r['cnt']:4}x] {r['instrument']} | act={r['action']} | reas={r['reason']}")

print("\n================ 3. TRADES SUMMARY & PERFORMANCE BY STRATEGY ================")
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
    tot = r['wins'] + r['losses']
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"Source: {r['source']} | Trades: {r['total_trades']} (Open: {r['open_trades']}) | W/L/BE: {r['wins']}/{r['losses']}/{r['be']} (WR: {wr:.1f}%) | Total R: {r['total_rr']} | Total PnL: ${r['total_pnl']}")

print("\n================ 4. PERFORMANCE BY INSTRUMENT (TOP 20 & WORST 10) ================")
cur.execute("""
    SELECT 
        instrument,
        COUNT(*) as total,
        SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(realized_rr), 2) as total_rr,
        ROUND(SUM(net_pnl), 2) as total_pnl
    FROM trades
    WHERE status = 'CLOSED'
    GROUP BY instrument
    HAVING total >= 5
    ORDER BY total_rr DESC
""")
all_instr = cur.fetchall()
print(f"--- Top 15 Best Performing Instruments (by Net R) ---")
for r in all_instr[:15]:
    tot = r['wins'] + r['losses']
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"  {r['instrument']:25} | N={r['total']:3} | WR={wr:5.1f}% | Net R={r['total_rr']:+6.2f}R | PnL=${r['total_pnl']:+8.2f}")

print(f"\n--- Worst 10 Performing Instruments (by Net R) ---")
for r in all_instr[-10:]:
    tot = r['wins'] + r['losses']
    wr = (r['wins'] / tot * 100) if tot > 0 else 0
    print(f"  {r['instrument']:25} | N={r['total']:3} | WR={wr:5.1f}% | Net R={r['total_rr']:+6.2f}R | PnL=${r['total_pnl']:+8.2f}")

print("\n================ 5. CENTINELA (MARKET REGIME) AUDIT EVENTS ================")
cur.execute("""
    SELECT action, reason, COUNT(*) as cnt
    FROM daemon_audit_events
    WHERE event_type LIKE '%REGIME%' OR action LIKE '%REGIME%'
    GROUP BY action, reason
    ORDER BY cnt DESC
""")
regime_events = cur.fetchall()
for r in regime_events:
    print(f"  [{r['cnt']:4}x] act={r['action']} | reas={r['reason']}")

print("\n================ 6. RECENT 10 TRADES EXECUTED ================")
cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, status, result, entry_time, exit_time, entry_price, exit_price, realized_rr, net_pnl, exit_reason
    FROM trades
    ORDER BY id DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  #{r['id']} | {r['instrument']} {r['direction']} | {r['status']} ({r['result']}) | In: {r['entry_time'][:16]} Out: {str(r['exit_time'])[:16]} | R: {r['realized_rr']} | PnL: ${r['net_pnl']} | Exit: {r['exit_reason']}")

print("\n================ 7. POSITION VISUAL AUDITS SAMPLE ================")
cur.execute("""
    SELECT id, source, bot_profile, instrument, updated_at
    FROM position_visual_audits
    ORDER BY id DESC
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  Audit #{r['id']} | {r['instrument']} | profile={r['bot_profile']} | updated={r['updated_at']}")

conn.close()
