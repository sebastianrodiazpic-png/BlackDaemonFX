files = [
    ('f8sSwcP9KwQ', 'Toni Maura'),
    ('QFvkAZjUnUE', 'Fede Esses'),
    ('R3sAS1J3_fE', 'Sabri Malle 500e'),
    ('lGChZzNybGY', 'Sabri Malle 1000e 3 pasos'),
    ('EO8odUZNdjc', 'Sabri Malle Order Blocks')
]

for vid, label in files:
    fpath = f'scratch/transcript_{vid}.txt'
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print("=" * 80)
    print(f"VIDEO: {vid} - {label}")
    # find lines mentioning hours, steps, timeframes
    for i, line in enumerate(lines):
        l_low = line.lower()
        if any(w in l_low for w in [
            "paso 1", "paso 2", "paso 3", "primer paso", "segundo paso", "tercer paso",
            "horario", "hora de", "sesion", "killzone", "11 a 12", "silver bullet",
            "order block cinco estrellas", "fvg", "ratio", "stop loss", "tp", "take profit",
            "asian", "londres", "nueva york"
        ]):
            print(f"  {line.strip()}")
