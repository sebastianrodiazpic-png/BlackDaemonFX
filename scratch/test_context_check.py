import json
import pandas as pd
import math

with open("scratch/inspect_single_payload.py") as f:
    pass

import sqlite3
db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
r = conn.execute(
    "SELECT payload_json FROM daemon_audit_events WHERE action='OPERACION_RECHAZADA_POR_RIESGO' AND reason='MSNR_ENTRY_CONTEXT_CHANGED' ORDER BY event_time DESC LIMIT 1"
).fetchone()[0]

signal = json.loads(r).get('result', {})
direction = signal['direction']
entry = signal['shadow_plan']['entry_price']

print("Keys in signal:", sorted(signal.keys()))
print("Does 'atr' exist?", 'atr' in signal)
print("Does 'ref_level' exist?", 'ref_level' in signal)
print("Does 'setup_expires_at' exist?", 'setup_expires_at' in signal)
print("Does 'invalidation_level' exist?", 'invalidation_level' in signal)

try:
    sign = 1 if direction == 'BUY' else -1
    atr = float(signal['atr'])
    distance = sign * (float(entry) - float(signal['ref_level'])) / atr
    deadline = pd.Timestamp(signal.get('setup_execution_deadline_at') or signal['setup_expires_at'])
    expired = pd.isna(deadline) or pd.Timestamp.now(tz='UTC') > deadline
    bound = float(signal['invalidation_level'])
    invalidated = sign * (float(entry) - bound) <= 0
    permitted = (math.isfinite(distance) and math.isfinite(bound) and atr > 0 and not expired and not invalidated
                 and 0 <= distance <= float(signal['max_entry_distance_atr']))
    print("Permitted:", permitted)
except Exception as e:
    import traceback
    print("EXCEPTION OCCURRED:", type(e).__name__, e)
    traceback.print_exc()
