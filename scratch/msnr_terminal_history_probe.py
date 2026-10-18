from pathlib import Path
from datetime import datetime, timezone
import json
import MetaTrader5 as mt5
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'storage/analysis/msnr_v21_two_years_20261011'
OUT.mkdir(parents=True, exist_ok=True)
if not mt5.initialize():
    raise SystemExit(f'MT5 read-only initialization failed: {mt5.last_error()}')
symbols = mt5.symbols_get() or ()
(OUT / 'terminal_catalog.json').write_text(json.dumps([{'name':s.name,'visible':s.visible,'trade_mode':s.trade_mode,'path':s.path,'point':s.point,'spread':s.spread} for s in symbols],indent=2), encoding='utf-8')
start = datetime(2024, 8, 15, tzinfo=timezone.utc)
end = datetime(2024, 10, 11, tzinfo=timezone.utc)
for name in ('Boom 1000 Index', 'EURUSD', 'Step Index 400', 'Volatility 90 Index'):
    for tf, const in (('H1',mt5.TIMEFRAME_H1), ('M15',mt5.TIMEFRAME_M15), ('D1',mt5.TIMEFRAME_D1)):
        rates = mt5.copy_rates_range(name, const, start, end)
        frame = pd.DataFrame(rates) if rates is not None else pd.DataFrame()
        if len(frame):
            frame['time'] = pd.to_datetime(frame.time,unit='s',utc=True)
        print(json.dumps({'symbol':name, 'tf':tf,'rows':len(frame),'start':str(frame.time.min()) if len(frame) else None,'error':mt5.last_error()}),flush=True)
print(json.dumps({'catalog_count':len(symbols), 'visible_count':sum(s.visible for s in symbols)}),flush=True)
mt5.shutdown()
