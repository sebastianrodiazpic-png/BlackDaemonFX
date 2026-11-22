import os

target_dirs = ["config", "dashboard", "strategy", "app", "tests"]
matches = []

for td in target_dirs:
    for root, dirs, files in os.walk(td):
        for file in files:
            if not file.endswith((".py", ".html", ".js", ".json", ".md")):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, 1):
                        if "sabri" in line.lower():
                            matches.append((path, idx, line.strip()))
            except Exception as e:
                pass

print(f"Total core matches: {len(matches)}")
files = sorted(set(m[0] for m in matches))
print(f"Files ({len(files)}):")
for f in files:
    count = sum(1 for m in matches if m[0] == f)
    print(f"  {f} ({count} matches)")

print("\nDetail:")
for p, l, text in matches[:40]:
    print(f"{p}:{l}: {text}")
