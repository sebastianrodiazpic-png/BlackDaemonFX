"""Read-only log and sampled telemetry analysis; no broker connection or orders."""
import json
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.database import resolve_db_path

OUT = ROOT/'storage/analysis/msnr_log_review_20261011'
OUT.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc)
cutoff = (now-timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')

def parse_time(value):
    return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=timezone.utc)

def count_map(items):
    return dict(Counter(items).most_common())

path = resolve_db_path()
with sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True, timeout=10) as db:
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    preferences = [dict(r) for r in db.execute("SELECT id,settings_json,updated_at FROM strategy_runtime_preferences WHERE source='DEMO' AND strategy_name='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 20")]
    states = [dict(r) for r in db.execute("SELECT bot_profile,status,cycle_number,last_elapsed_seconds,last_action,last_reason,updated_at FROM worker_runtime_states WHERE source='DEMO' AND bot_profile='MALAYSIAN_SNR'")]
    audit = []
    # source/event_type/time uses the existing composite index. LIKE only selects
    # candidate payloads; the decoded profile is checked below to avoid attribution errors.
    query = """SELECT id,event_time,event_type,instrument,action,reason,cycle_number,payload_json
        FROM daemon_audit_events WHERE source='DEMO' AND event_time>=?
        AND event_type IN ('SYMBOL_PROCESS_RESULT','DAEMON_CYCLE_END')
        AND payload_json LIKE '%MALAYSIAN_SNR%'
        ORDER BY event_time DESC,id DESC LIMIT 20000"""
    for row in db.execute(query, (cutoff,)):
        try:
            payload = json.loads(row['payload_json'] or '{}')
        except (ValueError, TypeError):
            continue
        if payload.get('bot_profile') != 'MALAYSIAN_SNR':
            continue
        result = payload.get('result') or {}
        diagnostics = result.get('diagnostics') or {}
        audit.append({**{k:row[k] for k in row.keys() if k!='payload_json'},
            'version':result.get('strategy_version'), 'settings_version':result.get('runtime_settings_version'),
            'valid':result.get('valid'), 'scenario':result.get('scenario') or diagnostics.get('scenario'),
            'setup_id':result.get('setup_id') or diagnostics.get('setup_id'),
            'elapsed_seconds':payload.get('elapsed_seconds'),
            'result':result, 'cycle_payload':payload if row['event_type']=='DAEMON_CYCLE_END' else None})
    trades = []
    rows = db.execute("""SELECT id,instrument,status,result,entry_time,exit_time,net_pnl,realized_rr,
        strategy_version,execution_key,details_json FROM trade_journal WHERE source='DEMO'
        AND (strategy_version LIKE 'msnr%' OR details_json LIKE '%MALAYSIAN_SNR%')
        ORDER BY id DESC LIMIT 5000""")
    for row in rows:
        details = json.loads(row['details_json'] or '{}')
        meta = details.get('metadata') or {}
        if not (str(row['strategy_version']).startswith('msnr') or meta.get('bot_profile')=='MALAYSIAN_SNR'
                or meta.get('strategy_name')=='MALAYSIAN_SNR'):
            continue
        trades.append({**{k:row[k] for k in row.keys() if k!='details_json'}, 'metadata':meta})

groups = defaultdict(list)
for event in audit:
    if event['event_type']=='SYMBOL_PROCESS_RESULT':
        groups[event['version'] or 'UNVERSIONED_OPERATIONAL_BLOCK'].append(event)
group_stats = {}
for version, events in groups.items():
    group_stats[version] = {'evaluations':len(events),
        'first_utc':min(e['event_time'] for e in events), 'last_utc':max(e['event_time'] for e in events),
        'reasons':count_map(e['reason'] for e in events), 'actions':count_map(e['action'] for e in events),
        'unique_setup_ids':len({e['setup_id'] for e in events if e['setup_id']}),
        'valid_events':sum(bool(e['valid']) for e in events),
        'settings_versions':count_map(str(e['settings_version']) for e in events)}
current = groups.get('msnr-v2.4-dynamic-fractal-distance', [])
start = parse_time(min(e['event_time'] for e in current)) if current else now-timedelta(hours=1)

log_path = ROOT/'storage/logs/bots/malaysian_snr.log'
with log_path.open('rb') as file:
    size = file.seek(0,2)
    offset = max(0,size-24*1024*1024)
    file.seek(offset)
    if offset:
        file.readline()
    text = file.read().decode('utf-8', errors='replace')
