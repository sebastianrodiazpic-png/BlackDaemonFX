import json, re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', content, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    multi = [d for d in data if d.get('strategy') == 'MultiStrategia']
    
    # Check JUMP
    jump = [d for d in multi if 'JUMP' in d.get('category', '') or 'Jump' in d['symbol']]
    print("--- JUMP ENTRIES ---")
    for d in jump:
        print(d)

    # Check BOOM / CRASH
    boom_crash = [d for d in multi if any(w in d.get('category', '') for w in ['BOOM', 'CRASH']) or any(w in d['symbol'] for w in ['Boom', 'Crash'])]
    print("\n--- BOOM & CRASH ENTRIES (first 5) ---")
    for d in boom_crash[:5]:
        print(d)

    # Check VOLATILITY
    vol = [d for d in multi if 'VOLATILITY' in d.get('category', '') or 'Volatility' in d['symbol']]
    print("\n--- VOLATILITY ENTRIES (first 5) ---")
    for d in vol[:5]:
        print(d)

    # Check STEP
    step = [d for d in multi if 'STEP' in d.get('category', '') or 'Step' in d['symbol']]
    print("\n--- STEP ENTRIES ---")
    for d in step:
        print(d)

    # Check REAL MARKETS
    real = [d for d in multi if any(w in d.get('category', '') for w in ['INDICESB', 'Materias Primas'])]
    print("\n--- REAL MARKETS (INDICES, COMMODITIES, CRYPTO) ---")
    for d in real:
        print(f"{d['symbol']} ({d.get('category')}): trades={d['trades']}, wr={d['win_rate']}, pnl={d['pnl']}")

    # Check FOREX
    forex = [d for d in multi if 'Forex' in d.get('category', '')]
    print(f"\n--- FOREX ({len(forex)} entries, first 5) ---")
    for d in forex[:5]:
        print(f"{d['symbol']} ({d.get('category')}): trades={d['trades']}, wr={d['win_rate']}, pnl={d['pnl']}")
