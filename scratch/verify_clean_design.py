"""
scratch/verify_clean_design.py
"""
import subprocess
from pathlib import Path

p = subprocess.run(["git", "show", "8162056:dashboard/strategy_bases_page.py"], capture_output=True, text=True, encoding="utf-8")
orig = p.stdout
curr = Path("dashboard/strategy_bases_page.py").read_text(encoding="utf-8")

# Verificar antes de const WINNERS_DATA
idx_orig_w = orig.find("const WINNERS_DATA =")
idx_curr_w = curr.find("const WINNERS_DATA =")

print("1. ¿El HTML y CSS antes de los datos es 100% idéntico?:", orig[:idx_orig_w] == curr[:idx_curr_w])

# Verificar después de const LOSERS_DATA = [...]
# Encontrar fin de LOSERS_DATA en ambos
idx_orig_l = orig.find(";", orig.find("const LOSERS_DATA =")) + 1
idx_curr_l = curr.find(";", curr.find("const LOSERS_DATA =")) + 1

print("2. ¿El JavaScript, renderers y diseño después de los datos es 100% idéntico?:", orig[idx_orig_l:] == curr[idx_curr_l:])
