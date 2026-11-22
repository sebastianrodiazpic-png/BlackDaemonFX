import sqlite3, os
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

flops = ['Volatility 25 Index', 'Crash 300 Index', 'Crash 600 Index', 'Jump 10 Index', 'US SP 500', 'Volatility 15 Index', 'EURUSD', 'Step Index', 'Volatility 50 (1s) Index', 'Boom 900 Index']

print("================ BREAKDOWN OF FLOP INSTRUMENTS BY STRATEGY ================")
for sym in flops:
    cur.execute(f"""
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
            COUNT(*) as cnt,
            SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
            ROUND(SUM(realized_rr), 2) as sum_r,
            ROUND(SUM(net_pnl), 2) as sum_pnl
        FROM trades
        WHERE instrument = '{sym}' AND status = 'CLOSED'
        GROUP BY strat
        ORDER BY sum_r ASC
    """)
    rows = cur.fetchall()
    print(f"\nInstrument: {sym}")
    for r in rows:
        tot = (r['wins'] or 0) + (r['losses'] or 0)
        wr = (r['wins'] / tot * 100) if tot > 0 else 0
        print(f"  {r['strat']:16} | N={r['cnt']:3} | WR={wr:5.1f}% | Net R={r['sum_r']:+6.2f}R | PnL=${r['sum_pnl']:+8.2f}")

conn.close()
