"""
scratch/audit_15_zero_trade_assets.py
Investiga el embudo de filtrado para los 23 activos canónicos de Malaysian SNR:
- Señales en base mecánica (msnr_faithful_trades.csv)
- Señales tras ADX >= 30
- Señales tras ADX >= 30 y ATR <= 1.5
- Señales tras ADX >= 30, ATR <= 1.5 y Cap=1
- Distinción rigurosa entre "sin señales en base", "filtrado por régimen", y "operaciones insuficientes (N <= 3)"
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def main():
    csv_path = PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv'
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    # Limpiar micro si existe
    full_allowlist = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    
    print(f"Total allowlist symbols ({len(full_allowlist)}): {full_allowlist}\n")

    # Embudo
    df_raw = df[df['symbol'].isin(full_allowlist)].copy()
    df_adx = df_raw[df_raw['adx'] >= 30.0].copy()
    df_adx_atr = df_adx[df_adx['risk_atr'] <= 1.5].copy()

    # Ahora veamos el walk-forward de 4 folds exacto para V4
    total = len(df_raw)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    all_v4_trades = []
    causal_pos_syms_per_fold = {}

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
        causal_pos_syms_per_fold[f+1] = pos_syms

        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        
        # Cap = 1
        accepted = []
        open_positions = []
        for idx, row in v2.iterrows():
            t_entry = row['time']
            open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
            if len(open_positions) < 1:
                accepted.append(row)
                open_positions.append(row['exit_time'])
        if len(accepted) > 0:
            all_v4_trades.extend(accepted)

    df_v4 = pd.DataFrame(all_v4_trades)

    funnel = []
    for sym in full_allowlist:
        sub_raw = df_raw[df_raw['symbol'] == sym]
        sub_adx = df_adx[df_adx['symbol'] == sym]
        sub_adx_atr = df_adx_atr[df_adx_atr['symbol'] == sym]
        sub_v4 = df_v4[df_v4['symbol'] == sym] if len(df_v4) > 0 else pd.DataFrame()

        n_raw = len(sub_raw)
        raw_pnl = round(sub_raw['rr'].sum(), 2) if n_raw > 0 else 0.0
        raw_wr = round((sub_raw['rr'] > 0).mean() * 100, 1) if n_raw > 0 else 0.0

        n_adx = len(sub_adx)
        adx_pnl = round(sub_adx['rr'].sum(), 2) if n_adx > 0 else 0.0

        n_adx_atr = len(sub_adx_atr)
        adx_atr_pnl = round(sub_adx_atr['rr'].sum(), 2) if n_adx_atr > 0 else 0.0

        n_v4 = len(sub_v4)
        v4_pnl = round(sub_v4['rr'].sum(), 2) if n_v4 > 0 else 0.0
        v4_wr = round((sub_v4['rr'] > 0).mean() * 100, 1) if n_v4 > 0 else 0.0

        # Clasificación de causa
        if n_raw == 0:
            classification = "SIN_SENALES_BASE (0 en histórico)"
        elif n_v4 == 0:
            if n_adx == 0:
                classification = "FILTRADO_POR_ADX (ADX nunca >= 30)"
            elif n_adx_atr == 0:
                classification = "FILTRADO_POR_ATR (ATR > 1.5)"
            else:
                classification = "BLOQUEADO_POR_CAP1"
        elif n_v4 <= 3:
            classification = f"MUESTRA_MICRO (N={n_v4}, Incierta)"
        else:
            classification = f"OPERATIVO (N={n_v4})"

        funnel.append({
            "symbol": sym,
            "raw_trades": n_raw,
            "raw_wr%": raw_wr,
            "raw_pnl_r": raw_pnl,
            "adx_trades": n_adx,
            "adx_pnl_r": adx_pnl,
            "adx_atr_trades": n_adx_atr,
            "v4_trades": n_v4,
            "v4_wr%": v4_wr,
            "v4_pnl_r": v4_pnl,
            "diagnostico": classification
        })

    res_df = pd.DataFrame(funnel)
    print(res_df.to_string(index=False))

    print("\n=== RESUMEN DE LOS 15 ACTIVOS SIN TRADES EN V4 ===")
    zero_v4 = res_df[res_df['v4_trades'] == 0]
    print(f"Total con 0 trades en V4: {len(zero_v4)}")
    for d, group in zero_v4.groupby('diagnostico'):
        print(f"\nCategoría: {d} ({len(group)} activos):")
        for s in group['symbol']:
            raw_t = group[group['symbol'] == s]['raw_trades'].values[0]
            raw_p = group[group['symbol'] == s]['raw_pnl_r'].values[0]
            print(f"  - {s:25s} | Trades Base: {raw_t:3d} | PnL Base: {raw_p:+6.2f} R")

    print("\n=== ACTIVOS CON MUESTRAS PEQUEÑAS (N <= 3) EN V4 ===")
    small_v4 = res_df[(res_df['v4_trades'] > 0) & (res_df['v4_trades'] <= 3)]
    for idx, r in small_v4.iterrows():
        print(f"  - {r['symbol']:25s} | Trades V4: {r['v4_trades']} | WR: {r['v4_wr%']}% | PnL: {r['v4_pnl_r']:+6.2f} R | Diagnóstico: {r['diagnostico']}")

if __name__ == '__main__':
    main()
