with open('config/ict_instrument_policy.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''# Canasta Élite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
MSNR_ELITE_SYNTHETICS = MSNR_ACIERTO47_SYNTHETICS
MSNR_ELITE_BASKET_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "1").strip().lower() in ("1", "true", "on")'''

replacement = '''# Canasta Élite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
# Ganadores top probados: Boom 1000 (+21.0 R), Crash 1000 (+14.4 R), Vol 25 (+15.8 R), Vol 10 (+14.2 R), Step Index (+5.5 R).
# Excluidos por destrucción probada: Jump 25 (-43.0 R) y Volatility 75 (-27.4 R).
MSNR_ELITE_SYNTHETICS = (
    "Boom 1000 Index", "Crash 1000 Index", "Step Index", "Volatility 25 Index", "Volatility 10 Index",
    "Volatility 90 Index", "Volatility 50 (1s) Index", "Boom 500 Index", "Crash 900 Index",
    "Boom 300 Index", "Crash 600 Index", "VolSwitch High Vol Index", "High Frequency Vol 100 Index",
    "High Frequency Vol 50 Index", "Volatility 15 Index", "Volatility 75 (1s) Index",
    "Volatility 150 (1s) Index", "Volatility 250 (1s) Index", "Volatility 5 Index", "Jump 10 Index",
)
MSNR_ELITE_BASKET_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "1").strip().lower() in ("1", "true", "on")'''

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm
text_norm = text_norm.replace(target_norm, replacement_norm)

with open('config/ict_instrument_policy.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm.replace('\n', '\r\n'))

print("Restored MSNR_ELITE_SYNTHETICS tuple in config/ict_instrument_policy.py")
