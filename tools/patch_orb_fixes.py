import os
import pathlib
import shutil

# 1. Patch new_york_orb.py
orb_path = pathlib.Path("strategy/orb/new_york_orb.py")
orb_content = orb_path.read_text(encoding="utf-8")

if '    if name in {"btcusd"' in orb_content:
    idx = orb_content.find('    if name in {"btcusd"')
    end_idx = orb_content.find('    if name in {"gbpusd"', idx)
    orb_content = orb_content[:idx] + '    if name == "btcusd":\n        return "BTCUSD"\n\n    if name == "usdcad":\n        return "USDCAD"\n\n' + orb_content[end_idx:]
    orb_path.write_text(orb_content, encoding="utf-8")
    print("Patched new_york_orb.py successfully")
else:
    print("new_york_orb.py already updated or pattern not found")

# 2. Patch realtime_dashboard.py
dash_path = pathlib.Path("dashboard/realtime_dashboard.py")
dash_content = dash_path.read_text(encoding="utf-8")

old_orb_defaults = """    "ORB": [
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
        "BTCUSD",
        "BTCUSDmicro",
        "USDCAD",
        "USDCADmicro",
        "GBPUSD",
        "GBPUSDmicro",
        "AUDUSD",
        "AUDUSDmicro",
        "XAGUSD",
        "XAGUSDmicro",
        "microXAGUSD",
        "US Oil",
        "USDCHF",
        "USDCHFmicro",
    ],"""

new_orb_defaults = """    "ORB": [
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
        "BTCUSD",
        "USDCAD",
    ],"""

if old_orb_defaults in dash_content:
    dash_content = dash_content.replace(old_orb_defaults, new_orb_defaults, 1)
    print("Replaced DEFAULT_PRIORITIZED_SYMBOLS['ORB']")

old_pruned_start = """ORB_PRUNED_INFO = {
    # Poda cuantitativa demostrada en replay multianual ORB (activos con WR <= 47% o R/op negativo)
    "Wall Street 30": "PODA PREVENTIVA: WR = 28.57% (-7.99 R en replay), sin edge en campana de apertura 09:30 NY.",
    "US30": "PODA PREVENTIVA: WR = 28.57% (-7.99 R en replay), sin edge en apertura cash NY.",
    "UK Brent Oil": "PODA PREVENTIVA: WR = 40.64% (-39.63 R en replay), falsos quiebres continuos sin recuperación.",
    "NZDUSD": "PODA PREVENTIVA: WR = 42.27% (-24.78 R en replay), recorrido intradía insuficiente en sesión NY.",
    "NZDUSDmicro": "PODA PREVENTIVA: WR = 42.27% (-24.78 R en replay).",
    "EURUSD": "PODA PREVENTIVA: WR = 47.14% (-17.92 R en replay), sesión NY en consolidación post-Londres; operado en ICT.",
    "EURUSDmicro": "PODA PREVENTIVA: WR = 47.14% (-17.92 R en replay).",
    "USDJPY": "PODA PREVENTIVA: Asimetría negativa (-7.09 R), stops mayores a los recorridos alcanzados.",
    "USDJPYmicro": "PODA PREVENTIVA: Asimetría negativa (-7.09 R).",
    "US SP 500": "PODA PREVENTIVA: WR = 44.12% (-7.48 R en replay), falsos rompimientos en campana 09:30 NY.",
    "US500": "PODA PREVENTIVA: WR = 44.12% (-7.48 R en replay).",
    "US Tech 100": "PODA PREVENTIVA: WR = 37.50% (-3.27 R en replay) en M5; operado con éxito en ICT Sabri Malle (75.0% WR).",
    "NAS100": "PODA PREVENTIVA: WR = 37.50% (-3.27 R en replay) en M5; operado en ICT.",
    "ETHUSD": "PODA PREVENTIVA: WR = 46.67% (-2.12 R en replay), falta de volumen relativo frente a BTCUSD.",
    "US Small Cap 2000": "PODA PREVENTIVA: WR = 16.67% (-3.65 R en replay), liquidez deficiente en apertura M5.",
    "US Mid Cap 400": "PODA PREVENTIVA: Liquidez deficiente en apertura cash M5.",
}"""

new_pruned_start = """ORB_PRUNED_INFO = {
    # Poda cuantitativa de Fase 1 y auditoría multianual ORB
    "Wall Street 30": "PODA PREVENTIVA: WR = 28.57% (-7.99 R en replay), sin edge en campana de apertura 09:30 NY.",
    "US30": "PODA PREVENTIVA: WR = 28.57% (-7.99 R en replay), sin edge en apertura cash NY.",
    "XAGUSD": "PODA PREVENTIVA (Fase 1): WR clásico = 45.45% (-3.03 R); requiere modo HTF_SWEEP condicional para operar (WR 81.82%).",
    "microXAGUSD": "PODA PREVENTIVA (Fase 1): Variante micro de XAGUSD.",
    "US Oil": "PODA PREVENTIVA (Fase 1): WR breakout clásico = 39.4% (-17.0 R); requiere filtro direccional Solo BUY + HTF (WR 76.47%).",
    "UK Brent Oil": "PODA PREVENTIVA: WR = 40.64% (-39.63 R en replay), falsos quiebres continuos sin recuperación.",
    "NZDUSD": "PODA PREVENTIVA: WR = 42.27% (-24.78 R en replay), recorrido intradía insuficiente en sesión NY.",
    "NZDUSDmicro": "PODA PREVENTIVA: WR = 42.27% (-24.78 R en replay).",
    "EURUSD": "PODA PREVENTIVA: WR = 47.14% (-17.92 R en replay), sesión NY en consolidación post-Londres; operado en ICT.",
    "EURUSDmicro": "PODA PREVENTIVA: WR = 47.14% (-17.92 R en replay).",
    "USDJPY": "PODA PREVENTIVA: Asimetría negativa (-7.09 R), stops mayores a los recorridos alcanzados.",
    "USDJPYmicro": "PODA PREVENTIVA: Asimetría negativa (-7.09 R).",
    "US SP 500": "PODA PREVENTIVA: WR = 44.12% (-7.48 R en replay), falsos rompimientos en campana 09:30 NY.",
    "US500": "PODA PREVENTIVA: WR = 44.12% (-7.48 R en replay).",
    "US Tech 100": "PODA PREVENTIVA: WR = 37.50% (-3.27 R en replay) en M5; operado con éxito en ICT Sabri Malle (75.0% WR).",
    "NAS100": "PODA PREVENTIVA: WR = 37.50% (-3.27 R en replay) en M5; operado en ICT.",
    "ETHUSD": "PODA PREVENTIVA: WR = 46.67% (-2.12 R en replay), falta de volumen relativo frente a BTCUSD.",
    "US Small Cap 2000": "PODA PREVENTIVA: WR = 16.67% (-3.65 R en replay), liquidez deficiente en apertura M5.",
    "US Mid Cap 400": "PODA PREVENTIVA: Liquidez deficiente en apertura cash M5.",
}"""

if old_pruned_start in dash_content:
    dash_content = dash_content.replace(old_pruned_start, new_pruned_start, 1)
    print("Replaced ORB_PRUNED_INFO")

tmp_path = pathlib.Path("dashboard/realtime_dashboard.py.tmp")
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(dash_content)

os.replace(tmp_path, dash_path)
print("Successfully replaced realtime_dashboard.py via temp file")
