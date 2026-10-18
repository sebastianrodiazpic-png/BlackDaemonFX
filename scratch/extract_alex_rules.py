for vid in ['J3qTJefkD-A', 'zgpstRvSwhk']:
    fpath = f'scratch/transcript_{vid}.txt'
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print("=" * 80)
    print(f"DETAILS FOR {vid}")
    for i, line in enumerate(lines):
        # Look for hours, rules, entry details
        if any(w in line.lower() for w in ["paso", "horario", "hora", "minuto", "regla", "stop", "take profit", "ratio", "order block", "fvg", "5 minutos", "1 minuto", "15 minutos"]):
            print(f"L{i}: {line.strip()}")
