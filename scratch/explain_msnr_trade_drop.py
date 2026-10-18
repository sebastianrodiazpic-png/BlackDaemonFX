"""Read-only evidence for changes in executed SNR frequency; no broker access."""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol

OUT=ROOT/'storage/analysis/msnr_trade_drop_20261012'
OUT.mkdir(parents=True,exist_ok=True)
def family(symbol):
    if is_synthetic_symbol(symbol): return 'synthetics'
    if symbol in ('XAUUSD','XAGUSD'): return 'metals'
    if any(k in symbol.upper() for k in ('BTC','ETH','LTC','SOL','XRP','BCH','ADA','DOGE')): return 'crypto'
    if len(symbol.removesuffix('micro'))==6 and symbol.isalpha(): return 'forex'
    return 'other'
def counts(values): return dict(Counter(values).most_common())

path=Path(os.environ['LOCALAPPDATA'])/'BlackDaemonFx/trading_bot.sqlite3'
db=sqlite3.connect(f'file:{path.as_posix()}?mode=ro',uri=True,timeout=10)
db.row_factory=sqlite3.Row
db.execute('PRAGMA query_only=ON')
entries=[]
profiles=Counter()
for r in db.execute('SELECT * FROM trade_journal ORDER BY entry_time'):
    details=json.loads(r['details_json'] or '{}')
    meta=details.get('metadata') or {}
    profile=meta.get('bot_profile') or meta.get('strategy_name') or r['strategy_version']
    profiles[profile]+=1
    if not (str(r['strategy_version']).startswith('msnr') or 'MALAYSIAN_SNR' in str(profile).upper()):
        continue
    entries.append({'time':r['entry_time'],'exit':r['exit_time'],'symbol':r['instrument'],
        'family':family(r['instrument']),'status':r['status'],'result':r['result'],
        'net_pnl':r['net_pnl'],'realized_rr':r['realized_rr'],'source':r['source'],
        'version':r['strategy_version'],'execution_key':r['execution_key'],
        'leg':meta.get('leg_role') or meta.get('execution_leg') or meta.get('leg_name'),
        'profile':profile,'metadata_keys':list(meta),
        'scenario':meta.get('scenario'),'setup_id':meta.get('setup_id'),
        'magic':meta.get('magic'),'external_sync':meta.get('external_sync')})
days=defaultdict(list)
for r in entries:
    days[str(r['time'])[:10]].append(r)
daily=[]
for day, rows in sorted(days.items()):
    if day<'2026-10-01': continue
    daily.append({'day_utc':day,'legs':len(rows),'symbols':counts(r['symbol'] for r in rows),
        'families':counts(r['family'] for r in rows),'versions':counts(r['version'] for r in rows),
        'net_pnl':round(sum(r['net_pnl'] for r in rows if r['status']=='CLOSED'),2),
        'closed_legs':sum(r['status']=='CLOSED' for r in rows),
        'results':counts(r['result'] for r in rows)})
candidate_rows=[dict(r) for r in db.execute("SELECT symbol,variant,first_seen,last_seen,first_reason,last_reason,state,evaluations,confirmed_at,executed FROM msnr_candidates WHERE source='DEMO'")]
candidates={'count':len(candidate_rows),'first_reasons':counts(r['first_reason'] for r in candidate_rows),
    'last_reasons':counts(r['last_reason'] for r in candidate_rows),'families':counts(family(r['symbol']) for r in candidate_rows),
    'confirmed':sum(bool(r['confirmed_at']) for r in candidate_rows),'executed':sum(r['executed'] for r in candidate_rows)}
audit_counts=[dict(r) for r in db.execute("SELECT substr(event_time,1,10) day,event_type,count(*) n FROM daemon_audit_events WHERE event_time>='2026-10-05' AND payload_json LIKE '%MALAYSIAN_SNR%' AND event_type IN ('DAEMON_CYCLE_END','SYMBOL_PROCESS_RESULT') GROUP BY day,event_type")]
preferences=[dict(r) for r in db.execute("SELECT id,updated_at,settings_json FROM strategy_runtime_preferences WHERE strategy_name='MALAYSIAN_SNR' AND source='DEMO' ORDER BY id")]
db.close()

log=ROOT/'storage/logs/bots/malaysian_snr.log'
per_day=defaultdict(lambda: {'cycles':0,'evaluations':0,'orders':0,'errors':0,'symbols_per_cycle':Counter(),'reasons':Counter(),'actions':Counter(),'families':Counter()})
day=None
pending=None
for line in log.open(encoding='utf-8',errors='replace'):
    match=re.search(r'CICLO #\d+ \| (\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} UTC \| s.mbolos=(\d+)',line)
    if match:
        day=match[1]
        per_day[day]['cycles']+=1
        per_day[day]['symbols_per_cycle'][match[2]]+=1
        pending=None
    elif day:
        match=re.search(r'\[\d+/\d+\] END\s+(.+?) \| ([0-9.]+)s \| (.+)',line)
        if match:
            pending=match[1]
            per_day[day]['evaluations']+=1
            per_day[day]['actions'][match[3].strip()]+=1
            per_day[day]['families'][family(pending)]+=1
        elif pending and 'Motivo:' in line:
            per_day[day]['reasons'][line.split('Motivo:',1)[1].strip()]+=1
            pending=None
        elif 'Nuevas ' in line and 'rdenes:' in line:
            per_day[day]['orders']+=int(line.rsplit(':',1)[1].strip())
        elif line.startswith('Errores:'):
            per_day[day]['errors']+=int(line.rsplit(':',1)[1].strip())

report={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'journal_profiles':dict(profiles),
    'snr_journal_total_legs':len(entries),'daily_journal':daily,'candidates':candidates,
    'active_symbols':list(MalaysianSNRConfig().allowed_symbols),
    'active_families':counts(family(s) for s in MalaysianSNRConfig().allowed_symbols),
    'audit_counts':audit_counts,'log_by_day':dict(per_day),
    'latest_entry_examples':entries[-12:],'preferences':preferences}
(OUT/'evidence.json').write_text(json.dumps(report,indent=2,default=dict),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('latest_entry_examples','preferences','audit_counts')},indent=2,default=dict))
print('ENTRY EXAMPLES',json.dumps(entries[-6:],indent=2))
