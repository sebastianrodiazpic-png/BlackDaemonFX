"""Frozen, paired offline video hypotheses; no broker initialization or orders."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.replay_msnr_confirmations import Provider, load_frames, accelerated, simulate_native, stats
from tools.fetch_msnr_confirmation_history import OUT as HISTORY, save_json
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import normalize_msnr_settings
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.research_comparison import compare_samples
from strategy.execution.live_trading_engine import LiveTradingEngine

PROFILES = {
    'baseline': {},
    'breaker': {'breaker_pair_mode': 'live'},
    'pinbar': {'retest_pinbar_mode': 'live'},
    'expanded_quality': {'breaker_pair_mode': 'live', 'retest_pinbar_mode': 'live',
        'session_policy': 'market_hours', 'obstacle_av_definition': 'body_turns', 'h4_obstacle_mode': 'live'},
    'reference': {'session_policy': 'market_hours', 'obstacle_av_definition': 'body_turns'},
}


def primary_controls(settings, symbol, patch):
    controls = dict(settings)
    # Disable only observation branches: they cannot authorize primary fills.
    for key, value in list(controls.items()):
        if key.endswith('_mode') and value == 'shadow':
            controls[key] = 'off'
    controls.update(breaker_pair_mode='off', retest_pinbar_mode='off',
                    session_policy='legacy_utc', obstacle_av_definition='engulfing', h4_obstacle_mode='off')
    controls.update(patch)
    # A research fill is explicitly marked for assets in observation or outside
    # selection. This does not change preferences or authorize execution.
    controls['asset_modes'] = {**settings['asset_modes'], symbol: 'live'}
    return controls


def paired_replay(row, frames, settings, start, split, end):
    provider = Provider(frames, row)
    config_names = {f.name for f in fields(MalaysianSNRConfig)}
    states = {}
    for name, patch in PROFILES.items():
        controls = primary_controls(settings, row['symbol'], patch)
        cfg = MalaysianSNRConfig(allowed_symbols=(), **{k:v for k,v in controls.items() if k in config_names})
        analyzer = MalaysianSNRStrategy(provider, cfg, lambda c=controls: c)
        # No constructor, executor, connection or order method. These two pure
        # decision gates use only captured signals and CLOSED cached candles.
        gate_engine = object.__new__(LiveTradingEngine)
        gate_engine.config = SimpleNamespace(bot_profile='MALAYSIAN_SNR', step_min_adx=25.)
        gate_engine.provider = provider
        gate_engine.malaysian_snr_strategy = analyzer
        states[name] = dict(analyzer=analyzer, gate_engine=gate_engine, controls=controls,
                            busy=-1, seen=set(), trades=[], reasons=Counter())
    m5 = frames['M5']
    indices = np.flatnonzero(((m5.time>=start) & (m5.time<end)).to_numpy())
    for i in indices:
        if i<1 or m5.time.iloc[i-1]+pd.Timedelta(minutes=5)!=m5.time.iloc[i]:
            continue
        provider.now = m5.time.iloc[i]
        spread_quote = provider.get_current_tick(row['symbol'])
        spread = spread_quote['ask']-spread_quote['bid']
        for name, state in states.items():
            if i<=state['busy']:
                continue
            reading = state['analyzer'].analyze_symbol(row['symbol'], provider.now)
            if not reading.get('valid') or reading.get('shadow_only'):
                state['reasons'][reading.get('reason', 'SHADOW')]+=1
                continue
            sig = dict(reading['signal'])
            if sig['setup_id'] in state['seen']:
                continue
            if provider.now-pd.Timestamp(sig['confirmation_closed_at'])>pd.Timedelta(seconds=60):
                state['reasons']['STALE_CONFIRMATION']+=1
                continue
            sign = 1 if sig['direction']=='BUY' else -1
            fill = float(m5.open.iloc[i])+(spread if sign==1 else 0.)
            stop = float(sig['stop_loss'])
            risk = sign*(fill-stop)
            if risk<=0 or sign*(float(m5.open.iloc[i])+(spread if sign==-1 else 0.)-stop)<=0:
                state['reasons']['INVALID_INITIAL_STOP']+=1
                continue
            distance = sign*(fill-sig['ref_level'])/sig['atr']
            if not (0<=distance<=sig['max_entry_distance_atr'] and sign*(fill-sig['invalidation_level'])>0
                    and provider.now<=pd.Timestamp(sig['setup_execution_deadline_at'])):
                state['reasons']['FILL_CONTEXT_CHANGED']+=1
                continue
            sig['entry_price'] = fill
            gate = state['gate_engine']._step_quality_gate(row['symbol'], sig, reading)
            if gate is None:
                gate = state['gate_engine']._boom_crash_quality_gate(row['symbol'], sig['direction'], sig, reading)
            if gate:
                state['reasons'][gate['reason']]+=1
                continue
            runner = float(sig['runner_rr'])
            if sig.get('obstacle_level'):
                room = sign*(sig['tp2_price']-fill)/risk
                if room<2:
                    state['reasons']['FILL_OBSTACLE_BEFORE_2R']+=1
                    continue
                runner = min(runner, room)
            # Separate evaluation windows. No result path crosses the declared
            # holdout split; unresolved outcomes are censored instead of wins.
            boundary = split if provider.now<split else end
            future = m5.iloc[i:i+601]
            future = future[future.time+pd.Timedelta(minutes=5)<=boundary]
            outcome = simulate_native(sig['direction'], fill, stop, fill+sign*2*risk,
                                       fill+sign*runner*risk, future, row['point'])
            state['busy'] = i+max(0, outcome['bars']-1)
            state['seen'].add(sig['setup_id'])
            state['trades'].append(dict(profile=name, symbol=row['symbol'], time=provider.now.isoformat(),
                window='development' if provider.now<split else 'held_out', scenario=sig['scenario'],
                entry_timeframe=sig['entry_timeframe'], direction=sig['direction'],
                setup_id=sig['setup_id'], entry=fill, stop=stop, runner_rr=runner,
                pinbar_only=sig['retest_evidence'].get('pinbar_only', False),
                entry_spread_proxy=spread, simulation_only=True, training_eligible=False,
                requested_asset_mode=settings['asset_modes'].get(row['symbol'], 'inherit'), **outcome))
    return {name: {'trades':s['trades'], 'reasons':dict(s['reasons'])} for name,s in states.items()}


def run_row(row, settings, start, split, end):
    begun = time.monotonic()
    try:
        frames = load_frames(row)
        if any(frame.time.iloc[0]>start-pd.Timedelta(days=7) for frame in frames.values()):
            raise ValueError('INSUFFICIENT_PREWINDOW_NATIVE_HISTORY')
        with accelerated():
            result = paired_replay(row, frames, settings, start, split, end)
        return {'symbol':row['symbol'], 'profiles':result, 'seconds':round(time.monotonic()-begun,2)}
    except (ValueError, KeyError) as exc:
        return {'symbol':row['symbol'], 'error':str(exc)}


def summarize(results, settings):
    trades = [t for r in results for p in r.get('profiles', {}).values() for t in p['trades']]
    summary = {'automatic_promotion':False, 'failed':[r for r in results if 'error' in r],
               'profiles':{}, 'comparisons':{}, 'by_symbol':{}}
    for window in ('all', 'development', 'held_out'):
        rows = trades if window=='all' else [t for t in trades if t['window']==window]
        summary['profiles'][window] = {p:stats([t for t in rows if t['profile']==p]) for p in PROFILES}
        base = [t for t in rows if t['profile']=='baseline']
        summary['comparisons'][window] = {p:compare_samples(base,[t for t in rows if t['profile']==p],
            settings,same_window_and_feed=True) for p in PROFILES if p!='baseline'}
        summary['by_symbol'][window] = {symbol:{p:stats([t for t in rows if t['symbol']==symbol and t['profile']==p])
            for p in PROFILES} for symbol in sorted({t['symbol'] for t in trades})}
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--symbols', default='Step Index,EURUSD,BTCUSD')
    ap.add_argument('--start',default='2026-09-27T00:00:00Z')
    ap.add_argument('--split',default='2026-10-04T00:00:00Z')
    ap.add_argument('--end',default='2026-10-11T00:00:00Z')
    ap.add_argument('--output',default='storage/analysis/msnr_videos_20261013/replay')
    ap.add_argument('--jobs',type=int,choices=(1,2,3),default=3)
    args = ap.parse_args()
    start, split, end = map(pd.Timestamp,(args.start,args.split,args.end))
    if not all(x.tzinfo is not None for x in (start,split,end)) or not start<split<end:
        ap.error('Use increasing timezone-aware dates')
    target = (ROOT/args.output).resolve()
    if not target.is_relative_to(ROOT):ap.error('Output must stay within workspace')
    target.mkdir(parents=True,exist_ok=True)
    if (target/'run.json').exists():ap.error('Use a new output directory; frozen experiments are immutable')
    exported = json.loads((ROOT/'storage/analysis/msnr_configuracion_guiada_20261012/settings_after.json').read_text())
    settings = normalize_msnr_settings({k:v for k,v in exported['settings'].items() if k not in ('version','updated_at')})
    settings.update(research_min_frequency_ratio=1.05,research_min_resolved_trades=50,research_min_win_rate_improvement_pp=1.)
    sources = [Path(__file__).relative_to(ROOT).as_posix(), 'tools/replay_msnr_confirmations.py',
        'tools/replay_msnr_two_year_comparison.py', 'tools/replay_msnr_live_faithful.py',
        'strategy/execution/live_trading_engine.py', *[p.relative_to(ROOT).as_posix() for p in (ROOT/'strategy/malaysian_snr').glob('*.py')]]
    hashes = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    for name in sources:
        path = target/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((ROOT/name).read_bytes())
    manifest_path = HISTORY/'confirmation_history_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    symbols = set(args.symbols.split(','))
    rows = [r for r in manifest['symbols'] if r['symbol'] in symbols]
    if symbols!={r['symbol'] for r in rows}:ap.error('Requested symbol absent from native snapshot')
    save_json(target/'run.json',dict(start=start.isoformat(),split=split.isoformat(),end=end.isoformat(),
        settings=settings,profiles=PROFILES,symbols=sorted(symbols),source_hashes=hashes,
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),strategy_version=MalaysianSNRConfig().strategy_version,
        limitations=['spread proxy; fees/slippage/swap not verified','no AI veto, portfolio limits or lot/tick/stop rounding',
            'Step and Boom/Crash gates applied BEFORE fills; other shared gates not reproduced',
            'historically selected data; held-out window is temporal, not pristine independent validation',
            'OHLC ambiguity and censored outcomes; no two-year native-M5 coverage']))
    results=[]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for future in as_completed([pool.submit(run_row,r,settings,start,split,end) for r in rows]):
            result=future.result();results.append(result)
            save_json(target/(result['symbol'].replace(' ','_')+'.json'),result)
            save_json(target/'summary.json',summarize(results,settings))
            print(json.dumps({k:v for k,v in result.items() if k!='profiles'}),flush=True)
    return 1 if any('error' in r for r in results) else 0


if __name__=='__main__':
    raise SystemExit(main())
