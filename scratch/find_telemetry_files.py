import glob
import os
import json

print("=== BUSCANDO ARCHIVOS CON REGISTROS DE TELEMETRÍA, TRADES O AUDITORÍA ===")

# Buscar en storage
for root, dirs, files in os.walk("storage"):
    for f in files:
        if any(w in f.lower() for w in ['telemetry', 'trade', 'quality', 'audit', 'learning', 'replay', 'metalabel']):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            if sz > 100:
                print(f"  {fp} ({sz} bytes)")
