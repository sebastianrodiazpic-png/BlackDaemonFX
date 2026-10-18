"""Read-only broker and primary-feed verification; never construct an executor."""
import sys
import json
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from marketdata.factory import build_market_data_provider
from strategy.malaysian_snr.history import useful_history

connector=MT5Connector()
if not connector.connect():
    raise SystemExit('MT5_UNAVAILABLE')
metadata=MT5DataProvider(connector)
provider=build_market_data_provider(metadata)
report=[]
try:
    provider.connect()
    now=pd.Timestamp.now(tz='UTC')
    for symbol in ('Wall Street 30','AUDNZD','USDJPY'):
        for timeframe,count,minimum in [('H1',80,28),('D1',40,30),('M5',180,20)]:
            frame,diagnostic=useful_history(provider,symbol,timeframe,count,minimum,now,limit=320)
            row={'symbol':symbol,'rows':len(frame),**diagnostic}
            report.append(row)
            print(json.dumps(row,ensure_ascii=False),flush=True)
finally:
    provider.disconnect()
Path('storage/analysis/msnr_v27_live_history.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
