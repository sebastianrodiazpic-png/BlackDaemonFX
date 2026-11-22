import glob
import re

patterns = ["CENSO COMPLETO", "FAMILIA JUMP", "Trades Vivo", "PnL Vivo", "Veredicto", "DEJAR ACTIVO", "DESBLOQUEAR (ALTA CONVICCIÓN)"]

print("Searching in storage and .md files...")
for p in glob.glob("**/*.md", recursive=True):
    if ".venv" in p or ".git" in p: continue
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
            for pat in patterns:
                if pat in c:
                    print(f"Match '{pat}' in {p}")
                    break
    except Exception as e:
        pass
