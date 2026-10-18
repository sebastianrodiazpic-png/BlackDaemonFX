"""Read-only inspection of MSNR preference, worker and broker positions."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.database import resolve_db_path

path = resolve_db_path()
with sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True, timeout=10) as conn:
    rows = conn.execute("SELECT id,instrument,details_json FROM trades WHERE source='DEMO' AND status='OPEN'").fetchall()
    owned = []
    for trade_id, symbol, raw in rows:
        metadata = (json.loads(raw or '{}').get('metadata') or {})
        if metadata.get('bot_profile') == 'MALAYSIAN_SNR' or str(metadata.get('mt5_magic') or metadata.get('daemon_magic')) == '26082031':
            owned.append({'id':trade_id,'symbol':symbol})
    runtime = conn.execute("SELECT pid,status,last_action,last_reason,updated_at,details_json FROM worker_runtime_states WHERE source='DEMO' AND bot_profile='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone()
    settings = conn.execute("SELECT id,settings_json FROM strategy_runtime_preferences WHERE source='DEMO' AND strategy_name='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone()
    print(json.dumps({'db_open_msnr_positions':owned,'settings':settings,
                      'runtime': list(runtime[:5]) if runtime else None,
                      'runtime_details': json.loads(runtime[5] or '{}') if runtime else None}, ensure_ascii=False, default=str))

import MetaTrader5 as mt5
if not mt5.initialize():
    raise RuntimeError('No se pudo verificar el terminal')
try:
    positions = mt5.positions_get()
    if positions is None:
        raise RuntimeError('No se pudieron consultar posiciones')
    print(json.dumps({'broker_open_msnr_positions':sum(p.magic == 26082031 for p in positions)}))
finally:
    mt5.shutdown()
