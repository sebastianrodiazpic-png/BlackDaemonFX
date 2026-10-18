"""Paired causal replay of the actual pre-change and current MSNR detectors.

Offline only. Frozen native broker candles, identical execution assumptions,
bounded memoization of immutable closed prefixes, and no parameter fitting.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, subprocess, sys, time, types
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import strategy.malaysian_snr.malaysian_snr_strategy as current
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.validation import av_levels as validation_av_levels
from tools.audit_msnr_causal import statistics
from tools.replay_msnr_live_faithful import HistoricalProvider, MAX_HOLD_BARS

TF_MINUTES = {'M15':15,'H1':60,'D1':1440}
OUT = ROOT / 'storage/analysis/msnr_v21_two_years_20261011'

def read_manifest(out=OUT):
    shards=list(out.glob('history_manifest_shard_*.json'))
    if shards:
        manifests=[]
        for p in shards:
            for attempt in range(5):
                try:
                    manifests.append(json.loads(p.read_text()))
                    break
                except (OSError,ValueError):
                    if attempt==4:
                        raise
                    time.sleep(.05)
        return {**manifests[0],'symbols':sorted([r for m in manifests for r in m['symbols']],key=lambda r:r['symbol'])}
    return json.loads((out/'history_manifest.json').read_text())

def baseline_modules(out):
    sources = {}
    for filename in ('config','validation','malaysian_snr_strategy'):
        path = f'strategy/malaysian_snr/{filename}.py'
        saved = out / 'baseline_source' / f'{filename}.py'
        if saved.exists():
            sources[filename]=saved.read_text(encoding='utf-8-sig')
        else:
            sources[filename] = subprocess.run(['git','show',f'HEAD:{path}'],cwd=ROOT,check=True,capture_output=True).stdout.decode('utf-8-sig')
            saved.parent.mkdir(parents=True,exist_ok=True)
            saved.write_text(sources[filename],encoding='utf-8')
    modules = {}
    for name in ('config','validation','malaysian_snr_strategy'):
        mod = types.ModuleType(f'msnr_audit_baseline_{name}')
        sys.modules[mod.__name__] = mod
        source = sources[name].replace('from strategy.malaysian_snr.config import', 'from msnr_audit_baseline_config import').replace('from strategy.malaysian_snr.validation import', 'from msnr_audit_baseline_validation import')
        exec(compile(source,str(out/'baseline_source'/f'{name}.py'),'exec'),mod.__dict__)
        modules[name] = mod
    return modules['malaysian_snr_strategy'],modules['config'].MalaysianSNRConfig, sources

def prefix_key(frame):
    if frame.empty:
        return (0,)
    return (len(frame),frame.time.iloc[0].value,frame.time.iloc[-1].value)

def memoized(function):
    cache = {}
    def call(frame,*args,**kwargs):
        key = (prefix_key(frame),args,tuple(sorted(kwargs.items())))
        if key not in cache:
            if len(cache) >= 512:
                cache.clear()
            cache[key] = function(frame,*args,**kwargs)
        return cache[key]
    return call

class LastIndicator:
    """Offline callers only consume iloc[-1]; retain the exact original scalar."""
    def __init__(self,value):
        self.value=value
        self.iloc=self
    def __getitem__(self,index):
        if index!=-1:
            raise AssertionError('Replay indicator cache supports only iloc[-1]')
        return self.value

def memoized_indicator(function,name,cache):
    def call(frame,*args,**kwargs):
        key=(name,prefix_key(frame),args,tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key]=LastIndicator(function(frame,*args,**kwargs).iloc[-1])
        return cache[key]
    return call

def fast_quasimodo(frame,radius=2):
    """Same strict pivot/BOS rules as validation.py, with vectorized neighbors."""
    n = len(frame)
    if n <= 2*radius:
        return []
    h,l,c = (frame[k].to_numpy(float) for k in ('high','low','close'))
    hw = np.lib.stride_tricks.sliding_window_view(h,2*radius+1)
    lw = np.lib.stride_tricks.sliding_window_view(l,2*radius+1)
    hp = hw[:,radius] > np.maximum(hw[:,:radius].max(axis=1),hw[:,radius+1:].max(axis=1))
    lp = lw[:,radius] < np.minimum(lw[:,:radius].min(axis=1),lw[:,radius+1:].min(axis=1))
    swings = []
    for j in np.flatnonzero(hp != lp):
        i = int(j+radius)
        high = bool(hp[j])
        point = {'type':'HIGH' if high else 'LOW','idx':i,'price':float(h[i] if high else l[i])}
        if swings and swings[-1]['type'] == point['type']:
            if (high and point['price'] > swings[-1]['price']) or (not high and point['price'] < swings[-1]['price']):
                swings[-1] = point
        else:
            swings.append(point)
    candidates = []
    for a,b,head in zip(swings,swings[1:],swings[2:]):
        bullish = a['type']=='LOW' and b['type']=='HIGH' and head['type']=='LOW' and head['price'] < a['price']
        bearish = a['type']=='HIGH' and b['type']=='LOW' and head['type']=='HIGH' and head['price'] > a['price']
        if not (bullish or bearish):
            continue
        offset = head['idx']+radius+1
        breaks = np.flatnonzero(c[offset:] > b['price'] if bullish else c[offset:] < b['price'])
        if len(breaks) and offset+breaks[0] == n-1:
            candidates.append({'direction':'BUY' if bullish else 'SELL','shoulder':a['price'],'head':head['price'],'neckline':b['price']})
    return list(reversed(candidates))

def has_fractal(frame, minimum_body_ratio=.55):
    if len(frame)<3:
        return False
    x = frame[['open','high','low','close']].to_numpy(float)[-3:]
    a,b,last = x
    span = last[1]-last[2]
    return bool(span>0 and abs(last[3]-last[0])/span >= minimum_body_ratio and
                ((b[2]<a[2] and last[3]>last[0] and last[3]>a[1]) or
                 (b[1]>a[1] and last[3]<last[0] and last[3]<a[2])))

def fast_active_av_levels(frame, definition='engulfing'):
    """Same body invalidation rule; slice immutable price arrays instead of frames."""
    closes=frame.close.to_numpy(float)
    return [level for level in validation_av_levels(frame,include_latest=True,definition=definition)
            if not np.any(closes[level['idx']+1:] > level['level'] if level['type']=='A_RESISTANCE'
                          else closes[level['idx']+1:] < level['level'])]

class ClosedProvider(HistoricalProvider):
    """Whole snapshot validated once; return only sorted, closed, reset prefixes."""
    def __init__(self,frames):
        super().__init__(frames)
        self._last = {}
    def get_candles(self,symbol,timeframe,count=100):
        frame,close_times = self._frames[timeframe]
        index = int(np.searchsorted(close_times,np.datetime64(self.now.tz_convert('UTC').tz_localize(None)),side='right'))
        key = (index,count)
        if timeframe not in self._last or self._last[timeframe][0] != key:
            result = frame.iloc[max(0,index-count):index].reset_index(drop=True)
            self._last[timeframe] = (key,result)
        return self._last[timeframe][1]

def verified_closed(frame,timeframe,now):
    # The caller validates the entire snapshot before enabling this shortcut.
    if len(frame) and frame.time.iloc[-1]+pd.Timedelta(minutes=TF_MINUTES[timeframe])>now:
        raise AssertionError('Future candle in replay provider')
    return frame

def install_acceleration(module,indicator_cache=None):
    original = {name:getattr(module,name) for name in ('closed_candles','compute_atr','compute_adx','av_levels','quasimodo_candidates')}
    module.closed_candles = verified_closed
    indicator_cache={} if indicator_cache is None else indicator_cache
    module.compute_atr = memoized_indicator(original['compute_atr'],'atr',indicator_cache)
    module.compute_adx = memoized_indicator(original['compute_adx'],'adx',indicator_cache)
    module.av_levels = memoized(original['av_levels'])
    module.quasimodo_candidates = memoized(fast_quasimodo)
    if hasattr(module,'active_av_levels'):
        original['active_av_levels'] = module.active_av_levels
        module.active_av_levels = memoized(fast_active_av_levels)
    if hasattr(module.MalaysianSNRStrategy,'_setups_at_break'):
        method = module.MalaysianSNRStrategy._setups_at_break
        original['_setups_at_break'] = method
        cache = {}
        def setups(self,frame,*args,**kwargs):
            minimum_body = kwargs.get('fractal_min_body_ratio', getattr(self.config, 'fractal_min_body_ratio', .55))
            maximum_distance = kwargs.get('fractal_max_entry_distance_atr', getattr(self.config, 'fractal_max_entry_distance_atr', None))
            key = (self, prefix_key(frame), minimum_body, maximum_distance, args, tuple(sorted(kwargs.items())))
            if key not in cache:
                if len(cache)>=512:
                    cache.clear()
                if not self.config.enable_scenario_1_continuation and not (
                        (self.config.enable_quasimodo_pattern and module.quasimodo_candidates(frame,self.config.qm_swing_radius)) or
                        (self.config.enable_scenario_3_fractal and has_fractal(frame, minimum_body))):
                    cache[key] = []
                else:
                    cache[key] = method(self,frame,*args,**kwargs)
            return cache[key]
        module.MalaysianSNRStrategy._setups_at_break = setups
    return original

def restore(module,original):
    for name,value in original.items():
        if name=='_setups_at_break':
            module.MalaysianSNRStrategy._setups_at_break=value
        else:
            setattr(module,name,value)

def load_snapshot(row,out=OUT):
    frames = {}
    for tf in TF_MINUTES:
        meta = row['frames'].get(tf,{})
        if not meta.get('rows') or meta.get('duplicates') or meta.get('invalid_ohlc'):
            raise ValueError(f'Insufficient/invalid {tf}: {meta}')
        path = out / meta['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError(f'Snapshot changed: {path.name}')
        frame = pd.read_pickle(path)
        frame['time'] = pd.to_datetime(frame.time,utc=True)
        frames[tf] = frame.sort_values('time').reset_index(drop=True)
    return frames

def simulate_buffered(direction,entry,sl,tp1,tp2,o,h,l,c,spreads,be_multiplier=1.5):
    """Bid OHLC, ask exits for SELL, adverse ambiguity and gaps, split 50/50."""
    sign = 1 if direction=='BUY' else -1
    risk = sign*(entry-sl)
    first_rr = sign*(tp1-entry)/risk
    runner_rr = sign*(tp2-entry)/risk
    first_done = False
    active_sl = sl
    for i in range(min(MAX_HOLD_BARS,len(h))):
        spread = spreads[i]
        shift = spread if sign==-1 else 0.
        high,low,opening = h[i]+shift,l[i]+shift,o[i]+shift
        if sign*(opening-active_sl)<=0:
            move = sign*(opening-entry)/risk
            return (.5*(first_rr+move) if first_done else move),'GAP_SL',i+1
        hit_sl = low<=active_sl if sign==1 else high>=active_sl
        if hit_sl:
            move = sign*(active_sl-entry)/risk
            return (.5*(first_rr+move) if first_done else move),('TP1+BE' if first_done else 'SL'),i+1
        hit_first = high>=tp1 if sign==1 else low<=tp1
        hit_runner = high>=tp2 if sign==1 else low<=tp2
        if not first_done and hit_first and hit_runner and tp1==tp2:
            # Both resting targets fill at the same price before BE can move.
            return .5*(first_rr+runner_rr),'TP2',i+1
        if not first_done and hit_first:
            first_done = True
            active_sl = entry+sign*be_multiplier*spread
            if sign*(tp1-active_sl)<=0:
                # Impossible safe BE placement: broker-level guard unavailable.
                active_sl = entry
            crossed_be = low<=active_sl if sign==1 else high>=active_sl
            if crossed_be:
                move=sign*(active_sl-entry)/risk
                return .5*(first_rr+move),'TP1+BE_AMBIGUOUS',i+1
        if first_done and hit_runner:
            return .5*(first_rr+runner_rr),'TP2',i+1
    n=min(MAX_HOLD_BARS,len(h))
    if not n:
        return 0.,'NO_DATA',0
    move=sign*(c[n-1]+(spreads[n-1] if sign==-1 else 0.)-entry)/risk
    return (.5*(first_rr+move) if first_done else move),('TIMEOUT' if n==MAX_HOLD_BARS else 'RIGHT_CENSORED'),n

def replay(row,frames,module,cfg,start,end,*,accelerated=True,screen=True):
    provider = ClosedProvider(frames) if accelerated else HistoricalProvider(frames)
    strat = module.MalaysianSNRStrategy(provider,cfg)
    m = frames['M15']
    o,h,l,c = (m[k].to_numpy(float) for k in ('open','high','low','close'))
    closes = m.time+pd.Timedelta(minutes=15)
    ns = closes.to_numpy(dtype='datetime64[ns]')
    indices = np.flatnonzero((closes>=start)&(closes<end))
    if 'spread' in m and row.get('point') and (m.spread>0).any():
        spreads=m.spread.to_numpy(float)*row['point']
        spread_source='historical_MT5_points'
    else:
        spreads=np.full(len(m),row.get('legacy_spread') or row.get('fallback_spread') or 0.)
        spread_source='fixed_estimate'
    counters=Counter()
    records=[]
    busy=-1
    executed=set()
    last_structure=None
    eligible=False
    possible=[]
    started=time.monotonic()
    for i in indices:
        if i+1>=len(m):
            continue
        if i<=busy:
            counters['BUSY_POSITION']+=1
            continue
        provider.now=closes.iloc[i]
        if screen:
            if cfg.enable_session_killzones_filter and not module.is_synthetic_symbol(row['symbol']):
                hour=provider.now.hour+provider.now.minute/60
                if not (7<=hour<11 or 12.5<=hour<17):
                    counters['SESSION_FILTER_OUTSIDE_KILLZONE']+=1
                    continue
            hf=provider.get_candles(row['symbol'],'H1',80)
            structure_key=prefix_key(hf)
            if structure_key!=last_structure:
                last_structure=structure_key
                if len(hf)<28:
                    eligible=False
                    possible=[]
                elif hasattr(strat,'_setups_at_break'):
                    anchors=int(cfg.retest_window_minutes/60)+2
                    possible=[]
                    for j in range(len(hf)-1,max(26,len(hf)-anchors-1),-1):
                        prefix=hf.iloc[:j+1]
                        closed_at=prefix.time.iloc[-1]+pd.Timedelta(hours=1)
                        # Older anchors cannot emit a signal within the configured window.
                        if provider.now-closed_at>pd.Timedelta(minutes=cfg.retest_window_minutes):
                            continue
                        possible.extend((s['direction'],closed_at) for s in strat._setups_at_break(prefix) if not s.get('blocked_reason'))
                    eligible=bool(possible)
                else:
                    if cfg.enable_scenario_1_continuation:
                        raise ValueError('Screening is proven only with continuation disabled')
                    directions=[p['direction'] for p in module.quasimodo_candidates(hf,cfg.qm_swing_radius)] if cfg.enable_quasimodo_pattern else []
                    if cfg.enable_scenario_3_fractal and has_fractal(hf, getattr(cfg, 'fractal_min_body_ratio', .55)):
                        directions.append('BUY' if hf.close.iloc[-1]>hf.open.iloc[-1] else 'SELL')
                    possible=[(direction,hf.time.iloc[-1]+pd.Timedelta(hours=1)) for direction in directions]
                    eligible=bool(possible)
            if not eligible:
                counters['SKIPPED_PROVEN_NO_H1_PATTERN']+=1
                continue
            daily_direction=None
            daily_enforced = cfg.enable_daily_storyline_filter and (
                not module.is_synthetic_symbol(row['symbol']) or
                getattr(cfg, 'enable_synthetic_daily_storyline_filter', True))
            if cfg.enable_daily_storyline_filter:
                daily=provider.get_candles(row['symbol'],'D1',40)
                if daily.empty or (daily_enforced and daily.close.iloc[-1]==daily.open.iloc[-1]):
                    counters['SKIPPED_MISSING_OR_NEUTRAL_D1']+=1
                    continue
                if daily_enforced:
                    daily_direction='BUY' if daily.close.iloc[-1]>daily.open.iloc[-1] else 'SELL'
            window=pd.Timedelta(minutes=cfg.retest_window_minutes) if hasattr(cfg,'retest_window_minutes') else pd.Timedelta(minutes=59)
            if not any(module.is_direction_allowed(row['symbol'],direction) and
                       (daily_direction is None or direction==daily_direction) and
                       pd.Timedelta(0)<provider.now-closed_at<=window for direction,closed_at in possible):
                counters['SKIPPED_PROVEN_DIRECTION_OR_TIME_REJECTION']+=1
                continue
        result=strat.analyze_symbol(row['symbol'],now_utc=provider.now.to_pydatetime())
        counters[result.get('reason','VALID' if result.get('valid') else 'UNKNOWN')]+=1
        if not result.get('valid'):
            continue
        sig=result['signal']
        identity=sig.get('setup_id')
        if identity and identity in executed:
            counters['SETUP_DEDUPLICATED']+=1
            continue
        if m.time.iloc[i+1]!=provider.now:
            counters['NEXT_OPEN_DATA_GAP']+=1
            continue
        direction=sig['direction']
        sign=1 if direction=='BUY' else -1
        entry=o[i+1]+(spreads[i+1] if sign==1 else 0.)
        sl=float(sig['stop_loss'])
        risk=sign*(entry-sl)
        if risk<=0:
            counters['INVALID_FILL_RISK']+=1
            continue
        exit_quote=o[i+1]+(spreads[i+1] if sign==-1 else 0.)
        if sign*(exit_quote-sl)<=0:
            # SL must be below executable Bid for BUY and above Ask for SELL.
            # An already-crossed SL is an invalid entry, not a realized gap loss.
            counters['INVALID_INITIAL_SL_QUOTE']+=1
            continue
        if identity:
            distance=sign*(entry-float(sig['ref_level']))/float(sig['atr'])
            deadline=pd.Timestamp(sig['setup_execution_deadline_at'])
            if not (0<=distance<=float(sig['max_entry_distance_atr']) and sign*(entry-float(sig['invalidation_level']))>0 and provider.now<=deadline):
                counters['MSNR_ENTRY_CONTEXT_CHANGED']+=1
                continue
        rr2=float(sig['runner_rr'])
        if sig.get('obstacle_level'):
            room_rr=sign*(float(sig['tp2_price'])-entry)/risk
            if room_rr<cfg.tp1_min_rr:
                counters['FILL_OBSTACLE_BEFORE_TP1']+=1
                continue
            rr2=min(rr2,room_rr)
        tp1=entry+sign*cfg.tp1_min_rr*risk
        tp2=entry+sign*rr2*risk
        future_end=min(len(m),i+1+MAX_HOLD_BARS)
        reward,outcome,bars=simulate_buffered(direction,entry,sl,tp1,tp2,o[i+1:future_end],h[i+1:future_end],l[i+1:future_end],c[i+1:future_end],spreads[i+1:future_end],cfg.be_spread_buffer_multiplier)
        busy=i+bars
        if identity:
            executed.add(identity)
        records.append({'symbol':row['symbol'],'version':cfg.strategy_version,'time':str(provider.now),
                        'exit_time':str(closes.iloc[i+bars]),'scenario':sig['scenario'],'setup_id':identity,
                        'structure_closed_at':sig.get('structure_closed_at'),'trigger':sig.get('entry_confirmation'),
                        'direction':direction,'entry':entry,'stop':sl,'tp1':tp1,'tp2':tp2,'runner_rr':rr2,
                        'spread':float(spreads[i+1]),'spread_source':spread_source,'risk_atr':risk/sig['atr'],
                        'rr':float(reward),'outcome':outcome,'bars':bars,'freshness':(sig.get('freshness') or {}).get('state')})
    return records,{'clock_bars':len(indices),'counters':dict(counters),'seconds':round(time.monotonic()-started,2),'spread_source':spread_source}

def win_interval(frame):
    if frame.empty:
        return None
    n=len(frame);p=float((frame.rr>0).mean());z=1.95996398454
    center=(p+z*z/(2*n))/(1+z*z/n)
    width=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [round(100*(center-width),3),round(100*(center+width),3)]

def metrics(records):
    frame=pd.DataFrame(records)
    if len(frame):
        frame=frame[frame.outcome!='RIGHT_CENSORED'].sort_values(['exit_time','symbol','time'])
    result=statistics(frame)
    result['win_ci95_wilson']=win_interval(frame)
    result['censored_trades']=sum(r['outcome']=='RIGHT_CENSORED' for r in records)
    return result

def run_symbol(row,out=OUT,verify=False):
    baseline,baseline_cfg,_=baseline_modules(out)
    manifest=read_manifest(out)
    start,end=pd.Timestamp(manifest['audit_start']),pd.Timestamp(manifest['audit_end'])
    target=out/'results'/f'{row["symbol"].replace(" ","_")}.json'
    target.parent.mkdir(exist_ok=True)
    if row.get('error'):
        result={'symbol':row['symbol'],'error':row['error']}
        target.write_text(json.dumps(result,indent=2),encoding='utf-8')
        return result
    frames=load_snapshot(row,out)
    configs=[baseline_cfg(allowed_symbols=()),MalaysianSNRConfig(allowed_symbols=())]
    if verify:
        # Paired identical clocks near both the first and last part of the history.
        checks=[]
        windows=[(start,start+pd.Timedelta(days=7)),(end-pd.Timedelta(days=14),end)]
        if target.exists():
            prior=json.loads(target.read_text())
            episodes=set()
            for variant in prior.get('versions',{}).values():
                for trade in variant['trades'][:1]:
                    day=pd.Timestamp(trade['time']).normalize()
                    episodes.add(day)
            windows=[(day-pd.Timedelta(days=1),day+pd.Timedelta(days=2)) for day in sorted(episodes)] or windows
        for module,cfg in zip((baseline,current),configs):
            for lower,upper in windows:
                reference,_=replay(row,frames,module,cfg,lower,upper,accelerated=False,screen=False)
                original=install_acceleration(module)
                try:
                    fast,_=replay(row,frames,module,cfg,lower,upper)
                finally:
                    restore(module,original)
                if reference!=fast:
                    raise AssertionError(f'Acceleration mismatch for {row["symbol"]} {cfg.strategy_version} {lower}: {reference} != {fast}')
                checks.append({'version':cfg.strategy_version,'start':str(lower),'end':str(upper),'identical_trades':len(fast)})
        proof={'symbol':row['symbol'],'verification':checks}
        (out/f'verification_{row["symbol"].replace(" ","_")}.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
        return proof
    result={'symbol':row['symbol'],'full_two_year_start':row['frames']['M15']['full_two_year_start'],
            'available_start':row['frames']['M15']['start'],'frames':row['frames'],'versions':{}}
    indicator_cache={}
    for module,cfg,label in zip((baseline,current),configs,('baseline','v21')):
        original=install_acceleration(module,indicator_cache)
        try:
            records,details=replay(row,frames,module,cfg,start,end)
        finally:
            restore(module,original)
        result['versions'][label]={'metrics':metrics(records),'execution':details,'trades':records}
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    return {'symbol':row['symbol'],'full_two_year_start':result['full_two_year_start'],**{k:v['metrics'] for k,v in result['versions'].items()}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbol',required=True)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    manifest=read_manifest()
    row=next(r for r in manifest['symbols'] if r['symbol']==args.symbol)
    print(json.dumps(run_symbol(row,verify=args.verify),ensure_ascii=True),flush=True)

if __name__=='__main__':
    main()
