"""Apply the user-authorized SNR DEMO profile through its existing settings API."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.malaysian_snr.runtime_settings import validate_msnr_patch

OUT=ROOT/'storage/analysis/msnr_perfil_selectivo_20261013'
BASE='http://127.0.0.1:8765'
PATH='/api/strategies/malaysian-snr/settings'
PROFILE={
    'enable_synthetic_daily_storyline_filter':False,
    'fractal_min_body_ratio':.45,
    'fractal_max_entry_distance_atr':.50,
    'continuation_max_entry_distance_atr':.50,
    'qm_max_entry_distance_atr':.50,
    'continuation_mode':'live',
    'continuation_min_body_ratio':.50,
    'continuation_min_adx':20.,
    'continuation_maximum_breakout_wick_ratio':.25,
    'continuation_fresh_only':False,
    'retest_window_minutes':90,
    'recovery_window_minutes':45,
    'recovery_min_body_ratio':.35,
    'step_min_adx':25.,
    'step_symbol_min_adx':{'Step Index':23.},
    'm5_confirmation_mode':'shadow',
    'macro_structure_mode':'live',
    'macro_bias_method':'d1_structure',
    'macro_pivot_radius':2,
    'session_policy':'legacy_utc',
    'obstacle_av_definition':'engulfing',
    'breaker_pair_mode':'shadow',
    'breaker_pair_min_body_ratio':.50,
    'breaker_pair_min_displacement_atr':.50,
    'retest_pinbar_mode':'shadow',
    'retest_pinbar_min_wick_ratio':.55,
    'retest_pinbar_min_close_ratio':.75,
    'h4_obstacle_mode':'shadow',
    'h4_neutral_fallback_mode':'shadow',
    'research_min_frequency_ratio':1.05,
    'research_min_resolved_trades':50,
    'research_min_win_rate_improvement_pp':1.,
}
STEPS=('Step Index','Step Index 200','Step Index 400','Step Index 500')


def request(path=PATH,patch=None):
    req=urllib.request.Request(BASE+path,data=None if patch is None else json.dumps(patch).encode('utf8'),
        headers={} if patch is None else {'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as response:
        data=response.read()
    return json.loads(data) if path==PATH else data


def dump(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def worker_snapshot():
    db=Path(os.environ.get('DAEMONBLACKFX_DB_PATH') or
        Path(os.environ['LOCALAPPDATA'])/'BlackDaemonFx/trading_bot.sqlite3')
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=15) as con:
        con.row_factory=sqlite3.Row
        row=con.execute("SELECT * FROM worker_runtime_states WHERE bot_profile='MALAYSIAN_SNR' AND source='DEMO' ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if (OUT/'settings_after.json').exists():
        raise ValueError('Application evidence already exists; inspect it rather than overwriting this snapshot')
    raw=request()
    dump('settings_before_refresh.json',raw)
    # Existing dashboard page reloads only its own modules and settings routes.
    request('/strategy-bases')
    before=request()
    if not before.get('ok') or before.get('scope')!='MALAYSIAN_SNR':
        raise ValueError('SNR settings API unavailable or wrong scope')
    dump('settings_before.json',before)
    worker=worker_snapshot();dump('worker_before.json',worker)
    details=json.loads((worker or {}).get('details_json') or '{}')
    def values(node,key):
        if isinstance(node,dict):
            if key in node:yield node[key]
            for value in node.values():yield from values(value,key)
        elif isinstance(node,list):
            for value in node:yield from values(value,key)
    worker_versions=set(map(str,values(details,'strategy_version')))
    current=before['settings']
    patch=dict(PROFILE)
    for key in ('asset_modes','m5_symbol_modes','continuation_symbol_modes'):
        patch[key]={**current[key],**dict.fromkeys(STEPS,'live')}
    patch=validate_msnr_patch(patch)
    dump('requested_profile.json',patch)
    changes={k:{'before':current.get(k),'after':v} for k,v in patch.items() if current.get(k)!=v}
    dump('changes.json',changes)
    if not args.apply:
        print(json.dumps({'prepared':True,'settings_version':current['version'],'changes':changes,
            'controls_available':len(before['defaults']),'worker_pid':(worker or {}).get('pid'),
            'worker_status':(worker or {}).get('status'),'worker_updated_at':(worker or {}).get('updated_at'),
            'worker_strategy_versions':sorted(worker_versions),
            'worker_settings_versions':list(set(map(str,values(details,'runtime_settings_version'))))},ensure_ascii=False))
        return
    # The nine new controls require the new worker parser. Do not write them
    # while an old worker is running; it would reject the complete preferences.
    if worker and worker.get('status')=='RUNNING' and worker_versions!={'msnr-v2.9-video-evidence'}:
        raise ValueError('Running worker has not demonstrated the new settings parser; profile not changed')
    result=request(patch=patch)
    if not result.get('ok'):raise ValueError('Profile save was not confirmed')
    after=request();dump('settings_after.json',after)
    if not after.get('ok') or any(after['settings'].get(k)!=v for k,v in patch.items()):
        raise ValueError('Saved profile does not match the authorized settings')
    untouched={k for k in current if k not in {*patch,'version','updated_at'}}
    if any(current[k]!=after['settings'][k] for k in untouched):
        raise ValueError('Unrequested preferences changed')
    dump('applied.json',{'applied_at_utc':datetime.now(timezone.utc).isoformat(),
        'settings_version':after['settings']['version'],'requested_values_verified':True,
        'unrequested_values_preserved':True,'source':'DEMO','orders_sent_by_this_tool':False})
    print(json.dumps({'saved':True,'settings_version':after['settings']['version'],
        'verified_controls':len(patch),'new_candidates':'SHADOW','source':'DEMO'}))


if __name__=='__main__':main()
