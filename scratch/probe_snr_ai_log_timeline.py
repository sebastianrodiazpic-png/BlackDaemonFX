import json,re
from pathlib import Path
from collections import Counter
root=Path(__file__).resolve().parents[1]
time=None; pending=None; events=[]
for line in (root/'storage/logs/bots/malaysian_snr.log').open(encoding='utf-8',errors='replace'):
    m=re.search(r'CICLO #\d+ \| (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC',line)
    if m: time=m[1];pending=None
    elif time and time.startswith('2026-10-12'):
        m=re.search(r'\[\d+/\d+\] END\s+(.+?) \| [0-9.]+s \| (.+)',line)
        if m:
            pending={'time':time,'symbol':m[1],'action':m[2].strip()}
        elif pending and 'Motivo:' in line:
            pending['reason']=line.split('Motivo:',1)[1].strip()
            if 'META LABEL' in pending['action'] or 'SHADOW' in pending['action']:
                events.append(pending)
            pending=None
result={'events':events,'counts':dict(Counter((e['action']+' | '+e['reason']) for e in events)),
    'symbols':dict(Counter(e['symbol'] for e in events))}
(root/'storage/analysis/msnr_trade_drop_20261012/ai_timeline.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'counts':result['counts'],'symbols':result['symbols'],'first':events[:2],'last':events[-3:]},indent=2))
