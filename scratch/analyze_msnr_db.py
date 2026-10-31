import sqlite3
import json

for db_path in ['trading_bot.sqlite3', 'storage/trading_bot.sqlite3']:
    print(f"=== DB: {db_path} ===")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT id, instrument, direction, status, pnl, profit_loss, planned_rr, details, opened_at, closed_at
        FROM trades
        WHERE details LIKE '%MALAYSIAN_SNR%' OR details LIKE '%MSNR%'
        ORDER BY opened_at ASC
    """)
    rows = c.fetchall()
    print(f"Total MSNR trades: {len(rows)}")
    wins, losses, be = 0, 0, 0
    total_pnl = 0.0
    by_day = {}
    for r in rows:
        pnl = r[4] if r[4] is not None else (r[5] if r[5] is not None else 0.0)
        total_pnl += pnl
        day = str(r[8])[:10] if r[8] else 'unknown'
        by_day.setdefault(day, {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0})
        by_day[day]['trades'] += 1
        by_day[day]['pnl'] += pnl
        if pnl > 0.01:
            wins += 1
            by_day[day]['wins'] += 1
        elif pnl < -0.01:
            losses += 1
            by_day[day]['losses'] += 1
        else:
            be += 1
    print(f"Wins: {wins}, Losses: {losses}, BE: {be}, Total PnL: ${total_pnl:.2f}")
    for day, stats in sorted(by_day.items()):
        print(f"  {day}: {stats['trades']} trades | {stats['wins']}W / {stats['losses']}L | PnL: ${stats['pnl']:.2f}")
