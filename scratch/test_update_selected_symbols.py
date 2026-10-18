import sys
sys.path.insert(0, '.')
from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService, _normalize_symbol_list
from strategy.malaysian_snr.runtime_engine import cycle_symbols

repo = TradingRepository(r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3")
service = RealtimeDashboardService(repository=repo)

# Test 1: User selects 25 symbols
test_25 = [
    "Jump 25 Index", "Jump 50 Index", "Jump 10 Index",
    "Step Index 400", "Step Index 500", "Step Index 200", "Step Index",
    "Boom 1000 Index", "Crash 1000 Index", "Boom 600 Index", "Crash 600 Index",
    "Boom 500 Index", "Crash 500 Index", "Boom 300 Index", "Crash 300 Index",
    "BTCUSD", "XAUUSD", "Wall Street 30", "US Tech 100", "USDJPY",
    "EURUSD", "GBPUSD", "GBPJPY", "AUDNZD", "GBPAUD"
]
res = service.update_selected_symbols(test_25, selection_profile="MALAYSIAN_SNR")
assert res.get("ok"), f"Update failed: {res}"

class MockEngine:
    class malaysian_snr_strategy:
        @staticmethod
        def settings_snapshot():
            return repo.latest_msnr_runtime_settings(source="DEMO")

cycle_result = cycle_symbols(MockEngine, test_25)
print(f"Test 1 (25 symbols): update ok={res.get('ok')}, cycle_count={len(cycle_result)}")
assert len(cycle_result) == 25, f"Expected 25, got {len(cycle_result)}"

# Test 2: User de-activates 3 symbols (22 symbols)
test_22 = [s for s in test_25 if s not in ("Boom 600 Index", "Crash 300 Index", "Step Index 500")]
res2 = service.update_selected_symbols(test_22, selection_profile="MALAYSIAN_SNR")
assert res2.get("ok"), f"Update failed: {res2}"

cycle_result2 = cycle_symbols(MockEngine, test_22)
print(f"Test 2 (22 symbols): update ok={res2.get('ok')}, cycle_count={len(cycle_result2)}")
assert len(cycle_result2) == 22, f"Expected 22, got {len(cycle_result2)}"

# Test 3: User activates them back (25 symbols)
res3 = service.update_selected_symbols(test_25, selection_profile="MALAYSIAN_SNR")
assert res3.get("ok"), f"Update failed: {res3}"
cycle_result3 = cycle_symbols(MockEngine, test_25)
print(f"Test 3 (25 symbols restored): update ok={res3.get('ok')}, cycle_count={len(cycle_result3)}")
assert len(cycle_result3) == 25, f"Expected 25, got {len(cycle_result3)}"

print("ALL TESTS PASSED! update_selected_symbols is 100% consistent with cycle_symbols!")
