import sys
sys.path.insert(0, ".")

from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from marketdata.factory import build_market_data_provider
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.config import MalaysianSNRConfig
import json

connector = MT5Connector()
connected = connector.connect()
print("MT5 Connected:", connected)
if not connected:
    sys.exit(1)

metadata = MT5DataProvider(connector)
provider = build_market_data_provider(metadata)
provider.connect()

strat = MalaysianSNRStrategy(data_provider=provider, config=MalaysianSNRConfig())

symbols_23 = [
    "Step Index 400", "XAGUSD", "AUDNZD", "Crash 1000 Index", "Jump 25 Index",
    "GBPJPY", "USDJPY", "GBPUSD", "Boom 300 Index", "Volatility 250 (1s) Index",
    "Step Index", "Jump 10 Index", "GBPAUD", "Wall Street 30", "EURUSD",
    "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 1000 Index",
    "Step Index 200", "EURCHF", "EURGBP", "XAUUSD", "Crash 600 Index",
]

print(f"\n=== EVALUACION EN VIVO CON COTIZACIONES ACTUALES ({len(symbols_23)} ACTIVOS) ===")
for s in symbols_23:
    res = strat.analyze_symbol(s)
    valid = res.get("valid")
    action = res.get("action")
    reason = res.get("reason")
    adx = res.get("momentum_adx")
    scen = res.get("scenario")
    print(f"[{s:26s}] Valid: {valid!s:5s} | Act: {action:20s} | Reason: {reason}")
    if valid:
        print(f"   >>> SIGNAL: {res.get('signal')}")

provider.disconnect()
connector.disconnect()
