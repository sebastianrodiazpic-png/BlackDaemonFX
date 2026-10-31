import sys
sys.path.insert(0, ".")
from types import SimpleNamespace
from app.main import _resolve_live_symbols_for_profile

args = SimpleNamespace(symbol=None)
syms = _resolve_live_symbols_for_profile(args, "MALAYSIAN_SNR")
print(f"Total symbols: {len(syms)}")
bad = [s for s in syms if "550" in s]
print("550 symbols:", bad)
