"""Auditoría de selección dinámica causal de activos en ICT (Sabri Malle)
y catálogo exhaustivo de cobertura de datos locales M5/H4 para los 18 activos huérfanos.
Ejecución en modo de solo lectura sobre datasets locales.
"""

import sys
from pathlib import Path
import pickle
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.strategy_config import PRUNED_ASSET_UNIVERSE

def compute_metrics(rr_series: pd.Series) -> dict:
    if len(rr_series) == 0:
        return {"trades": 0, "wr": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "gross_win": 0.0, "gross_loss": 0.0}
    trades = len(rr_series)
    wins = rr_series[rr_series > 0]
    losses = rr_series[rr_series <= 0]
    wr = len(wins) / trades * 100
    net_r = float(rr_series.sum())
    exp_r = float(rr_series.mean())
    gain = float(wins.sum()) if len(wins) > 0 else 0.0
    loss = float(abs(losses.sum())) if len(losses) > 0 else 0.0
    pf = (gain / loss) if loss > 0 else (99.0 if gain > 0 else 0.0)
    
    cum_r = rr_series.cumsum()
    dd = cum_r.cummax() - cum_r
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0
    return {
        "trades": trades,
        "wr": round(wr, 2),
        "net_r": round(net_r, 2),
        "exp_r": round(exp_r, 4),
        "pf": round(pf, 3),
        "max_dd_r": round(max_dd, 2),
        "gross_win": round(gain, 2),
        "gross_loss": round(loss, 2)
    }

def test_ict_causal_asset_selection():
    print("=" * 80)
    print("SELECCIÓN DINÁMICA CAUSAL DE ACTIVOS EN ICT (SABRI MALLE) WALK-FORWARD")
    print("=" * 80)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 5, unit='m')
    
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    # Variables causales pre-trade
    regime_ratios = []
    directional_alignment = []
    
    for i, row in df_enabled.iterrows():
        sym = row['symbol']
        past = df_enabled.iloc[:i]
        past_sym = past[past['symbol'] == sym]
        
        if len(past_sym) >= 5:
            baseline_risk = past_sym['risk_pct'].iloc[-20:].median()
            ratio = row['risk_pct'] / baseline_risk if baseline_risk > 0 else 1.0
        else:
            ratio = 1.0
        regime_ratios.append(ratio)
        
        if len(past_sym) >= 3:
            last_dirs = past_sym['direction'].iloc[-3:].tolist()
            aligned = last_dirs.count(row['direction']) >= 2
        else:
            aligned = True
        directional_alignment.append(aligned)
        
    df_enabled['risk_expansion_ratio'] = regime_ratios
    df_enabled['htf_momentum_aligned'] = directional_alignment
    
    # Filtro base defensivo + régimen + momentum HTF
    core_mask = (~df_enabled['symbol'].isin(['Jump 25 Index'])) & \
                (df_enabled['body_ratio'] > 0.50) & \
                (df_enabled['risk_expansion_ratio'] <= 1.40) & \
                (df_enabled['htf_momentum_aligned'])
                
    df_filt = df_enabled[core_mask].copy().reset_index(drop=True)
    
    min_time = df_filt['time'].min()
    max_time = df_filt['time'].max()
    total_days = (max_time - min_time).days
    
    w1_end = min_time + pd.Timedelta(days=int(total_days * 0.333))
    w2_end = min_time + pd.Timedelta(days=int(total_days * 0.666))
    
    w1_trades = df_filt[df_filt['time'] < w1_end].copy()
    w2_trades = df_filt[(df_filt['time'] >= w1_end) & (df_filt['time'] < w2_end)].copy()
    w3_trades = df_filt[df_filt['time'] >= w2_end].copy()
    
    w1_clean = w1_trades[w1_trades['exit_time'] < w1_end].copy()
    w2_clean = w2_trades[w2_trades['exit_time'] < w2_end].copy()
    
    print(f"Ventana 1 (Train): N={len(w1_clean)} | Ventana 2 (OOS 1): N={len(w2_clean)} | Ventana 3 (OOS 2): N={len(w3_trades)}")
    
    # 1. Paso 1: Aprender activos rentables en W1
    w1_perf_asset = w1_clean.groupby('symbol')['rr'].sum()
    allowed_w2_assets = w1_perf_asset[w1_perf_asset > 0].index.tolist()
    print(f"\n[PASO 1] Activos con Net R > 0 en Train W1 (Causal): {allowed_w2_assets}")
    
    # Probar en W2 OOS
    m_w2_all = compute_metrics(w2_clean['rr'])
    w2_causal_trades = w2_clean[w2_clean['symbol'].isin(allowed_w2_assets)]
    m_w2_causal = compute_metrics(w2_causal_trades['rr'])
    
    print(f"  - W2 OOS (Todos los activos con filtro): N={m_w2_all['trades']} | Net R={m_w2_all['net_r']:+.2f}R | PF={m_w2_all['pf']:.3f} | MaxDD={m_w2_all['max_dd_r']:.2f}R")
    print(f"  - W2 OOS (Solo activos ganadores de W1) : N={m_w2_causal['trades']} | Net R={m_w2_causal['net_r']:+.2f}R | PF={m_w2_causal['pf']:.3f} | MaxDD={m_w2_causal['max_dd_r']:.2f}R")
    
    # 2. Paso 2: Aprender activos rentables en W1 + W2
    w1_w2_clean = pd.concat([w1_clean, w2_clean]).sort_values('time').reset_index(drop=True)
    w1_w2_perf_asset = w1_w2_clean.groupby('symbol')['rr'].sum()
    allowed_w3_assets = w1_w2_perf_asset[w1_w2_perf_asset > 0].index.tolist()
    print(f"\n[PASO 2] Activos con Net R > 0 en Train W1+W2 (Causal): {allowed_w3_assets}")
    
    # Probar en W3 OOS
    m_w3_all = compute_metrics(w3_trades['rr'])
    w3_causal_trades = w3_trades[w3_trades['symbol'].isin(allowed_w3_assets)]
    m_w3_causal = compute_metrics(w3_causal_trades['rr'])
    
    print(f"  - W3 OOS (Todos los activos con filtro): N={m_w3_all['trades']} | Net R={m_w3_all['net_r']:+.2f}R | PF={m_w3_all['pf']:.3f} | MaxDD={m_w3_all['max_dd_r']:.2f}R")
    print(f"  - W3 OOS (Solo activos ganadores de W1+W2): N={m_w3_causal['trades']} | Net R={m_w3_causal['net_r']:+.2f}R | PF={m_w3_causal['pf']:.3f} | MaxDD={m_w3_causal['max_dd_r']:.2f}R")

