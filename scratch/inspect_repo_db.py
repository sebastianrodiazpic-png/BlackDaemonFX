import sqlite3
import glob
import os
import json
from pathlib import Path

print("=== INSPECCIÓN DE BASES DE DATOS ===")
candidates = glob.glob('data/*.db') + glob.glob('storage/*.db') + glob.glob('storage/*.sqlite3') + glob.glob('storage/runtime/**/*.db', recursive=True)

for db_path in candidates:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        print(f"\nDB: {db_path} -> {len(tables)} tablas")
        for t in tables[:10]:
            try:
                cur.execute(f'SELECT count(*) FROM "{t}"')
                cnt = cur.fetchone()[0]
                print(f"   {t}: {cnt} registros")
            except Exception as e:
                print(f"   {t}: error {e}")
        conn.close()
    except Exception as e:
        print(f"Error opening {db_path}: {e}")

print("\n=== INSPECCIÓN DE MODELOS IA EN STORAGE ===")
model_files = glob.glob('storage/models/**/*', recursive=True) + glob.glob('storage/**/*.json', recursive=True)
for mf in model_files:
    if 'metalabel' in mf.lower() or 'model' in mf.lower() or 'ai' in mf.lower() or 'telemetry' in mf.lower():
        size = os.path.getsize(mf)
        print(f"  {mf} ({size} bytes)")
