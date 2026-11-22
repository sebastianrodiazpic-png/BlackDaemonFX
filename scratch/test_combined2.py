import os
os.environ["DISABLE_MT5_LIVE"] = "1"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.operator_chatbot import (
    MASTER_PRICE_PROFILES,
    resolve_price_profile_and_bounds,
    validate_and_sanitize_chart_data,
)

MASTER_PRICE_PROFILES["Germany 40"] = (25990.0, 35.0, 1, (21000.0, 32000.0))

print("Profile:", resolve_price_profile_and_bounds("Germany 40"))

mock_pos = {
    "instrument": "Germany 40",
    "direction": "SELL",
    "entry_price": 25992.30,
    "stop_loss": 26084.33,
    "take_profit": 25900.27,
}

# Test sanitize with 25992.30
raw_payload = {
    "symbol": "Germany 40",
    "direction": "SELL",
    "timeframe": "M5",
    "digits": 1,
    "current_price": 25992.30,
    "atr": 35.0,
    "candles": [{"open": 25990.0, "high": 26010.0, "low": 25980.0, "close": 25992.30}],
}
val = validate_and_sanitize_chart_data("Germany 40", raw_payload)
print("Sanitized cur price:", val["current_price"])
assert val["current_price"] == 25992.30
print("SUCCESS: 25992.30 is preserved!")
