import re

def extract_alchemist_core():
    files = [
        "scratch/transcripts/lqlkspVKt7s.txt",
        "scratch/transcripts/CH9iW5caHHk.txt",
        "scratch/transcripts/QbyhRLF53RI.txt",
        "scratch/transcripts/XvXWWv3gD8k.txt"
    ]
    
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"\n==================== {fpath} ====================")
        # Search for definitions of: C-trade, V-trade, Fresh, Fakeout, Major/Minor, Timeframes
        patterns = [
            r"c[\s-]trade[^\.\?\!]{10,250}[\.\?\!]",
            r"fresh[^\.\?\!]{10,250}[\.\?\!]",
            r"fakeout[^\.\?\!]{10,250}[\.\?\!]",
            r"quasimodo[^\.\?\!]{10,250}[\.\?\!]",
            r"storyline[^\.\?\!]{10,250}[\.\?\!]",
            r"trendline[^\.\?\!]{10,250}[\.\?\!]",
            r"entry[^\.\?\!]{10,250}[\.\?\!]"
        ]
        combined = re.compile("|".join(patterns), re.IGNORECASE)
        matches = combined.findall(text)
        print(f"Total matches found: {len(matches)}")
        for m in matches[:8]:
            print(" -> ", m.strip().replace("\n", " "))

extract_alchemist_core()
