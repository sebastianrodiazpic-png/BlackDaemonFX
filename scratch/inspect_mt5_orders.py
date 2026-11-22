import os
import glob
from pathlib import Path

# 1. Check recent log files in logs/
log_files = glob.glob("logs/**/*.log", recursive=True) + glob.glob("*.log")
print("Found log files:", len(log_files))
for lf in sorted(log_files, key=os.path.getmtime, reverse=True)[:5]:
    print("Recent log:", lf, "size:", os.path.getsize(lf))
    with open(lf, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print(f"  Last 5 lines of {lf}:")
        for line in lines[-5:]:
            print("   ", line.strip())

# 2. Check if we can inspect MT5 connector / open positions via mt5_trade_executor or MetaTrader5
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        print("\n--- MT5 Connected ---")
        positions = mt5.positions_get()
        print("Open positions count:", len(positions) if positions else 0)
        if positions:
            for p in positions:
                print(f"Pos ticket={p.ticket} sym={p.symbol} magic={p.magic} type={p.type} vol={p.volume} open={p.price_open} sl={p.sl} tp={p.tp} pnl={p.profit} comment={p.comment}")
        orders = mt5.orders_get()
        print("Pending orders count:", len(orders) if orders else 0)
        if orders:
            for o in orders:
                print(f"Order ticket={o.ticket} sym={o.symbol} magic={o.magic} type={o.type} vol={o.volume_current} open={o.price_open} sl={o.sl} tp={o.tp} comment={o.comment}")
        mt5.shutdown()
    else:
        print("MT5 initialize returned False")
except Exception as e:
    print("MT5 check exception:", e)
