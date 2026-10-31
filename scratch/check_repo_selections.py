import sys
sys.path.insert(0, ".")
from database.repository import TradingRepository

repo = TradingRepository()
print("Repo DB path:", repo.db_path)

valid_profiles = ["SYNTHETICS", "FOREX", "ICT", "ORB", "MALAYSIAN_SNR", "TREND_PULLBACK"]
for p in valid_profiles:
    try:
        sel = repo.latest_instrument_selection_profile(p)
        syms = sel.get("selected_symbols", []) if sel else []
        print(f"Profile: {p} -> {len(syms)} symbols in DB")
        print(f"  Symbols: {syms}")
    except Exception as e:
        print(f"Profile {p} error: {e}")

print("\n--- OPEN TRADES / POSITIONS ---")
try:
    open_trades = repo.open_trades(source="DEMO")
    print(f"Open trades (DEMO): {len(open_trades)}")
    for t in open_trades:
        print(" ", t)
except Exception as e:
    print("Error getting open trades:", e)

print("\n--- RECENT COMPLETED TRADES ---")
try:
    recent = repo.list_trades(limit=10, source="DEMO")
    print(f"Recent trades: {len(recent)}")
    for t in recent:
        print(f"  ID={t.id} | {t.symbol} | {t.direction} | Entry={t.entry_price} | Status={t.status} | Created={t.created_at} | Closed={t.closed_at} | NetR={t.net_r}")
except Exception as e:
    print("Error listing trades:", e)

print("\n--- WORKER RUNTIME STATES ---")
try:
    with repo.session_scope() as session:
        from database.models import WorkerRuntimeState
        states = session.query(WorkerRuntimeState).all()
        for s in states:
            print(f"Worker {s.worker_name:<16} PID={s.pid} Status={s.status:<12} Cycle={s.cycle_number:<4} Syms={s.symbols_processed}/{s.symbols_total} LastAction={s.last_action} LastReason={s.last_reason}")
except Exception as e:
    print("Error reading worker states:", e)
