from pathlib import Path
import os

target_file = Path("app") / "main.py"
tmp_file = Path("app") / "main.py.tmp"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Quitar Vol over Boom/Crash 550 de BOT_PROFILES["MALAYSIAN_SNR"]
t1 = """            "Step Index 500",
            "Vol over Boom 550",
            "Vol over Crash 550",
            "VolSwitch High Vol Index","""

r1 = """            "Step Index 500",
            "VolSwitch High Vol Index","""

# 2. Blindar resolución de universo en MALAYSIAN_SNR
t2 = """    elif profile == "MALAYSIAN_SNR":
        universe = sorted(set(spec.get("symbols", [])) | set(spec.get("pruned_symbols", [])))"""

r2 = """    elif profile == "MALAYSIAN_SNR":
        candidates = sorted(set(spec.get("symbols", [])) | set(spec.get("pruned_symbols", [])))
        unlisted = {"Vol over Boom 550", "Vol over Crash 550"}
        universe = []
        for sym in candidates:
            if sym in unlisted:
                continue
            try:
                if provider.get_symbol_info(sym):
                    universe.append(sym)
            except Exception:
                pass
        universe = sorted(set(universe or [s for s in candidates if s not in unlisted]))"""

def do_rep(txt, tgt, rep, name):
    if tgt in txt:
        print(f"{name} found with LF")
        return txt.replace(tgt, rep, 1)
    tgt_c = tgt.replace("\n", "\r\n")
    rep_c = rep.replace("\n", "\r\n")
    if tgt_c in txt:
        print(f"{name} found with CRLF")
        return txt.replace(tgt_c, rep_c, 1)
    print(f"ERROR: {name} NOT found")
    return txt

content = do_rep(content, t1, r1, "t1")
content = do_rep(content, t2, r2, "t2")

with open(tmp_file, "w", encoding="utf-8") as f:
    f.write(content)

os.replace(tmp_file, target_file)
print("app/main.py updated successfully with MSNR fix.")
