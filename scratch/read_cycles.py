with open("storage/logs/bots/orb.log", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Let's find cycles 0398, 0408, 0418, 0428, 0438 in orb.log
for cycle_id in ["0398", "0408", "0418", "0428", "0438"]:
    target = f"CICLO #{cycle_id}"
    idx = text.find(target)
    if idx != -1:
        end_idx = text.find("CICLO #", idx + len(target))
        print("=" * 80)
        print(target)
        cycle_chunk = text[idx:end_idx if end_idx != -1 else idx + 2000]
        # print lines mentioning US SP 500 or US Tech 100
        for l in cycle_chunk.split("\n"):
            if any(k in l for k in ["US SP 500", "US Tech 100", "Motivo", "Confirmaciones"]):
                print(" ", l)
