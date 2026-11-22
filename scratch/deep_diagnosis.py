import sqlite3
import json

con = sqlite3.connect('storage/trading_bot.sqlite3')
cur = con.cursor()

print("==================================================")
print("1. RESUMEN DE TRADES EN BASE DE DATOS")
print("==================================================")
cur.execute("SELECT count(*) FROM trades")
print(f"Total registros en trades: {cur.fetchone()[0]}")
cur.execute("SELECT count(*) FROM trade_journal")
print(f"Total registros en trade_journal: {cur.fetchone()[0]}")

cur.execute("SELECT count(*), sum(case when net_pnl > 0 then 1 else 0 end), sum(case when net_pnl < 0 then 1 else 0 end), sum(coalesce(net_pnl, 0)) FROM trade_journal")
row = cur.fetchone()
print(f"Trade Journal -> Totales: {row[0]}, Ganadores: {row[1]}, Perdedores: {row[2]}, PnL Neto: {row[3]:.2f}")

print("\n--- ÚLTIMOS 15 TRADES CERRADOS EN TRADE_JOURNAL ---")
cur.execute("""
    SELECT broker_position_ticket, instrument, direction, volume, planned_rr, realized_rr, net_pnl, status, entry_time, exit_time 
    FROM trade_journal ORDER BY id DESC LIMIT 15
""")
for r in cur.fetchall():
    pnl = r[6] if r[6] is not None else 0.0
    print(f"Ticket: {r[0]} | {r[1]} {r[2]} | Vol: {r[3]} | RR_plan: {r[4]} | RR_real: {r[5]} | PnL: {pnl:.2f} | Status: {r[7]} | Entrada: {r[8]} | Salida: {r[9]}")

print("\n==================================================")
print("2. DESGLOSE DE AUDITORÍA DE EVENTOS Y VETOS")
print("==================================================")
cur.execute("""
    SELECT reason, count(*) as cnt 
    FROM daemon_audit_events 
    GROUP BY reason 
    ORDER BY cnt DESC 
    LIMIT 30
""")
print(f"{'Razón de Auditoría / Descarte':<50} | {'Conteo':<8}")
print("-" * 62)
for r in cur.fetchall():
    print(f"{str(r[0])[:50]:<50} | {r[1]:<8}")

print("\n==================================================")
print("3. ACCIONES DE AUDITORÍA POR TIPO")
print("==================================================")
cur.execute("""
    SELECT action, count(*) as cnt 
    FROM daemon_audit_events 
    GROUP BY action 
    ORDER BY cnt DESC 
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"{str(r[0])[:40]:<40} | {r[1]:<8}")

print("\n==================================================")
print("4. TOP 10 ACTIVOS CON MÁS EVENTOS Y SUS RAZONES")
print("==================================================")
cur.execute("""
    SELECT instrument, count(*) as cnt 
    FROM daemon_audit_events 
    WHERE instrument IS NOT NULL AND instrument != ''
    GROUP BY instrument 
    ORDER BY cnt DESC 
    LIMIT 10
""")
top_instruments = [r[0] for r in cur.fetchall()]
for inst in top_instruments:
    cur.execute("""
        SELECT reason, count(*) 
        FROM daemon_audit_events 
        WHERE instrument = ? 
        GROUP BY reason 
        ORDER BY count(*) DESC 
        LIMIT 3
    """, (inst,))
    reasons = cur.fetchall()
    print(f"\nActivo: {inst}")
    for rea, c in reasons:
        print(f"   -> [{c}] {rea}")

print("\n==================================================")
print("5. ESTADO DE LOS WORKERS EN RUNTIME")
print("==================================================")
cur.execute("""
    SELECT source, daemon_magic, status, cycle_number, current_symbol, last_action, last_reason, updated_at 
    FROM worker_runtime_states
""")
for r in cur.fetchall():
    print(f"Worker: {r[0]:<15} | Magic: {r[1]} | Status: {r[2]:<20} | Ciclos: {r[3]:<4} | Activo: {r[4]} | Acción: {r[5]} | Razón: {str(r[6])[:40]}")

con.close()
