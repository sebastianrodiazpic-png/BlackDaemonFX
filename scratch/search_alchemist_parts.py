import re

def slice_search_multiple(files, terms):
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"\n==================== {fpath} ====================")
        for term in terms:
            matches = list(re.finditer(re.escape(term), text, re.IGNORECASE))
            print(f"[{term}]: Total matches = {len(matches)}")
            for m in matches[:4]:
                idx = m.start()
                start = max(0, idx - 100)
                end = min(len(text), idx + 200)
                snippet = text[start:end].replace('\n', ' ')
                print(f"   -> ...{snippet}...")

slice_search_multiple([
    "scratch/transcripts/CH9iW5caHHk.txt",
    "scratch/transcripts/QbyhRLF53RI.txt",
    "scratch/transcripts/XvXWWv3gD8k.txt"
], ["c trade", "fresh", "quasimodo", "sbr", "rbs", "engulfing", "storyline", "trend line", "trendline"])
