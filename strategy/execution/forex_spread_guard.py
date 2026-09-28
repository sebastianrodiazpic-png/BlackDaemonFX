"""Persistent Forex spread baseline and post-rollover stabilization; no orders."""
import json
import math
import os
import statistics
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

_LOCK = threading.RLock()

ROOT = Path(__file__).resolve().parents[2] / 'storage/runtime/forex_spread'

class ForexSpreadGuard:
    def __init__(self, worker, root=None, minimum_samples=20, multiplier=2., max_pips=5., stable_samples=5):
        self.path = Path(root or ROOT) / (str(worker)+'.json')
        self.minimum_samples, self.multiplier = minimum_samples, multiplier
        self.max_pips, self.stable_samples = max_pips, stable_samples
        try:
            self.state = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.state = {'worker':worker,'symbols':{}}

    def observe(self, symbol, quote, now=None):
        with _LOCK:
            return self._observe(symbol, quote, now)

    def _observe(self, symbol, quote, now=None):
        now = now or datetime.now(timezone.utc)
        local = now.astimezone(ZoneInfo('America/New_York'))
        session = (local.date() if local.hour >= 17 else local.date()-timedelta(days=1)).isoformat()
        item = self.state['symbols'].setdefault(symbol, {'samples':[], 'stable_count':0})
        if item.get('session') != session:
            item.update(session=session, stable_count=0, last_stable_at=None)
        previous = item.get('observed_at')
        if previous and (now-datetime.fromisoformat(previous)).total_seconds()>45:
            item['stable_count']=0
        item.update(observed_at=now.isoformat(), quote=dict(quote))
        valid = quote.get('spread_status') == 'AVAILABLE' and quote.get('spread_source') == 'MT5_EXECUTION'
        try:
            stamp = datetime.fromisoformat(str(quote['spread_quote_time']).replace('Z','+00:00'))
            age = (now-stamp).total_seconds()
            valid = valid and 0 <= age <= 30
        except (ValueError, KeyError, TypeError):
            valid = False
        pip = .01 if str(symbol).upper()[3:6] == 'JPY' else .0001
        spread = quote.get('spread')
        valid = valid and isinstance(spread,(float,int)) and math.isfinite(spread) and spread>=0
        samples = [x for x in item['samples'] if x['at'] >= (now-timedelta(days=7)).isoformat()]
        median = statistics.median(x['spread'] for x in samples) if len(samples)>=self.minimum_samples else None
        normal = bool(valid and spread/pip<=self.max_pips and median is not None and spread<=median*self.multiplier)
        # Calls at pre-send do not fabricate additional stabilization observations.
        spaced = previous is None or (now-datetime.fromisoformat(previous)).total_seconds() >= 14
        if not normal:
            item['stable_count']=0
        elif spaced:
            item['stable_count']+=1
        # Exclude the thin-liquidity interval from the baseline, and reject spikes.
        if valid and spaced and not 16<=local.hour<18 and spread/pip<=self.max_pips and (median is None or spread<=median*self.multiplier):
            samples.append({'at':now.isoformat(),'spread':spread})
        item['samples']=samples[-720:]
        item.update(baseline=median, samples_count=len(samples), spread_pips=spread/pip if valid else None,
            normal=normal, ready=normal and item['stable_count']>=self.stable_samples,
            reason='QUOTE_UNAVAILABLE' if not valid else 'BASELINE_WARMUP' if median is None else 'SPREAD_ABOVE_LIMIT' if not normal else 'WAITING_STABLE_SPREAD' if item['stable_count']<self.stable_samples else 'SPREAD_NORMALIZED')
        self.state['updated_at']=now.isoformat()
        self.state['limits']={'max_pips':self.max_pips,'max_multiple':self.multiplier,'minimum_samples':self.minimum_samples,'stable_samples':self.stable_samples}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
        health = {'worker':self.state.get('worker'), 'at':now.isoformat(), 'status':'OK'}
        try:
            temp.write_text(json.dumps(self.state,ensure_ascii=False),encoding='utf-8')
            for attempt in range(3):
                try:
                    temp.replace(self.path)
                    break
                except PermissionError:
                    if attempt == 2:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        except OSError as exc:
            health.update(status='DEGRADED', error=str(exc))
            raise  # Preserve the existing failure behavior; never bypass the spread gate.
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                health_path=self.path.with_suffix('.health.json')
                health_tmp=health_path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
                health_tmp.write_text(json.dumps(health),encoding='utf-8')
                health_tmp.replace(health_path)
            except OSError:
                pass  # The original exception is still emitted by the worker audit.

        return dict(item)

    def check(self, symbol, quote, direction, stop, max_risk_ratio=.10, now=None):
        item=self.observe(symbol,quote,now)
        entry=quote.get('execution_ask' if direction=='BUY' else 'execution_bid')
        distance=(entry-stop if direction=='BUY' else stop-entry) if isinstance(entry,(float,int)) else 0
        ratio=quote['spread']/distance if distance>0 and quote.get('spread') is not None else None
        allowed=bool(item['ready'] and ratio is not None and ratio<=max_risk_ratio)
        return {'allowed':allowed,'reason':item['reason'] if not item['ready'] else 'SPREAD_RISK_RATIO_EXCEEDED' if not allowed else 'SPREAD_ACCEPTED',
            'spread_risk_ratio':ratio,'max_risk_ratio':max_risk_ratio,'baseline':item.get('baseline'),
            'spread_pips':item.get('spread_pips'),'stable_count':item['stable_count'],'quote':quote}


def snapshot(root=None):
    result=[]
    for path in Path(root or ROOT).glob('*.json'):
        if path.name.endswith('.health.json'):
            continue
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            try:
                health=json.loads(path.with_suffix('.health.json').read_text(encoding='utf-8'))
            except (OSError,ValueError):
                health={'status':'UNKNOWN'}
            for symbol, item in data.get('symbols',{}).items():
                result.append({'worker':data.get('worker'),'symbol':symbol,'persistence':health,**{k:v for k,v in item.items() if k!='samples'}})
        except (OSError,ValueError):
            continue
    return result
