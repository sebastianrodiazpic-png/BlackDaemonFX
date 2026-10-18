import glob
import re

files = [
    'scratch/transcript_J3qTJefkD-A.txt',
    'scratch/transcript_zgpstRvSwhk.txt',
    'scratch/transcript_GWn5LiOSBlA.txt',
    'scratch/transcript_f8sSwcP9KwQ.txt',
    'scratch/transcript_Iq_MxtYvRww.txt',
    'scratch/transcript_QFvkAZjUnUE.txt',
    'scratch/transcript_R3sAS1J3_fE.txt',
    'scratch/transcript_lGChZzNybGY.txt',
    'scratch/transcript_EO8odUZNdjc.txt'
]

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0].strip()
    url = lines[1].strip()
    content = " ".join([l.strip() for l in lines[3:]])
    print("=" * 60)
    print(header)
    print(url)
    print(f"Total lines: {len(lines)}, total chars: {len(content)}")
    # Print sample text / key keywords
    keywords = ["temporalidad", "minuto", "fvg", "fair value", "order block", "killzone", "londres", "nueva york", "sesion", "entrada", "stop", "take profit", "ratio", "winrate", "oro", "silver bullet", "amd", "judas", "sweep", "barrido", "mss", "choch", "bos"]
    found_kw = {}
    for kw in keywords:
        matches = len(re.findall(re.escape(kw), content, re.IGNORECASE))
        if matches > 0:
            found_kw[kw] = matches
    print("Keywords found:", found_kw)
