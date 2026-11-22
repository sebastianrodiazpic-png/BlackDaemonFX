import os
import glob
import re

logs = glob.glob("storage/logs/bots/*.log")
patterns = [
    r"SEÑAL DETECTADA",
    r"SENAL DETECTADA",
    r"SIGNAL GENERATED",
    r"EVALUANDO CRITERIO HUMANO",
    r"CRITERIO HUMANO VETO",
    r"CRITERIO HUMANO APROBADO",
    r"HUMAN_CRITERIA",
    r"TRIPARTITA",
    r"VETO",
    r"Nuevas órdenes:\s*[1-9]",
    r"Validadas DRY RUN:\s*[1-9]",
    r"ORDEN ENVIADA",
    r"ORDER SENT",
    r"TRADE EXECUTED"
]

compiled = [re.compile(p, re.IGNORECASE) for p in patterns]

for log_path in sorted(logs):
    bot_name = os.path.basename(log_path).replace(".log", "")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    matches = []
    # Revisar las últimas 50,000 líneas
    search_lines = lines[-50000:]
    for idx, line in enumerate(search_lines):
        for c in compiled:
            if c.search(line):
                # Tomar contexto de 2 líneas antes y 2 después
                start = max(0, idx - 2)
                end = min(len(search_lines), idx + 3)
                context = [l.strip() for l in search_lines[start:end]]
                matches.append((idx, line.strip(), context))
                break
    
    print(f"\n==========================================")
    print(f"Bot: {bot_name} (checked last {len(search_lines)} lines, matches: {len(matches)})")
    print(f"==========================================")
    if matches:
        # Mostrar los últimos 5 eventos encontrados
        for m in matches[-5:]:
            print(f"  Line {m[0]}: {m[1]}")
            for c in m[2]:
                print(f"     | {c}")
