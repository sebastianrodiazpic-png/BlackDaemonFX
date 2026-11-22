import os
import glob
import datetime
import sqlite3
import json

now = datetime.datetime.now()
print(f"=== HORA ACTUAL LOCAL: {now} ===")

# 1. Chequear timestamps de los logs
print("\n--- TIMESTAMPS DE LOGS DE BOTS ---")
for p in sorted(glob.glob("storage/logs/bots/*.log")):
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
    delta = (now - mtime).total_seconds()
    size = os.path.getsize(p)
    print(f"{os.path.basename(p):<22} | {size:>10} bytes | modificado hace {delta:.1f}s ({mtime})")

# 2. Chequear la base viva en AppData
p = 'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
if os.path.exists(p):
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    cur = conn.cursor()
    
    print("\n--- WORKER RUNTIME STATES (POST-REINICIO) ---")
    cur.execute("SELECT id, bot_profile, status, pid, cycle_number, last_action, last_reason, updated_at FROM worker_runtime_states ORDER BY id")
    for r in cur.fetchall():
        print(f"ID {r[0]:>2} | Profile: {str(r[1]):<15} | Status: {str(r[2]):<20} | PID: {r[3]} | Ciclo: {r[4]} | Acción: {str(r[5]):<25} | {r[7]}")
        
    print("\n--- EVENTOS RECIENTES EN DAEMON_AUDIT_EVENTS (ÚLTIMOS 15) ---")
    cur.execute("""
        SELECT id, created_at, source, event_type, instrument, action, reason
        FROM daemon_audit_events
        ORDER BY id DESC LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"[{r[1]}] ID:{r[0]} | {r[2]} | {r[3]} | Inst:{r[4]} | Action:{r[5]} | Reason:{r[6]}")

    print("\n--- ÚLTIMAS SEÑALES PERSISTIDAS (ÚLTIMAS 5) ---")
    cur.execute("""
        SELECT id, instrument, timeframe, signal_time, direction, valid, created_at
        FROM signals
        ORDER BY id DESC LIMIT 5
    """)
    for r in cur.fetchall():
        print(f"Signal #{r[0]} | {r[1]} {r[2]} {r[4]} | valid={r[5]} | signal_time: {r[3]} | saved: {r[6]}")

    print("\n--- TRADES ACTIVOS O RECIENTES ---")
    cur.execute("SELECT id, external_ticket, instrument, direction, status, entry_price, stop_loss, take_profit, created_at FROM trades ORDER BY id DESC LIMIT 5")
    for r in cur.fetchall():
        print(f"Trade #{r[0]} | Ticket: {r[1]} | {r[2]} {r[3]} | Status: {r[4]} | Entry: {r[5]} | SL: {r[6]} | TP: {r[7]} | {r[8]}")

    conn.close()
