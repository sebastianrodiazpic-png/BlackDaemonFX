with open('config/ict_instrument_policy.py', 'rb') as f:
    content = f.read()

# Normalize all \r\r\n or \r\n to \n
content_norm = content.replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')

target = b'''# Canasta \xc3\x89lite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
MSNR_ELITE_SYNTHETICS = MSNR_ACIERTO47_SYNTHETICS
MSNR_ELITE_BASKET_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "1").strip().lower() in ("1", "true", "on")'''

replacement = b'''# Canasta \xc3\x89lite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
# Ganadores top probados: Boom 1000 (+21.0 R), Crash 1000 (+14.4 R), Vol 25 (+15.8 R), Vol 10 (+14.2 R), Step Index (+5.5 R).
# Excluidos por destrucci\xc3\xb3n probada: Jump 25 (-43.0 R) y Volatility 75 (-27.4 R).
MSNR_ELITE_SYNTHETICS = (
    "Boom 1000 Index", "Crash 1000 Index", "Step Index", "Volatility 25 Index", "Volatility 10 Index",
    "Volatility 90 Index", "Volatility 50 (1s) Index", "Boom 500 Index", "Crash 900 Index",
    "Boom 300 Index", "Crash 600 Index", "VolSwitch High Vol Index", "High Frequency Vol 100 Index",
    "High Frequency Vol 50 Index", "Volatility 15 Index", "Volatility 75 (1s) Index",
    "Volatility 150 (1s) Index", "Volatility 250 (1s) Index", "Volatility 5 Index", "Jump 10 Index",
)
MSNR_ELITE_BASKET_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "1").strip().lower() in ("1", "true", "on")'''

assert target in content_norm, "Target not found in normalized content"
content_norm = content_norm.replace(target, replacement)

# Save with standard CRLF
with open('config/ict_instrument_policy.py', 'wb') as f:
    f.write(content_norm.replace(b'\n', b'\r\n'))

print("File normalized and MSNR_ELITE_SYNTHETICS restored!")
