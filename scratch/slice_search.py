import re

def slice_search(fpath, terms):
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"\n==================== {fpath} ====================")
    for term in terms:
        for m in re.finditer(re.escape(term), text, re.IGNORECASE):
            idx = m.start()
            start = max(0, idx - 100)
            end = min(len(text), idx + 200)
            snippet = text[start:end].replace('\n', ' ')
            print(f"[{term}]: ...{snippet}...")

# Let's inspect Part 2 (lqlkspVKt7s)
slice_search("scratch/transcripts/lqlkspVKt7s.txt", ["fresh", "c trade", "breakout", "rule", "setup"])
