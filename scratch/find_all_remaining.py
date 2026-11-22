import os, re

ignore_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "graphify-out", ".agents", "scratch"}
ignore_exts = {".png", ".jpg", ".jpeg", ".ico", ".pkl", ".db", ".sqlite", ".sqlite3", ".pyc"}

files_with_sabri_malle = []

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in ignore_exts:
            continue
        path = os.path.join(root, file)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "ict sabri malle" in content.lower():
                files_with_sabri_malle.append((path, len(re.findall(r"ict sabri malle", content, re.IGNORECASE))))
        except Exception:
            pass

print(f"Files still containing 'ICT Sabri Malle' ({len(files_with_sabri_malle)}):")
for p, c in sorted(files_with_sabri_malle):
    print(f"  {p} ({c})")
