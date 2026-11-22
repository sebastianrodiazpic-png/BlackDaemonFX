with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '"SYNTHETICS": [' in line:
        start_idx = i
    if start_idx is not None and '"FOREX": [' in line:
        for j in range(i-1, start_idx, -1):
            if '],' in lines[j]:
                end_idx = j
                break
        break

print(f'start: {start_idx+1}, end: {end_idx+1}')

active_synths = [
    "Jump 10 Index",
    "Jump 25 Index",
    "Jump 50 Index",
    "Jump 75 Index",
    "Jump 100 Index",
    "Boom 300 Index",
    "Boom 500 Index",
    "Boom 600 Index",
    "Boom 900 Index",
    "Boom 1000 Index",
    "Crash 500 Index",
    "Crash 900 Index",
    "Crash 1000 Index",
    "Volatility 5 Index",
    "Volatility 10 Index",
    "Volatility 50 Index",
    "Volatility 75 Index",
    "Volatility 90 Index",
    "Volatility 100 Index",
    "Volatility 5 (1s) Index",
    "Volatility 10 (1s) Index",
    "Volatility 15 (1s) Index",
    "Volatility 25 (1s) Index",
    "Volatility 30 (1s) Index",
    "Volatility 75 (1s) Index",
    "Volatility 90 (1s) Index",
    "Volatility 100 (1s) Index",
    "Volatility 150 (1s) Index",
    "Volatility 250 (1s) Index",
    "Step Index 400",
    "Step Index 500",
]

replacement = '    "SYNTHETICS": [\n'
for s in active_synths:
    replacement += f'        "{s}",\n'
replacement += '    ],\n'

lines[start_idx:end_idx+1] = [replacement]

with open('dashboard/realtime_dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Successfully updated DEFAULT_PRIORITIZED_SYMBOLS[SYNTHETICS]')
