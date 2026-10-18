import sys
from pathlib import Path

PROJECT_ROOT = Path('.').resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE

omitted = [
    'AUDNZD', 'Boom 300 Index', 'Crash 600 Index', 'EURCHF', 'EURGBP',
    'GBPAUD', 'GBPJPY', 'GBPUSD', 'Jump 10 Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index'
]

print("=== SPREADS IN ASSET_UNIVERSE FOR 14 OMITTED SYMBOLS ===")
for s in omitted:
    info = ASSET_UNIVERSE.get(s, {})
    spread = info.get('base_spread', 'N/A')
    cat = info.get('category', 'N/A')
    print(f"{s:26s} | Spread: {spread} | Category: {cat}")
