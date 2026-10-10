import os
import glob
import re

def summarize_file(fname):
    with open(fname, "r", encoding="utf-8") as f:
        text = f.read()
    
    title_m = re.search(r"Title:\s*(.+)", text)
    author_m = re.search(r"Author:\s*(.+)", text)
    title = title_m.group(1) if title_m else fname
    author = author_m.group(1) if author_m else ""
    
    sentences = re.split(r'(?<=[.?!])\s+', text)
    
    extracted = []
    patterns = [
        r"soporte", r"resistencia", r"fresh", r"ruptura", r"retest", r"quasimodo",
        r"c-trade", r"c trade", r"v-trade", r"h1", r"h4", r"m15", r"m5", r"m1",
        r"temporalidad", r"envolvente", r"engulfing", r"stop loss", r"take profit",
        r"línea", r"cuerpo", r"mecha", r"punto a", r"punto v", r"patrón a", r"patrón v"
    ]
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    
    for s in sentences:
        if regex.search(s) and 30 < len(s) < 300:
            extracted.append(s.strip())
            
    return title, author, extracted

groups = {
    "Albert": ["scratch/transcripts/L_vwb_jf6og.txt", "scratch/transcripts/wDK7qO4mf-E.txt"],
    "Pol Castella": ["scratch/transcripts/sTRxqo4EwPU.txt"],
    "Nestor Santos": ["scratch/transcripts/1x57n_5iRsU.txt", "scratch/transcripts/dGv5zwrK9vY.txt", "scratch/transcripts/YmK59hyKX0U.txt", "scratch/transcripts/qT-TWP2sUgA.txt", "scratch/transcripts/odvBj8IpZ74.txt"],
    "MBA": ["scratch/transcripts/xYlpAr5pwXg.txt", "scratch/transcripts/9ZNPazzfDcU.txt", "scratch/transcripts/5oTQEdSV7p0.txt"],
    "MR.R (Alchemist)": ["scratch/transcripts/lqlkspVKt7s.txt", "scratch/transcripts/CH9iW5caHHk.txt", "scratch/transcripts/QbyhRLF53RI.txt", "scratch/transcripts/XvXWWv3gD8k.txt", "scratch/transcripts/FM0XkqUIrAI.txt", "scratch/transcripts/sxn-jP9St9I.txt"]
}

with open("scratch/summaries_out_utf8.txt", "w", encoding="utf-8") as out:
    for group_name, file_list in groups.items():
        out.write(f"\n==================== GROUP: {group_name} ====================\n")
        for fpath in file_list:
            if os.path.exists(fpath):
                t, a, extr = summarize_file(fpath)
                out.write(f"\n--- {t} ({a}) ---\n")
                for i, item in enumerate(extr[:10], 1):
                    out.write(f"  {i}. {item}\n")

print("Done writing scratch/summaries_out_utf8.txt")
