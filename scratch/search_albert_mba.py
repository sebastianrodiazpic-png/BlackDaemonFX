import re

def inspect_file(fpath):
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"\n==================== {fpath} ====================")
    terms = ["fresh", "patrón a", "patrón v", "cuerpo", "mecha", "retest", "temporalidad", "break", "quasimodo", "entrada", "stop loss"]
    for t in terms:
        matches = list(re.finditer(re.escape(t), text, re.IGNORECASE))
        print(f"[{t}] {len(matches)} matches")
        for m in matches[:3]:
            idx = m.start()
            s = text[max(0, idx-80):min(len(text), idx+180)].replace('\n', ' ')
            print(f"   -> {s}")

inspect_file("scratch/transcripts/L_vwb_jf6og.txt")
inspect_file("scratch/transcripts/wDK7qO4mf-E.txt")
inspect_file("scratch/transcripts/xYlpAr5pwXg.txt")
