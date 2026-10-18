import json,os,sqlite3,sys
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol
def family(symbol):
    if is_synthetic_symbol(symbol): return 'synthetics'
    if symbol in ('XAUUSD','XAGUSD'): return 'metals'
    if 'BTC' in symbol or 'ETH' in symbol: return 'crypto'
    if len(symbol)==6 and symbol.isalpha(): return 'forex'
    return 'other'
p=Path(os.environ['LOCALAPPDATA'])/'BlackDaemonFx/trading_bot.sqlite3'
c=sqlite3.connect(f'file:{p.as_posix()}?mode=ro',uri=True)
c.row_factory=sqlite3.Row
c.execute('PRAGMA query_only=ON')
out=[]; groups=defaultdict(list); count=Counter()
for r in c.execute("SELECT * FROM trade_journal WHERE entry_time>='2026-10-05' AND entry_time<'2026-10-11'"):
    m=json.loads(r['details_json'] or '{}').get('metadata') or {}
    if m.get('bot_profile')!='MALAYSIAN_SNR': continue
    count[(r['strategy_version'],str(m.get('strategy_version')),str(m.get('strategy_name')),str(m.get('msnr_scenario') or m.get('scenario')))]+=1
    key=m.get('parent_execution_key') or str(r['execution_key']).rsplit(':',1)[0]
    groups[key].append(r)
    if len(out)<5 and r['strategy_version']=='smc-v1':
        out.append({'time':r['entry_time'],'symbol':r['instrument'],'row_version':r['strategy_version'],
            'meta':{k:m.get(k) for k in ('strategy_version','strategy_name','bot_profile','scenario','msnr_scenario','h1_trend','m15_setup_type','setup_reason','trade_leg')}})
ops=[]
core=set(MalaysianSNRConfig().allowed_symbols)
for key,rs in groups.items():
    ops.append({'day':rs[0]['entry_time'][:10],'symbol':rs[0]['instrument'],'family':family(rs[0]['instrument']),
        'legs':len(rs),'pnl':sum(x['net_pnl'] for x in rs),'closed':all(x['status']=='CLOSED' for x in rs),
        'version':rs[0]['strategy_version'],'allowed_now':rs[0]['instrument'] in core})
daily={}
for day in sorted({x['day'] for x in ops}):
    xs=[x for x in ops if x['day']==day]
    daily[day]={'operations':len(xs),'legs':sum(x['legs'] for x in xs),
        'net_pnl':round(sum(x['pnl'] for x in xs),2),'positive':sum(x['pnl']>0 for x in xs),
        'negative':sum(x['pnl']<0 for x in xs),'fully_closed':sum(x['closed'] for x in xs)}
report={'daily':daily,'versions_and_scenarios':[[list(k),v] for k,v in count.items()],
    'examples':out,'operations':len(ops),'legs':sum(x['legs'] for x in ops),
    'removed_operations':sum(not x['allowed_now'] for x in ops),
    'family_operations':dict(Counter(x['family'] for x in ops)),
    'active_operations_by_family':dict(Counter(x['family'] for x in ops if x['allowed_now'])),
    'removed_symbols':dict(Counter(x['symbol'] for x in ops if not x['allowed_now'])),
    'by_symbol':{symbol:{'operations':len(xs:=[x for x in ops if x['symbol']==symbol]),
         'net_pnl':round(sum(x['pnl'] for x in xs),2),'positive':sum(x['pnl']>0 for x in xs),
         'negative':sum(x['pnl']<0 for x in xs),'allowed_now':symbol in core} for symbol in sorted({x['symbol'] for x in ops})},
    'net_pnl':round(sum(x['pnl'] for x in ops),2)}
c.close()
(ROOT/'storage/analysis/msnr_trade_drop_20261012/episodes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
