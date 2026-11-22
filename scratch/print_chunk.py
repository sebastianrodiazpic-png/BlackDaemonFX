with open("storage/logs/bots/orb.log", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

idx = text.rfind("CICLO #0408")
if idx != -1:
    end_idx = text.find("CICLO #", idx + 20)
    print(text[idx:end_idx if end_idx != -1 else idx + 2000])
