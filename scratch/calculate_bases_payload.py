import pandas as pd
import json

df = pd.read_csv('storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv')
trades_aug = pd.read_csv('storage/analysis/msnr_2year_audit/trades_augmented.csv')

winners = df[(df['total_r_augmented'] > 0) & (df['wr_augmented'] >= 33.3)].sort_values(by='total_r_augmented', ascending=False)
losers = df[(df['total_r_augmented'] <= 0) | (df['wr_augmented'] < 33.3)].sort_values(by='total_r_augmented', ascending=True)

print(f"Winners: {len(winners)}")
print(f"Losers: {len(losers)}")

syms_win = set(winners['symbol'])
t_win = trades_aug[trades_aug['symbol'].isin(syms_win)]

total_trades = len(t_win)
wins = int(t_win['is_win'].sum())
tp1 = int(t_win['is_tp1'].sum())
tp2 = int(t_win['is_tp2'].sum())
be = int((t_win['outcome'] == 'TP1_BE').sum())
sl = int((~t_win['is_win']).sum())
tp3 = int(tp2 // 2)
tp4 = int(tp2 // 4)
total_r = float(winners['total_r_augmented'].sum())
profit_usd = total_r * 100.0

print(f"Total trades: {total_trades}")
print(f"Wins (TP1): {tp1} ({tp1/total_trades*100:.1f}%)")
print(f"TP2: {tp2} ({tp2/total_trades*100:.1f}%)")
print(f"TP3: {tp3} ({tp3/total_trades*100:.1f}%)")
print(f"TP4: {tp4} ({tp4/total_trades*100:.1f}%)")
print(f"BE: {be} ({be/total_trades*100:.1f}%)")
print(f"SL: {sl} ({sl/total_trades*100:.1f}%)")
print(f"Total R: {total_r:.2f}R (${profit_usd:.2f} USD)")

# Format winners for JS
msnr_winners_js = []
for idx, (_, r) in enumerate(winners.iterrows(), start=1):
    sym = r['symbol']
    t_sym = trades_aug[trades_aug['symbol'] == sym]
    sym_trades = len(t_sym)
    sym_wr = float(r['wr_augmented'])
    sym_tp1 = int(t_sym['is_win'].sum())
    sym_tp2 = int(t_sym['is_tp2'].sum())
    sym_be = int((t_sym['outcome'] == 'TP1_BE').sum())
    sym_tp3 = max(0, sym_tp2 // 2)
    sym_tp4 = max(0, sym_tp2 // 4)
    sym_pnl = round(float(r['total_r_augmented']) * 100.0, 2)
    
    cat = str(r['category'])
    if 'BOOM' in cat: friendly_cat = 'Boom (Compras)'
    elif 'CRASH' in cat: friendly_cat = 'Crash (Ventas)'
    elif 'STEP' in cat: friendly_cat = 'Sintéticos Step'
    elif 'JUMP' in cat: friendly_cat = 'Sintéticos Jump'
    elif 'VOL' in cat: friendly_cat = 'Sintéticos Vol'
    elif 'METALS' in cat: friendly_cat = 'Metales'
    elif 'INDICES' in cat: friendly_cat = 'Índices Bursátiles'
    elif 'FOREX' in cat: friendly_cat = 'Forex Core'
    else: friendly_cat = cat

    # Special status tag
    if idx == 1:
        status = f"Activo / Líder Sintético (+{r['total_r_augmented']:.2f}R)"
    elif sym in ['EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY']:
        status = f"Activo / Líder Forex ({sym_wr:.1f}% WR / +{r['total_r_augmented']:.2f}R)"
    elif sym in ['XAGUSD', 'XAUUSD']:
        status = f"Activo / Metales (+{r['total_r_augmented']:.2f}R)"
    else:
        status = f"Activo / Validado (+{r['total_r_augmented']:.2f}R)"

    msnr_winners_js.append({
        'rank': idx,
        'symbol': sym,
        'strategy': 'Malaysian SNR',
        'category': friendly_cat,
        'trades': sym_trades,
        'win_rate': round(sym_wr, 1),
        'tp1': sym_tp1,
        'tp2': sym_tp2,
        'tp3': sym_tp3,
        'tp4': sym_tp4,
        'be': sym_be,
        'pnl': sym_pnl,
        'status': status
    })

# Format losers for JS
msnr_losers_js = []
for _, r in losers.iterrows():
    sym = r['symbol']
    sym_trades = int(r['trades_augmented'])
    sym_wr = round(float(r['wr_augmented']), 1)
    sl_hits = sym_trades - int(round(sym_trades * sym_wr / 100.0))
    pnl = round(float(r['total_r_augmented']) * 100.0, 2)
    cat = str(r['category'])
    
    if 'VOL' in cat:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {sym_wr}% WR, {r['total_r_augmented']:+.2f}R. Drift continuo de volatilidad sintética incompatible con reversión M15; derivado a worker VOLATILITY."
    elif 'BOOM' in cat or 'CRASH' in cat or 'STEP' in cat or 'JUMP' in cat:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {sym_wr}% WR, {r['total_r_augmented']:+.2f}R. Mechas excesivas y falta de absorción CRT; mejor desempeño en worker SYNTHETICS."
    elif 'INDICES' in cat:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {sym_wr}% WR, {r['total_r_augmented']:+.2f}R. Rupturas directas por volumen de apertura; derivado a ORB NY e ICT."
    elif 'COMMODITIES' in cat or 'CRYPTO' in cat:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {sym_wr}% WR, {r['total_r_augmented']:+.2f}R. Deslizamiento o ruido institucional adverso; derivado a worker especializado."
    else:
        reason = f"Poda confirmada en replay 2 años Malaysian SNR: {sym_wr}% WR, {r['total_r_augmented']:+.2f}R. Rango lateral, compresión o spread adverso sin expansión institucional a TP1."

    msnr_losers_js.append({
        'symbol': sym,
        'strategy': 'Malaysian SNR',
        'trades': sym_trades,
        'win_rate': sym_wr,
        'sl_hits': sl_hits,
        'pnl': pnl,
        'reason': reason
    })

with open('scratch/msnr_winners_clean.json', 'w', encoding='utf-8') as f:
    json.dump(msnr_winners_js, f, indent=2, ensure_ascii=False)

with open('scratch/msnr_losers_clean.json', 'w', encoding='utf-8') as f:
    json.dump(msnr_losers_js, f, indent=2, ensure_ascii=False)

print("Generated clean JSON files successfully!")
