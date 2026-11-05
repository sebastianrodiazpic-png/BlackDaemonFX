import json

with open('storage/dashboard/last_state.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

sp = d.get('selection_profiles', {}).get('SYNTHETICS', [])
for s in ['Volatility Boom 550 Index', 'Volatility Crash 550 Index', 'Vol over Boom 550', 'Vol over Crash 550']:
    if s not in sp:
        sp.append(s)

d['selection_profiles']['SYNTHETICS'] = sp

sel_syms = d.get('selected_symbols', [])
for s in ['Volatility Boom 550 Index', 'Volatility Crash 550 Index']:
    if s not in sel_syms:
        sel_syms.append(s)
d['selected_symbols'] = sel_syms

with open('storage/dashboard/last_state.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('Updated storage/dashboard/last_state.json')
