"""
scratch/discover_data_and_replays.py
====================================
Script de solo lectura para inventariar los datasets de caché, archivos de análisis,
scripts de replay y cobertura temporal por activo y estrategia en el repositorio.
"""
from pathlib import Path
import pickle
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

for folder in ["data", "data/cache", "data/cache_msnr", "data/research", "storage/analysis", "tools"]:
    p = PROJECT_ROOT / folder
    print(f"\n=== FOLDER: {folder} (exists={p.exists()}) ===")
    if p.exists():
        files = sorted([f for f in p.iterdir() if f.is_file()])
        print(f"Total files: {len(files)}")
        for f in files[:60]:
            print(f"  {f.name:48s} | {f.stat().st_size:12,d} bytes")
        if len(files) > 60:
            print(f"  ... (+{len(files)-60} more files)")
