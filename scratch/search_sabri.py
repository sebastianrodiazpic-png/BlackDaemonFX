import os
import re

ignore_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "graphify-out", ".agents"}
ignore_exts = {".png", ".jpg", ".jpeg", ".ico", ".pkl", ".db", ".sqlite", ".sqlite3", ".pyc"}

results = []

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in ignore_exts:
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if "sabri" in line.lower():
                        results.append((filepath, line_num, line.strip()))
        except Exception as e:
            pass

print(f"Total matches found: {len(results)}")
files_matched = set(r[0] for r in results)
print(f"Files matched ({len(files_matched)}):")
for f in sorted(files_matched):
    print(" ", f)

print("\nSamples (first 25):")
for f, l, text in results[:25]:
    print(f"{f}:{l}: {text[:120]}")
