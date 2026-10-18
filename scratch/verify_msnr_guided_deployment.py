import json
import os
import sqlite3
import hashlib
from datetime import datetime, timezone
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'storage/analysis/msnr_configuracion_guiada_20261012'
with urllib.request.urlopen('http://127.0.0.1:8765/api/strategies/malaysian-snr/settings') as response:
    state=json.load(response)
path=Path(os.environ['LOCALAPPDATA'])/'BlackDaemonFx/trading_bot.sqlite3'
with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=30) as connection:
    connection.row_factory=sqlite3.Row
    worker=dict(connection.execute("SELECT * FROM worker_runtime_states WHERE bot_profile='MALAYSIAN_SNR' AND source='DEMO' ORDER BY id DESC LIMIT 1").fetchone())
    tables=[row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    since=datetime.fromtimestamp((OUT/'step_reload_before.json').stat().st_mtime,timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    monitor_rows=[dict(row) for row in connection.execute("SELECT * FROM daemon_audit_events WHERE source='DEMO' AND event_type='POSITION_MONITOR' AND event_time>=? ORDER BY id DESC LIMIT 200",(since,))]
monitors=[row for row in monitor_rows if 'MALAYSIAN_SNR' in str(row)][0:3]
model=ROOT/'storage/ai_models/metalabel_MALAYSIAN_SNR_MALAYSIAN_SNR.json'
evidence={'settings':state['settings'],'worker':worker,'recent_position_monitors':monitors,
    'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest()}
(OUT/'deployment_verification.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
details=json.loads(worker['details_json'])
def nested_versions(node):
    if isinstance(node,dict):
        yield from [value for key,value in node.items() if key=='runtime_settings_version']
        for value in node.values():yield from nested_versions(value)
    elif isinstance(node,list):
        for value in node:yield from nested_versions(value)
versions=list(nested_versions(details))
print(json.dumps({'version':state['settings']['version'],'worker_status':worker['status'],
    'symbols':worker['symbols_total'],'cycle':worker['cycle_number'],
    'worker_preferences_13':13 in versions,
    'position_monitor_events':len(monitors),'step_adx':state['settings']['step_symbol_min_adx'],
    'model_sha256':evidence['model_sha256']},ensure_ascii=False))
