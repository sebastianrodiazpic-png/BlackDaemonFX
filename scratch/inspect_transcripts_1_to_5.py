files = [
    ('J3qTJefkD-A', 'scratch/transcript_J3qTJefkD-A.txt'),
    ('zgpstRvSwhk', 'scratch/transcript_zgpstRvSwhk.txt'),
    ('GWn5LiOSBlA', 'scratch/transcript_GWn5LiOSBlA.txt'),
    ('f8sSwcP9KwQ', 'scratch/transcript_f8sSwcP9KwQ.txt'),
    ('Iq_MxtYvRww', 'scratch/transcript_Iq_MxtYvRww.txt'),
]

for vid, fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    print("=" * 80)
    print(f"ANALYZING: {vid}")
    lines = text.split("\n")
    print(lines[0])
    
    # print all lines where time is between 00:00 and 06:00 or where rules are stated
    for i, line in enumerate(lines[2:]):
        # find mentions of steps, strategy, entry, rules
        l_low = line.lower()
        if any(w in l_low for w in [
            "estrategia", "paso", "minuto", "temporalidad", "hora", "regla", "fvg", "order",
            "entrada", "stop", "take profit", "ratio", "oro", "sesion", "killzone", "londres", "nueva york",
            "silver bullet", "bias", "tendencia", "barrido", "liquidez", "rompimiento", "choch", "mss"
        ]):
            print(line)
