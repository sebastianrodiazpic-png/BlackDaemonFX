"""Summarize existing offline evidence; no new optimization or strategy changes."""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig

OUT = ROOT/'storage/analysis/msnr_log_review_20261011'
live = json.loads((OUT/'telemetry.json').read_text(encoding='utf-8'))
frames = pd.read_csv(ROOT/'storage/analysis/msnr_v21_two_years_20261011/trades.csv')
per_symbol = pd.read_csv(ROOT/'storage/analysis/msnr_v21_two_years_20261011/per_symbol.csv')
old = frames[(frames.variant=='v21') & frames.synthetic & frames.full_two_years & ~frames.is_micro].copy()
old['time'] = pd.to_datetime(old.time,utc=True)
old['structure_closed_at'] = pd.to_datetime(old.structure_closed_at,utc=True)
old['age_minutes'] = (old.time-old.structure_closed_at).dt.total_seconds()/60
old = old[old.outcome!='RIGHT_CENSORED']
old['year'] = old.time.map(lambda t:'year1' if t<pd.Timestamp('2025-10-11',tz='UTC') else 'year2')

def metrics(frame):
    wins = int((frame.rr>0).sum())
    losses = float(-frame.loc[frame.rr<0,'rr'].sum())
    return {'trades':len(frame),'wins':wins,'win_pct':round(100*wins/len(frame),2) if len(frame) else None,
        'mean_r':round(float(frame.rr.mean()),4) if len(frame) else None,
        'profit_factor':round(float(frame.loc[frame.rr>0,'rr'].sum())/losses,3) if losses else None}

names = ['Jump 50 Index','Jump 75 Index','Jump 100 Index','Step Index 500','Multi Step 2 Index',
         'Volatility 75 Index','Volatility 100 Index','Volatility 75 (1s) Index',
         'Boom 1000 Index','Boom 300 Index','Crash 600 Index','Step Index 400','Jump 25 Index','Jump 10 Index']
candidates = []
for symbol in names:
    group = old[old.symbol==symbol]
    rows = per_symbol[per_symbol.symbol==symbol]
    candidates.append({'symbol':symbol,'currently_allowed':symbol in MalaysianSNRConfig().allowed_symbols,
        **metrics(group),'years':{year:metrics(group[group.year==year]) for year in ('year1','year2')},
        'win_ci95':rows.iloc[0].v21_win_ci95 if len(rows) else None})

latest = []
for event in live['latest_symbol_diagnostics']:
    if event['setup_id'] and event['version']=='msnr-v2.4-dynamic-fractal-distance':
        latest.append({'symbol':event['instrument'],'setup_id':event['setup_id'],'reason':event['reason'],
                       'scenario':event['scenario'],'event_time':event['event_time'],
                       'diagnostics':event['result'].get('diagnostics')})
summary = {'historical_config_note':'Existing v2.1: synthetic D1 veto ON, Fractal body >=55%, Fractal distance <=0.40 ATR. NOT a replay of v2.4 (D1 OFF, body 45%, distance 0.50 ATR).',
    'win_definition':'Positive net R per simulated split setup, not winning legs separately.',
    'synthetic_complete_nonmicro':metrics(old),
    'by_scenario':{str(k):metrics(g) for k,g in old.groupby('scenario')},
    'by_trigger':{str(k):metrics(g) for k,g in old.groupby('trigger')},
    'early_15_to_45':metrics(old[(old.age_minutes>=15)&(old.age_minutes<=45)]),
    'late_60_to_90':metrics(old[(old.age_minutes>=60)&(old.age_minutes<=90)]),
    'asset_candidates_and_comparators':candidates,
    'current_latest_setups':latest}
(OUT/'historical_evidence.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(summary,indent=2,ensure_ascii=False))
