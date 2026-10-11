# 1. Quitar Wall Street 30 de MALAYSIAN_SNR_PRUNED_INFO en dashboard/realtime_dashboard.py
path_dash = 'dashboard/realtime_dashboard.py'
with open(path_dash, 'r', encoding='utf-8') as f:
    dash = f.read().replace('\r\n', '\n')

old_line = '    "Wall Street 30": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 23.1%, -1.50R (-$150 USD). Momentum no apto para reversión pasiva; derivado a ORB New York.",\n'
if old_line in dash:
    dash = dash.replace(old_line, '')
    with open(path_dash, 'w', encoding='utf-8') as f:
        f.write(dash)
    print("Wall Street 30 removido de MALAYSIAN_SNR_PRUNED_INFO")

# 2. Asegurar Jump 25 Index en WINNERS_DATA en dashboard/strategy_bases_page.py
path_bases = 'dashboard/strategy_bases_page.py'
with open(path_bases, 'r', encoding='utf-8') as f:
    bases = f.read().replace('\r\n', '\n')

if "Jump 25 Index" not in bases:
    jump_25_entry = '        { rank: 8, symbol: "Jump 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 447, win_rate: 37.6, tp1: 168, tp2: 101, tp3: 35, tp4: 11, be: 44, pnl: 3583.25, status: "Activo / Alta Precisión" },\n'
    target = '{ rank: 1, symbol: "Boom 1000 Index"'
    bases = bases.replace(target, jump_25_entry + '        ' + target)
    with open(path_bases, 'w', encoding='utf-8') as f:
        f.write(bases)
    print("Jump 25 Index agregado a strategy_bases_page.py")
else:
    print("Jump 25 Index ya está presente")

# 3. También asegurar Wall Street 30 en app/main.py symbols para MALAYSIAN_SNR
path_main = 'app/main.py'
with open(path_main, 'r', encoding='utf-8') as f:
    main = f.read().replace('\r\n', '\n')

# Asegurar que Wall Street 30 esté en symbols y no en pruned_symbols
if '"Wall Street 30",\n' in main and 'pruned_symbols' in main:
    main = main.replace('            "US Tech 100", "Wall Street 30", "US SP 500",\n', '            "US Tech 100", "US SP 500",\n')
    if '"Wall Street 30",' not in main.split('"symbols": [')[1].split(']')[0]:
        main = main.replace('"XAUUSD",\n', '"XAUUSD",\n            "Wall Street 30",\n')
    with open(path_main, 'w', encoding='utf-8') as f:
        f.write(main)
    print("Wall Street 30 ajustado en app/main.py")

# 4. Asegurar Wall Street 30 en tools/persist_instruments_pruning.py
path_persist = 'tools/persist_instruments_pruning.py'
with open(path_persist, 'r', encoding='utf-8') as f:
    persist = f.read().replace('\r\n', '\n')

if '"Wall Street 30"' not in persist.split('"MALAYSIAN_SNR": [')[1].split(']')[0]:
    persist = persist.replace('"Boom 1000 Index",', '"Wall Street 30",              # Activo en observación\n        "Boom 1000 Index",')
    with open(path_persist, 'w', encoding='utf-8') as f:
        f.write(persist)
    print("Wall Street 30 agregado a persist_instruments_pruning.py")
