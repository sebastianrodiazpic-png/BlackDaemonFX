"""
scratch/diagnose_signal_flow.py
===============================
Diagnóstico forense del flujo de captura de señales post-corte (17:35:16 UTC).
Conexión estrictamente de SOLO LECTURA a trading_bot.sqlite3 (?mode=ro) y shadow_research.sqlite3.
"""
import sqlite3
import json
import pandas as pd
from pathlib import Path

live_db = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
shadow_db = Path("storage/runtime/shadow_research.sqlite3")

print("=== DIAGNÓSTICO FORENSE DEL FLUJO DE CAPTURA ===")

if not live_db.exists():
    print(f"Error: No se encontró live_db en {live_db}")
    exit(1)

# Conectar en solo lectura a trading_bot.sqlite3
conn_live = sqlite3.connect(f"file:{live_db}?mode=ro", uri=True)
conn_live.row_factory = sqlite3.Row
cur_live = conn_live.cursor()

# Consultar señales generadas post 17:35:16 UTC
cur_live.execute("""
    SELECT id, created_at, signal_time, instrument, direction, valid, details_json
    FROM signals
    WHERE created_at >= '2026-10-15 17:35:16'
    ORDER BY id ASC
""")
rows_post = cur_live.fetchall()
print(f"Total señales registradas en trading_bot.sqlite3 post 17:35:16: {len(rows_post)}")

enabled_msnr = [
    'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
    'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
    'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
    'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
]

enabled_ict = [
    'XAUUSD', 'EURUSD', 'Jump 50 Index', 'Crash 300 Index', 'Boom 500 Index',
    'Boom 300 Index', 'Boom 1000 Index', 'Boom 600 Index', 'Jump 25 Index',
    'BTCUSD', 'Step Index 400', 'Wall Street 30', 'US Tech 100', 'US SP 500'
]

strat_counts = {}
eligible_ict = []
eligible_msnr = []

for r in rows_post:
    det = {}
    if r['details_json']:
        try:
            det = json.loads(r['details_json'])
        except Exception:
            pass
    strat = det.get('strategy_name', det.get('strategy', 'UNKNOWN')).upper()
    strat_counts[strat] = strat_counts.get(strat, 0) + 1
    
    sym = r['instrument']
    
    if "ICT" in strat and sym in enabled_ict:
        eligible_ict.append({
            'id': r['id'], 'created_at': r['created_at'], 'signal_time': r['signal_time'],
            'symbol': sym, 'direction': r['direction'], 'valid': r['valid'], 'details': det
        })
    elif ("MSNR" in strat or "MALAYSIAN" in strat) and sym in enabled_msnr:
        eligible_msnr.append({
            'id': r['id'], 'created_at': r['created_at'], 'signal_time': r['signal_time'],
            'symbol': sym, 'direction': r['direction'], 'valid': r['valid'], 'details': det
        })

print("\nDistribución por estrategia de las señales post-corte en trading_bot.sqlite3:")
for st, cnt in sorted(strat_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {st:<30}: {cnt} señales")

print(f"\nSeñales elegibles para ICT en universo habilitado post-corte: {len(eligible_ict)}")
for e in eligible_ict:
    print(f"  ICT: ID={e['id']} | Created={e['created_at']} | SigTime={e['signal_time']} | {e['symbol']} {e['direction']} | Valid: {e['valid']}")

print(f"\nSeñales elegibles para MSNR en universo habilitado post-corte: {len(eligible_msnr)}")
for e in eligible_msnr:
    print(f"  MSNR: ID={e['id']} | Created={e['created_at']} | SigTime={e['signal_time']} | {e['symbol']} {e['direction']} | Valid: {e['valid']}")

conn_live.close()
