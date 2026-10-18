"""
scratch/audit_ict_walk_forward.py
==================================
Evaluación Walk-Forward / Partición Cronológica Fuera de Muestra para ICT Sabri Malle.
Detecta si los filtros de horario sufren de sesgo de selección retrospectiva (data snooping).
"""
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_ict_walk_forward():
    csv_path = PROJECT_ROOT / 'storage/analysis/ict_faithful_trades.csv'
    df = pd.read_csv(csv_path)
    
    # 1. Parsear a New York con DST
    df['time_utc'] = pd.to_datetime(df['time'], utc=True)
    ny_tz = ZoneInfo("America/New_York")
    df['time_ny'] = df['time_utc'].dt.tz_convert(ny_tz)
    df['ny_hour_exact'] = df['time_ny'].dt.hour
    df['ny_minute_exact'] = df['time_ny'].dt.minute
    df['time_ny_float'] = df['ny_hour_exact'] + df['ny_minute_exact'] / 60.0
    
    df = df.sort_values('time_utc').reset_index(drop=True)
    
    # Definir variantes
    def apply_filter(d, variant):
        if variant == 'base':
            return d.copy()
        elif variant == 'lock_0700_0930':
            mask = (d['time_ny_float'] >= 7.0) & (d['time_ny_float'] < 9.5)
            return d[~mask].copy()
        elif variant == 'lock_0700_1000':
            mask = (d['time_ny_float'] >= 7.0) & (d['time_ny_float'] < 10.0)
            return d[~mask].copy()
        elif variant == 'london_only':
            mask = (d['time_ny_float'] >= 2.0) & (d['time_ny_float'] < 5.0)
            return d[mask].copy()
        raise ValueError(f"Unknown variant {variant}")
        
    def metrics(sub_df):
        if sub_df.empty:
            return {'n': 0, 'net_r': 0.0, 'wr': 0.0, 'pf': 0.0, 'max_dd': 0.0}
        n = len(sub_df)
        net_r = sub_df['rr'].sum()
        wr = (sub_df['rr'] > 0).mean() * 100.0
        gw = sub_df[sub_df['rr'] > 0]['rr'].sum()
        gl = abs(sub_df[sub_df['rr'] < 0]['rr'].sum())
        pf = (gw / gl) if gl > 0 else (999.0 if gw > 0 else 0.0)
        cum = sub_df['rr'].cumsum()
        dd = (cum - cum.cummax()).min()
        return {'n': n, 'net_r': net_r, 'wr': wr, 'pf': pf, 'max_dd': abs(dd) if not np.isnan(dd) else 0.0}

    print("=========================================================================================")
    print("ICT SABRI MALLE: AUDITORÍA DE PARTICIÓN CRONOLÓGICA WALK-FORWARD (DETECCIÓN DE SNOOPING)")
    print("=========================================================================================")
    print(f"Total Trades Históricos: {len(df)} ({df['time_utc'].iloc[0]} a {df['time_utc'].iloc[-1]})")
    
    # Particiones Cronológicas:
    # Ventana 1 (In-Sample / Selección): Primeros 6 meses (2025-10 a 2026-04)
    # Ventana 2 (OOS Validación 1): Siguientes 3 meses (2026-04 a 2026-07)
    # Ventana 3 (OOS Holdout Final): Últimos 3 meses (2026-07 a 2026-10)
    t0 = df['time_utc'].iloc[0]
    t_split1 = pd.Timestamp("2026-04-10 00:00:00+00:00")
    t_split2 = pd.Timestamp("2026-07-10 00:00:00+00:00")
    t_end = df['time_utc'].iloc[-1]
    
    w1 = df[df['time_utc'] < t_split1]
    w2 = df[(df['time_utc'] >= t_split1) & (df['time_utc'] < t_split2)]
    w3 = df[df['time_utc'] >= t_split2]
    
    windows = [
        ("W1: In-Sample (2025-10 a 2026-04)", w1),
        ("W2: OOS Val-1 (2026-04 a 2026-07)", w2),
        ("W3: OOS Holdout-2 (2026-07 a 2026-10)", w3),
        ("TOTAL MUESTRA COMPLETA", df)
    ]
    
    variants = ['base', 'lock_0700_0930', 'lock_0700_1000', 'london_only']
    
    for w_name, w_df in windows:
        print(f"\n--- {w_name} [Total trades disponibles: {len(w_df)}] ---")
        rows = []
        for v in variants:
            filtered = apply_filter(w_df, v)
            m = metrics(filtered)
            rows.append({
                'Variante': v,
                'Trades': m['n'],
                'Net R': round(m['net_r'], 2),
                'Win Rate (%)': round(m['wr'], 1),
                'Profit Factor': round(m['pf'], 3),
                'Max Drawdown (R)': round(m['max_dd'], 2),
                'Exp (R/t)': round(m['net_r'] / m['n'], 4) if m['n'] > 0 else 0.0
            })
        print(pd.DataFrame(rows).to_string(index=False))
        
    print("\n--- DESGLOSE POR ACTIVO EN LA VENTANA OOS HOLDOUT-2 (W3: 2026-07 a 2026-10) ---")
    for v in ['base', 'lock_0700_1000', 'london_only']:
        v_w3 = apply_filter(w3, v)
        print(f"\nVariante: {v} en W3 (OOS Final):")
        grp_res = []
        for sym, grp in v_w3.groupby('symbol'):
            m = metrics(grp)
            grp_res.append({'Símbolo': sym, 'Trades': m['n'], 'Net R': round(m['net_r'], 2), 'WR (%)': round(m['wr'], 1)})
        df_grp = pd.DataFrame(grp_res).sort_values('Net R', ascending=False)
        print(df_grp.head(10).to_string(index=False))
        print("...")
        print(f"Total W3 para {v}: {len(v_w3)} trades, Net R: {v_w3['rr'].sum():.2f} R")

if __name__ == '__main__':
    run_ict_walk_forward()
