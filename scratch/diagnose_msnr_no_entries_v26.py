"""Read-only sampled audit and completed log-cycle diagnosis of SNR entry funnel."""
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.database import resolve_db_path
from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol

now = datetime.now(timezone.utc)
OUT = ROOT / 'storage/analysis' / ('msnr_no_entries_' + now.strftime('%Y%m%d_%H%M%S'))
OUT.mkdir(parents=True, exist_ok=True)
def counts(values):
    return dict(Counter(values).most_common())

with sqlite3.connect(f'file:{resolve_db_path().as_posix()}?mode=ro', uri=True, timeout=15) as db:
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    preference = dict(db.execute("SELECT id,settings_json,updated_at FROM strategy_runtime_preferences WHERE source='DEMO' AND strategy_name='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone())
    settings = json.loads(preference.pop('settings_json'))
    since = str(preference['updated_at'])[:19]
    cutoff = (now-timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
    audit = []
    for row in db.execute("""SELECT event_time,event_type,instrument,action,reason,cycle_number,payload_json
        FROM daemon_audit_events WHERE source='DEMO' AND event_time>=?
        AND event_type IN ('SYMBOL_PROCESS_RESULT','DAEMON_CYCLE_END','ORDER_OPENED','SPLIT_ORDER_OPENED')
        AND payload_json LIKE '%MALAYSIAN_SNR%' ORDER BY event_time DESC LIMIT 20000""", (cutoff,)):
        payload = json.loads(row['payload_json'] or '{}')
        if payload.get('bot_profile') != 'MALAYSIAN_SNR':
            continue
        audit.append({**{k:row[k] for k in row.keys() if k!='payload_json'},'payload':payload})
    workers = [dict(r) for r in db.execute("SELECT bot_profile,status,pid,cycle_number,last_action,last_reason,updated_at,details_json FROM worker_runtime_states WHERE source='DEMO'")]
    for worker in workers:
        details = json.loads(worker.pop('details_json') or '{}')
        worker['result'] = details.get('result')
    recent_trades=[]
    for row in db.execute("""SELECT id,instrument,status,entry_time,exit_time,strategy_version,net_pnl,details_json
        FROM trade_journal WHERE source='DEMO' AND entry_time>=? ORDER BY id DESC LIMIT 2000""",(cutoff,)):
        details=json.loads(row['details_json'] or '{}');meta=details.get('metadata') or {}
        recent_trades.append({**{k:row[k] for k in row.keys() if k!='details_json'},
                              'bot_profile':meta.get('bot_profile') or meta.get('strategy_name')})

evaluations = [e for e in audit if e['event_type']=='SYMBOL_PROCESS_RESULT']
current = [e for e in evaluations if (e['payload'].get('result') or {}).get('runtime_settings_version')==preference['id']]
latest = {}
for event in current:
    latest.setdefault(event['instrument'],event)
setup_events = defaultdict(list)
for event in current:
    result = event['payload'].get('result') or {}
    diag = result.get('diagnostics') or {}
    sid = result.get('setup_id') or diag.get('setup_id')
    if sid:
        setup_events[sid].append(event)
h1=[]
for event in current:
    result=event['payload'].get('result') or {}
    snapshot=(result.get('diagnostics') or {}).get('h1_snapshot')
    if snapshot:
        h1.append({'symbol':event['instrument'],'event_time':event['event_time'],**snapshot})

path=ROOT/'storage/logs/bots/malaysian_snr.log'
with path.open('rb') as log:
    size=log.seek(0,2);offset=max(0,size-24*1024*1024);log.seek(offset)
    if offset:log.readline()
    text=log.read().decode('utf-8',errors='replace')
cycles=[];cycle=None;pending=None
for line in text.splitlines():
    match=re.search(r'CICLO #(\d+) \| (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC \| s.mbolos=(\d+)',line)
    if match:
        cycle={'number':int(match[1]),'start_utc':match[2],'symbols':int(match[3]),'evaluations':[],'completed':False}
        cycles.append(cycle);pending=None
    elif cycle:
        match=re.search(r'\[(\d+)/(\d+)\] END\s+(.+?) \| ([0-9.]+)s \| (.+)',line)
        if match:
            pending={'symbol':match[3],'seconds':float(match[4]),'action':match[5],'reason':None}
            cycle['evaluations'].append(pending)
        elif pending and 'Motivo:' in line:
            pending['reason']=line.split('Motivo:',1)[1].strip();pending=None
        elif 'del ciclo:' in line:
            match=re.search(r':\s*([0-9.]+)s',line)
            if match:cycle['seconds']=float(match[1]);cycle['completed']=True
        elif line.startswith('Nuevas '):
            cycle['orders']=int(line.rsplit(':',1)[1].strip())
        elif line.startswith('Errores:'):
            cycle['errors']=int(line.rsplit(':',1)[1].strip())
completed=[c for c in cycles if c['completed'] and c['start_utc']>=since]
reads=[e for c in completed for e in c['evaluations']]
synthetic=[e for e in reads if is_synthetic_symbol(e['symbol'])]
traditional=[e for e in reads if not is_synthetic_symbol(e['symbol'])]
def summarize(items):
    return {'reads':len(items),'reasons':counts(e['reason'] for e in items),'actions':counts(e['action'] for e in items)}
durations=sorted(c['seconds'] for c in completed)
summary={'generated_utc':now.isoformat(),'preference':preference,'settings':settings,
    'completed_cycles':len(completed),'first_cycle_utc':completed[0]['start_utc'] if completed else None,
    'last_cycle_utc':completed[-1]['start_utc'] if completed else None,
    'orders':sum(c.get('orders',0) for c in completed),'errors':sum(c.get('errors',0) for c in completed),
    'all_reads':summarize(reads),'synthetic_reads':summarize(synthetic),'traditional_reads':summarize(traditional),
    'cycle_duration':{'median':median(durations),'p95':durations[min(len(durations)-1,int(.95*len(durations)))],
                      'max':max(durations),'over_30_seconds':sum(d>30 for d in durations)} if durations else {},
    'sampled_audit_count':len(current),'sampled_reasons':counts(e['reason'] for e in current),
    'sampled_versions':counts((e['payload'].get('result') or {}).get('strategy_version') for e in current),
    'sampled_valid_events':sum(bool((e['payload'].get('result') or {}).get('valid')) for e in current),
    'shadow_observation_events':sum(e['action']=='MSNR_SHADOW_SIGNAL' for e in current),
    'nested_shadow_plans':sum(len((e['payload'].get('result') or {}).get('shadow_candidates') or []) for e in current),
    'unique_setup_count':len(setup_events),
    'h1_snapshots':h1,'h1_reason_counts':counts(reason for s in h1 for reason in s['rejections']),
    'per_symbol':{s:summarize([e for e in reads if e['symbol']==s]) for s in sorted({e['symbol'] for e in reads})},
    'recent_trade_journal_count':len(recent_trades),
    'recent_trade_profiles':counts(t['bot_profile'] or t['strategy_version'] for t in recent_trades),
    'recent_msnr_trades':[t for t in recent_trades if str(t['strategy_version']).startswith('msnr') or t['bot_profile']=='MALAYSIAN_SNR']}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'details.json').write_text(json.dumps({'latest_by_symbol':latest,'setups':setup_events,
    'workers':workers,'cycles':completed,'audit':audit},indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('h1_snapshots','per_symbol')},indent=2,ensure_ascii=False))
print('OUTPUT_DIRECTORY',OUT)
for symbol,event in latest.items():
    result=event['payload'].get('result') or {}
    print(json.dumps({'symbol':symbol,'time':event['event_time'],'reason':event['reason'],
        'scenario':result.get('scenario'),'gap_reason':result.get('gap_data_reason'),
        'diagnostics':result.get('diagnostics')},ensure_ascii=False))
