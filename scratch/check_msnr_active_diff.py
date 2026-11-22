import sys
sys.path.insert(0, '.')
from dashboard.realtime_dashboard import DEFAULT_PRIORITIZED_SYMBOLS
from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE

msnr_dash = DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"]
print("Dashboard len:", len(msnr_dash))
print("Policy len:", len(MALAYSIAN_SNR_ACTIVE))
print("In policy not dash:", set(MALAYSIAN_SNR_ACTIVE) - set(msnr_dash))
print("In dash not policy:", set(msnr_dash) - set(MALAYSIAN_SNR_ACTIVE))
print("Duplicates in dash:", len(msnr_dash) - len(set(msnr_dash)))
from collections import Counter
dash_counts = Counter(msnr_dash)
dups = [k for k, v in dash_counts.items() if v > 1]
print("Duplicate symbols in dash:", dups)
