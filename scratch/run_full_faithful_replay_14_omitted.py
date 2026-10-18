"""
scratch/run_full_faithful_replay_14_omitted.py
Replay Fiel Offline Aislado de los 14 Activos Canónicos Omitidos de Malaysian SNR.
- Cero conexión a MT5 o brokers.
- Utiliza únicamente data/cache_msnr/*.pkl.
- Multiprocesamiento paralelo (8 workers).
- Salida: scratch/omitted_14_msnr_faithful_trades.csv
"""

import sys
import time
import os
from pathlib import Path
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Patch closed_candles in memory for speed
import strategy.malaysian_snr.malaysian_snr_strategy as msnr_mod
import strategy.malaysian_snr.validation as val_mod
import strategy.malaysian_snr.history as hist_mod

def fast_closed_candles(raw, timeframe, now):
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    delta = val_mod.timeframe_delta(timeframe)
    mask = (raw['time'] + delta) <= now
    return raw[mask].copy()

msnr_mod.closed_candles = fast_closed_candles
hist_mod.closed_candles = fast_closed_candles
val_mod.closed_candles = fast_closed_candles

from tools.replay_msnr_live_faithful import HistoricalProvider, replay_frames
from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE

OMITTED_SYMBOLS = [
    'AUDNZD', 'Boom 300 Index', 'Crash 600 Index', 'EURCHF', 'EURGBP',
    'GBPAUD', 'GBPJPY', 'GBPUSD', 'Jump 10 Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index'
]

def build_d1_from_h1(h1_df: pd.DataFrame) -> pd.DataFrame:
    df = h1_df.copy()
    col = 'time' if 'time' in df.columns else df.columns[0]
    df['time'] = pd.to_datetime(df[col], utc=True)
    df = df.set_index('time')
    d1 = df.resample('1D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'tick_volume': 'sum' if 'tick_volume' in df.columns else 'count'
    }).dropna().reset_index()
    return d1

def replay_worker(symbol_name: str, days: int = 180):
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"
    slug = symbol_name.replace(' ', '_').replace('(', '').replace(')', '')
    slug_alt = symbol_name.replace(' ', '_')
    
    p_m15 = cache_dir / f"{slug}_M15.pkl"
    if not p_m15.exists():
        p_m15 = cache_dir / f"{slug_alt}_M15.pkl"
    p_h1 = cache_dir / f"{slug}_H1.pkl"
    if not p_h1.exists():
        p_h1 = cache_dir / f"{slug_alt}_H1.pkl"
        
    if not p_m15.exists() or not p_h1.exists():
        return symbol_name, [], f"Archivos faltantes M15/H1", 0.0
        
    m15 = pd.read_pickle(p_m15)
    h1 = pd.read_pickle(p_h1)
    
    col_m15 = 'time' if 'time' in m15.columns else m15.columns[0]
    m15['time'] = pd.to_datetime(m15[col_m15], utc=True)
    
    col_h1 = 'time' if 'time' in h1.columns else h1.columns[0]
    h1['time'] = pd.to_datetime(h1[col_h1], utc=True)
    
    d1 = build_d1_from_h1(h1)
    
    frames = {"M15": m15, "H1": h1, "D1": d1}
    cfg = MalaysianSNRConfig()
    spread = ASSET_UNIVERSE.get(symbol_name, {}).get('base_spread', 0.0)
    
    t0 = time.time()
    trades = replay_frames(symbol_name, frames, days=days, cfg=cfg, spread=spread)
    elapsed = time.time() - t0
    
    return symbol_name, trades, "OK", elapsed

def main():
    print(f"=== INICIANDO REPLAY FIEL OFFLINE PARA {len(OMITTED_SYMBOLS)} ACTIVOS OMITIDOS (180 DÍAS) ===")
    start_total = time.time()
    
    all_trades = []
    summary = []
    
    # Usar 8 workers en paralelo
    workers = min(8, os.cpu_count() or 4)
    print(f"Lanzando ProcessPoolExecutor con {workers} workers...")
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(replay_worker, sym, 180): sym for sym in OMITTED_SYMBOLS}
        for future in as_completed(futures):
            sym = futures[future]
            try:
                symbol_name, trades, status, elapsed = future.result()
                n = len(trades)
                net_r = round(sum(t['rr'] for t in trades), 2) if n > 0 else 0.0
                wr = round(100.0 * sum(1 for t in trades if t['rr'] > 0) / n, 1) if n > 0 else 0.0
                print(f"  [✓] {symbol_name:25s} | Trades: {n:3d} | WR: {wr:5.1f}% | Net R: {net_r:+6.2f} R | Tiempo: {elapsed:5.1f}s | Estado: {status}")
                if n > 0:
                    all_trades.extend(trades)
                summary.append({"symbol": symbol_name, "trades": n, "win_rate_pct": wr, "net_r": net_r, "elapsed_s": round(elapsed, 1), "status": status})
            except Exception as exc:
                print(f"  [✗] {sym:25s} | Error: {exc}")
                summary.append({"symbol": sym, "trades": 0, "win_rate_pct": 0.0, "net_r": 0.0, "elapsed_s": 0.0, "status": f"ERROR: {exc}"})

    total_time = time.time() - start_total
    print(f"\nReplay completado en {total_time:.1f}s ({total_time/60:.1f} minutos). Total operaciones detectadas: {len(all_trades)}")

    # Guardar operaciones en scratch
    out_csv = PROJECT_ROOT / "scratch" / "omitted_14_msnr_faithful_trades.csv"
    if all_trades:
        df_out = pd.DataFrame(all_trades)
        df_out.to_csv(out_csv, index=False)
        print(f"Guardado CSV de operaciones omitidas en: {out_csv}")
    else:
        print("No se generaron operaciones en los activos omitidos.")
        pd.DataFrame().to_csv(out_csv, index=False)

    # Resumen
    df_summary = pd.DataFrame(summary).sort_values("trades", ascending=False)
    sum_csv = PROJECT_ROOT / "scratch" / "omitted_14_msnr_summary.csv"
    df_summary.to_csv(sum_csv, index=False)
    print(f"Guardado resumen en: {sum_csv}")

if __name__ == '__main__':
    main()
