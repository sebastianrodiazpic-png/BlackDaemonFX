"""
tools/run_msnr_exp_all_60_catalog_replay.py
===========================================
Replay completo y exhaustivo de MSNR Variante Experimental sobre TODOS LOS 60 ACTIVOS DISPONIBLES:
- 29 Índices Sintéticos (Fase 1: 2 años completos)
- 31 Activos Tradicionales (Fase 2: 24 Forex, 2 Metales, 3 Índices, 1 Cripto, 1 Commodity)
- Enriquecimiento causal con ADX H1, ATR H1 y Body Ratio M15
- Simulación secuencial estricta de Cap=1 por portafolio
- Almacenamiento local en storage/analysis/ para entrenamiento de modelos de IA
- Estadísticas completas por activo y clasificación: Más rentables vs Candidatos a Poda
"""

import pickle
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.replay_malaysian_snr_2year_audit import compute_atr, compute_adx

def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996
    p_hat = k / n
    denom = 1 + (z**2) / n
    center = (p_hat + (z**2) / (2 * n)) / denom
    margin = (z * np.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * n)) / n)) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (round(lower * 100, 1), round(upper * 100, 1))

def compute_kpis(series: pd.Series):
    n = len(series)
    if n == 0:
        return {"n": 0, "wins": 0, "losses": 0, "wr": 0.0, "ci_95": "[0.0%, 0.0%]",
                "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "payoff": 0.0, "max_dd": 0.0}
    w = (series > 0).sum()
    l = (series < 0).sum()
    wr = 100.0 * w / n
    ci = wilson_score_interval(w, n)
    net_r = series.sum()
    exp_r = net_r / n
    gw = series[series > 0].sum()
    gl = abs(series[series < 0].sum())
    pf = gw / gl if gl > 0 else (999.0 if gw > 0 else 0.0)
    payoff = (gw / w) / (gl / l) if (w > 0 and l > 0 and gl > 0) else (gw / w if w > 0 else 0.0)
    
    eq = series.cumsum()
    pk = eq.cummax()
    dd = (pk - eq).max()
    return {
        "n": n, "wins": w, "losses": l, "wr": round(wr, 1), "ci_95": f"[{ci[0]}%, {ci[1]}%]",
        "net_r": round(net_r, 2), "exp_r": round(exp_r, 4), "pf": round(pf, 2) if pf < 100 else 999.0,
        "payoff": round(payoff, 2), "max_dd": round(dd, 2)
    }

def main():
    t0_start = time.time()
    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"

    # 1. Cargar el dataset base de 8,721 operaciones sobre los 60 activos
    df_base = pd.read_csv(out_dir / "msnr_2year_audit" / "trades_baseline.csv")
    symbols = sorted(df_base['symbol'].unique())
    print(f"Iniciando enriquecimiento de {len(df_base)} operaciones sobre los {len(symbols)} activos del catálogo...")

    enriched_chunks = []
    for sym in symbols:
        sub_df = df_base[df_base['symbol'] == sym].copy()
        prefix = sym.replace(' ', '_').replace('(', '').replace(')', '')
        p_m15 = cache_dir / f'{prefix}_M15.pkl'
        if not p_m15.exists():
            prefix_alt = sym.replace(' ', '_')
            p_m15 = cache_dir / f'{prefix_alt}_M15.pkl'
            p_h1 = cache_dir / f'{prefix_alt}_H1.pkl'
        else:
            p_h1 = cache_dir / f'{prefix}_H1.pkl'
            
        if not p_m15.exists() or not p_h1.exists():
            continue
            
        with open(p_m15, 'rb') as f:
            m15 = pickle.load(f)
        with open(p_h1, 'rb') as f:
            h1 = pickle.load(f)
            
        m15['time'] = pd.to_datetime(m15['time'], utc=True).astype('datetime64[ns, UTC]')
        h1['time'] = pd.to_datetime(h1['time'], utc=True).astype('datetime64[ns, UTC]')
        
        h1['atr'] = compute_atr(h1, 14)
        h1['adx'] = compute_adx(h1, 14)
        
        span = m15['high'] - m15['low']
        body = (m15['close'] - m15['open']).abs()
        m15['body_ratio'] = np.where(span > 0, body / span, 0.0)
        
        sub_df['time_utc'] = pd.to_datetime(sub_df['time'], utc=True).astype('datetime64[ns, UTC]')
        sub_df['exit_time_utc'] = sub_df['time_utc'] + pd.to_timedelta(sub_df['bars_held'] * 15, unit='m')
        
        sub_df = pd.merge_asof(
            sub_df.sort_values('time_utc'),
            m15[['time', 'body_ratio']].sort_values('time'),
            left_on='time_utc', right_on='time',
            direction='backward'
        ).drop(columns=['time_y'], errors='ignore')
        
        sub_df = pd.merge_asof(
            sub_df.sort_values('time_utc'),
            h1[['time', 'adx', 'atr']].sort_values('time'),
            left_on='time_utc', right_on='time',
            direction='backward',
            suffixes=('', '_h1')
        ).drop(columns=['time'], errors='ignore')
        
        sub_df['risk_atr'] = np.where(sub_df['atr'] > 0, sub_df['risk_dist'] / sub_df['atr'], np.nan)
        enriched_chunks.append(sub_df)

    df_all_enriched = pd.concat(enriched_chunks, ignore_index=True)
    print(f"Enriquecimiento completado en {time.time() - t0_start:.2f}s. Total filas enriquecidas: {len(df_all_enriched)}")

    # Clasificación por Familia
    SYNTH_CORE = set([
        'Boom 1000 Index', 'Boom 300 Index', 'Boom 500 Index', 'Boom 600 Index', 'Boom 900 Index',
        'Crash 1000 Index', 'Crash 300 Index', 'Crash 500 Index', 'Crash 600 Index', 'Crash 900 Index',
        'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'Jump 75 Index', 'Jump 100 Index',
        'Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500',
        'Volatility 10 Index', 'Volatility 15 Index', 'Volatility 25 Index', 'Volatility 50 Index',
        'Volatility 75 Index', 'Volatility 100 Index', 'Volatility 250 (1s) Index',
        'Volatility 50 (1s) Index', 'Volatility 75 (1s) Index', 'Volatility 90 Index'
    ])
    FOREX_ALL = set([
        'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY',
        'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
        'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD', 'USDCAD', 'USDCHF', 'USDJPY'
    ])
    METALS_INDICES_CRYPTO = set([
        'XAUUSD', 'XAGUSD', 'Wall Street 30', 'US Tech 100', 'US SP 500', 'BTCUSD', 'US Oil'
    ])

    def get_class(s):
        if s in SYNTH_CORE: return 'SINTETICO'
        elif s in FOREX_ALL: return 'FOREX'
        return 'METALES_INDICES_CRYPTO'

    df_all_enriched['asset_class'] = df_all_enriched['symbol'].apply(get_class)

    # =========================================================================
    # FASE 1: SINTÉTICOS (Replay 2 Años sobre TODOS los 29 Activos Sintéticos)
    # =========================================================================
    df_synth = df_all_enriched[df_all_enriched['asset_class'] == 'SINTETICO'].copy()
    c_s = (df_synth['adx'] >= 30.0) & (df_synth['risk_atr'] <= 1.5) & (df_synth['body_ratio'] >= 0.50)
    df_synth_exp = df_synth[c_s].copy().sort_values('time_utc').reset_index(drop=True)

    # Simulación Cap=1 Secuencial
    open_pos_s = []
    synth_accepted = []
    for idx, row in df_synth_exp.iterrows():
        t_entry = row['time_utc']
        open_pos_s = [t_exit for t_exit in open_pos_s if t_exit > t_entry]
        if len(open_pos_s) < 1:
            open_pos_s.append(row['exit_time_utc'])
            synth_accepted.append(row)

    df_phase1 = pd.DataFrame(synth_accepted)
    phase1_csv = out_dir / "replay_msnr_exp_fase1_sinteticos_all29_2y.csv"
    df_phase1.to_csv(phase1_csv, index=False)

    # =========================================================================
    # FASE 2: FOREX, METALES, CRIPTO E ÍNDICES (TODOS los 31 Activos Tradicionales)
    # =========================================================================
    df_trad = df_all_enriched[df_all_enriched['asset_class'].isin(['FOREX', 'METALES_INDICES_CRYPTO'])].copy()
    c_t = (df_trad['adx'] >= 30.0) & (df_trad['risk_atr'] <= 1.2)
    df_trad_exp = df_trad[c_t].copy().sort_values('time_utc').reset_index(drop=True)

    # Simulación Cap=1 Secuencial
    open_pos_t = []
    trad_accepted = []
    for idx, row in df_trad_exp.iterrows():
        t_entry = row['time_utc']
        open_pos_t = [t_exit for t_exit in open_pos_t if t_exit > t_entry]
        if len(open_pos_t) < 1:
            open_pos_t.append(row['exit_time_utc'])
            trad_accepted.append(row)

    df_phase2 = pd.DataFrame(trad_accepted)
    phase2_csv = out_dir / "replay_msnr_exp_fase2_tradicionales_all31_2y.csv"
    df_phase2.to_csv(phase2_csv, index=False)

    print("=" * 135)
    print("DATASETS GENERADOS Y ALMACENADOS EN DISCO LOCAL:")
    print(f"  * FASE 1 (Sintéticos - 29 Activos)     : {phase1_csv} ({len(df_phase1)} ops)")
    print(f"  * FASE 2 (Tradicionales - 31 Activos)  : {phase2_csv} ({len(df_phase2)} ops)")
    print("=" * 135)

    # =========================================================================
    # REPORTE FASE 1: SINTÉTICOS (RANKING COMPLETO DE LOS 29 ACTIVOS)
    # =========================================================================
    print("\n" + "=" * 135)
    print("FASE 1: RANKING Y CLASIFICACIÓN DE LOS 29 ACTIVOS SINTÉTICOS (REPLAY 2 AÑOS COMPLETO)")
    print("=" * 135)
    print(f"{'Activo Sintético':26s} | {'N':3s} | {'W':2s} | {'L':2s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Net PnL (R)':11s} | {'PF':5s} | {'Payoff':6s} | {'Exp (R)':8s} | {'MaxDD':6s} | {'Dictamen'}")
    print("-" * 135)

    p1_stats = []
    traded_synth = set(df_phase1['symbol'].unique()) if len(df_phase1) > 0 else set()
    for sym in sorted(list(SYNTH_CORE)):
        if sym in traded_synth:
            grp = df_phase1[df_phase1['symbol'] == sym]
            kp = compute_kpis(grp['rr'])
            estado = "RENTABLE (CONSERVAR)" if kp['net_r'] > 0 else ("NEUTRO" if kp['net_r'] == 0 else "NO RENTABLE (PODAR)")
            p1_stats.append({
                "symbol": sym, "n": kp['n'], "w": kp['wins'], "l": kp['losses'], "wr": kp['wr'],
                "ci_95": kp['ci_95'], "net_r": kp['net_r'], "pf": kp['pf'], "payoff": kp['payoff'],
                "exp_r": kp['exp_r'], "max_dd": kp['max_dd'], "estado": estado
            })
        else:
            raw_s = df_synth[df_synth['symbol'] == sym]
            p1_stats.append({
                "symbol": sym, "n": 0, "w": 0, "l": 0, "wr": 0.0,
                "ci_95": "[0.0%, 0.0%]", "net_r": 0.0, "pf": 0.0, "payoff": 0.0,
                "exp_r": 0.0, "max_dd": 0.0, "estado": "SIN OPERACIONES (BLOQUEADO EX ANTE)"
            })

    df_p1_rep = pd.DataFrame(p1_stats).sort_values(['net_r', 'n'], ascending=[False, False])
    for idx, r in df_p1_rep.iterrows():
        pf_str = f"{r['pf']:5.2f}" if r['pf'] < 100 else "  INF"
        print(f"{r['symbol']:26s} | {r['n']:3d} | {r['w']:2d} | {r['l']:2d} | {r['wr']:4.1f}% | {r['ci_95']:16s} | {r['net_r']:+10.2f} R | {pf_str} | {r['payoff']:6.2f} | {r['exp_r']:+7.4f}R | {r['max_dd']:5.2f}R | {r['estado']}")

    # =========================================================================
    # REPORTE FASE 2: TRADICIONALES (RANKING COMPLETO DE LOS 31 ACTIVOS)
    # =========================================================================
    print("\n" + "=" * 135)
    print("FASE 2: RANKING Y CLASIFICACIÓN DE LOS 31 ACTIVOS TRADICIONALES (MÁXIMA HISTORIA VERIFICABLE)")
    print("=" * 135)
    print(f"{'Activo Tradicional':26s} | {'N':3s} | {'W':2s} | {'L':2s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Net PnL (R)':11s} | {'PF':5s} | {'Payoff':6s} | {'Exp (R)':8s} | {'MaxDD':6s} | {'Dictamen'}")
    print("-" * 135)

    p2_stats = []
    all_trad_symbols = sorted(list(FOREX_ALL.union(METALS_INDICES_CRYPTO)))
    traded_trad = set(df_phase2['symbol'].unique()) if len(df_phase2) > 0 else set()
    for sym in all_trad_symbols:
        if sym in traded_trad:
            grp = df_phase2[df_phase2['symbol'] == sym]
            kp = compute_kpis(grp['rr'])
            estado = "RENTABLE (CONSERVAR)" if kp['net_r'] > 0 else ("NEUTRO" if kp['net_r'] == 0 else "NO RENTABLE (PODAR)")
            p2_stats.append({
                "symbol": sym, "n": kp['n'], "w": kp['wins'], "l": kp['losses'], "wr": kp['wr'],
                "ci_95": kp['ci_95'], "net_r": kp['net_r'], "pf": kp['pf'], "payoff": kp['payoff'],
                "exp_r": kp['exp_r'], "max_dd": kp['max_dd'], "estado": estado
            })
        else:
            p2_stats.append({
                "symbol": sym, "n": 0, "w": 0, "l": 0, "wr": 0.0,
                "ci_95": "[0.0%, 0.0%]", "net_r": 0.0, "pf": 0.0, "payoff": 0.0,
                "exp_r": 0.0, "max_dd": 0.0, "estado": "SIN OPERACIONES (BLOQUEADO EX ANTE)"
            })

    df_p2_rep = pd.DataFrame(p2_stats).sort_values(['net_r', 'n'], ascending=[False, False])
    for idx, r in df_p2_rep.iterrows():
        pf_str = f"{r['pf']:5.2f}" if r['pf'] < 100 else "  INF"
        print(f"{r['symbol']:26s} | {r['n']:3d} | {r['w']:2d} | {r['l']:2d} | {r['wr']:4.1f}% | {r['ci_95']:16s} | {r['net_r']:+10.2f} R | {pf_str} | {r['payoff']:6.2f} | {r['exp_r']:+7.4f}R | {r['max_dd']:5.2f}R | {r['estado']}")

if __name__ == '__main__':
    main()
