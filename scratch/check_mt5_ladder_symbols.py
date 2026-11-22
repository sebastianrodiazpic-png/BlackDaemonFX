"""
Verificación de símbolos de Deriv MT5 para Volatility, Ladder y VolSwitch
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from config.instruments import InstrumentManager

connector = MT5Connector()
provider = MT5DataProvider(connector)

connected = provider.connect()
print(f"MT5 connected: {connected}")

if connected:
    manager = InstrumentManager(provider.connector)
    all_syms = manager.get_active_symbols()
    print(f"Total active symbols in MT5: {len(all_syms)}")
    
    vol_syms = manager.get_active_symbols(categories=["volatility"])
    print(f"Total symbols in 'volatility' category: {len(vol_syms)}")
    
    matches = [s for s in all_syms if any(k in s.lower() for k in ("ladder", "volswitch", "switch", "down", "up"))]
    print(f"Matches for ladder/volswitch in all symbols ({len(matches)}):")
    for m in matches:
        info = provider.get_symbol_info(m)
        path = getattr(info, "path", None)
        print(f"  - '{m}' | path={path}")
    
    # Comprobar específicamente los 5 targets:
    targets = [
        "Ladder Volatility Down Index",
        "Ladder Volatility Up Index",
        "Ladder Volatility Up",
        "VolSwitch Low Vol Index",
        "VolSwitch Medium Vol Index",
    ]
    for t in targets:
        info = provider.get_symbol_info(t)
        print(f"Target '{t}': exists={info is not None}")
        if info:
            print(f"   path: {getattr(info, 'path', '')}")

    provider.disconnect()
else:
    print("Could not connect to MT5.")
