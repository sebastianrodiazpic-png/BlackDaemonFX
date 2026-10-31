import sys
sys.path.insert(0, ".")
from database.repository import TradingRepository

repo = TradingRepository()
print("DB Path:", repo.db_path)
open_trades = repo.open_trades(source="DEMO")
print(f"Open trades: {len(open_trades)}")
for t in open_trades:
    print(" ", t)

from database.models import Trade
with repo.session_scope() as session:
    last_trades = session.query(Trade).order_by(Trade.id.desc()).limit(5).all()
    print(f"\nLast 5 trades in DB:")
    for t in last_trades:
        print(f"  ID={t.id} | {t.symbol} | {t.direction} | Status={t.status} | Created={t.created_at} | Closed={t.closed_at}")
