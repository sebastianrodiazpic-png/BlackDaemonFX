import os

target_dirs = ["config", "dashboard", "strategy"]
for td in target_dirs:
    for root, dirs, files in os.walk(td):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, 1):
                    if "sabri" in line.lower():
                        print(f"{path}:{idx}: {line.strip()[:140]}")
