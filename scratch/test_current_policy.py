import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from config.ict_instrument_policy import (
    ICT_5Y_SYNTH_PRUNED,
    ICT_SYNTHETIC_FAMILIES,
    ICT_FOREX_ACTIVE_BASES,
    MSNR_ACIERTO47_SYNTHETICS,
    MSNR_REAL_MARKET_SYMBOLS,
    ict_active_symbols,
    preventive_prune_reason
)

print("Current active SYNTHETICS:", len(ict_active_symbols("SYNTHETICS")))
print("Current active FOREX:", len(ict_active_symbols("FOREX")))
print("Current active ICT:", len(ict_active_symbols("ICT")))
print("Current active MSNR:", len(ict_active_symbols("MALAYSIAN_SNR")))
print("Current active TP:", len(ict_active_symbols("TREND_PULLBACK")))
