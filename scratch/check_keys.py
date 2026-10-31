with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

keys = [
    'msnr_jump', 'msnr_step', 'msnr_volatility', 'msnr_indices', 'msnr_boom', 'msnr_crash', 'msnr_forex', 'msnr_metals', 'msnr_pruned',
    'night_indices', 'drift_switch', 'rsi2_us_indices', 'carry_fx_g10',
    'gold_cuartos_xauusd', 'gold_cuartos_micro_xauusd', 'gold_cuartos_xagusd', 'gold_cuartos_micro_xagusd',
]

for k in keys:
    print(f'{k}: {text.count(k)}')
