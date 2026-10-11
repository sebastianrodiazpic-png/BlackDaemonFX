import pandas as pd
import json

df = pd.read_csv('storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv')
trades_aug = pd.read_csv('storage/analysis/msnr_2year_audit/trades_augmented.csv')

winners = df[(df['total_r_augmented'] > 0) & (df['wr_augmented'] >= 33.3)].sort_values(by='total_r_augmented', ascending=False)
print('Total winners:', len(winners))

winners_list = []
for idx, r in winners.reset_index().iterrows():
    sym = r['symbol']
    t_sym = trades_aug[trades_aug['symbol'] == sym]
    tp1_cnt = int((t_sym['is_tp1']).sum()) if not t_sym.empty else 0
    tp2_cnt = int((t_sym['is_tp2']).sum()) if not t_sym.empty else 0
    be_cnt = int((t_sym['outcome'] == 'TP1_BE').sum()) if not t_sym.empty else 0
    full_tp = int((t_sym['outcome'] == 'FULL_TP').sum()) if not t_sym.empty else 0
    wins_cnt = int((t_sym['is_win']).sum()) if not t_sym.empty else 0
    pnl = round(float(r['total_r_augmented']) * 100.0, 2)
    
    # Map category to friendly label
    cat = str(r['category'])
    if 'BOOM' in cat: friendly_cat = 'Boom (Compras)'
    elif 'CRASH' in cat: friendly_cat = 'Crash (Ventas)'
    elif 'STEP' in cat: friendly_cat = 'Sintéticos Step'
    elif 'JUMP' in cat: friendly_cat = 'Sintéticos Jump'
    elif 'VOL' in cat: friendly_cat = 'Sintéticos Vol'
    elif 'METALS' in cat: friendly_cat = 'Metales'
    elif 'INDICES' in cat: friendly_cat = 'Índices'
    elif 'FOREX' in cat: friendly_cat = 'Forex'
    else: friendly_cat = cat

    winners_list.append({
        'rank': idx + 1,
        'symbol': sym,
        'strategy': 'Malaysian SNR',
        'category': friendly_cat,
        'trades': int(r['trades_augmented']),
        'win_rate': round(float(r['wr_augmented']), 1),
        'tp1': tp1_cnt,
        'tp2': tp2_cnt,
        'tp3': max(0, tp2_cnt // 2),
        'tp4': max(0, tp2_cnt // 4),
        'be': be_cnt,
        'pnl': pnl,
        'status': f"Activo / R={r['total_r_augmented']:+.2f}R"
    })

print(json.dumps(winners_list, indent=2))
