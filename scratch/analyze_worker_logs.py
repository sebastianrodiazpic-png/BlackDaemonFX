import os

workers = ['boom', 'crash', 'volatility_1', 'step', 'jump', 'malaysian_snr', 'ict', 'forex_1']

for w in workers:
    logfile = f'storage/logs/bots/{w}.log'
    if not os.path.exists(logfile):
        continue
    print(f"\n==================== WORKER: {w.upper()} ====================")
    with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Count frequency of reasons in the last 200 lines
    reasons = {}
    signals = []
    hc_evals = []
    for l in lines[-200:]:
        l_str = l.strip()
        if 'Motivo:' in l_str or 'REASON:' in l_str:
            reasons[l_str] = reasons.get(l_str, 0) + 1
        if 'SIGNAL' in l_str or 'ORDER' in l_str or 'EXECUTE' in l_str or 'TRIGGER' in l_str:
            signals.append(l_str)
        if 'HUMAN_CRITERIA' in l_str or 'criterio humano' in l_str.lower():
            hc_evals.append(l_str)

    print(f"Top reject reasons in last 200 checks for {w.upper()}:")
    for r, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  [{count}x] {r}")
    
    if signals:
        print(f"Signals/Triggers in last 200 lines ({len(signals)}):")
        for s in signals[-5:]:
            print(f"  {s}")
    else:
        print("No execution triggers in last 200 lines.")
    
    if hc_evals:
        print(f"Human criteria mentions ({len(hc_evals)}):")
        for h in hc_evals[-5:]:
            print(f"  {h}")
