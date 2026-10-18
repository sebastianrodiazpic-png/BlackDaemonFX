import re

files = [
    ('J3qTJefkD-A', 'scratch/transcript_J3qTJefkD-A.txt'),
    ('zgpstRvSwhk', 'scratch/transcript_zgpstRvSwhk.txt'),
    ('GWn5LiOSBlA', 'scratch/transcript_GWn5LiOSBlA.txt'),
    ('f8sSwcP9KwQ', 'scratch/transcript_f8sSwcP9KwQ.txt'),
    ('Iq_MxtYvRww', 'scratch/transcript_Iq_MxtYvRww.txt'),
    ('QFvkAZjUnUE', 'scratch/transcript_QFvkAZjUnUE.txt'),
    ('R3sAS1J3_fE', 'scratch/transcript_R3sAS1J3_fE.txt'),
    ('lGChZzNybGY', 'scratch/transcript_lGChZzNybGY.txt'),
    ('EO8odUZNdjc', 'scratch/transcript_EO8odUZNdjc.txt')
]

for vid, fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
    
    print("=" * 80)
    print(f"FILE: {fpath}")
    lines = text.split("\n")
    print(f"TITLE & URL: {lines[0]} | {lines[1]}")
    
    # Let's extract blocks of text with timestamps
    # Print every 20th line or search for key parts
    print("\n--- RESUMEN DE SEGMENTOS CLAVE ---")
    
    # We can scan for sentences mentioning rules, steps, paso, temporalidad, estrategia, regla, etc.
    key_lines = []
    for line in lines[2:]:
        if any(term in line.lower() for term in [
            "paso 1", "paso 2", "paso 3", "paso 4", "primer paso", "segundo paso", "tercer paso",
            "regla", "estrategia", "temporalidad", "minutos", "horas", "fvg", "order block",
            "liquidez", "sesion", "killzone", "nueva york", "londres", "asia", "horario",
            "stop loss", "take profit", "ratio", "entrada", "gatillo", "desplazamiento",
            "ruptura", "barrido", "mitigacion", "inversion", "silver bullet", "amd"
        ]):
            key_lines.append(line)
            
    print(f"Total key lines found: {len(key_lines)}")
    for kl in key_lines[:35]: # show first 35
        print(kl)
    if len(key_lines) > 35:
        print(f"... and {len(key_lines) - 35} more key lines")
