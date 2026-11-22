import os
from database.repository import TradingRepository

repo = TradingRepository()

print("=== WORKER RUNTIME STATES ===")
try:
    workers = repo.worker_runtime_states(source="DEMO")
    for w in workers:
        prof = w.get("bot_profile")
        pid = w.get("pid")
        magic = w.get("magic")
        cycle = w.get("cycle_number")
        sym = w.get("current_symbol")
        action = w.get("last_action")
        reason = w.get("last_reason")
        status = w.get("status")
        print(f"{prof:<16} | Status: {status:<15} | PID {pid} | Magic {magic} | Cycle {cycle} | Sym: {sym} | Action: {action} | Reason: {reason}")
except Exception as e:
    print("Error fetching workers:", e)

print("\n=== RECENT CLOSED / OPEN TRADES ===")
try:
    open_trades = repo.open_trades(source="DEMO") or []
    print(f"Open trades: {len(open_trades)}")
    for t in open_trades:
        print(f"  Trade {t.get('id')} | {t.get('instrument')} | {t.get('direction')} | {t.get('strategy_name')} | Entry: {t.get('entry_price')} | Magic: {t.get('magic')}")
except Exception as e:
    print("Error open trades:", e)

print("\n=== RECENT ANALYSIS / RECENT EVENTS ===")
try:
    if hasattr(repo, "recent_events"):
        evts = repo.recent_events(limit=20, source="DEMO")
        for e in evts[:10]:
            print(f"  Event: {e}")
except Exception as e:
    print("Error recent events:", e)

print("\n=== RECENT DECISIONS / PROCESS RESULTS ===")
try:
    if hasattr(repo, "latest_worker_process_results"):
        res = repo.latest_worker_process_results(source="DEMO")
        for k, v in res.items():
            print(f"  {k}: {v}")
except Exception as e:
    print("Error latest results:", e)
