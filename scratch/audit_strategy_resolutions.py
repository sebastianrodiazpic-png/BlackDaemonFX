from pathlib import Path
import re

files = [
    "strategy/ict/ict_strategy.py",
    "strategy/malaysian_snr/malaysian_snr_strategy.py",
    "strategy/orb/new_york_orb.py",
    "strategy/gold_quarters.py"
]

print("=====================================================================")
print("ANÁLISIS DE RESOLUCIÓN Y TEMPORALIDAD REQUERIDA POR CADA ESTRATEGIA")
print("=====================================================================")

for f_str in files:
    p = Path(f_str)
    if not p.exists():
        print(f"File not found: {f_str}")
        continue
    content = p.read_text(encoding="utf-8")
    
    print(f"\n>>> ARCHIVO: {f_str}")
    
    # Buscar timeframes, timeframe por defecto, HTF, LTF
    matches = re.findall(r'(?:timeframe|tf|time_frame|period|resolution)\s*[:=]\s*["\']?([A-Za-z0-9_]+)["\']?', content, re.IGNORECASE)
    print("  Parámetros de timeframe encontrados:", set(matches))
    
    # Buscar patrones de resample o timeframes fijos
    tfs = set(re.findall(r'TIMEFRAME_[A-Z0-9]+|["\']M1["\']|["\']M5["\']|["\']M15["\']|["\']H1["\']|["\']H4["\']|["\']D1["\']', content))
    print("  Constantes de timeframe:", tfs)
    
    # Buscar docstrings o comentarios en cabecera
    header_lines = [l.strip() for l in content.splitlines()[:30] if l.strip().startswith(("#", '"""', "*"))]
    print("  Cabecera/Docstring:")
    for l in header_lines[:5]:
        print("   ", l[:90])
