"""
scratch/investigate_snr_ai_588_deep_dive.py
Investigación profunda solicitada por el usuario:
¿Por qué la selección causal con IA reporta +5.88 R en el holdout y se sostiene en ventanas y costos independientes?
"""

import pandas as pd
import numpy as np

def run_investigation():
    print("=" * 90)
    print("INVESTIGACIÓN PROFUNDA: ORIGEN Y ROBUSTEZ DEL RESULTADO DE +5.88 R (SNR + IA)")
    print("=" * 90)
    
    # 1. Base trades
    df = pd.read_csv('storage/analysis/msnr_faithful_trades.csv')
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    
    cutoff_oos = pd.to_datetime('2026-05-18', utc=True)
    train_df = df[df['time'] < cutoff_oos].copy()
    holdout_df = df[df['time'] >= cutoff_oos].copy()
    
    # Symbols positive in train
    pnl_by_symbol_train = train_df.groupby('symbol')['rr'].sum()
    pos_syms = set(pnl_by_symbol_train[pnl_by_symbol_train > 0].index)
    
    # Causal nested selection in holdout
    causal_holdout = holdout_df[holdout_df['symbol'].isin(pos_syms)].copy()
    n_causal = len(causal_holdout)
    r_causal = causal_holdout['rr'].sum()
    
    print(f"1. Selección Causal Dinámica en Holdout OOS:")
    print(f"   Trades: {n_causal} | Net PnL: {r_causal:.2f} R | Expectancy: {causal_holdout['rr'].mean():.4f} R")
    print(f"   Activos Seleccionados desde Train: {sorted(list(pos_syms))}")
    
    # Detailed per-asset breakdown in causal holdout
    print("\n   Desglose por Activo en Selección Causal Holdout:")
    for sym, grp in causal_holdout.groupby('symbol'):
        print(f"     • {sym:25s}: N={len(grp):2d} | Net R={grp['rr'].sum():+6.2f} R | WR={(grp['rr']>0).mean()*100:5.1f}%")
        
    # The 9 trades filtered by AI
    # In earlier report: causal + AI (prob >= 0.35) gave N=52, Net R = +5.88 R
    # Delta: N = 61 -> 52 (9 trades descartados), Net R = +4.12 R -> +5.88 R (salva +1.76 R)
    print("\n2. Mecánica Marginal del Filtro de IA (+1.76 R de mejora neta):")
    print(f"   Trades Base Causal: {n_causal} (+4.12 R)")
    print(f"   Trades con IA:      52 (+5.88 R)")
    print(f"   Trades Filtrados:    9 (-1.76 R eliminados)")
    print(f"   -> La IA no inventa operaciones nuevas; elimina 9 operaciones con PnL neto de -1.76 R.")
    
    # 3. Robustez a Costos de la variante +5.88 R
    print("\n3. Sensibilidad a Fricción de la variante +5.88 R (N=52):")
    costs = [
        ("Estándar (Spread Deriv)", 0.0, 0.0),
        ("Moderada (+0.05 R slip + 15% gap)", 0.05, 0.15),
        ("Severa   (+0.10 R slip + 20% gap)", 0.10, 0.20)
    ]
    for label, slip_r, gap_pct in costs:
        adj_r = 5.88 - (52 * slip_r) - (52 * (1 - 0.462) * gap_pct * 1.0) # gap on losses
        print(f"   • {label:35s}: Net R = {adj_r:+6.2f} R")
        
    # 4. Comportamiento en Ventanas Walk-Forward Independientes (desde evaluate_causal_improvements.py)
    print("\n4. Comportamiento en Ventanas Walk-Forward Independientes (4 Folds):")
    print("   • Fold 1 (W1 OOS): N=160 | Net R = +18.80 R | PF = 1.188  [POSITIVA]")
    print("   • Fold 2 (W2 OOS): N=170 | Net R =  -5.93 R | PF = 0.948  [NEGATIVA]")
    print("   • Fold 3 (W3 OOS): N=168 | Net R =  -7.86 R | PF = 0.931  [NEGATIVA]")
    print("   • Fold 4 (W4 OOS): N=129 | Net R =  -7.82 R | PF = 0.911  [NEGATIVA]")
    print("   -> Total Walk-Forward OOS: N=627 | Net R = -2.80 R | Ventanas Rentables: 1 / 4 (25.0%)")
    print("   -> CONCLUSIÓN: La mejora de +5.88 R es un aporte defensivo local (+1.76 R de poda),")
    print("      pero NO se sostiene como sistema rentable en todas las ventanas walk-forward (3 de 4 negativas)")
    print("      y colapsa a negativo bajo fricción severa.")

if __name__ == '__main__':
    run_investigation()
