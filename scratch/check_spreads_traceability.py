import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

cfg = MalaysianSNRConfig()
canonical = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
cache_dir = PROJECT_ROOT / "data" / "cache_msnr"

print(f"{'Símbolo':26s} | {'Spread Config':14s} | {'Precio Medio M15':17s} | {'Spread / Precio':15s} | {'¿Consistente?':14s}")
print("-" * 95)

for sym in canonical:
    info = ASSET_UNIVERSE.get(sym, {})
    sp = info.get('base_spread', 0.0)
    
    slug = sym.replace(' ', '_').replace('(', '').replace(')', '')
    slug_alt = sym.replace(' ', '_')
    p_m15 = cache_dir / f"{slug}_M15.pkl"
    if not p_m15.exists():
        p_m15 = cache_dir / f"{slug_alt}_M15.pkl"
        
    avg_price = 0.0
    if p_m15.exists():
        df = pd.read_pickle(p_m15)
        col = 'time' if 'time' in df.columns else df.columns[0]
        df['time'] = pd.to_datetime(df[col], utc=True)
        sub = df[df['time'] >= '2026-04-14']
        if len(sub) > 0:
            avg_price = float(sub['close'].mean())
        else:
            avg_price = float(df['close'].mean())
            
    ratio = (sp / avg_price) if avg_price > 0 else 0.0
    consistent = "ANOMALÍA GRAVE" if ratio > 0.05 else ("OK" if ratio < 0.01 else "REVISAR")
    print(f"{sym:26s} | {sp:14.5f} | {avg_price:17.4f} | {ratio:15.5f} | {consistent:14s}")
