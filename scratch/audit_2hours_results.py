import sqlite3
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
cur = conn.cursor()

start_time = '2026-10-13 14:10:00'

# 1. Worker status
cur.execute("SELECT cycle_number, status, last_action, last_reason, updated_at FROM worker_runtime_states WHERE bot_profile='MALAYSIAN_SNR' ORDER BY updated_at DESC LIMIT 1")
worker = cur.fetchone()

# 2. Trades
cur.execute("SELECT id, instrument, direction, status, entry_time, exit_time, net_pnl, realized_rr, strategy_version, details_json FROM trade_journal WHERE entry_time >= ? ORDER BY id ASC", (start_time,))
trades = cur.fetchall()

# 3. Audit events
cur.execute("SELECT instrument, action, reason, payload_json, cycle_number, event_time FROM daemon_audit_events WHERE source='DEMO' AND event_type='SYMBOL_PROCESS_RESULT' AND payload_json LIKE '%MALAYSIAN_SNR%' AND event_time >= ? ORDER BY id ASC", (start_time,))
events = cur.fetchall()

reasons = Counter()
scenarios = Counter()
stages = Counter()
symbols_with_setups = set()
retest_confirmed_events = []

for inst, act, rsn, p_json, cycle, ev_time in events:
    reasons[rsn] += 1
    try:
        p = json.loads(p_json or '{}')
    except Exception:
        continue
    diag = (p.get('result') or {}).get('diagnostics') or {}
    sc = diag.get('scenario')
    st = diag.get('stage')
    if sc:
        scenarios[sc] += 1
        symbols_with_setups.add(inst)
    if st:
        stages[st] += 1
    if st == 'RETEST_CONFIRMED' or p.get('result', {}).get('valid'):
        retest_confirmed_events.append({
            'time': ev_time,
            'instrument': inst,
            'scenario': sc,
            'action': act,
            'reason': rsn
        })

print("=== AUDITORIA DE 2 HORAS (14:10 UTC a 16:11 UTC) ===")
print(f"Ciclos ejecutados: {worker[0]}")
print(f"Estado del worker: {worker[1]} ({worker[2]}, ultimo motivo: {worker[3]})")
print(f"Total de evaluaciones de símbolos: {len(events)}")
print(f"\nSímbolos con setups detectados ({len(symbols_with_setups)}):")
print(", ".join(sorted(symbols_with_setups)))

print("\nEscenarios detectados en el embudo:")
for sc, count in scenarios.most_common():
    print(f"  - {sc}: {count} veces")

print("\nEtapas del embudo (Stages):")
for st, count in stages.most_common():
    print(f"  - {st}: {count}")

print("\nTop 10 motivos de espera / filtro:")
for r, count in reasons.most_common(10):
    print(f"  - {r}: {count}")

print(f"\nEventos con RETEST_CONFIRMED ({len(retest_confirmed_events)}):")
for ev in retest_confirmed_events:
    print(f"  [{ev['time']}] {ev['instrument']} | {ev['scenario']} | Action: {ev['action']} | Reason: {ev['reason']}")

print(f"\nOperaciones en trade_journal ({len(trades)}):")
total_pnl = 0.0
for t in trades:
    pnl = t[6] or 0.0
    total_pnl += pnl
    print(f"  - #{t[0]}: {t[1]} {t[2]} | Status: {t[3]} | Entry: {t[4]} | Exit: {t[5]} | Net PnL: ${pnl:.2f} | RR: {t[7]}")
print(f"Total PnL periodo: ${total_pnl:.2f}")
