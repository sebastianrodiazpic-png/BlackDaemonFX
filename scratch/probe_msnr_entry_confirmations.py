"""Frozen read-only Deriv/MT5 market snapshot; diagnostic comparisons, no orders."""
import json
import sys
from dataclasses import replace
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from marketdata.factory import ExternalMarketDataSettings, build_market_data_provider
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy, compute_atr
from strategy.malaysian_snr.validation import closed_candles, timeframe_delta

out=Path(sys.argv[1])
summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
now=pd.Timestamp(summary['generated_utc'])
settings={**summary['settings'],'version':summary['preference']['id']}
symbols=['Boom 1000 Index','Step Index 200','Volatility 90 Index','Jump 25 Index','Jump 10 Index','Step Index 400']
connector=MT5Connector();connector.connect()
metadata=MT5DataProvider(connector)
provider=build_market_data_provider(metadata,settings=ExternalMarketDataSettings.from_environment('external'))
provider.connect()
results=[]
class Frozen:
    def __init__(self,frames):self.frames=frames
    def get_candles(self,symbol,timeframe,count=100):return self.frames[timeframe].tail(count)
    def get_symbol_info(self,symbol):return {'trade_tick_size':0.}
    def get_current_tick(self,symbol):return {'bid':0.,'ask':0.}
try:
    for symbol in symbols:
        frames={};sources={}
        for tf,count in [('H1',80),('M15',60),('D1',40)]:
            frames[tf]=provider.get_candles(symbol,tf,count)
            sources[tf]=dict(frames[tf].attrs)
            frames[tf].to_pickle(out/f'{symbol.replace(" ","_")}_{tf}.pkl')
        cfg=MalaysianSNRConfig(tp2_runner_rr=4.)
        strategy=MalaysianSNRStrategy(Frozen(frames),cfg,lambda:settings)
        baseline=strategy.analyze_symbol(symbol,now)
        diag=baseline.get('diagnostics') or {}
        comparisons={}
        # Diagnostic only: never change persisted settings, send orders, or infer WinRate.
        for minimum in [.40,.35]:
            alternate={**settings,'fractal_min_body_ratio':minimum}
            result=MalaysianSNRStrategy(Frozen(frames),cfg,lambda:alternate).analyze_symbol(symbol,now)
            comparisons[f'body_{minimum}']={'valid':result.get('valid'),'reason':result.get('reason'),
                'scenario':(result.get('signal') or {}).get('scenario') or result.get('scenario')}
        level=diag.get('level');original=diag.get('structure_closed_at')
        bars=[]
        if level is not None and original:
            closed=closed_candles(frames['M15'],'M15',now)
            closed=closed[closed.time>=pd.Timestamp(original)]
            h1=closed_candles(frames['H1'],'H1',now)
            anchor=h1[h1.time+pd.Timedelta(hours=1)<=pd.Timestamp(original)]
            atr=float(compute_atr(anchor).iloc[-1])
            sign=1 if baseline.get('direction')=='BUY' else -1
            for bar in closed.itertuples():
                span=float(bar.high-bar.low)
                bars.append({'closed_at':(bar.time+pd.Timedelta(minutes=15)).isoformat(),
                    'open':bar.open,'high':bar.high,'low':bar.low,'close':bar.close,
                    'within_zone':bool(bar.low<=level+.35*atr and bar.high>=level-.35*atr),
                    'directional_body_ratio':sign*float(bar.close-bar.open)/span if span>0 else 0.,
                    'distance_atr':sign*(bar.close-level)/atr,
                    'penetration_atr':max(0.,-sign*((bar.low if sign==1 else bar.high)-level)/atr)})
        item={'symbol':symbol,'evaluated_at':now.isoformat(),'source':sources,
              'valid':baseline.get('valid'),'reason':baseline.get('reason'),'scenario':baseline.get('scenario'),
              'direction':baseline.get('direction'),'diagnostics':diag,'m15_retest_bars':bars,
              'counterfactual_body_minima':comparisons}
        results.append(item)
        print(json.dumps({k:v for k,v in item.items() if k!='source'},ensure_ascii=False,default=str),flush=True)
finally:
    provider.disconnect()
(out/'entry_probes.json').write_text(json.dumps(results,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
