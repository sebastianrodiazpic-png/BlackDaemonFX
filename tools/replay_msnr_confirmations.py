"""Paired current-rule M15 / native M5 / neutral-D1 H4 experiments, offline.

No broker connection, executor, orders, model activation or preference writes.
Historical spread is a proxy; outputs are never verified training captures.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import fields, replace
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.fetch_msnr_confirmation_history import OUT, TF, save_json
from tools.replay_msnr_live_faithful import HistoricalProvider
from tools.replay_msnr_two_year_comparison import prefix_key, fast_quasimodo
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import normalize_msnr_settings
from strategy.malaysian_snr.research_comparison import compare_samples
from strategy.malaysian_snr.validation import closed_candles
import strategy.malaysian_snr.malaysian_snr_strategy as strategy_module
import strategy.malaysian_snr.history as history_module

VARIANTS = {'M15': ('off', 'off'), 'M15_M5': ('live', 'off'), 'M15_H4': ('off', 'live')}


class Provider(HistoricalProvider):
    def __init__(self, frames, row):
        super().__init__(frames)
        self.row = row
        self.cache = {}
    def get_candles(self, symbol, timeframe, count=100):
        df, closes = self._frames[timeframe]
        idx = int(np.searchsorted(closes, self.now.tz_localize(None).to_datetime64(), side='right'))
        key = (timeframe, idx, count)
        if key not in self.cache:
            if len(self.cache)>40:
                self.cache.clear()
            self.cache[key] = df.iloc[max(0, idx-count):idx].reset_index(drop=True)
        return self.cache[key]
    def get_symbol_info(self, symbol):
        return {'point': self.row['point'], 'trade_tick_size': self.row['tick_size']}
    def get_current_tick(self, symbol):
        df, closes = self._frames['M5']
        idx = int(np.searchsorted(closes, self.now.tz_localize(None).to_datetime64(), side='right'))
        if not idx or self.row['point']<=0 or 'spread' not in df:
            raise ValueError('No causal spread observation')
        # Last CLOSED bar, never the next bar's future aggregated spread.
        bid = float(df.close.iloc[idx-1])
        spread = float(df.spread.iloc[idx-1])*self.row['point']
        return {'bid': bid, 'ask': bid+spread}


def load_frames(row):
    frames = {}
    for tf in TF:
        meta = row['frames'].get(tf, {})
        if not meta.get('rows'):
            raise ValueError(f'NO_NATIVE_{tf}')
        path = (ROOT/meta['file']).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError(f'CHANGED_SNAPSHOT_{tf}')
        raw = pd.read_pickle(path)
        frames[tf] = closed_candles(raw, tf, pd.Timestamp(meta['last_closed_at']))
        if len(frames[tf])!=meta['rows']:
            raise ValueError(f'INVALID_SNAPSHOT_{tf}')
    return frames


def config_for(settings, variant):
    names = {f.name for f in fields(MalaysianSNRConfig)}
    direct = {key: value for key, value in settings.items() if key in names}
    direct.update(allowed_symbols=(), tp1_min_rr=2., tp2_runner_rr=4.,
                  minimum_body_ratio=settings['continuation_min_body_ratio'],
                  enable_scenario_1_continuation=settings['continuation_mode']!='off',
                  m5_confirmation_mode=VARIANTS[variant][0], h4_neutral_fallback_mode=VARIANTS[variant][1])
    return MalaysianSNRConfig(**direct)


@contextmanager
def accelerated():
    """Cache immutable prefixes only. No pattern or macro rejection shortcut."""
    originals = {}
    def verified(frame, tf, now):
        if len(frame) and frame.time.iloc[-1]+pd.Timedelta(minutes=TF[tf])>now:
            raise AssertionError('Future candle exposed')
        return frame
    for module, name in ((strategy_module, 'closed_candles'), (history_module, 'closed_candles')):
        originals[module, name] = getattr(module, name)
        setattr(module, name, verified)
    def cached(function):
        cache = {}
        def call(frame, *args, **kwargs):
            key = (prefix_key(frame), args, tuple(sorted(kwargs.items())))
            if key not in cache:
                if len(cache)>512:
                    cache.clear()
                cache[key] = function(frame, *args, **kwargs)
            return cache[key]
        return call
    for name in ('compute_atr', 'compute_adx', 'av_levels', 'active_av_levels', 'quasimodo_candidates', 'structural_bias'):
        originals[strategy_module, name] = getattr(strategy_module, name)
        function = fast_quasimodo if name=='quasimodo_candidates' else originals[strategy_module, name]
        setattr(strategy_module, name, cached(function))
    try:
        yield
    finally:
        for (module, name), original in originals.items():
            setattr(module, name, original)


def simulate_native(direction, entry, stop, tp1, tp2, frame, point, horizon_hours=50):
    sign = 1 if direction=='BUY' else -1
    risk = sign*(entry-stop)
    if risk<=0 or frame.empty:
        return {'outcome': 'NO_DATA', 'rr': None, 'bars': 0, 'ambiguous': False}
    start = frame.time.iloc[0]
    limit = start+pd.Timedelta(hours=horizon_hours)
    first_rr, runner_rr = sign*(tp1-entry)/risk, sign*(tp2-entry)/risk
    first_done, ambiguous, active_stop = False, False, stop
    def result(move, outcome, index):
        return {'rr': .5*first_rr+.5*move if first_done else move,
                'outcome': outcome, 'bars': index+1, 'ambiguous': ambiguous}
    prior = None
    for i, bar in enumerate(frame.itertuples(index=False)):
        if bar.time>=limit:
            return {'outcome': 'HORIZON_CENSORED', 'rr': None, 'bars': i, 'ambiguous': ambiguous}
        if prior is not None and bar.time-prior!=pd.Timedelta(minutes=5):
            # Includes weekend gaps: avoid inventing an intragap execution.
            return {'outcome': 'HISTORY_GAP_CENSORED', 'rr': None, 'bars': i, 'ambiguous': ambiguous}
        prior = bar.time
        spread = float(getattr(bar, 'spread', 0))*point
        shift = spread if sign==-1 else 0.
        high, low, opening = bar.high+shift, bar.low+shift, bar.open+shift
        if sign*(opening-active_stop)<=0:
            return result(sign*(opening-entry)/risk, 'GAP_STOP', i)
        stop_hit = low<=active_stop if sign==1 else high>=active_stop
        first_hit = high>=tp1 if sign==1 else low<=tp1
        runner_hit = high>=tp2 if sign==1 else low<=tp2
        if stop_hit:
            ambiguous = ambiguous or (runner_hit if first_done else first_hit)
            return result(sign*(active_stop-entry)/risk, 'BE' if first_done else 'STOP', i)
        if not first_done and first_hit:
            first_done = True
            if tp1==tp2:
                return result(runner_rr, 'TP2', i)
            active_stop = entry+sign*(spread+2*point)
            new_stop_hit = low<=active_stop if sign==1 else high>=active_stop
            if new_stop_hit:
                ambiguous = True
                # Initial resting runner may have filled first: conservative lower bound.
                return result(sign*(active_stop-entry)/risk, 'TP1_BE_AMBIGUOUS', i)
        if first_done and runner_hit:
            return result(runner_rr, 'TP2', i)
    return {'outcome': 'RIGHT_CENSORED', 'rr': None, 'bars': len(frame), 'ambiguous': ambiguous}


def replay(row, frames, settings, start, end):
    provider = Provider(frames, row)
    variants = {}
    for name in VARIANTS:
        controls = {**settings, 'm5_confirmation_mode': VARIANTS[name][0],
                    'h4_neutral_fallback_mode': VARIANTS[name][1], 'additional_symbols': [], 'version': settings.get('version', 0)}
        # Research fills of observation assets remain entirely offline. Baseline
        # always excludes M5, even if an operator enabled it for one instrument.
        controls['asset_modes'] = {**settings.get('asset_modes', {}), row['symbol']:'live'}
        controls['m5_symbol_modes'] = ({s:('live' if mode=='shadow' else mode)
            for s,mode in settings.get('m5_symbol_modes', {}).items()}
            if name=='M15_M5' else {row['symbol']:'off'})
        controls['continuation_symbol_modes'] = {s:('live' if mode=='shadow' else mode)
            for s,mode in settings.get('continuation_symbol_modes', {}).items()}
        variants[name] = {'analyzer': strategy_module.MalaysianSNRStrategy(provider, config_for(settings, name),
            runtime_settings_loader=lambda c=controls: c), 'busy': -1, 'seen': set(), 'trades': [], 'reasons': Counter()}
    m5 = frames['M5']
    indices = np.flatnonzero(((m5.time>=start) & (m5.time<end)).to_numpy())
    for i in indices:
        if i<1:
            continue
        provider.now = m5.time.iloc[i]
        if m5.time.iloc[i-1]+pd.Timedelta(minutes=5)!=provider.now:
            continue
        quote = provider.get_current_tick(row['symbol'])
        spread = quote['ask']-quote['bid']
        for name, state in variants.items():
            if i<=state['busy']:
                state['reasons']['BUSY_POSITION']+=1
                continue
            reading = state['analyzer'].analyze_symbol(row['symbol'], now_utc=provider.now.to_pydatetime())
            state['reasons'][reading.get('reason', 'CONFIRMED' if reading.get('valid') else 'UNKNOWN')]+=1
            if not reading.get('valid') or reading.get('shadow_only'):
                continue
            sig = reading['signal']
            if sig['setup_id'] in state['seen']:
                state['reasons']['EPISODE_DEDUPLICATED']+=1
                continue
            # Signal only fresh within the existing execution grace.
            if provider.now-pd.Timestamp(sig['confirmation_closed_at'])>pd.Timedelta(seconds=60):
                state['reasons']['STALE_CONFIRMATION']+=1
                continue
            sign = 1 if sig['direction']=='BUY' else -1
            fill = float(m5.open.iloc[i])+(spread if sign==1 else 0.)
            stop = float(sig['stop_loss'])
            risk = sign*(fill-stop)
            exit_quote = float(m5.open.iloc[i])+(spread if sign==-1 else 0.)
            if risk<=0 or sign*(exit_quote-stop)<=0:
                state['reasons']['INVALID_INITIAL_STOP']+=1
                continue
            distance = sign*(fill-sig['ref_level'])/sig['atr']
            if not (0<=distance<=sig['max_entry_distance_atr'] and sign*(fill-sig['invalidation_level'])>0
                    and provider.now<=pd.Timestamp(sig['setup_execution_deadline_at'])):
                state['reasons']['FILL_CONTEXT_CHANGED']+=1
                continue
            runner = float(sig['runner_rr'])
            if sig.get('obstacle_level'):
                room = sign*(sig['tp2_price']-fill)/risk
                if room<2.:
                    state['reasons']['FILL_OBSTACLE_BEFORE_2R']+=1
                    continue
                runner = min(runner, room)
            future = m5.iloc[i:i+601]
            future = future[future.time+pd.Timedelta(minutes=5)<=end]
            outcome = simulate_native(sig['direction'], fill, stop, fill+sign*2*risk, fill+sign*runner*risk, future, row['point'])
            state['busy'] = i+max(0, outcome['bars']-1)
            state['seen'].add(sig['setup_id'])
            state['trades'].append({'variant': name, 'symbol': row['symbol'], 'cohort': row['cohort'],
                'category': row.get('category'), 'time': provider.now.isoformat(), 'setup_id': sig['setup_id'],
                'scenario': sig['scenario'], 'entry_timeframe': sig['entry_timeframe'], 'direction': sig['direction'],
                'freshness': sig['freshness']['state'], 'hour_utc': provider.now.hour,
                'h4_fallback_used': sig.get('h4_neutral_fallback_used', False),
                'entry': fill, 'stop': stop, 'runner_rr': runner, 'entry_spread_proxy': spread,
                'risk_atr': risk/sig['atr'], 'training_eligible': False, 'simulation_only':True,
                'requested_asset_mode':settings.get('asset_modes', {}).get(row['symbol'], 'inherit'), **outcome})
    return {name: {'trades': state['trades'], 'reasons': dict(state['reasons'])} for name, state in variants.items()}


def stats(records):
    closed = [r for r in records if r['rr'] is not None]
    definitive = [r for r in closed if not r['ambiguous']]
    def metrics(rows, cost=0.):
        if not rows:
            return {'trades': 0, 'win_pct': None, 'expectancy_r': None, 'profit_factor': None}
        values = np.array([r['rr']-cost for r in rows])
        loss = -values[values<0].sum()
        n, p, z = len(rows), float((values>0).mean()), 1.95996398454
        center = (p+z*z/(2*n))/(1+z*z/n)
        width = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
        return {'trades': len(rows), 'win_pct': round(100*p, 3),
                'win_ci95_wilson': [round(100*(center-width), 3), round(100*(center+width), 3)],
                'expectancy_r': round(float(values.mean()), 5), 'total_r': round(float(values.sum()), 5),
                'profit_factor': round(float(values[values>0].sum()/loss), 4) if loss else None}
    return {'conservative_ohlc': metrics(closed), 'unambiguous_only': metrics(definitive),
            'extra_cost_0_05r': metrics(closed, .05), 'extra_cost_0_10r': metrics(closed, .10),
            'ambiguous': len(closed)-len(definitive), 'censored': len(records)-len(closed)}


def run_row(row, settings, start, end, reference):
    begun = time.monotonic()
    result = {'symbol': row['symbol'], 'cohort': row['cohort'], 'complete_two_year_start': row.get('complete_two_year_start', False)}
    try:
        frames = load_frames(row)
        if any(frame.time.iloc[0]>start-pd.Timedelta(minutes=TF[tf]) for tf, frame in frames.items()):
            raise ValueError('REQUESTED_WINDOW_UNAVAILABLE')
        from contextlib import nullcontext
        with nullcontext() if reference else accelerated():
            result['variants'] = replay(row, frames, settings, start, end)
        result['seconds'] = round(time.monotonic()-begun, 2)
    except (ValueError, KeyError) as exc:
        result['error'] = str(exc)
    return result


def summarize(results, start, end, target, settings=None):
    all_trades = [trade for r in results for v in r.get('variants', {}).values() for trade in v['trades']]
    summary = {'requested_start': start.isoformat(), 'requested_end': end.isoformat(), 'symbols_completed': len(results),
        'failed_symbols': [r for r in results if r.get('error')], 'promotion': 'NONE; research only', 'groups': {}}
    for variant in VARIANTS:
        for cohort in ('core23', 'historically_pruned37'):
            rows = [r for r in all_trades if r['variant']==variant and r['cohort']==cohort]
            summary['groups'][variant+'_'+cohort] = stats(rows)
    for dimension in ('symbol', 'category', 'scenario', 'freshness', 'entry_timeframe', 'hour_utc'):
        summary['by_'+dimension] = {variant: {str(value): stats([r for r in all_trades if r['variant']==variant and r[dimension]==value])
            for value in sorted({r[dimension] for r in all_trades if r['variant']==variant}, key=str)} for variant in VARIANTS}
    base_ids = {(r['symbol'], r['setup_id']) for r in all_trades if r['variant']=='M15'}
    summary['additional_episodes'] = {variant: stats([r for r in all_trades if r['variant']==variant and
        (r['symbol'], r['setup_id']) not in base_ids]) for variant in VARIANTS if variant!='M15'}
    summary['paired_episodes'] = {variant: len(base_ids & {(r['symbol'], r['setup_id']) for r in all_trades if r['variant']==variant})
        for variant in VARIANTS if variant!='M15'}
    if settings is not None:
        summary['frequency_and_reward_checks'] = {}
        for dimension in ('symbol', 'category', 'scenario'):
            summary['frequency_and_reward_checks'][dimension] = {}
            for value in sorted({r[dimension] for r in all_trades}, key=str):
                base = [r for r in all_trades if r['variant']=='M15' and r[dimension]==value]
                summary['frequency_and_reward_checks'][dimension][str(value)] = {
                    variant: compare_samples(base, [r for r in all_trades if r['variant']==variant and r[dimension]==value],
                        settings, same_window_and_feed=True) for variant in VARIANTS if variant!='M15'}
    save_json(target/'summary.json', summary)
    if all_trades:
        pd.DataFrame(all_trades).to_csv(target/'trades.csv', index=False)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--start', default='2026-10-04T00:00:00Z')
    ap.add_argument('--end', default='2026-10-11T00:00:00Z')
    ap.add_argument('--symbols', default='')
    ap.add_argument('--run-name', default='pilot_7d')
    ap.add_argument('--reference', action='store_true', help='Disable prefix caches for parity checks')
    ap.add_argument('--jobs', type=int, default=1, choices=(1, 2, 3))
    ap.add_argument('--settings-file', help='Frozen exported settings JSON, workspace path')
    args = ap.parse_args()
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)
    if start.tzinfo is None or end.tzinfo is None or start>=end:
        ap.error('Use increasing UTC-aware dates')
    if Path(args.run_name).name!=args.run_name:
        ap.error('Run name must be one directory name')
    manifest = json.loads((OUT/'confirmation_history_manifest.json').read_text())
    settings_path = Path(args.settings_file).resolve() if args.settings_file else OUT/'settings_after.json'
    if not settings_path.is_relative_to(ROOT):
        ap.error('Settings file must be within the workspace')
    settings = json.loads(settings_path.read_text())['settings']
    settings = {**normalize_msnr_settings({k:v for k,v in settings.items() if k not in ('version', 'updated_at')}),
                'version':settings.get('version',0),'updated_at':settings.get('updated_at')}
    target = OUT/args.run_name
    target.mkdir(parents=True, exist_ok=True)
    sources = ['tools/replay_msnr_confirmations.py', 'tools/replay_msnr_live_faithful.py',
               'strategy/malaysian_snr/config.py', 'strategy/malaysian_snr/runtime_settings.py',
               'strategy/malaysian_snr/malaysian_snr_strategy.py', 'strategy/malaysian_snr/validation.py',
               'strategy/malaysian_snr/opportunity_rules.py', 'strategy/malaysian_snr/experiments.py',
               'strategy/malaysian_snr/history.py', 'strategy/malaysian_snr/video_rules.py', 'config/symbol_policy.py',
               'strategy/malaysian_snr/universe.py', 'strategy/malaysian_snr/research_comparison.py']
    source_hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    manifest_hash = hashlib.sha256((OUT/'confirmation_history_manifest.json').read_bytes()).hexdigest()
    if (target/'run.json').exists():
        prior = json.loads((target/'run.json').read_text())
        if (prior['start']!=start.isoformat() or prior['end']!=end.isoformat() or prior['settings']!=settings
                or prior.get('source_hashes')!=source_hashes or prior.get('manifest_hash')!=manifest_hash):
            raise ValueError('Existing checkpoint belongs to a different frozen experiment')
    save_json(target/'run.json', {'start': start.isoformat(), 'end': end.isoformat(), 'settings': settings,
        'variants': VARIANTS, 'strategy_version': MalaysianSNRConfig().strategy_version,
        'source_hash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_hashes': source_hashes, 'manifest_hash': manifest_hash,
        'limitations': ['historical spread proxy; no verified fees/slippage/swap',
            'structural DEMO experiment; incompatible classifier observed', 'no cross-symbol portfolio limits',
            'OHLC ambiguity reported; missing outcome bars censored', 'historically selected universe; no pristine holdout',
            'bar-close decision cadence, broker stop-distance/tick rounding not reproduced']})
    selected = set(args.symbols.split(',')) if args.symbols else None
    results = []
    from concurrent.futures import ProcessPoolExecutor, as_completed
    rows = [row for row in manifest['symbols'] if selected is None or row['symbol'] in selected]
    if selected is not None and selected-set(row['symbol'] for row in rows):
        ap.error('A requested symbol is absent from the snapshot')
    pending = []
    for row in rows:
        file = target/f'{row["symbol"].replace(" ", "_")}.json'
        if file.exists():
            results.append(json.loads(file.read_text()))
        else:
            pending.append(row)
    summarize(results, start, end, target, settings)
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_row, row, settings, start, end, args.reference) for row in pending]
        for future in as_completed(futures):
            result = future.result()
            save_json(target/f'{result["symbol"].replace(" ", "_")}.json', result)
            results.append(result)
            print(json.dumps({'symbol': result['symbol'], 'seconds': result.get('seconds'), 'error': result.get('error'),
                'completed': len(results), 'total': len(rows),
                'trades': {k: len(v['trades']) for k,v in result.get('variants', {}).items()}}), flush=True)
            summarize(results, start, end, target, settings)


if __name__=='__main__':
    main()
