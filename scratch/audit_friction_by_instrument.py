"""
scratch/audit_friction_by_instrument.py
Desglose detallado de fricción por instrumento en el candidato N=40 (ADX>=30 + ATR<=1.5 + Cap=1).
Distingue spread real observado vs slippage y gaps hipotéticos.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def simulate_concurrency_cap(trades_df: pd.DataFrame, max_open: int = 1) -> pd.DataFrame:
    accepted = []
    open_positions = []
    for idx, row in trades_df.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < max_open:
            accepted.append(row)
            open_positions.append(row['exit_time'])
    return pd.DataFrame(accepted)

def main():
    df = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv')
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    all_v4 = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df['time'].iloc[train_end]
        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        v4 = simulate_concurrency_cap(v2, max_open=1) if len(v2) > 0 else pd.DataFrame()
        all_v4.append(v4)

    df_v4 = pd.concat(all_v4, ignore_index=True)

    print("=" * 110)
    print("DESGLOSE DE FRICCIÓN Y COSTOS POR INSTRUMENTO EN EL CANDIDATO COMBINADO (N=40)")
    print("=" * 110)
    print("Mapeo de costos:")
    print("  1. Base Real (Observado): Spread por tick de Deriv en M15 ya descontado en 'rr'.")
    print("  2. Fricción Moderada (Hipotética): -0.05 R slippage entrada/salida + 15% gap en SL perdedores.")
    print("  3. Fricción Severa (Hipotética): -0.10 R slippage entrada/salida + 20% gap en SL perdedores.\n")

    symbols = sorted(df_v4['symbol'].unique())
    print(f"{'Instrumento':25s} | {'N':2s} | {'Base Net R':10s} | {'Base PF':7s} | {'Mod Net R':10s} | {'Mod PF':7s} | {'Sev Net R':10s} | {'Sev PF':7s}")
    print("-" * 110)

    for s in symbols:
        sub = df_v4[df_v4['symbol'] == s].copy()
        n = len(sub)
        
        # Base
        base_rr = sub['rr'].values
        base_net = base_rr.sum()
        gw = base_rr[base_rr > 0].sum()
        gl = abs(base_rr[base_rr < 0].sum())
        base_pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
        
        # Mod
        mod_rr = base_rr.copy() - 0.05
        l_mask = mod_rr < 0
        mod_rr[l_mask] -= abs(mod_rr[l_mask]) * 0.15
        mod_net = mod_rr.sum()
        gw_mod = mod_rr[mod_rr > 0].sum()
        gl_mod = abs(mod_rr[mod_rr < 0].sum())
        mod_pf = (gw_mod / gl_mod) if gl_mod > 0 else (99.0 if gw_mod > 0 else 0.0)
        
        # Sev
        sev_rr = base_rr.copy() - 0.10
        l_mask_sev = sev_rr < 0
        sev_rr[l_mask_sev] -= abs(sev_rr[l_mask_sev]) * 0.20
        sev_net = sev_rr.sum()
        gw_sev = sev_rr[sev_rr > 0].sum()
        gl_sev = abs(sev_rr[sev_rr < 0].sum())
        sev_pf = (gw_sev / gl_sev) if gl_sev > 0 else (99.0 if gw_sev > 0 else 0.0)
        
        print(f"{s:25s} | {n:2d} | {base_net:+9.2f} R | {base_pf:7.2f} | {mod_net:+9.2f} R | {mod_pf:7.2f} | {sev_net:+9.2f} R | {sev_pf:7.2f}")

    print("-" * 110)
    # Total
    tot_base = df_v4['rr'].values
    tot_base_net = tot_base.sum()
    gw_tot = tot_base[tot_base > 0].sum()
    gl_tot = abs(tot_base[tot_base < 0].sum())
    tot_base_pf = gw_tot / gl_tot

    tot_mod = tot_base.copy() - 0.05
    tot_mod[tot_mod < 0] -= abs(tot_mod[tot_mod < 0]) * 0.15
    tot_mod_net = tot_mod.sum()
    gw_mod_tot = tot_mod[tot_mod > 0].sum()
    gl_mod_tot = abs(tot_mod[tot_mod < 0].sum())
    tot_mod_pf = gw_mod_tot / gl_mod_tot

    tot_sev = tot_base.copy() - 0.10
    tot_sev[tot_sev < 0] -= abs(tot_sev[tot_sev < 0]) * 0.20
    tot_sev_net = tot_sev.sum()
    gw_sev_tot = tot_sev[tot_sev > 0].sum()
    gl_sev_tot = abs(tot_sev[tot_sev < 0].sum())
    tot_sev_pf = gw_sev_tot / gl_sev_tot

    print(f"{'TOTAL PORTAFOLIO':25s} | {len(df_v4):2d} | {tot_base_net:+9.2f} R | {tot_base_pf:7.2f} | {tot_mod_net:+9.2f} R | {tot_mod_pf:7.2f} | {tot_sev_net:+9.2f} R | {tot_sev_pf:7.2f}")

if __name__ == '__main__':
    main()
