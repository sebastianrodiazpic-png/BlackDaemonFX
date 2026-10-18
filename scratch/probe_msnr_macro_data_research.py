"""Read-only feed depth and structural bias comparisons for blocked traditional assets."""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from marketdata.factory import ExternalMarketDataSettings,build_market_data_provider
from strategy.malaysian_snr.validation import closed_candles
from strategy.malaysian_snr.opportunity_rules import structural_bias

out=Path(sys.argv[1]);now=pd.Timestamp.now(tz='UTC')
connector=MT5Connector();connector.connect();metadata=MT5DataProvider(connector)
provider=build_market_data_provider(metadata,settings=ExternalMarketDataSettings.from_environment('external'))
provider.connect();results=[]
try:
    for symbol in ('Wall Street 30','AUDNZD','USDJPY'):
        item={'symbol':symbol,'at':now.isoformat(),'frames':{}}
        for tf,n in (('H1',80),('M15',60),('D1',40),('H4',80),('H1',160),('D1',80)):
            try:
                raw=provider.get_candles(symbol,tf,n);closed=closed_candles(raw,tf,now)
                reference=closed_candles(metadata.get_candles(symbol,tf,n),tf,now)
                key=tf if n in (80,60,40) and not (tf=='D1' and n==80) else f'{tf}_{n}'
                item['frames'][key]={'requested':n,'primary_closed_rows':len(closed),
                    'mt5_closed_rows':len(reference),'source':raw.attrs.get('market_data_source'),
                    'first_time':str(closed.time.iloc[0]) if len(closed) else None,
                    'last_time':str(closed.time.iloc[-1]) if len(closed) else None,
                    'structural_bias_radius2':structural_bias(closed,2),
                    'mt5_structural_bias_radius2':structural_bias(reference,2)}
                raw.to_pickle(out/f'macro_{symbol.replace(" ","_")}_{key}.pkl')
            except Exception as exc:
                item['frames'][tf]={'error':type(exc).__name__+': '+str(exc)}
        results.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
finally:provider.disconnect()
(out/'macro_data_probes.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
