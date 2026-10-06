"""Read-only counterfactual gate comparison, not a PnL backtest or execution engine."""
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]

def walk(value):
    if isinstance(value,dict):
        yield value
        for item in value.values():yield from walk(item)
    elif isinstance(value,list):
        for item in value:yield from walk(item)

def analyze():
    day='2026-09-28'
    orb=json.loads((ROOT/'storage/runtime/orb_audit'/f'{day}.json').read_text())
    rows=[]
    for symbol,d in orb.get('latest',{}).items():
        amp=d.get('range_amplitude') or {}; ratio=amp.get('ratio'); critical=(d.get('session_cancellation') or {}).get('critical_ratio')
        rows.append(dict(symbol=symbol,atr=amp.get('atr'),range_size=amp.get('range_size'),ratio=ratio,
            critical=critical,action=d.get('action'),frozen_at=d.get('atr_frozen_at'),
            arithmetic_valid=abs(amp['range_size']/amp['atr']-ratio)<1e-8 if amp.get('atr') and ratio else None,
            shadow_passes={str(mult):ratio<=critical*mult for mult in (1,1.1,1.25,1.5)} if ratio and critical else {}))
    snapshots={};events={}
    for p in (ROOT/'storage/runtime/smc_telemetry').glob('*.json'):
        d=json.loads(p.read_text(encoding='utf-8-sig'));name=d.get('bot_name')
        if name not in snapshots or d['timestamp']>snapshots[name]['timestamp']:snapshots[name]=d
    candidates=list(snapshots.values())
    for p in (ROOT/'storage/runtime/smc_trial').glob('*.json'):
        try:candidates.append(json.loads(p.read_text(encoding='utf-8-sig')))
        except (ValueError,OSError):pass
    for p in (ROOT/'storage/runtime/smc_telemetry').glob('*.jsonl'):
        for line in p.read_text().splitlines():
            try:candidates.append(json.loads(line))
            except ValueError:pass
    # Older workers only logged periodic cumulative snapshots; recover what survived.
    for p in (ROOT/'storage/logs/bots').glob('*.log'):
        with p.open(encoding='utf-8', errors='replace') as stream:
            for line in stream:
                if 'SMC TELEMETRY | ' not in line:continue
                try:
                    value=json.loads(line.split('SMC TELEMETRY | ',1)[1])
                    if value.get('start_time','') >= '2026-09-28T17:17':candidates.append(value)
                except ValueError:pass
    for source in candidates:
        for d in walk(source):
            m=d.get('m5_detail') or {}
            if m.get('diagnostic_tag')!='M5_SWEEP_M1_CHOCH_EARLY_TRIGGER':continue
            key=d.get('evaluation_id')
            if key is None:continue
            events[(d.get('symbol'),str(key))]=d
    tags=Counter()
    for d in snapshots.values():
        if d.get('start_time','')>='2026-09-28T17:17':tags.update(d.get('m5_diagnostic_tags',{}))
    comparisons=[]
    from datetime import datetime
    for d in events.values():
        m=d['m5_detail'];gap=None
        if m.get('confirmation_timestamp') and m.get('sweep_timestamp'):
            gap=(datetime.fromisoformat(m['confirmation_timestamp'])-datetime.fromisoformat(m['sweep_timestamp'])).total_seconds()/60
        score=d.get('score',d.get('final_score'));reasons=d.get('reasons') or []
        only_score=all('insuficiente' in str(r).lower() for r in reasons)
        comparisons.append(dict(symbol=d.get('symbol'),score=score,breakdown=d.get('score_breakdown'),reasons=reasons,
            h1=d.get('h1_context'),m5=m,gap_minutes=gap,
            shadow_thresholds={str(t):bool(only_score and score is not None and score>=t) for t in (60,65,70,75)},
            shadow_max_gap={str(t):gap<=t if gap is not None else None for t in (15,30,60,90)}))
    return dict(day=day,orb=rows,m1_tag_count_current_sessions=tags['M5_SWEEP_M1_CHOCH_EARLY_TRIGGER'],
        recovered_m1_candidates=comparisons,limitations=['Gate sensitivity only; no profit or win rate estimate.',
        'Snapshots overwrite candidates; recovered events are not the complete historical ten.',
        'Threshold approval is not execution authorization.'])

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
    text=json.dumps(analyze(),indent=2,ensure_ascii=False)
    if args.output:Path(args.output).write_text(text,encoding='utf-8')
    else:print(text)
