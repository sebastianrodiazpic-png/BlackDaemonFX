"""Offline first-confirmation timeline; static comparisons are not performance tests."""
import json
import sys
from pathlib import Path
from dataclasses import replace
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy

out=Path(sys.argv[1]);summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
settings={**summary['settings'],'version':summary['preference']['id']}
class Frozen:
    def __init__(self,symbol):
        self.frames={tf:pd.read_pickle(out/f'{symbol.replace(" ","_")}_{tf}.pkl') for tf in ('H1','M15','D1')}
    def get_candles(self,symbol,timeframe,count=100):return self.frames[timeframe].tail(count)
    def get_symbol_info(self,symbol):return {'trade_tick_size':0.}
    def get_current_tick(self,symbol):return {'bid':0.,'ask':0.}
results=[]
for symbol in ('Boom 1000 Index','Jump 25 Index'):
    provider=Frozen(symbol)
    for distance,body in ((.5,.45),(.7,.45),(.5,.35)):
        cfg=MalaysianSNRConfig(tp2_runner_rr=4.,max_entry_distance_atr=distance)
        alternative={**settings,'fractal_min_body_ratio':body}
        strategy=MalaysianSNRStrategy(provider,cfg,lambda:alternative)
        records=[]
        for at in pd.date_range('2026-10-12T00:15Z','2026-10-12T01:15Z',freq='15min'):
            result=strategy.analyze_symbol(symbol,at)
            records.append({'at':at.isoformat(),'valid':result.get('valid'),'reason':result.get('reason'),
                'scenario':(result.get('signal') or {}).get('scenario') or result.get('scenario'),
                'level':(result.get('diagnostics') or {}).get('level'),
                'retest':(result.get('diagnostics') or {}).get('retest')})
        item={'symbol':symbol,'qm_av_max_distance_atr':distance,'fractal_body':body,'timeline':records}
        results.append(item)
        print(json.dumps(item,ensure_ascii=False))
(out/'frozen_timelines.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')

import MetaTrader5 as mt5
if not mt5.initialize():raise RuntimeError('No se pudo consultar el terminal')
try:
    terminal=mt5.terminal_info();account=mt5.account_info()
    permission={'terminal_connected':bool(terminal and terminal.connected),
        'terminal_trade_allowed':bool(terminal and terminal.trade_allowed),
        'account_trade_allowed':bool(account and account.trade_allowed),
        'account_expert_allowed':bool(account and account.trade_expert),
        'is_demo':bool(account and account.trade_mode==mt5.ACCOUNT_TRADE_MODE_DEMO)}
    print(json.dumps({'broker_permissions':permission}))
    (out/'broker_permissions.json').write_text(json.dumps(permission,indent=2),encoding='utf-8')
finally:mt5.shutdown()
