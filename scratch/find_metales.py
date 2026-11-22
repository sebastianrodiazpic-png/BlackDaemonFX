import os

for root, dirs, files in os.walk("."):
    if any(k in root for k in (".git", ".venv", "__pycache__", ".pytest_cache")):
        continue
    for f in files:
        if f.endswith((".py", ".html", ".js", ".json", ".md", ".sh", ".bat")):
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    for num, line in enumerate(fp, 1):
                        if "metales, cripto" in line.lower() or "metales,cripto" in line.lower():
                            print(f"{p}:{num}: {line.strip()[:140]}")
            except Exception:
                pass
