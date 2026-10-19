"""
scratch/audit_v4_by_direction_and_asset.py
Calcula métricas detalladas de Malaysian SNR V4:
- Por dirección (BUY vs SELL)
- Por fold walk-forward
- Por activo individual
- Desglose de los 23 activos distinguiendo 'sin señales en base', 'filtrado causal de entrenamiento', 'bloqueo por filtros' y 'muestras micro'.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def wilson_ci(wins, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    spread = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return round(max(0.0, centre - spread) * 100, 1), round(min(1.0, centre + spread) * 100, 1)

def compute_metrics(trades_df, friction=0.0):
    if len(trades_df) == 0:
        return {
            "n": 0, "wr%": 0.0, "ci95": (0.0, 0.0), "net_r": 0.0, "exp_r": 0.0,
            "payoff": 0.0, "pf": 0.0, "max_dd": 0.0, "gross_win": 0.0, "gross_loss": 0.0
        }
    n = len(trades_df)
    rrs = trades_df['rr'].values - friction
    wins = np.sum(rrs > 0)
    wr = round(wins / n * 100, 1)
    ci = wilson_ci(wins, n)
    net_r = round(float(np.sum(rrs)), 2)
    exp_r = round(float(np.mean(rrs)), 4)
    
    pos_r = rrs[rrs > 0]
    neg_r = rrs[rrs <= 0]
    gross_win = round(float(np.sum(pos_r)), 2)
    gross_loss = round(float(abs(np.sum(neg_r))), 2)
    
    avg_win = float(np.mean(pos_r)) if len(pos_r) > 0 else 0.0
    avg_loss = float(abs(np.mean(neg_r))) if len(neg_r) > 0 else 1.0
    payoff = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 99.0
    
    # Max DD
    cum = np.cumsum(rrs)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd = round(float(np.max(dd)), 2) if len(dd) > 0 else 0.0
    
    return {
        "n": n, "wr%": wr, "ci95": ci, "net_r": net_r, "exp_r": exp_r,
        "payoff": payoff, "pf": pf, "max_dd": max_dd,
        "gross_win": gross_win, "gross_loss": gross_loss
    }

def main():
    csv_path = PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv'
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    full_allowlist = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    df_raw = df[df['symbol'].isin(full_allowlist)].copy()

    total = len(df_raw)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    all_v4_trades = []
    fold_details = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        split_time = df_raw['time'].iloc[train_end]
        train_slice = df_raw.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        test_slice = df_raw.iloc[train_end:test_end].copy().reset_index(drop=True)

        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)

        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        
        accepted = []
        open_positions = []
        for idx, row in v2.iterrows():
            t_entry = row['time']
            open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
            if len(open_positions) < 1:
                row_dict = row.to_dict()
                row_dict['fold'] = f + 1
                accepted.append(row_dict)
                open_positions.append(row['exit_time'])
        
        fold_df = pd.DataFrame(accepted)
        if len(fold_df) > 0:
            m_fold = compute_metrics(fold_df)
            m_fold['fold'] = f + 1
            m_fold['start_date'] = str(test_slice['time'].min())[:10]
            m_fold['end_date'] = str(test_slice['time'].max())[:10]
            m_fold['pos_syms'] = list(pos_syms)
            fold_details.append(m_fold)
            all_v4_trades.extend(accepted)

    df_v4 = pd.DataFrame(all_v4_trades)
    print("=== DESGLOSE GENERAL V4 BASE ===")
    m_total = compute_metrics(df_v4)
    print(m_total)

    print("\n=== DESGLOSE POR DIRECCIÓN (BUY vs SELL) ===")
    df_buy = df_v4[df_v4['direction'].str.upper() == 'BUY']
    df_sell = df_v4[df_v4['direction'].str.upper() == 'SELL']
    m_buy = compute_metrics(df_buy)
    m_sell = compute_metrics(df_sell)
    print("BUY :", m_buy)
    print("SELL:", m_sell)

    print("\n=== DESGLOSE POR FOLD WALK-FORWARD ===")
    for fd in fold_details:
        print(f"Fold {fd['fold']} ({fd['start_date']} a {fd['end_date']}): N={fd['n']}, WR={fd['wr%']}%, Net={fd['net_r']}R, PF={fd['pf']}, MaxDD={fd['max_dd']}R, Exp={fd['exp_r']}R, Payoff={fd['payoff']}, Activos Causalmente Habilitados: {fd['pos_syms']}")

    print("\n=== DESGLOSE POR ACTIVO INDIVIDUAL EN V4 ===")
    for sym in sorted(df_v4['symbol'].unique()):
        sub = df_v4[df_v4['symbol'] == sym]
        m_sym = compute_metrics(sub)
        print(f"{sym:22s} | N={m_sym['n']:2d} | WR={m_sym['wr%']:5.1f}% | CI={m_sym['ci95']} | Net={m_sym['net_r']:+6.2f}R | PF={m_sym['pf']:4.2f} | MaxDD={m_sym['max_dd']:4.2f}R | Payoff={m_sym['payoff']:4.2f}")

    print("\n=== DESGLOSE POR ACTIVO Y DIRECCIÓN ===")
    for sym in sorted(df_v4['symbol'].unique()):
        sub = df_v4[df_v4['symbol'] == sym]
        for d in ['BUY', 'SELL']:
            sub_d = sub[sub['direction'].str.upper() == d]
            if len(sub_d) > 0:
                m_d = compute_metrics(sub_d)
                print(f"{sym:22s} | {d:4s} | N={m_d['n']:2d} | WR={m_d['wr%']:5.1f}% | Net={m_d['net_r']:+6.2f}R | PF={m_d['pf']:4.2f}")

if __name__ == '__main__':
    main()
