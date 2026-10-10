import os
import glob
import re

files = glob.glob("scratch/transcripts/*.txt")

keywords = [
    "snr", "soporte", "resistencia", "fresh", "line", "linea", "vela", "mecha",
    "cuerpo", "h1", "h4", "m15", "m5", "m1", "daily", "semanal", "c trade", "c-trade",
    "continuation", "reversal", "quasimodo", "qm", "qmr", "fakeout", "engulfing",
    "envolvente", "stop loss", "sl", "take profit", "tp", "retest", "pullback",
    "break", "ruptura", "rompimiento", "bos", "choch", "rejection", "entrada",
    "entry", "timeframe", "temporalidad", "multitimeframe", "alchemist", "setup"
]

def analyze_transcript(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    header = lines[:5]
    text = " ".join(lines[5:])
    
    # Extract snippets around key concepts
    matches = {}
    for kw in ["fresh", "c trade", "quasimodo", "timeframe", "temporalidad", "stop loss", "tp", "retest", "engulfing", "envolvente", "fakeout"]:
        found = [m.start() for m in re.finditer(re.escape(kw), text, re.IGNORECASE)]
        matches[kw] = len(found)
        
    return "".join(header), len(text), matches

print("Transcript Analysis Overview:")
for f in sorted(files):
    h, length, m = analyze_transcript(f)
    fname = os.path.basename(f)
    print(f"=== {fname} ({length} chars) ===")
    print(h.strip())
    top_kw = {k: v for k, v in m.items() if v > 0}
    print("Keywords:", top_kw)
    print("-" * 50)
