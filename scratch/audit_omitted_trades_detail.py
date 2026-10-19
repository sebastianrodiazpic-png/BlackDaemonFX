import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path('.').resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from scratch.test_subfamily_and_filter_improvements import (
    evaluate_variant, get_subfamily
)

csv_path = PROJECT_ROOT / 'scratch' / 'msnr_complete_23_faithful_trades_clean.csv'
df = pd.read_csv(csv_path)
df['time'] = pd.to_datetime(df['time'], utc=True)
df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
df['subfamily'] = df['symbol'].apply(get_subfamily)
df = df.sort_values('time').reset_index(drop=True)

def f_v4(d):
    return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

def f_comb_body50(d):
    c_mf = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
    c_s = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5) & (d['body_ratio'] >= 0.50)
    return d[c_mf | c_s]

res_v4 = evaluate_variant(df, f_v4, cap=1, n_folds=4)
res_exp = evaluate_variant(df, f_comb_body50, cap=1, n_folds=4)

t_v4 = res_v4['trades'].copy()
t_exp = res_exp['trades'].copy()

v4_keys = set(zip(t_v4['symbol'], t_v4['time'].astype(str)))
exp_keys = set(zip(t_exp['symbol'], t_exp['time'].astype(str)))

omitted = t_v4[~t_v4.apply(lambda r: (r['symbol'], str(r['time'])) in exp_keys, axis=1)]
new_in_exp = t_exp[~t_exp.apply(lambda r: (r['symbol'], str(r['time'])) in v4_keys, axis=1)]

print(f"Total trades in V4: {len(t_v4)}, in Exp: {len(t_exp)}")
print(f"Trades in V4 but NOT in Exp (N={len(omitted)}):")
for idx, r in omitted.iterrows():
    t_str = str(r['time'])[:19]
    print(f"  * {r['symbol']:20s} | {t_str} | {r['outcome']:8s} | RR: {r['rr']:+5.2f} R | ADX: {r['adx']:4.1f} | ATR: {r['risk_atr']:4.2f} | Body: {r['body_ratio']:4.2f}")

print(f"\nSum of omitted PnL: {omitted['rr'].sum():+.2f} R")

losses_avoided = omitted[omitted['rr'] < 0]
gains_omitted = omitted[omitted['rr'] > 0]
print(f"  Pérdidas evitadas: {len(losses_avoided)} ops -> {losses_avoided['rr'].sum():+.2f} R (ahorro contrafactual)")
print(f"  Ganancias omitidas: {len(gains_omitted)} ops -> {gains_omitted['rr'].sum():+.2f} R (costo de oportunidad)")
print(f"  Balance neto de filtros: {losses_avoided['rr'].abs().sum() - gains_omitted['rr'].sum():+.2f} R neto")

print(f"\nTrades in Exp but NOT in V4 (due to Cap=1 freeing earlier slots): N={len(new_in_exp)}")
for idx, r in new_in_exp.iterrows():
    t_str = str(r['time'])[:19]
    print(f"  * {r['symbol']:20s} | {t_str} | {r['outcome']:8s} | RR: {r['rr']:+5.2f} R | ADX: {r['adx']:4.1f} | ATR: {r['risk_atr']:4.2f} | Body: {r['body_ratio']:4.2f}")
