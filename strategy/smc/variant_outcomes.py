"""Read-only replay of immutable shadow plans on broker bars; never learning labels."""
import json
import hashlib
import math
import os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd


def evaluate(candles, candidate, point, now=None):
    base = {'entry_authorized':False, 'eligible_for_learning':False,
            'price_model':'CAPTURED_MT5_ENTRY_BID_BARS', 'cost_model':'BAR_SPREAD_NO_COMMISSION_OR_SWAP'}
    try:
        plan = candidate['plan']
        planned_entry, stop, target = (float(plan[k]) for k in ('entry_price','stop_loss','take_profit'))
        direction = str(plan['direction']).upper()
        direction = {'LONG':'BUY','SHORT':'SELL'}.get(direction, direction)
        quote = candidate.get('execution_quote') or {}
        if quote.get('spread_status') != 'AVAILABLE' or quote.get('spread_source') != 'MT5_EXECUTION':
            return {**base,'outcome':'MISSING_EXECUTABLE_ENTRY_QUOTE'}
        entry = float(quote['execution_ask'] if direction=='BUY' else quote['execution_bid'])
        base.update(planned_entry=planned_entry, captured_entry=entry, stop=stop, target=target)
        if direction not in {'BUY','SELL'} or not all(math.isfinite(v) for v in (entry,stop,target,point)) or point<=0:
            raise ValueError('invalid plan')
        if not (stop<entry<target if direction=='BUY' else target<entry<stop):
            raise ValueError('invalid barriers')
        observed = pd.to_datetime(candidate['observed_at'], utc=True)
        confirmation = pd.to_datetime(candidate['confirmation_time'], utc=True)+pd.Timedelta(minutes=5)
        quote_time = pd.to_datetime(quote.get('spread_quote_time'), utc=True)
        quote_age = (observed-quote_time).total_seconds()
        if pd.isna(quote_time) or not math.isfinite(quote_age) or quote_age < -60 or quote_age > 180:
            return {**base,'outcome':'MISSING_EXECUTABLE_ENTRY_QUOTE'}
        if pd.isna(observed) or pd.isna(confirmation) or observed<confirmation:
            raise ValueError('unclosed confirmation')
    except (KeyError, TypeError, ValueError):
        return {**base,'outcome':'MISSING_CAUSAL_PLAN'}
    data = candles.copy()
    data['time'] = pd.to_datetime(data['time'], utc=True)
    data = data[(data.time>=observed.floor('5min')) & (data.time+pd.Timedelta(minutes=5)<=pd.Timestamp(now or datetime.now(timezone.utc)))].sort_values('time')
    if data.empty:
        return {**base,'outcome':'PENDING_BARS'}
    expected = observed.floor('5min')
    risk = abs(entry-stop)
    for _, bar in data.iterrows():
        if bar.time != expected:
            return {**base,'outcome':'INCOMPLETE_BROKER_HISTORY'}
        expected += pd.Timedelta(minutes=5)
        try:
            spread = float(bar['spread'])*point
            if not math.isfinite(spread) or spread<0:
                raise ValueError()
            low, high = float(bar.low), float(bar.high)
            if not math.isfinite(low+high) or high<low:
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            return {**base,'outcome':'MISSING_BROKER_COST_OR_PRICES'}
        if direction=='SELL':
            low, high = low+spread, high+spread
        sl = low<=stop if direction=='BUY' else high>=stop
        tp = high>=target if direction=='BUY' else low<=target
        if sl or tp:
            if bar.time<observed:
                return {**base,'outcome':'AMBIGUOUS_ENTRY_BAR'}
            if sl and tp:
                return {**base,'outcome':'AMBIGUOUS_BOTH_BARRIERS'}
            return {**base,'outcome':'SL' if sl else 'TP', 'closed_at':bar.time.isoformat(),
                    'gross_r':-1. if sl else abs(target-entry)/risk}
    return {**base,'outcome':'PENDING_BARRIERS'}


