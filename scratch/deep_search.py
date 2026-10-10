import re

def search_text(file_path, keywords, max_results=10):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"\n==================== {file_path} ====================")
    found = 0
    # Split text into chunks of ~150 chars or sentences
    chunks = [c.strip() for c in re.split(r'[\.\?\!\n]+', text) if len(c.strip()) > 20]
    
    for c in chunks:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', c, re.IGNORECASE):
                print(f"[{kw}] {c}")
                found += 1
                break
        if found >= max_results:
            break

# 1. MBA Dia 1
search_text("scratch/transcripts/xYlpAr5pwXg.txt", ["snr", "malaysian", "patron", "soporte", "resistencia", "fresh", "quasimodo", "entrada", "confirmacion"])

# 2. MR.R Alchemist Part 2
search_text("scratch/transcripts/lqlkspVKt7s.txt", ["fresh", "c trade", "retest", "support", "resistance", "breakout", "entry", "timeframe", "stop loss"])

# 3. MR.R Alchemist Part 3
search_text("scratch/transcripts/CH9iW5caHHk.txt", ["fresh", "c trade", "retest", "support", "resistance", "breakout", "entry", "timeframe", "stop loss"])

# 4. MR.R Alchemist Part 4 & 5
search_text("scratch/transcripts/QbyhRLF53RI.txt", ["fresh", "c trade", "retest", "support", "resistance", "quasimodo", "entry", "timeframe"])
search_text("scratch/transcripts/XvXWWv3gD8k.txt", ["fresh", "c trade", "retest", "support", "resistance", "quasimodo", "entry", "timeframe"])

# 5. MR.R Alchemist 2024
search_text("scratch/transcripts/FM0XkqUIrAI.txt", ["fresh", "c trade", "retest", "engulfing", "support", "resistance", "entry"])
