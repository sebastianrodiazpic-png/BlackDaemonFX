"""ORB diagnostics and immutable per-confirmation comparisons, never orders."""
import json
import os
import threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'storage/runtime/orb_audit'
_LOCK=threading.Lock()

def record(result,root=None):
    audit=result.get('orb_audit')
    if not audit or result.get('strategy_name')!='ORB_NEW_YORK':return
    root=Path(root or ROOT)
    with _LOCK:
        root.mkdir(parents=True,exist_ok=True)
        day=str(audit['range_start'])[:10]
        target=root/(day+'.json')
        try:state=json.loads(target.read_text(encoding='utf-8'))
        except (OSError,ValueError):state={'day':day,'latest':{},'candidates':{}}
        state['updated_at']=audit['evaluated_at']
        state['latest'][audit['symbol']]={**audit,'action':result.get('action'),'reason':result.get('reason')}
        momentum=audit.get('momentum') or {}
        if momentum.get('evaluated'):
            key='|'.join([audit['symbol'],str(momentum['confirmation_time']),str(momentum['direction'])])
            state['candidates'].setdefault(key,audit)
        temp=root/(day+'.'+str(os.getpid())+'.tmp')
        temp.write_text(json.dumps(state,ensure_ascii=False,default=str),encoding='utf-8');temp.replace(target)

def snapshot(root=None):
    paths=sorted(Path(root or ROOT).glob('*.json'))
    if not paths:return {}
    try:return json.loads(paths[-1].read_text(encoding='utf-8'))
    except (OSError,ValueError):return {'error':'ORB_AUDIT_UNAVAILABLE'}
