import json

with open("storage/dashboard/last_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

catalog = state.get("instrument_catalog") or []
all_symbols = set()
for g in catalog:
    for s in g.get("symbols") or []:
        all_symbols.add(s)

print("Símbolos en el catálogo con 'crash':")
crash_syms = sorted([s for s in all_symbols if "crash" in s.lower()])
for s in crash_syms:
    print(" -", s)
