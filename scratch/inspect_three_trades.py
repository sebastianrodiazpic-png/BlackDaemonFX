import os

tickets = {
    "4791625098": "HF Vol 75 (BUY MSNR)",
    "4791632115": "Vol 5 (SELL ICT)",
    "4791658071": "Crash 900 (SELL MSNR)",
}

# Also partials
partials = ["47916250", "47916321", "47916580"]

logs = [
    "storage/logs/bots/volatility_1.log",
    "storage/logs/bots/volatility_2.log",
    "storage/logs/bots/volatility_3.log",
    "storage/logs/bots/crash.log",
    "storage/logs/bots/ict.log",
    "storage/logs/bots/indicesb_snr.log",
]

for p in logs:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    found_lines = []
    for idx, line in enumerate(lines):
        for part in partials:
            if part in line:
                # Capture context around opening or closing
                if any(w in line.lower() for w in ["orden", "abierta", "entrada", "sl", "tp", "cierre", "closed", "loss", "stop", "evaluando", "posicion"]):
                    found_lines.append((idx + 1, line.strip()))
    
    if found_lines:
        print(f"\n=================== LOG: {p} ({len(found_lines)} hits) ===================")
        # Show first 5 and last 10 hits
        sample = found_lines[:5] + found_lines[-8:] if len(found_lines) > 13 else found_lines
        for lno, text in sample:
            print(f"[{lno}] {text[:160]}")
