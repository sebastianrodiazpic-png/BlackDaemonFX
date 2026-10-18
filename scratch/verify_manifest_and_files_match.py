"""Verificación de coincidencia exacta entre confirmation_history_manifest.json
y los archivos pickle M5 reales en disco para los 16 activos huérfanos.
Ejecución en modo de solo lectura sobre datasets locales.
"""

import sys
from pathlib import Path
import json
import hashlib
import pickle
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_manifest():
    manifest_p = PROJECT_ROOT / "storage" / "analysis" / "msnr_v27_m5_reference_20261012" / "confirmation_history_manifest.json"
    with open(manifest_p, encoding='utf-8') as f:
        manifest = json.load(f)
        
    hist_dir = PROJECT_ROOT / "storage" / "analysis" / "msnr_v27_m5_reference_20261012" / "history"
    
    missing_16 = [
        'AUDNZD', 'Boom 300 Index', 'Boom 600 Index', 'Crash 300 Index', 'Crash 600 Index',
        'EURCHF', 'EURGBP', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'Jump 10 Index',
        'Step Index 200', 'Step Index 400', 'Volatility 250 (1s) Index',
        'Volatility 50 (1s) Index', 'Volatility 90 Index'
    ]
    
    symbols_map = {s['symbol']: s for s in manifest.get('symbols', [])}
    
    print("=" * 115)
    print("VERIFICACIÓN DE CONCORDANCIA MANIFIESTO VS. ARCHIVOS FÍSICOS M5 EN DISCO (16 ACTIVOS)")
    print("=" * 115)
    print(f"{'Activo':25s} | {'Filas Manif':11s} | {'Filas Pkl':10s} | {'Hash SHA256 Match':18s} | {'Costos / Tick Size':20s} | {'Estado':12s}")
    print("-" * 115)
    
    for sym in missing_16:
        s_data = symbols_map.get(sym)
        if not s_data:
            print(f"{sym:25s} | {'NO EN MANIFIESTO':65s}")
            continue
            
        m5_info = s_data.get('frames', {}).get('M5', {})
        manif_rows = m5_info.get('rows', 0)
        manif_sha = m5_info.get('sha256', '')
        manif_file = m5_info.get('file', '')
        
        file_path = PROJECT_ROOT / manif_file
        
        if not file_path.exists():
            print(f"{sym:25s} | {manif_rows:11d} | {'NO EXISTE':10s} | {'FALTA':18s} | {'-':20s} | {'ERROR':12s}")
            continue
            
        disk_sha = compute_sha256(file_path)
        sha_match = (disk_sha.lower() == manif_sha.lower())
        
        with open(file_path, 'rb') as f:
            df = pickle.load(f)
        disk_rows = len(df)
        rows_match = (manif_rows == disk_rows)
        
        point = s_data.get('point', 'N/A')
        tick_size = s_data.get('tick_size', 'N/A')
        fallback_spread = s_data.get('fallback_spread', 'N/A')
        cost_str = f"pt={point}, sp={fallback_spread}"
        
        status = "CONFORME" if (sha_match and rows_match) else "DISCREPANCIA"
        print(f"{sym:25s} | {manif_rows:11d} | {disk_rows:10d} | {str(sha_match):18s} | {cost_str:20s} | {status:12s}")

if __name__ == "__main__":
    verify_manifest()
