import sqlite3, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
cur = conn.cursor()

# Get the latest DAEMON_CYCLE_END or SYMBOL_PROCESS_RESULT
cur.execute("""
    SELECT instrument, action, reason, payload_json
    FROM daemon_audit_events
    WHERE source='DEMO' AND event_type='SYMBOL_PROCESS_RESULT' AND payload_json LIKE '%MALAYSIAN_SNR%'
    ORDER BY id DESC LIMIT 150
""")

rows = cur.fetchall()
reasons = Counter()
symbol_details = {}

for inst, act, rsn, p_json in rows:
    try:
        p = json.loads(p_json or '{}')
    except Exception:
        continue
    if p.get('bot_profile') != 'MALAYSIAN_SNR':
        continue
    reasons[rsn] += 1
    if inst not in symbol_details:
        diag = (p.get('result') or {}).get('diagnostics') or {}
        symbol_details[inst] = {
            'action': act,
            'reason': rsn,
            'scenario': diag.get('scenario'),
            'stage': diag.get('stage'),
            'shadow_only': (p.get('result') or {}).get('shadow_only'),
            'valid': (p.get('result') or {}).get('valid')
        }

print("TOP REASONS:")
for r, c in reasons.most_common(15):
    print(f"  {r}: {c}")

print("\nPER SYMBOL LATEST STATUS:")
for s, d in sorted(symbol_details.items()):
    print(f"  {s}: action={d['action']}, reason={d['reason']}, stage={d['stage']}, scenario={d['scenario']}, shadow={d['shadow_only']}")
