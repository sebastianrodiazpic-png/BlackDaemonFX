import sys
sys.path.insert(0, '.')
import traceback
from marketdata.factory import get_data_provider
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

provider = get_data_provider()
print("Provider type:", type(provider))
print("Connecting provider...")
provider.connect()
print("Connected:", provider.is_connected())

config = LiveTradingConfig(bot_profile="VOLATILITY_1")
engine = LiveTradingEngine(provider=provider, config=config)

symbol = "Volatility 10 Index"
print(f"Testing process_symbol on {symbol}...")
try:
    res = engine.process_symbol(symbol)
    print("Result action:", (res or {}).get("action"), "reason:", (res or {}).get("reason"))
except Exception as e:
    print("Caught exception:")
    traceback.print_exc()
