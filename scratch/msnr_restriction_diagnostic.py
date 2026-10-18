"""Read-only live telemetry summary; never contacts a broker or sends orders."""
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = Path(r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3")
connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=10)
connection.row_factory = sqlite3.Row
states = connection.execute(
    "SELECT bot_profile,status,cycle_number,last_action,last_reason,last_event_time,updated_at "
    "FROM worker_runtime_states WHERE bot_profile='MALAYSIAN_SNR'"
).fetchall()
# Bound the scan by primary key rather than searching all multi-GB payloads.
rows = connection.execute(
    "SELECT id,event_time,event_type,instrument,action,reason,payload_json "
    "FROM daemon_audit_events ORDER BY id DESC LIMIT 30000"
).fetchall()
selected = []
latest = {}
for row in rows:
    if row['event_type'] != 'SYMBOL_PROCESS_RESULT':
        continue
    payload_text = row['payload_json'] or ''
    if 'MALAYSIAN_SNR' not in payload_text and 'MALAYSIAN' not in (row['action'] or ''):
        continue
    item = {key: row[key] for key in ('id','event_time','instrument','action','reason')}
    selected.append(item)
    latest.setdefault(row['instrument'], item)
summary = {
    'worker_states': [dict(row) for row in states],
    'scan_rows': len(rows),
    'scan_newest_event_time': rows[0]['event_time'] if rows else None,
    'scan_oldest_event_time': rows[-1]['event_time'] if rows else None,
    'msnr_symbol_evaluations': len(selected),
    'reason_counts': dict(Counter(item['reason'] for item in selected)),
    'latest_by_symbol': list(latest.values()),
    'note': 'Bounded observations, not unique setups or an outcome win rate.',
}
connection.close()
out = ROOT / 'storage/analysis/msnr_restriction_review_20261011'
out.mkdir(parents=True, exist_ok=True)
(out / 'live_reasons.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=True, indent=2))
