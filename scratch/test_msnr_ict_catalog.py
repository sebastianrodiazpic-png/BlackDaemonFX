import sys
sys.path.insert(0, ".")
from dashboard.realtime_dashboard import RealtimeDashboardService

svc = RealtimeDashboardService(repository=None)
cat = {
    "malaysian_snr_volatility": ["Volatility 10 Index", "Vol over Boom 550", "Vol over Crash 550"],
    "malaysian_snr_forex": ["USDCHF", "USDCHFmicro", "AUDCAD", "AUDCADmicro", "AUDUSD", "AUDUSDmicro", "EURUSD"],
    "malaysian_snr_indices": ["Germany 40", "Wall Street 30"],
    "malaysian_snr_metals": ["XAUUSD", "XAUUSDmicro", "XAUEUR", "XAUEURmicro"],
    "malaysian_snr_pruned": ["XAGUSD", "EURCHF"],
    "ict_metals_xauusd": ["XAUUSD", "XAUUSDmicro", "XAUEUR", "XAUEURmicro"],
    "ict_crypto_btcusd": ["BTCUSD", "BTCUSDmicro"],
}
svc.set_instrument_catalog(cat)
catalog = svc._state["instrument_catalog"]

print("=== ICT Groups ===")
for g in catalog:
    if g["selection_profile"] == "ICT":
        print(f"  {g['label']} ({g['category']}): {g['symbols']}")

print("=== Malaysian SNR Groups ===")
for g in catalog:
    if g["selection_profile"] == "MALAYSIAN_SNR":
        print(f"  {g['label']} ({g['category']}): {g['symbols']}")
