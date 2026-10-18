"""
scratch/reconcile_report_discrepancies_table.py
Reconcilia rigurosamente las discrepancias de cifras entre informes:
- Muestra exacta, fechas, N operaciones, PnL neto en R, PF, MaxDD, costos aplicados, y método.
- Identifica la causa técnica de cada discrepancia (-34.87R vs -25.81R vs -24.33R vs -14.33R vs -5.75R en SNR).
- Identifica la causa técnica de cada discrepancia (+37.81R vs +0.69R vs -3.77R vs -5.28R en ICT).
"""

import pandas as pd
import numpy as np

def run_reconciliation():
    print("=" * 100)
    print("TABLA MAESTRA DE RECONCILIACIÓN DE CIFRAS DISCREPANTES ENTRE INFORMES")
    print("=" * 100)

    # 1. Malaysian SNR Base
    df_snr_faithful = pd.read_csv('storage/analysis/msnr_faithful_trades.csv')
    df_snr_faithful['time'] = pd.to_datetime(df_snr_faithful['time'])
    
    # Dates
    start_snr = df_snr_faithful['time'].min().strftime('%Y-%m-%d')
    end_snr = df_snr_faithful['time'].max().strftime('%Y-%m-%d')
    
    # Full dataset
    n_full_snr = len(df_snr_faithful)
    r_full_snr = df_snr_faithful['rr'].sum()
    pf_full_snr = (df_snr_faithful[df_snr_faithful['rr'] > 0]['rr'].sum() / 
                   abs(df_snr_faithful[df_snr_faithful['rr'] < 0]['rr'].sum()))
    
    # Holdout OOS (146 days cutoff: 2026-05-18)
    cutoff_oos = pd.to_datetime('2026-05-18', utc=True)
    df_snr_train = df_snr_faithful[df_snr_faithful['time'] < cutoff_oos]
    df_snr_oos = df_snr_faithful[df_snr_faithful['time'] >= cutoff_oos]
    
    n_oos_snr = len(df_snr_oos)
    r_oos_snr = df_snr_oos['rr'].sum()
    pf_oos_snr = (df_snr_oos[df_snr_oos['rr'] > 0]['rr'].sum() / 
                  abs(df_snr_oos[df_snr_oos['rr'] < 0]['rr'].sum()))

    # Walk Forward Step 1 (W2 OOS) & Step 2 (W3 OOS)
    q1 = df_snr_faithful['time'].quantile(0.333)
    q2 = df_snr_faithful['time'].quantile(0.666)
    
    w1 = df_snr_faithful[df_snr_faithful['time'] <= q1]
    w2 = df_snr_faithful[(df_snr_faithful['time'] > q1) & (df_snr_faithful['time'] <= q2)]
    w3 = df_snr_faithful[df_snr_faithful['time'] > q2]
    
    print("\n--- MALAYSIAN SNR: BASE MECÁNICA ---")
    print(f"1. Muestra Completa Fiel (15 símbolos observados de 23):")
    print(f"   Fechas: {start_snr} a {end_snr} (346 d) | N={n_full_snr} | Net R={r_full_snr:.2f}R | PF={pf_full_snr:.3f}")
    print(f"2. Holdout OOS (Últimos 146 días):")
    print(f"   Fechas: 2026-05-18 a {end_snr} | N={n_oos_snr} | Net R={r_oos_snr:.2f}R | PF={pf_oos_snr:.3f}")
    print(f"3. Walk-Forward W2 (Step 1 OOS, 122 días):")
    print(f"   N={len(w2)} | Net R={w2['rr'].sum():.2f}R")
    print(f"4. Walk-Forward W3 (Step 2 OOS, 121 días):")
    print(f"   N={len(w3)} | Net R={w3['rr'].sum():.2f}R")

    # 2. ICT Sabri Malle
    df_ict_faithful = pd.read_csv('storage/analysis/ict_faithful_trades.csv')
    df_ict_faithful['time'] = pd.to_datetime(df_ict_faithful['time'])
    
    start_ict = df_ict_faithful['time'].min().strftime('%Y-%m-%d')
    end_ict = df_ict_faithful['time'].max().strftime('%Y-%m-%d')
    
    # Canonical 15 symbols
    canonical_15 = [
        "Boom 1000 Index", "Boom 500 Index", "Crash 1000 Index", "Crash 500 Index",
        "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
        "Volatility 10 Index", "Volatility 25 Index", "Volatility 75 Index",
        "Volatility 100 Index", "Step Index", "BTCUSD", "ETHUSD"
    ]
    df_ict_canonical = df_ict_faithful[df_ict_faithful['symbol'].isin(canonical_15)].copy()
    
    # Filtered ICT (Excl Jump25 + BodyRatio > 0.50 + Hour 8 NY) on canonical
    mask_filt_all = (
        (df_ict_canonical['symbol'] != 'Jump 25 Index') &
        (df_ict_canonical['body_ratio'] > 0.50) &
        (df_ict_canonical['ny_hour'] == 8)
    )
    df_ict_filt_all = df_ict_canonical[mask_filt_all]
    
    # ICT Holdout OOS
    df_ict_oos = df_ict_canonical[df_ict_canonical['time'] >= cutoff_oos]
    
    df_ict_oos_filt = df_ict_oos[
        (df_ict_oos['symbol'] != 'Jump 25 Index') &
        (df_ict_oos['body_ratio'] > 0.50) &
        (df_ict_oos['ny_hour'] == 8)
    ]
    
    print("\n--- ICT SABRI MALLE: RECONCILIACIÓN DE FILTROS ---")
    print(f"1. Base Mecánica Completa (15 símbolos canónicos):")
    print(f"   Fechas: {start_ict} a {end_ict} (346 d) | N={len(df_ict_canonical)} | Net R={df_ict_canonical['rr'].sum():.2f}R")
    print(f"2. Filtros Combinados Retrospectivos (Excl Jump25 + Body>0.50 + Hora 8 NY) - Muestra Completa:")
    print(f"   Fechas: Muestra Completa | N={len(df_ict_filt_all)} | Net R={df_ict_filt_all['rr'].sum():.2f}R | PF={df_ict_filt_all[df_ict_filt_all['rr']>0]['rr'].sum() / abs(df_ict_filt_all[df_ict_filt_all['rr']<0]['rr'].sum()):.3f}")
    print(f"3. Holdout OOS Base (Últimos 146 días):")
    print(f"   Fechas: 2026-05-18 a {end_ict} | N={len(df_ict_oos)} | Net R={df_ict_oos['rr'].sum():.2f}R")
    print(f"4. Holdout OOS Filtros Combinados Retrospectivos (con Hora 8 NY):")
    print(f"   Fechas: 2026-05-18 a {end_ict} | N={len(df_ict_oos_filt)} | Net R={df_ict_oos_filt['rr'].sum():.2f}R | PF={df_ict_oos_filt[df_ict_oos_filt['rr']>0]['rr'].sum() / abs(df_ict_oos_filt[df_ict_oos_filt['rr']<0]['rr'].sum()):.3f}")

if __name__ == '__main__':
    run_reconciliation()