def refresh(worker, broker_provider, root=None, output_root=None):
    from dashboard.smc_trial import ROOT
    root, output_root = Path(root or ROOT), Path(output_root or ROOT / 'replay')
    report = {'worker':worker,'updated_at':datetime.now(timezone.utc).isoformat(),
        'mode':'SHADOW_ONLY','promotion_allowed':False,'variants':{},'candidates':[],
        'limitations':'Planes condicionales: no equivalen a órdenes ejecutables; spread por vela aproximado; sin comisión/swap.'}
    try:
        previous = json.loads((output_root/(str(worker)+'.json')).read_text(encoding='utf-8'))
    except (OSError,ValueError):
        previous = {}
    terminal = {r.get('fingerprint'):r for r in previous.get('candidates',[])
                if r.get('outcome') in {'TP','SL','AMBIGUOUS_BOTH_BARRIERS','AMBIGUOUS_ENTRY_BAR'}}
    seen, cache = set(), {}
    paths = sorted((root/'history').glob(str(worker)+'_*.json'))
    paths.append(root/(str(worker)+'.json'))
    for path in paths:
        if not path.exists():
            continue
        try:
            state = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for identity, setup in state.get('unique_setups',{}).items():
            for variant, candidate in setup.get('first_variant_ready',{}).items():
                key = (identity,variant)
                if key in seen:
                    continue
                seen.add(key)
                symbol = setup['symbol']
                fingerprint = hashlib.sha256(json.dumps([identity,variant,candidate],sort_keys=True,default=str).encode()).hexdigest()
                try:
                    if fingerprint in terminal:
                        outcome = dict(terminal[fingerprint])
                    elif not all((candidate.get('plan') or {}).get(k) is not None for k in ('entry_price','stop_loss','take_profit','direction')):
                        outcome = {'outcome':'MISSING_CAUSAL_PLAN','eligible_for_learning':False}
                    else:
                        if broker_provider is None:
                            raise ValueError('MT5_REFERENCE_UNAVAILABLE')
                        if symbol not in cache:
                            cache[symbol] = (broker_provider.get_candles(symbol,'M5',count=2000), broker_provider.get_symbol_info(symbol)['point'])
                        candles, point = cache[symbol]
                        outcome = evaluate(candles,candidate,point)
                except Exception as exc:
                    outcome = {'outcome':'BROKER_DATA_UNAVAILABLE','reason':str(exc),'eligible_for_learning':False}
                outcome['fingerprint'] = fingerprint
                report['candidates'].append({'setup_id':identity,'symbol':symbol,'variant':variant,**outcome})
                summary=report['variants'].setdefault(variant,{'unique_setups':0,'closed_replays':0,'tp':0,'sl':0,'gross_r_sum':0.,'excluded_or_pending':0})
                summary['unique_setups']+=1
                if outcome['outcome'] in {'TP','SL'}:
                    summary['closed_replays']+=1
                    summary[outcome['outcome'].lower()]+=1
                    summary['gross_r_sum']+=outcome['gross_r']
                else:
                    summary['excluded_or_pending']+=1
    closed = {(r['setup_id'],r['variant']):r for r in report['candidates'] if r['outcome'] in {'TP','SL'}}
    report['paired_comparisons'] = {}
    for variant in report['variants']:
        if variant == 'BASELINE':
            continue
        pairs = [(r,closed[(setup,'BASELINE')]) for (setup,name),r in closed.items()
                 if name==variant and (setup,'BASELINE') in closed]
        report['paired_comparisons'][variant] = {'paired_closed_setups':len(pairs),
            'mean_gross_r_difference':sum(a['gross_r']-b['gross_r'] for a,b in pairs)/len(pairs) if pairs else None,
            'decision':'INSUFFICIENT_VALIDATED_NET_OUTCOMES', 'promotion_allowed':False}
    output_root.mkdir(parents=True,exist_ok=True)
    target=output_root/(str(worker)+'.json')
    temp=output_root/(str(worker)+'.'+str(os.getpid())+'.tmp')
    temp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(target)
    return report

