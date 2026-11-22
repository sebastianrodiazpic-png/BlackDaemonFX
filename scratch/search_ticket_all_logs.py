import os
import glob

bots_dir = "storage/logs/bots"
target = "4786473610"

for p in glob.glob(f"{bots_dir}/*"):
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if target in content:
                print(f"ENCONTRADO en {p} (tamaño: {len(content)})")
                count = content.count(target)
                print(f"  Apariciones: {count}")
                # Buscar si hay ORDER_OPENED o SPLIT_ORDER cerca
                idx = content.find(target)
                while idx != -1:
                    start = max(0, idx - 400)
                    end = min(len(content), idx + 600)
                    snippet = content[start:end]
                    if "ORDER" in snippet or "ticket" in snippet.lower() or "tp" in snippet.lower():
                        print(f"  Snippet en pos {idx}:")
                        print("  " + "\n  ".join(snippet.splitlines()[:20]))
                        break
                    idx = content.find(target, idx + 1)
        except Exception as e:
            pass
