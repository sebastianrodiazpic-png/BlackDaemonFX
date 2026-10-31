"""Auditoría de mejoras e hipótesis de rescate para instrumentos podados en ORB."""
import pandas as pd
import numpy as np

df = pd.read_csv('storage/analysis/orb_sweep_expanded_trades.csv')
df['time'] = pd.to_datetime(df['signal_time'], utc=True)
df['hour_ny'] = df['time'].dt.tz_convert('America/New_York').dt.hour
df['minute_ny'] = df['time'].dt.tz_convert('America/New_York').dt.minute
df['time_min_ny'] = df['hour_ny'] * 60 + df['minute_ny']

pruned_symbols = ['EURUSD', 'USDJPY', 'USDCHF', 'NZDUSD', 'US Oil', 'UK Brent Oil', 'US SP 500', 'US Tech 100', 'Wall Street 30', 'ETHUSD', 'XAUEUR']

print('=== INVESTIGACIÓN DE MEJORAS INSTITUCIONALES EN ACTIVOS PODADOS ===\n')

for sym in pruned_symbols:
    sub = df[df['symbol'] == sym]
    if len(sub) == 0:
        continue
    sweep = sub[sub['variant'] == 'SWEEP']
    if len(sweep) == 0:
        continue
    base_n = len(sweep)
    base_wr = (sweep['net_r_ext'] > 0).mean() * 100
    base_r = sweep['net_r_ext'].mean()
    base_sum = sweep['net_r_ext'].sum()
    
    print(f'>> {sym} (BASE SWEEP: n={base_n}, WR={base_wr:.1f}%, R/t={base_r:+.3f}, Net={base_sum:+.1f}R)')
    
    # 1. Asimetría direccional
    for d in ['BUY', 'SELL']:
        s_d = sweep[sweep['direction'] == d]
        if len(s_d) >= 10:
            wr_d = (s_d['net_r_ext'] > 0).mean() * 100
            r_d = s_d['net_r_ext'].mean()
            net_d = s_d['net_r_ext'].sum()
            print(f'   - Solo {d:4s}: n={len(s_d):2d}, WR={wr_d:.1f}%, R/t={r_d:+.3f}, Net={net_d:+.1f}R')
            
    # 2. Ventana horaria (mañana 09:45-12:00 vs tarde)
    morning = sweep[sweep['time_min_ny'] <= 720] # <= 12:00 NY
    if len(morning) >= 10:
        wr_m = (morning['net_r_ext'] > 0).mean() * 100
        r_m = morning['net_r_ext'].mean()
        net_m = morning['net_r_ext'].sum()
        print(f'   - Ventana 09:45-12:00 NY: n={len(morning):2d}, WR={wr_m:.1f}%, R/t={r_m:+.3f}, Net={net_m:+.1f}R')
        
    # 3. HTF_SWEEP (alineación con tendencia H1/M15)
    htf = sub[sub['variant'] == 'HTF_SWEEP']
    if len(htf) >= 3:
        wr_h = (htf['net_r_ext'] > 0).mean() * 100
        r_h = htf['net_r_ext'].mean()
        net_h = htf['net_r_ext'].sum()
        print(f'   - Filtro HTF_SWEEP: n={len(htf):2d}, WR={wr_h:.1f}%, R/t={r_h:+.3f}, Net={net_h:+.1f}R')
        
    # 4. HTF + Asimetría
    for d in ['BUY', 'SELL']:
        h_d = htf[htf['direction'] == d]
        if len(h_d) >= 5:
            wr_hd = (h_d['net_r_ext'] > 0).mean() * 100
            r_hd = h_d['net_r_ext'].mean()
            net_hd = h_d['net_r_ext'].sum()
            print(f'   - HTF + Solo {d:4s}: n={len(h_d):2d}, WR={wr_hd:.1f}%, R/t={r_hd:+.3f}, Net={net_hd:+.1f}R')

    # 5. Fixed TP2 vs Extensión
    fixed_r = sweep['net_r'].mean()
    fixed_wr = (sweep['net_r'] > 0).mean() * 100
    fixed_sum = sweep['net_r'].sum()
    print(f'   - Variante FIJA (TP2 sin runner ext): WR={fixed_wr:.1f}%, R/t={fixed_r:+.3f}, Net={fixed_sum:+.1f}R')
            
    print()