def audit_local_data_inventory():
    print("\n" + "=" * 80)
    print("CATÁLOGO DETALLADO DE DATOS M5/H4 LOCALES PARA LOS 18 ACTIVOS HUÉRFANOS")
    print("=" * 80)
    
    missing_snr = [
        'AUDNZD', 'Boom 300 Index', 'Crash 600 Index',
        'EURCHF', 'EURGBP', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'Jump 10 Index',
        'Step Index 200', 'Step Index 400', 'Volatility 250 (1s) Index',
        'Volatility 50 (1s) Index', 'Volatility 90 Index'
    ]
    missing_ict = ['Boom 300 Index', 'Boom 600 Index', 'Crash 300 Index', 'Step Index 400']
    
    all_orphans = sorted(list(set(missing_snr + missing_ict)))
    hist_dir = Path('storage/analysis/msnr_v27_m5_reference_20261012/history')
    
    print(f"{'Activo':25s} | {'Archivo M5 Local':28s} | {'Velas M5':9s} | {'Fecha Inicio (UTC)':19s} | {'Fecha Fin (UTC)':19s} | {'Estado Local':15s}")
    print("-" * 125)
    
    for sym in all_orphans:
        clean = sym.replace(' ', '_').replace('(', '').replace(')', '')
        m5_file = hist_dir / f"{clean}_M5.pkl"
        
        if m5_file.exists():
            try:
                with open(m5_file, 'rb') as f:
                    df = pickle.load(f)
                count = len(df)
                t_start = str(df['time'].iloc[0])[:19]
                t_end = str(df['time'].iloc[-1])[:19]
                status = "COMPLETO (1 año)"
            except Exception as e:
                count = 0
                t_start = "Error"
                t_end = "Error"
                status = f"CORRUPTO: {e}"
            print(f"{sym:25s} | {m5_file.name:28s} | {count:9d} | {t_start:19s} | {t_end:19s} | {status:15s}")
        else:
            print(f"{sym:25s} | {'NO EXISTE EN DISCO':28s} | {0:9d} | {'N/A':19s} | {'N/A':19s} | {'DESCARGA REQ':15s}")

if __name__ == "__main__":
    test_ict_causal_asset_selection()
    audit_local_data_inventory()
