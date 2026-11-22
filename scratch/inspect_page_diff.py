"""
scratch/inspect_page_diff.py
"""
import subprocess
from pathlib import Path

# Obtener la versión de HEAD de dashboard/strategy_bases_page.py
p = subprocess.run(["git", "show", "8162056:dashboard/strategy_bases_page.py"], capture_output=True, text=True, encoding="utf-8")
original_html = p.stdout

current_html = Path("dashboard/strategy_bases_page.py").read_text(encoding="utf-8")

print(f"Original length: {len(original_html)} chars, lines: {len(original_html.splitlines())}")
print(f"Current length: {len(current_html)} chars, lines: {len(current_html.splitlines())}")

# ¿Dónde difieren?
# Separar antes de WINNERS_DATA y después de STRATEGY_METRICS
orig_split = original_html.find("const WINNERS_DATA =")
curr_split = current_html.find("const WINNERS_DATA =")

print(f"Original pre-data length: {orig_split}")
print(f"Current pre-data length: {curr_split}")

orig_pre = original_html[:orig_split]
curr_pre = current_html[:curr_split]

if orig_pre == curr_pre:
    print("Pre-data HTML/CSS is IDENTICAL!")
else:
    print("Pre-data HTML/CSS differs!")
    import difflib
    diff = list(difflib.unified_diff(orig_pre.splitlines(), curr_pre.splitlines(), lineterm=""))
    print("\n".join(diff[:40]))
