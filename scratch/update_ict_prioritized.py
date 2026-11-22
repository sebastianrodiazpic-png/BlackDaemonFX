with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '"ICT": [' in line:
        start_idx = i
    if start_idx is not None and '"COMMODITIES_SNR": [' in line:
        for j in range(i-1, start_idx, -1):
            if '],' in lines[j]:
                end_idx = j
                break
        break

print(f'ICT start: {start_idx+1}, end: {end_idx+1}')

active_ict = [
    "XAUUSD",
    "XAUUSDmicro",
    "BTCUSD",
    "BTCUSDmicro",
    "US Oil",
    "UK Brent Oil",
    "Wall Street 30",
    "US Tech 100",
    "Germany 40",
]

replacement = '    "ICT": [\n'
for s in active_ict:
    replacement += f'        "{s}",\n'
replacement += '    ],\n'

lines[start_idx:end_idx+1] = [replacement]

with open('dashboard/realtime_dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Successfully updated DEFAULT_PRIORITIZED_SYMBOLS[ICT]')
