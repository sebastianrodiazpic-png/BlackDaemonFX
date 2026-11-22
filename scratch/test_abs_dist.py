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

# En el retest_evidence de la señal:
# "penetration_atr": 0.0149, "distance_atr": 0.2288
retest = signal.get('retest_evidence', {})
print("retest_evidence:", retest)
distance_atr = float(retest.get('distance_atr', 0.2288))
print(f"distance_atr from setup: {distance_atr}")
max_dist = float(signal.get('max_entry_distance_atr') or 0.50)
print(f"max_dist: {max_dist}")

# If we compute abs distance:
# Entry is 4895.148, ref_level is 4894.141 -> diff is 1.007
# Since distance_atr is 0.2288, ATR is 1.007 / 0.2288 = 4.40 points!
atr_actual = 1.007 / distance_atr
abs_distance = abs(entry - float(signal['ref_level'])) / atr_actual
print(f"Calculated ATR: {atr_actual:.2f}, abs_distance: {abs_distance:.4f}")
print(f"abs_distance <= max_dist: {abs_distance <= max_dist}")
