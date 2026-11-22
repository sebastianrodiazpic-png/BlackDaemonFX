import inspect
import re
from pathlib import Path

# Buscar en todos los archivos de strategy/**/*.py cualquier comprobación de hora, sesión o killzone
pattern = re.compile(r'(\bhour\b|\bweekday\b|\bkillzone\b|\bsession\b|\brollover\b|\bstandby\b)', re.IGNORECASE)

root = Path("strategy")
results = []
for p in root.rglob("*.py"):
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for idx, line in enumerate(lines, 1):
        if pattern.search(line) and not line.strip().startswith("#"):
            results.append((str(p), idx, line.strip()))

print(f"Total coincidencias de tiempo/sesión en strategy/: {len(results)}")

# Filtrar aquellas que involucren símbolos o decisiones
interesting = [r for r in results if any(k in r[2].lower() for k in ("if ", "return", "def ", "gate", "guard", "filter", "check"))]
print(f"Coincidencias en condicionales/retornos: {len(interesting)}")

for file_path, line_no, code in interesting[:40]:
    print(f"{file_path}:{line_no} -> {code}")
