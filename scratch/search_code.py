import os

target = "POSICION_DEL_DAEMON_DESCUBIERTA_EN_MT5"
results = []
for root, dirs, files in os.walk("."):
    if ".venv" in root or ".git" in root or "__pycache__" in root:
        continue
    for f in files:
        if f.endswith(".py") or f.endswith(".md"):
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    for i, line in enumerate(fp, 1):
                        if target in line:
                            results.append((p, i, line.strip()))
            except Exception:
                pass

print(f"Found {len(results)} occurrences:")
for r in results:
    print(f"{r[0]}:{r[1]} -> {r[2]}")
