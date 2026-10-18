"""Read-only current-preference audit, model provenance and AI rejection inventory."""
import json
import sqlite3
import sys
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database.database import resolve_db_path
from strategy.ai.meta_labeling import MetaLabelingEngine,MetaLabelingConfig

out=Path(sys.argv[1]);summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
since=summary['preference']['updated_at'];version=summary['preference']['id']
events=[]
with sqlite3.connect(f'file:{resolve_db_path().as_posix()}?mode=ro',uri=True,timeout=15) as db:
    db.execute('PRAGMA query_only=ON')
    for row in db.execute("""SELECT event_time,event_type,instrument,action,reason,payload_json
        FROM daemon_audit_events WHERE source='DEMO' AND event_time>=?
        AND event_type IN ('SYMBOL_PROCESS_RESULT','META_LABEL_SIGNAL_SCORED')
        AND payload_json LIKE '%MALAYSIAN_SNR%' ORDER BY event_time LIMIT 30000""",(since,)):
        payload=json.loads(row[5] or '{}')
        if payload.get('bot_profile')!='MALAYSIAN_SNR':continue
        events.append({'time':row[0],'type':row[1],'symbol':row[2],'action':row[3],'reason':row[4],'payload':payload})
score_events=[e for e in events if e['type']=='META_LABEL_SIGNAL_SCORED']
rejects=[e for e in events if e['type']=='SYMBOL_PROCESS_RESULT' and e['reason']=='PROBABILITY_BELOW_THRESHOLD']
model=MetaLabelingEngine(MetaLabelingConfig(),worker='MALAYSIAN_SNR').load_model('MALAYSIAN_SNR')
model_dict=model.to_dict()
model_summary={k:model_dict.get(k) for k in ('worker','strategy_name','trained_at','average_win_rr','average_loss_rr')}
model_summary.update(trained=model.trained,samples=model.model.samples,
    feature_names=model.model.feature_names,calibrator=model_dict.get('calibrator'))
unique=defaultdict(list)
for e in rejects:
    result=e['payload'].get('result') or {}
    unique[(e['symbol'],result.get('execution_key') or e['payload'].get('execution_key') or result.get('setup_id') or 'unknown')].append(e)
result={'since':since,'events':len(events),'score_events':len(score_events),
    'event_reasons':dict(Counter(e['reason'] for e in events if e['type']=='SYMBOL_PROCESS_RESULT')),
    'rejected_evaluations':len(rejects),'unique_rejected_execution_keys':len(unique),
    'model':model_summary,'rejections':rejects,'score_details':score_events}
(out/'entry_gate_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('rejections','score_details')},indent=2,ensure_ascii=False,default=str))
if score_events:
    for e in (score_events[0],score_events[-1]):
        m=e['payload'].get('meta_label') or {}
        print(json.dumps({'time':e['time'],'symbol':e['symbol'],'probability':m.get('probability'),
            'thresholds':m.get('thresholds'),'features':m.get('features')},ensure_ascii=False))
for key,items in unique.items():
    print(json.dumps({'symbol':key[0],'execution_key':key[1],'count':len(items),
        'first':items[0]['time'],'last':items[-1]['time'],'last_result':items[-1]['payload'].get('result')},ensure_ascii=False))
