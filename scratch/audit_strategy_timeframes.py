import inspect
import sys
from pathlib import Path
import re

print("=====================================================================")
print("AUDITORÍA DE TEMPORALIDADES Y REQUERIMIENTOS POR ESTRATEGIA")
print("=====================================================================")

strat_dir = Path("src/strategies")
for p in sorted(strat_dir.glob("*.py")):
    if p.name.startswith("__"):
        continue
    content = p.read_text(encoding="utf-8")
    
    # Buscar menciones a timeframes
    tfs = set(re.findall(r'TIMEFRAME_[A-Z0-9]+|["\']M1["\']|["\']M5["\']|["\']M15["\']|["\']H1["\']|["\']H4["\']|["\']D1["\']', content))
    
    # Buscar métodos o parámetros de entrada
    lines = [l.strip() for l in content.splitlines() if "timeframe" in l.lower() or "tf" in l.lower() or "resample" in l.lower()]
    print(f"\nEstrategia: {p.name}")
    print(f"  Timeframes referenciados: {sorted(list(tfs))}")
    print(f"  Líneas clave:")
    for l in lines[:5]:
        print(f"    - {l[:100]}")

print("\n=====================================================================")
print("AUDITORÍA DE ARCHIVOS DE REPLAY DE GOLD QUARTERS")
print("=====================================================================")
for p in Path(".").glob("*gold*"):
    print(p)
for p in Path("scratch").glob("*gold*"):
    print(p)
for p in Path("data").rglob("*gold*"):
    print(p)
for p in Path("data").rglob("*XAU*"):
    print(p)

