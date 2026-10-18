import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path('.').resolve()
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

def test_symbol(symbol_name: str, days: int = 180):
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
        print(f"Archivos no encontrados para {symbol_name}")
        return
        
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
    
    print(f"Iniciando replay de {symbol_name} ({days} días) con spread {spread}...")
    t0 = time.time()
    trades = replay_frames(symbol_name, frames, days=days, cfg=cfg, spread=spread)
    elapsed = time.time() - t0
    
    print(f"[{symbol_name}] Replay {days} días completado en {elapsed:.2f}s | Operaciones detectadas: {len(trades)}")
    if len(trades) > 0:
        tdf = pd.DataFrame(trades)
        net_r = tdf['rr'].sum()
        wr = (tdf['rr'] > 0).mean() * 100
        print(f"  Resultados base: Net PnL = {net_r:+.2f} R | WinRate = {wr:.1f}%")
        print(tdf[['time', 'direction', 'adx', 'risk_atr', 'rr', 'outcome']].head(5))

if __name__ == '__main__':
    test_symbol("Boom 300 Index", days=30)
