for part, fpath in [("Parte 2", "scratch/transcripts/dGv5zwrK9vY.txt"), 
                     ("Parte 3", "scratch/transcripts/YmK59hyKX0U.txt"), 
                     ("Parte 4", "scratch/transcripts/qT-TWP2sUgA.txt"), 
                     ("Parte 5", "scratch/transcripts/odvBj8IpZ74.txt")]:
    with open(fpath, "r", encoding="utf-8") as f:
        t = f.read()
    print(f"\n--- NESTOR SANTOS {part} ---")
    for line in t.split('.'):
        if any(k in line.lower() for k in ["sbr", "rbs", "semanal", "diario", "entrada", "stop", "take profit", "confirmaci"]):
            print(" *", line.strip())
