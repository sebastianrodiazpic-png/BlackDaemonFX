"""Read-only verification of the deployed SNR controls and worker."""
import hashlib
import json
import os
import sqlite3
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'storage/analysis/msnr_v28_recovery_20261012'
result = {}
for name, endpoint in [('preferences','settings'), ('candidates','candidates')]:
    with urllib.request.urlopen('http://127.0.0.1:8765/api/strategies/malaysian-snr/'+endpoint, timeout=30) as response:
        result[name] = json.load(response)
db = Path(os.environ['LOCALAPPDATA']) / 'BlackDaemonFx/trading_bot.sqlite3'
with sqlite3.connect(db.as_uri()+'?mode=ro', uri=True, timeout=30) as conn:
    conn.row_factory = sqlite3.Row
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    worker_table = next(t for t in tables if 'worker_runtime' in t)
    result['workers'] = [dict(r) for r in conn.execute(f'SELECT * FROM {worker_table}')]
path = root/'storage/logs/bots/malaysian_snr.log'
with path.open('rb') as fh:
    fh.seek(max(0,path.stat().st_size-1200000))
    lines = fh.read().decode('utf-8',errors='replace').splitlines()
result['recent_log'] = [s for s in lines if any(k in s for k in ('v2.8','version=11','BTCUSD','Traceback','ERROR','symbols=31'))][-30:]
model = root/'storage/ai_models/metalabel_MALAYSIAN_SNR_MALAYSIAN_SNR.json'
result['model_sha256'] = hashlib.sha256(model.read_bytes()).hexdigest()
(out/'deployment_verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
settings = result['preferences']['settings']
print(json.dumps({'preferences_version':settings['version'], 'continuation_mode':settings['continuation_mode'],
    'recovery_modes':settings['asset_modes'],'catalogue_size':len(result['preferences']['asset_catalog']),
    'snr_workers':[w for w in result['workers'] if 'MALAYSIAN' in str(w)],
    'model_sha256':result['model_sha256'],'recent_log':result['recent_log']},ensure_ascii=False,indent=2))
