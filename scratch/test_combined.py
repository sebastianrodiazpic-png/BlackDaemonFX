import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.operator_chatbot import MASTER_PRICE_PROFILES, build_chart_data_for_symbol

MASTER_PRICE_PROFILES["Germany 40"] = (25990.0, 35.0, 1, (21000.0, 32000.0))

mock_pos = {
    "instrument": "Germany 40",
    "direction": "SELL",
    "entry_price": 25992.30,
    "stop_loss": 26084.33,
    "take_profit": 25900.27,
}

cd = build_chart_data_for_symbol("Germany 40", "SELL", active_position=mock_pos)
print("Symbol:", cd["symbol"])
print("Direction:", cd["direction"])
print("Current price:", cd["current_price"])
print("Entry price:", cd["entry_price"])
print("Stop Loss:", cd["stop_loss"])
print("Take Profit 1:", cd["take_profit_1"])
print("Last candle close:", cd["candles"][-1]["close"])
