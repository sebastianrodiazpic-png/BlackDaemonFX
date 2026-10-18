from pathlib import Path
import json,hashlib,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_msnr_two_year_comparison import OUT,read_manifest
changed=[]
for shard in OUT.glob('history_manifest_shard_*.json'):
    data=json.loads(shard.read_text())
    for row in data['symbols']:
        for tf,meta in row['frames'].items():
            if 'sha256' not in meta:
                continue
            digest=hashlib.sha256((OUT/meta['file']).read_bytes()).hexdigest()
            if digest!=meta['sha256']:
                changed.append((row['symbol'],tf))
                if '--repair' in sys.argv:
                    meta['sha256']=digest
                    meta['snapshot_refreshed_before_replay']=True
                    frame=pd.read_pickle(OUT/meta['file'])
                    meta['rows']=len(frame)
                    meta['start']=str(frame.time.min())
                    meta['last_open']=str(frame.time.max())
        checkpoint=OUT/'results'/f'{row["symbol"].replace(" ","_")}.json'
        if '--repair' in sys.argv and checkpoint.exists():
            prior=json.loads(checkpoint.read_text())
            if any(meta.get('sha256')!=prior.get('frames',{}).get(tf,{}).get('sha256') for tf,meta in row['frames'].items() if 'sha256' in meta):
                checkpoint.rename(checkpoint.with_suffix('.superseded.json'))
    if '--repair' in sys.argv:
        shard.write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps({'changed_frames':changed,'repaired':'--repair' in sys.argv}))
