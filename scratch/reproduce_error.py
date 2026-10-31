import os
import sys
sys.path.insert(0, '.')
import traceback

os.environ["DAEMON_MARKET_DATA_MODE"] = "external"
os.environ["DAEMON_MARKET_DATA_PROVIDER"] = "deriv"

from brokers.mt5_data import MT5DataProvider
from marketdata.factory import build_market_data_provider
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

meta_provider = MT5DataProvider()
print("Connecting MT5...")
meta_provider.connect()
print("MT5 Connected:", meta_provider.is_connected())

provider = build_market_data_provider(meta_provider)
print("Provider:", type(provider))

config = LiveTradingConfig(bot_profile="VOLATILITY_1", execution_enabled=False)
engine = LiveTradingEngine(provider=provider, config=config)

symbol = "High Frequency Vol 100 Index"
print(f"Calling _process_symbol_impl for {symbol}...")
try:
    res = engine._process_symbol_impl(symbol)
    print("Result:", res)
except Exception as e:
    print("Caught Exception:", type(e), e)
    traceback.print_exc()
