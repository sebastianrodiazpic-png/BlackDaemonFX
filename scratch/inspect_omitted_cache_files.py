import pandas as pd
from pathlib import Path

cache_dir = Path("data/cache_msnr")
omitted = [
    'AUDNZD', 'Boom 300 Index', 'Crash 600 Index', 'EURCHF', 'EURGBP',
    'GBPAUD', 'GBPJPY', 'GBPUSD', 'Jump 10 Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index'
]

print("=== INSPECTING CACHE FOR 14 OMITTED SYMBOLS ===")
for sym in omitted:
    slug = sym.replace(' ', '_').replace('(', '').replace(')', '')
    slug_alt = sym.replace(' ', '_')
    
    p_m15 = cache_dir / f"{slug}_M15.pkl"
    if not p_m15.exists():
        p_m15 = cache_dir / f"{slug_alt}_M15.pkl"
    
    p_h1 = cache_dir / f"{slug}_H1.pkl"
    if not p_h1.exists():
        p_h1 = cache_dir / f"{slug_alt}_H1.pkl"
        
    has_m15 = p_m15.exists()
    has_h1 = p_h1.exists()
    
    rows_m15 = 0
    start_m15, end_m15 = "", ""
    if has_m15:
        df = pd.read_pickle(p_m15)
        rows_m15 = len(df)
        col = 'time' if 'time' in df.columns else df.columns[0]
        ts = pd.to_datetime(df[col], utc=True)
        start_m15 = ts.min().strftime('%Y-%m-%d')
        end_m15 = ts.max().strftime('%Y-%m-%d')
        
    print(f"{sym:26s} | M15: {has_m15} ({rows_m15:6d} bars, {start_m15} to {end_m15}) | H1: {has_h1}")
