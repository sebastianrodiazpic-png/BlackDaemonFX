import config.ict_instrument_policy as ip

active = ip.ict_active_symbols('MALAYSIAN_SNR')
print(f"Count MSNR active: {len(active)}")
print("MSNR active:", active)
for s in ['Vol over Boom 550', 'Vol over Crash 550', 'Jump 75 Index', 'Step Index 200', 'Step Index 400', 'Step Index 500']:
    print(f"{s}: Active={s in active}, PruneReason={repr(ip.preventive_prune_reason(s, 'MALAYSIAN_SNR'))}")

for s in ['Volatility 10 Index', 'Volatility 50 (1s) Index', 'Crash 900 Index', 'Step Index', 'GBPJPY']:
    print(f"{s} (Pruned): Active={s in active}, PruneReason={repr(ip.preventive_prune_reason(s, 'MALAYSIAN_SNR'))}")
