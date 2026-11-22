import json
import pandas as pd
import math
import sqlite3

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
r = conn.execute(
    "SELECT payload_json FROM daemon_audit_events WHERE action='OPERACION_RECHAZADA_POR_RIESGO' AND reason='MSNR_ENTRY_CONTEXT_CHANGED' ORDER BY event_time DESC LIMIT 1"
).fetchone()[0]

signal = json.loads(r).get('result', {})
direction = signal['direction']
entry = signal['shadow_plan']['entry_price']

print("Testing improved logic on live payload:")

sign = 1 if direction == 'BUY' else -1
# In signal, atr is inside retest_evidence or diagnostics or let's see:
diag = signal.get('diagnostics') or {}
retest = signal.get('retest_evidence') or {}
atr = float(
    signal.get('atr')
    or diag.get('atr')
    or signal.get('atr_m5')
    or signal.get('atr_h1')
    or retest.get('atr')
    or (abs(float(signal.get('break_level', 0)) - float(signal.get('stop_loss', 0))) / 1.5 if signal.get('stop_loss') else 0.0)
    or 1.0
)
ref_lvl = float(signal.get('ref_level') or diag.get('level') or 0.0)
distance = sign * (float(entry) - ref_lvl) / atr if atr > 0 else 0.0
deadline_str = (
    signal.get('setup_execution_deadline_at')
    or signal.get('setup_expires_at')
    or diag.get('expires_at')
)
deadline = pd.Timestamp(deadline_str) if deadline_str else pd.Timestamp.now(tz='UTC') + pd.Timedelta(hours=1)
expired = pd.isna(deadline) or pd.Timestamp.now(tz='UTC') > deadline
bound_val = signal.get('invalidation_level') or diag.get('invalidation_level')
if bound_val is not None:
    bound = float(bound_val)
    invalidated = sign * (float(entry) - bound) <= 0
else:
    bound = float(signal.get('stop_loss') or 0.0)
    invalidated = False

max_dist = float(signal.get('max_entry_distance_atr') or diag.get('max_entry_distance_atr') or 0.50)

permitted = (
    math.isfinite(distance)
    and math.isfinite(bound)
    and atr > 0
    and not expired
    and not invalidated
    and -0.15 <= distance <= max_dist
)

print(f"  direction: {direction}")
print(f"  entry: {entry}")
print(f"  ref_lvl: {ref_lvl}")
print(f"  atr: {atr}")
print(f"  distance: {distance}")
print(f"  deadline: {deadline} (expired: {expired})")
print(f"  bound: {bound} (invalidated: {invalidated})")
print(f"  max_dist: {max_dist}")
print(f"  PERMITTED: {permitted}")
