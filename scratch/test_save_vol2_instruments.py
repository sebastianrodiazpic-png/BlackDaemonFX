"""
Simulación de guardado de instrumentos para SYNTHETICS incluyendo Volatility 2
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.realtime_dashboard import RealtimeDashboardService, _catalog_symbols_by_profile
from database.repository import TradingRepository

repo = TradingRepository()
service = RealtimeDashboardService(repository=repo)

# Cargamos el estado actual si existe
state = service.snapshot()
catalog = state.get("instrument_catalog") or []
print(f"Total grupos en catálogo: {len(catalog)}")
allowed_by_profile = _catalog_symbols_by_profile(catalog)
allowed_synths = allowed_by_profile.get("SYNTHETICS", [])
print(f"Símbolos permitidos en SYNTHETICS ({len(allowed_synths)}):")
for s in allowed_synths:
    if "ladder" in s.lower() or "volswitch" in s.lower():
        print(f"  - {s}")

vol2_targets = [
    "Ladder Volatility Down Index",
    "Ladder Volatility Up Index",
    "Ladder Volatility Up",
    "VolSwitch Low Vol Index",
    "VolSwitch Medium Vol Index",
]

for t in vol2_targets:
    print(f"Target '{t}' in allowed_synths: {t in allowed_synths}")

# Probemos llamar a update_selected_symbols con los símbolos actuales más los de vol2
current_sel = state.get("selection_profiles", {}).get("SYNTHETICS", [])
new_sel = list(set(current_sel + vol2_targets))

print(f"\nIntentando update_selected_symbols(new_sel, selection_profile='SYNTHETICS', allow_selective=False)...")
res = service.update_selected_symbols(new_sel, selection_profile="SYNTHETICS", allow_selective=False)
print("Resultado:")
print(res)

print(f"\nIntentando con allow_selective=True...")
res2 = service.update_selected_symbols(new_sel, selection_profile="SYNTHETICS", allow_selective=True)
print("Resultado 2:")
print(res2)
