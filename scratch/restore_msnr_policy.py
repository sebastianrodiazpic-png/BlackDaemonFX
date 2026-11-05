path = 'config/ict_instrument_policy.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Restaurar MSNR_ACIERTO47_SYNTHETICS a los 24 y añadir MSNR_ELITE_SYNTHETICS
new_block = """MSNR_ACIERTO47_SYNTHETICS = (
    "High Frequency Vol 100 Index", "VolSwitch High Vol Index", "Volatility 5 Index",
    "Volatility 50 (1s) Index", "Volatility 90 Index", "Step Index 500", "Boom 300 Index",
    "Step Index 200", "Volatility 150 (1s) Index", "Jump 25 Index", "Step Index 400",
    "Jump 75 Index", "Volatility 25 Index", "Volatility 75 Index", "Volatility 250 (1s) Index",
    "Crash 900 Index", "High Frequency Vol 50 Index", "Volatility 10 Index", "Jump 10 Index",
    "Boom 500 Index", "Volatility 15 Index", "Jump 50 Index", "Volatility 75 (1s) Index",
    "Step Index",
)
MSNR_ACIERTO47_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ACIERTO47", "on").strip().lower() not in ("0", "false", "off")

# Canasta Élite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
# Ganadores top probados: Boom 1000 (+21.0 R), Crash 1000 (+14.4 R), Vol 25 (+15.8 R), Vol 10 (+14.2 R), Step Index (+5.5 R).
# Excluidos por destrucción probada: Jump 25 (-43.0 R) y Volatility 75 (-27.4 R).
MSNR_ELITE_SYNTHETICS = (
    "Boom 1000 Index", "Crash 1000 Index", "Step Index", "Volatility 25 Index", "Volatility 10 Index",
    "Volatility 90 Index", "Volatility 50 (1s) Index", "Boom 500 Index", "Crash 900 Index",
    "Boom 300 Index", "Crash 600 Index", "VolSwitch High Vol Index", "High Frequency Vol 100 Index",
    "High Frequency Vol 50 Index", "Volatility 15 Index", "Volatility 75 (1s) Index",
    "Volatility 150 (1s) Index", "Volatility 250 (1s) Index", "Volatility 5 Index", "Jump 10 Index",
)
MSNR_ELITE_BASKET_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "1").strip().lower() in ("1", "true", "on")


def _malaysian_snr_synthetics() -> tuple:
    raw = os.getenv("DAEMONBLACKFX_MSNR_SYNTHETICS_ACTIVE", "").strip()
    if raw:
        return tuple(s.strip() for s in raw.split(",") if s.strip())
    # Si la variable de entorno de test o despliegue pide élite o si está activa:
    if os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "").strip().lower() in ("1", "true", "on"):
        return MSNR_ELITE_SYNTHETICS
    if MSNR_ACIERTO47_ENABLED:
        return MSNR_ACIERTO47_SYNTHETICS
    return (*MSNR_ACTIVE, *MSNR_DEMO_TEST_SYMBOLS)"""

# Buscamos el bloque actual de MSNR_ACIERTO47_SYNTHETICS hasta def _malaysian_snr_synthetics
import re
pattern = r'MSNR_ACIERTO47_SYNTHETICS = \(.*?\)\s*MSNR_ACIERTO47_ENABLED = os\.getenv.*?\ndef _malaysian_snr_synthetics\(\) -> tuple:'
match = re.search(pattern, c, re.DOTALL)
if match:
    c = c[:match.start()] + new_block + c[match.end():]
    print("Replaced MSNR block in ict_instrument_policy.py")
else:
    print("Pattern not matched!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
