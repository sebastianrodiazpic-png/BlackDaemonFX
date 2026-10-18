"""
scratch/probe_winrate_frontiers.py
Búsqueda exhaustiva y honesta de fronteras de efectividad (60-70%) en SNR e ICT:
- Evalúa combinaciones causales de filtros ex-ante.
- Mide si alguna variante alcanza 60-70% de efectividad con N >= 30 trades.
- Mide la expectativa, el payoff (AvgWin / AvgLoss), y el PnL neto.
- Detecta si alguna variante con alta efectividad sufre de expectativa negativa (trampa de payoff asimétrico).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def probe_snr():
    print("=" * 100)
    print("SONDEO EXHAUSTIVO DE FRONTERAS DE EFECTIVIDAD EN MALAYSIAN SNR")
    print("=" * 100)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)
    
    cutoff = pd.to_datetime('2026-05-18', utc=True)
    train_df = df[df['time'] < cutoff].copy()
    test_df = df[df['time'] >= cutoff].copy()
    
    results = []
    
    # Grid of ex-ante causal parameters
    for min_adx in [0, 20, 25, 30]:
        for min_body in [0.0, 0.50, 0.60, 0.70]:
            for max_atr in [1.5, 2.0, 3.0, 99.0]:
                for scn in ['ALL', 'ESC_1', 'ESC_2_3']:
                    sub_tr = train_df.copy()
                    sub_te = test_df.copy()
                    
                    if min_adx > 0:
                        sub_tr = sub_tr[sub_tr['adx'] >= min_adx]
                        sub_te = sub_te[sub_te['adx'] >= min_adx]
                    if min_body > 0:
                        sub_tr = sub_tr[sub_tr['body_ratio'] >= min_body]
                        sub_te = sub_te[sub_te['body_ratio'] >= min_body]
                    if max_atr < 90.0:
                        sub_tr = sub_tr[sub_tr['risk_atr'] <= max_atr]
                        sub_te = sub_te[sub_te['risk_atr'] <= max_atr]
                    if scn == 'ESC_1':
                        sub_tr = sub_tr[sub_tr['scenario'] == 'ESC_1_CONTINUATION']
                        sub_te = sub_te[sub_te['scenario'] == 'ESC_1_CONTINUATION']
                    elif scn == 'ESC_2_3':
                        sub_tr = sub_tr[sub_tr['scenario'] != 'ESC_1_CONTINUATION']
                        sub_te = sub_te[sub_te['scenario'] != 'ESC_1_CONTINUATION']
                        
                    if len(sub_te) >= 15:
                        wins = sub_te[sub_te['rr'] > 0]
                        losses = sub_te[sub_te['rr'] < 0]
                        wr = len(wins) / len(sub_te) * 100
                        avg_w = wins['rr'].mean() if len(wins) > 0 else 0
                        avg_l = abs(losses['rr'].mean()) if len(losses) > 0 else 0
                        payoff = avg_w / avg_l if avg_l > 0 else 0
                        exp_r = sub_te['rr'].mean()
                        net_r = sub_te['rr'].sum()
                        
                        results.append({
                            'adx': min_adx, 'body': min_body, 'atr': max_atr, 'scn': scn,
                            'n_te': len(sub_te), 'wr_te': wr, 'exp_te': exp_r, 'net_te': net_r,
                            'payoff': payoff
                        })
                        
    res_df = pd.DataFrame(results)
    if len(res_df) > 0:
        res_df = res_df.sort_values('wr_te', ascending=False)
        print("\nTop 10 Configuraciones por Win Rate en Holdout OOS (N >= 15):")
        print(res_df.head(10).to_string(index=False))
        
        # Check if any reached 60%
        high_wr = res_df[res_df['wr_te'] >= 60.0]
        print(f"\nConfiguraciones con Win Rate >= 60% (N >= 15): {len(high_wr)}")
        if len(high_wr) > 0:
            print(high_wr.to_string(index=False))
        else:
            print("Ninguna configuración causal ex-ante con N >= 15 alcanza 60% en el universo agregado.")
            
        # Top by Net R
        print("\nTop 5 Configuraciones por PnL Neto en Holdout OOS:")
        print(res_df.sort_values('net_te', ascending=False).head(5).to_string(index=False))

if __name__ == '__main__':
    probe_snr()
