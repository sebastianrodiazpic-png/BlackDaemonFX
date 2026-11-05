import re
from pathlib import Path

# 1. Update config/ict_instrument_policy.py
policy_path = Path("config/ict_instrument_policy.py")
content = policy_path.read_text(encoding="utf-8")

# ICT_5Y_SYNTH_PRUNED
old_synth_pruned = '''ICT_5Y_SYNTH_PRUNED = (
    (
        "Crash 1000 Index",             # WR = 44.60 %, -0.129 R/op, -27.5 R
        "Volatility 90 (1s) Index",     # WR = 45.71 %, -0.088 R/op, -9.2 R
        "High Frequency Vol 50 Index",  # WR = 42.39 %, -0.179 R/op, -16.5 R
        "Volatility 100 Index",         # WR con criterio humano = 49.7 % (<= 50.0 %)
    )'''

new_synth_pruned = '''ICT_5Y_SYNTH_PRUNED = (
    (
        "Crash 1000 Index",             # WR = 44.60 %, -0.129 R/op, -27.5 R
        "Volatility 90 (1s) Index",     # WR = 45.71 %, -0.088 R/op, -9.2 R
        "High Frequency Vol 50 Index",  # WR = 42.39 %, -0.179 R/op, -16.5 R
        "Volatility 100 Index",         # WR con criterio humano = 49.7 % (<= 51.0 %)
        "Boom 500 Index",               # WR con criterio humano = 50.4 % (<= 51.0 %)
        "Crash 900 Index",              # WR con criterio humano = 50.5 % (<= 51.0 %)
    )'''

content = content.replace(old_synth_pruned.replace("\r\n", "\n"), new_synth_pruned.replace("\r\n", "\n"))
content = content.replace(old_synth_pruned, new_synth_pruned)

# ICT_FOREX_ACTIVE_BASES
old_forex = '("GBPUSD", "USDCHF", "EURJPY", "CADCHF", "NZDUSD", "EURGBP", "GBPJPY", "GBPCHF")'
new_forex = '("GBPUSD", "USDCHF", "EURJPY", "CADCHF", "NZDUSD", "EURGBP", "GBPJPY")'
content = content.replace(old_forex, new_forex)

# MSNR_ACIERTO47_SYNTHETICS: remove Boom 300, Vol over Crash 550, Volatility 150 (1s)
old_msnr_part = '''    "Boom 300 Index",                # 51.0% WR, +1.9 R
    "Vol over Crash 550",            # 50.8% WR, +1.3 R
    "Volatility 150 (1s) Index",     # 50.8% WR, -0.9 R
)'''
new_msnr_part = ''')'''
content = content.replace(old_msnr_part.replace("\r\n", "\n"), new_msnr_part)
content = content.replace(old_msnr_part, new_msnr_part)

# Also update reason strings to 51.0%
content = content.replace("acierto <= 50.0 % bajo estrategia y criterio humano en Malaysian SNR", "acierto <= 51.0 % bajo estrategia y criterio humano en Malaysian SNR")
content = content.replace("WR <= 47 % tras las 6 mejoras", "WR <= 51.0 % tras las 6 mejoras")
content = content.replace("WR <= 47 % en el replay fiel de 5 años ICT", "WR <= 51.0 % en el replay fiel de 5 años ICT")

policy_path.write_text(content, encoding="utf-8")
print("Updated config/ict_instrument_policy.py successfully")

# 2. Update strategy/malaysian_snr/config.py: remove CADJPY
msnr_cfg_path = Path("strategy/malaysian_snr/config.py")
msnr_content = msnr_cfg_path.read_text(encoding="utf-8")
msnr_content = msnr_content.replace('"CADJPY"', '').replace(', ,', ',')
# Clean trailing comma before parenthesis if any
msnr_content = re.sub(r',\s*,', ',', msnr_content)
msnr_content = re.sub(r',\s*\)', ')', msnr_content)
msnr_cfg_path.write_text(msnr_content, encoding="utf-8")
print("Updated strategy/malaysian_snr/config.py successfully")
