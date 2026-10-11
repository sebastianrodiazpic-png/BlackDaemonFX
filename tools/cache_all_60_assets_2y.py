"""Descarga y cache local de 2 años (Oct 2024 - Oct 2026) para los 60 activos del Universo.
Guarda H1 y M15 en formato pickle optimizado en data/cache_msnr.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import MetaTrader5 as mt5

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE


def cache_all_assets(days: int = 730):
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 90)
    print(f"DESCARGANDO Y CACHEANDO 2 AÑOS HISTÓRICOS DE 60 ACTIVOS DESDE MT5 ({days} DÍAS)")
    print(f"Destino: {cache_dir}")
    print("=" * 90)

    if not mt5.initialize():
        print("ERROR: No se pudo inicializar MetaTrader 5.")
        return False

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    t0 = time.time()
    success = 0
    failed = []

    for idx, (sym, meta) in enumerate(ASSET_UNIVERSE.items(), start=1):
        sym_clean = sym.replace(" ", "_")
        h1_pkl = cache_dir / f"{sym_clean}_H1.pkl"
        m15_pkl = cache_dir / f"{sym_clean}_M15.pkl"

        # Si ya existe y es reciente, verificar
        if h1_pkl.exists() and m15_pkl.exists():
            print(f"[{idx:02d}/60] {sym:<25} -> Cache ya existente OK")
            success += 1
            continue

        print(f"[{idx:02d}/60] {sym:<25} -> Consultando MT5...", end=" ", flush=True)
        mt5.symbol_select(sym, True)
        r_h1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_H1, start, now)
        r_m15 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start, now)

        if r_h1 is None or len(r_h1) < 100 or r_m15 is None or len(r_m15) < 500:
            print("ERROR: Datos insuficientes")
            failed.append(sym)
            continue

        df_h1 = pd.DataFrame(r_h1)
        df_h1["time"] = pd.to_datetime(df_h1["time"], unit="s", utc=True)
        df_h1 = df_h1[["time", "open", "high", "low", "close", "tick_volume"]]
        df_h1.to_pickle(h1_pkl)

        df_m15 = pd.DataFrame(r_m15)
        df_m15["time"] = pd.to_datetime(df_m15["time"], unit="s", utc=True)
        df_m15 = df_m15[["time", "open", "high", "low", "close", "tick_volume"]]
        df_m15.to_pickle(m15_pkl)

        print(f"OK (H1: {len(df_h1)} bars, M15: {len(df_m15)} bars)")
        success += 1

    mt5.shutdown()
    t_end = time.time()
    print("=" * 90)
    print(f"Descarga finalizada en {t_end - t0:.2f}s. Exitosos: {success}/60. Fallidos: {len(failed)}")
    if failed:
        print(f"Fallidos: {failed}")
    return success == len(ASSET_UNIVERSE)


if __name__ == "__main__":
    cache_all_assets()
