import sys
sys.path.insert(0, '.')
import json
from datetime import datetime, timezone
from database.repository import TradingRepository
from strategy.malaysian_snr.ai_policy import settings_signature, active_model_status
from strategy.malaysian_snr.runtime_settings import normalize_msnr_settings

repo = TradingRepository(r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3")

# The 25 instruments selected in /instruments for Malaysian SNR
SELECTED_25 = [
    "Jump 25 Index",
    "Jump 50 Index",
    "Jump 10 Index",
    "Step Index 400",
    "Step Index 500",
    "Step Index 200",
    "Step Index",
    "Boom 1000 Index",
    "Crash 1000 Index",
    "Boom 600 Index",
    "Crash 600 Index",
    "Boom 500 Index",
    "Crash 500 Index",
    "Boom 300 Index",
    "Crash 300 Index",
    "BTCUSD",
    "XAUUSD",
    "Wall Street 30",
    "US Tech 100",
    "USDJPY",
    "EURUSD",
    "GBPUSD",
    "GBPJPY",
    "AUDNZD",
    "GBPAUD",
]

# 1. Save instrument selection profile
persisted = repo.save_instrument_selection_profile(SELECTED_25, selection_profile="MALAYSIAN_SNR", source="DEMO")
print(f"Persisted selection profile version {persisted.get('version')} with {len(persisted.get('selected_symbols', []))} symbols")

# 2. Synchronize strategy_runtime_preferences
current = repo.latest_msnr_runtime_settings(source="DEMO")
print(f"Current strategy_runtime_preferences version {current.get('version')}")

# All 60 known symbols in MSNR universe
from app.main import BOT_PROFILES
msnr_spec = BOT_PROFILES["MALAYSIAN_SNR"]
all_universe = set(msnr_spec["symbols"]) | set(msnr_spec["pruned_symbols"])

asset_modes = dict(current.get("asset_modes") or {})
for sym in SELECTED_25:
    asset_modes[sym] = "live"

for sym in all_universe:
    if sym not in SELECTED_25:
        asset_modes[sym] = "off"

updated_settings = repo.save_msnr_runtime_settings(
    source="DEMO",
    asset_modes=asset_modes,
    additional_symbols_mode="off",
    additional_symbols=[],
)

print(f"Updated strategy_runtime_preferences version {updated_settings.get('version')}")
print("Verifying active model compatibility:")
sig = settings_signature(updated_settings)
print(f"New settings_signature: {sig}")
model_st = active_model_status(updated_settings)
print(f"Model status: {model_st}")

# 3. Simulate cycle_symbols
from strategy.malaysian_snr.runtime_engine import cycle_symbols
class MockEngine:
    class malaysian_snr_strategy:
        @staticmethod
        def settings_snapshot():
            return repo.latest_msnr_runtime_settings(source="DEMO")

simulated = cycle_symbols(MockEngine, SELECTED_25)
print(f"\nSimulated cycle_symbols result count: {len(simulated)}")
print(f"Matches SELECTED_25 count exactly: {len(simulated) == len(SELECTED_25)}")
missing = set(SELECTED_25) - set(simulated)
extra = set(simulated) - set(SELECTED_25)
print(f"Missing from cycle: {missing}")
print(f"Extra in cycle: {extra}")
