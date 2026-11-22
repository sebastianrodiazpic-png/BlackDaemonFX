"""
Script de investigación profunda sobre la base de datos de producción:
C:\\Users\\sebas\\AppData\\Local\\BlackDaemonFx\\trading_bot.sqlite3
"""
import sys
import os
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

print("=" * 80)
print("1. EVENTOS DE AUDITORÍA REGISTRADOS TRAS EL REINICIO (18:26 UTC)")
print("=" * 80)

# Busquemos eventos desde las 18:00 UTC de hoy
cutoff = "2026-11-14 18:00:00"

c = conn.cursor()
q_types = """
SELECT event_type, action, count(*) 
FROM daemon_audit_events 
WHERE event_time >= ? 
GROUP BY event_type, action 
ORDER BY count(*) DESC
"""
print("Resumen de eventos desde las 18:00 UTC:")
for row in c.execute(q_types, (cutoff,)).fetchall():
    print(f"  {row[0]} | {row[1]}: {row[2]}")

print("\n" + "=" * 80)
print("2. VETOS O BLOQUEOS EN ÍNDICES SINTÉTICOS TRAS EL REINICIO")
print("=" * 80)

synth_terms = "('volatility', 'boom', 'crash', 'jump', 'step', 'ladder', 'volswitch')"
q_synth_audit = f"""
SELECT event_time, instrument, event_type, action, reason, payload_json 
FROM daemon_audit_events 
WHERE event_time >= ? 
  AND (
    LOWER(instrument) LIKE '%volatility%' OR 
    LOWER(instrument) LIKE '%boom%' OR 
    LOWER(instrument) LIKE '%crash%' OR 
    LOWER(instrument) LIKE '%jump%' OR 
    LOWER(instrument) LIKE '%step%' OR 
    LOWER(instrument) LIKE '%ladder%' OR 
    LOWER(instrument) LIKE '%volswitch%'
  )
ORDER BY event_time DESC 
LIMIT 50
"""

rows = c.execute(q_synth_audit, (cutoff,)).fetchall()
print(f"Total eventos encontrados para sintéticos desde las 18:00 UTC: {len(rows)}")
for r in rows[:25]:
    payload_str = ""
    if r[5]:
        try:
            p = json.loads(r[5])
            # extract key info
            sub = {k: v for k, v in p.items() if k in ('score', 'grade', 'reason', 'stage', 'action', 'ai_probability', 'tripartite_action', 'rule')}
            payload_str = str(sub)
        except Exception:
            payload_str = str(r[5])[:120]
    print(f"  [{r[0]}] {r[1]} | {r[2]} | {r[3]} | Reason: {r[4]} | Payload: {payload_str}")

print("\n" + "=" * 80)
print("3. SEÑALES GENERADAS EN SINTÉTICOS (HOY 14-NOV)")
print("=" * 80)
q_signals = """
SELECT created_at, symbol, direction, strategy, timeframe, status, reason, payload_json
FROM signals 
WHERE created_at >= '2026-11-14 00:00:00'
  AND (
    LOWER(symbol) LIKE '%volatility%' OR 
    LOWER(symbol) LIKE '%boom%' OR 
    LOWER(symbol) LIKE '%crash%' OR 
    LOWER(symbol) LIKE '%jump%' OR 
    LOWER(symbol) LIKE '%step%' OR 
    LOWER(symbol) LIKE '%ladder%' OR 
    LOWER(symbol) LIKE '%volswitch%'
  )
ORDER BY created_at DESC 
LIMIT 30
"""
sig_rows = c.execute(q_signals).fetchall()
print(f"Total señales hoy en sintéticos: {len(sig_rows)}")
for s in sig_rows[:20]:
    print(f"  [{s[0]}] {s[1]} | Dir: {s[2]} | Strat: {s[3]} | TF: {s[4]} | Status: {s[5]} | Reason: {s[6]}")

print("\n" + "=" * 80)
print("4. TRADES EN SINTÉTICOS (HOY 14-NOV)")
print("=" * 80)
q_trades = """
SELECT created_at, symbol, direction, magic, status, profit, comment
FROM trades 
WHERE created_at >= '2026-11-14 00:00:00'
ORDER BY created_at DESC 
LIMIT 20
"""
tr_rows = c.execute(q_trades).fetchall()
print(f"Total trades hoy en la base: {len(tr_rows)}")
for t in tr_rows:
    print(f"  [{t[0]}] {t[1]} | Dir: {t[2]} | Magic: {t[3]} | Status: {t[4]} | Profit: {t[5]} | Comm: {t[6]}")

print("\n" + "=" * 80)
print("5. ANÁLISIS DE WORKERS Y CICLOS ACTIVOS (ÚLTIMA HORA)")
print("=" * 80)
q_worker_status = """
SELECT worker_name, status, last_cycle_at, cycles_count, errors_count, metadata_json
FROM worker_status
ORDER BY last_cycle_at DESC
LIMIT 20
"""
try:
    ws_rows = c.execute(q_worker_status).fetchall()
    print("Estado de workers en worker_status:")
    for w in ws_rows:
        print(f"  Worker: {w[0]} | Status: {w[1]} | Last Cycle: {w[2]} | Cycles: {w[3]} | Errors: {w[4]}")
except Exception as e:
    print("Error consultando worker_status:", e)

conn.close()