cycles, cycle, pending = [], None, None
for line in text.splitlines():
    match = re.search(r'CICLO #(\d+) \| (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC \| s.mbolos=(\d+)',line)
    if match:
        cycle = {'number':int(match[1]), 'start_utc':match[2], 'symbols':int(match[3]),
                 'evaluations':[], 'completed':False}
        cycles.append(cycle)
        pending = None
    elif cycle:
        match = re.search(r'\[(\d+)/(\d+)\] END\s+(.+?) \| ([0-9.]+)s \| (.+)',line)
        if match:
            pending = {'symbol':match[3], 'seconds':float(match[4]), 'action':match[5], 'reason':None}
            cycle['evaluations'].append(pending)
        elif pending and 'Motivo:' in line:
            pending['reason'] = line.split('Motivo:',1)[1].strip()
            pending = None
        elif 'Duración del ciclo:' in line or 'Duraci' in line and 'del ciclo:' in line:
            match = re.search(r':\s*([0-9.]+)s',line)
            if match:
                cycle['seconds'] = float(match[1])
                cycle['completed'] = True
        elif 'Nuevas órdenes:' in line or 'Nuevas ' in line and 'rdenes:' in line:
            cycle['orders'] = int(line.rsplit(':',1)[1].strip())
        elif line.startswith('Errores:'):
            cycle['errors'] = int(line.rsplit(':',1)[1].strip())
recent = [c for c in cycles if c['completed'] and parse_time(c['start_utc'])>=start-timedelta(seconds=90)]
evaluations = [e for c in recent for e in c['evaluations']]
durations = sorted(c['seconds'] for c in recent)
elapsed = sorted(e['seconds'] for e in evaluations)
per_symbol = {}
for symbol in sorted({e['symbol'] for e in evaluations}):
    items = [e for e in evaluations if e['symbol']==symbol]
    per_symbol[symbol] = {'observations':len(items), 'reasons':count_map(e['reason'] for e in items),
        'mean_seconds':round(statistics.mean(e['seconds'] for e in items),3),
        'blocked_lock_seconds':round(sum(e['seconds'] for e in items if e['action']=='BLOCKED SYMBOL CYCLE'),3)}
def distribution(values):
    return {'count':len(values), 'median':round(statistics.median(values),3),
        'p95':round(values[min(len(values)-1,int(len(values)*.95))],3), 'max':values[-1]} if values else {}
latest = {}
setup_history = defaultdict(list)
for e in audit:
    if e['event_type']=='SYMBOL_PROCESS_RESULT':
        latest.setdefault(e['instrument'], e)
        if e['setup_id']:
            setup_history[e['setup_id']].append({k:e[k] for k in
                ('event_time','instrument','reason','version','settings_version','scenario')})
summary = {'generated_utc':now.isoformat(),'audit_requested_since_utc':cutoff,
    'audit_events':len(audit), 'audit_sampling_note':'Repeated waiting states are sampled; neither events nor cycles count unique trading opportunities.',
    'preferences':preferences, 'worker_states':states, 'audit_by_strategy_version':group_stats,
    'latest_symbol_diagnostics':list(latest.values()), 'unique_setup_histories':dict(setup_history),
    'current_version_log_window':{
        'first_cycle_utc':recent[0]['start_utc'] if recent else None,
        'last_cycle_utc':recent[-1]['start_utc'] if recent else None,
        'completed_cycles':len(recent), 'symbol_evaluations':len(evaluations),
        'reasons':count_map(e['reason'] for e in evaluations), 'actions':count_map(e['action'] for e in evaluations),
        'orders':sum(c.get('orders',0) for c in recent), 'errors':sum(c.get('errors',0) for c in recent),
        'cycles_over_30_seconds':sum(c['seconds']>30 for c in recent),
        'cycle_seconds':distribution(durations), 'evaluation_seconds':distribution(elapsed),
        'lock_block_seconds':round(sum(e['seconds'] for e in evaluations if e['action']=='BLOCKED SYMBOL CYCLE'),3),
        'per_symbol':per_symbol},
    'trade_journal_rows':trades,
    'trade_counts_by_version':count_map(t['strategy_version'] for t in trades),
    'current_version_trades':sum(t['strategy_version']=='msnr-v2.4-dynamic-fractal-distance' for t in trades)}
(OUT/'telemetry.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
(OUT/'cycles.json').write_text(json.dumps(recent,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in
    ('latest_symbol_diagnostics','unique_setup_histories','trade_journal_rows')},indent=2,ensure_ascii=False,default=str))
print('DETAILS:',str(OUT/'telemetry.json'))
