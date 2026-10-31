import sys
sys.path.insert(0, ".")
from database.repository import TradingRepository
from strategy.trend_pullback.config import DEFAULT_PULLBACK_SYMBOLS

repo = TradingRepository()
print("DB Path:", repo.db_path)

# 1. Recuperar TREND_PULLBACK si está vacía
tp_sel = repo.latest_instrument_selection_profile("TREND_PULLBACK")
print(f"Current TREND_PULLBACK: {len(tp_sel.get('selected_symbols', [])) if tp_sel else 0} symbols")
if not tp_sel or not tp_sel.get("selected_symbols"):
    repo.save_instrument_selection_profile(list(DEFAULT_PULLBACK_SYMBOLS), selection_profile="TREND_PULLBACK", source="DEMO")
    print(f"-> Saved {len(DEFAULT_PULLBACK_SYMBOLS)} symbols to TREND_PULLBACK profile.")

# 2. Sanitizar MALAYSIAN_SNR
msnr_sel = repo.latest_instrument_selection_profile("MALAYSIAN_SNR")
if msnr_sel and msnr_sel.get("selected_symbols"):
    curr = list(msnr_sel.get("selected_symbols"))
    unlisted = {"Vol over Boom 550", "Vol over Crash 550"}
    cleaned = [s for s in curr if s not in unlisted]
    print(f"Current MALAYSIAN_SNR: {len(curr)} symbols -> Cleaned: {len(cleaned)} symbols")
    if len(cleaned) != len(curr):
        repo.save_instrument_selection_profile(cleaned, selection_profile="MALAYSIAN_SNR", source="DEMO")
        print("-> Saved sanitized symbols to MALAYSIAN_SNR profile.")

# Verificar estado final
for p in ["TREND_PULLBACK", "MALAYSIAN_SNR"]:
    p_sel = repo.latest_instrument_selection_profile(p)
    print(f"VERIFIED {p}: {len(p_sel.get('selected_symbols', [])) if p_sel else 0} symbols")
