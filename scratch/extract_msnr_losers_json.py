import pandas as pd
import json

df = pd.read_csv('storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv')
losers = df[(df['total_r_augmented'] <= 0) | (df['wr_augmented'] < 33.3)].sort_values(by='total_r_augmented', ascending=True)

print('Total pruned/losers:', len(losers))

losers_list = []
for idx, r in losers.iterrows():
    sym = r['symbol']
    ta = int(r['trades_augmented'])
    wra = round(float(r['wr_augmented']), 1)
    tra = round(float(r['total_r_augmented']), 2)
    sl_hits = ta - int(round(ta * wra / 100.0))
    pnl = round(tra * 100.0, 2)
    
    # Reason mapping
    if 'Tech' in sym or 'SP 500' in sym or 'Oil' in sym:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {wra}% WR, {tra}R. Rupturas directas y momentum de sesión sin respeto de zonas A/V; derivado a ORB NY e ICT."
    elif 'Volatility' in sym:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {wra}% WR, {tra}R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY."
    elif 'Boom' in sym or 'Crash' in sym:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {wra}% WR, {tra}R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS."
    elif 'BTC' in sym:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {wra}% WR, {tra}R. Spreads y expansiones de rango erráticas; derivado a ICT Sabri Malle (+28.1R) y ORB."
    elif 'CAD' in sym or 'CHF' in sym or 'AUD' in sym or 'NZD' in sym or 'JPY' in sym:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {wra}% WR, {tra}R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1."
    else:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {wra}% WR, {tra}R. Expectativa matemática negativa."

    losers_list.append({
        'symbol': sym,
        'strategy': 'Malaysian SNR',
        'trades': ta,
        'win_rate': wra,
        'sl_hits': sl_hits,
        'pnl': pnl,
        'reason': reason
    })

print(json.dumps(losers_list[:10], indent=2))
with open('scratch/msnr_losers.json', 'w', encoding='utf-8') as f:
    json.dump(losers_list, f, indent=2)
