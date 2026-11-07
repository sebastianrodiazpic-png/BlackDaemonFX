import os, glob

for root, dirs, files in os.walk("storage/analysis"):
    for f in files:
        if f.endswith((".csv", ".json", ".md", ".txt")):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    if "USDCHF" in content and "75" in content and "msnr" in f.lower():
                        print(f"Match USDCHF & 75 in {path}")
                    if "AUDCAD" in content and "60" in content and "msnr" in f.lower():
                        print(f"Match AUDCAD & 60 in {path}")
            except Exception:
                pass
