"""Audit ORB experimental variant excluding XAUUSD on enabled universe."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

def run_orb_isolation_audit():
    df = pd.read_csv(PROJECT_ROOT / 'storage/analysis/orb_nunez_2y/trades.csv')
    current = df[df['variant'] == 'CURRENT'].sort_values('entry_time').reset_index(drop=True)
    
    enabled_all = ['Wall Street 30', 'US Tech 100', 'BTCUSD', 'XAUUSD']
    enabled_no_gold = ['Wall Street 30', 'US Tech 100', 'BTCUSD']
    
    df_all = current[current['symbol'].isin(enabled_all)].copy()
    df_no_gold = current[current['symbol'].isin(enabled_no_gold)].copy()
    
    print(f"=========================================================")
    print(f"AUDITORÍA ORB: UNIVERSO HABILITADO vs. VARIANTE SIN XAUUSD")
    print(f"=========================================================")
    print(f"Total trades Universo Habilitado (con Oro): {len(df_all)}")
    print(f"Total trades Variante Experimental (sin Oro): {len(df_no_gold)}")
    
    def calc_metrics(sub_df, label):
        n = len(sub_df)
        if n == 0:
            return f"{label}: 0 trades"
        net_r = sub_df['net_r'].sum()
        wr = (sub_df['net_r'] > 0).mean() * 100
        gw = sub_df[sub_df['net_r'] > 0]['net_r'].sum()
        gl = abs(sub_df[sub_df['net_r'] < 0]['net_r'].sum())
        pf = gw / gl if gl > 0 else float('inf')
        exp = net_r / n
        
        cum_r = sub_df['net_r'].cumsum()
        peak = cum_r.cummax()
        max_dd = (peak - cum_r).max()
        
        print(f"\n{label}:")
        print(f"  Trades: {n:3d} | Net R: {net_r:+6.2f} R | WR: {wr:5.1f}% | PF: {pf:5.3f} | Exp: {exp:+6.4f} R/t | MaxDD: {max_dd:5.2f} R")
        return {"n": n, "net_r": net_r, "wr": wr, "pf": pf, "exp": exp, "max_dd": max_dd}

    calc_metrics(df_all, "1. Universo Habilitado Completo (4 Activos: US30, NAS100, BTC, Oro)")
    calc_metrics(df_no_gold, "2. Variante Experimental Aislada (3 Activos: US30, NAS100, BTC - SIN ORO)")
    
    print("\n---------------------------------------------------------")
    print("DESGLOSE POR ACTIVO EN LA VARIANTE SIN ORO:")
    print("---------------------------------------------------------")
    for sym in enabled_no_gold:
        sym_df = df_no_gold[df_no_gold['symbol'] == sym]
        nature = "APERTURA OFICIAL CASH" if sym in ['Wall Street 30', 'US Tech 100'] else "HORARIO PROXY 24/7"
        calc_metrics(sym_df, f"  * {sym} ({nature})")

    # Chronological Split of the Experimental Variant (75% Train, 25% Holdout)
    sp = int(len(df_no_gold) * 0.75)
    train_ng = df_no_gold.iloc[:sp]
    holdout_ng = df_no_gold.iloc[sp:]
    
    print("\n---------------------------------------------------------")
    print("VALIDACIÓN CRONOLÓGICA DE LA VARIANTE SIN ORO (69 TRADES):")
    print("---------------------------------------------------------")
    calc_metrics(train_ng, f"  Train (75%, N={len(train_ng)})")
    calc_metrics(holdout_ng, f"  Holdout Intacto (25%, N={len(holdout_ng)})")

if __name__ == '__main__':
    run_orb_isolation_audit()
