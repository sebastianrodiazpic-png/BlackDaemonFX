import sys
sys.path.insert(0, '.')
from unittest.mock import MagicMock
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from database.repository import TradingRepository

repo = TradingRepository(db_path='storage/trading_bot.db')
config = LiveTradingConfig(bot_profile="ORB")
dummy_provider = MagicMock()
dummy_provider.resolve_symbol.side_effect = lambda s: s
engine = LiveTradingEngine(provider=dummy_provider, repository=repo, config=config)

sel_profile = engine._selection_profile_for_bot("ORB")
print("Selection profile for ORB:", sel_profile)

base_symbols = ['XAUUSD', 'BTCUSD', 'USDCAD', 'GBPUSD', 'AUDUSD']
print("From selection:", engine._selected_base_cycle_symbols_from_selection(base_symbols))
res = engine._selected_cycle_symbols(base_symbols)
print("Result of _selected_cycle_symbols:", res)
