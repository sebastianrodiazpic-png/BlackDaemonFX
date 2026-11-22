import sqlite3

for db_path in ['database/trading_bot.sqlite3', 'storage/trading_bot.sqlite3']:
    print(f"=== {db_path} ===")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for sym in ['Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500']:
        cur.execute("""
            SELECT COUNT(*), 
                   SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END), 
                   SUM(CASE WHEN net_pnl <= 0 THEN 1 ELSE 0 END), 
                   SUM(net_pnl) 
            FROM trades 
            WHERE instrument = ?
        """, (sym,))
        row = cur.fetchone()
        cnt, wins, losses, pnl = row[0], row[1] or 0, row[2] or 0, row[3] or 0.0
        wr = (wins / cnt * 100.0) if cnt > 0 else 0.0
        print(f"  {sym:<15}: {cnt:>3} trades vivo | {wins:>3} wins | {losses:>3} losses | WR: {wr:>5.1f}% | PnL: ${pnl:>9,.2f}")
