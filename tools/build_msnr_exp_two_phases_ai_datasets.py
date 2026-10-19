"""
tools/build_msnr_exp_two_phases_ai_datasets.py
==============================================
Generación, almacenamiento y reporte estadístico en dos fases de MSNR Variante Experimental:
- Fase 1: Sintéticos (Replay de 2 años sobre todos los activos sintéticos disponibles).
- Fase 2: Forex, Metales, Criptos e Índices (Replay sobre la máxima historia verificable disponible).
- Almacenamiento local con vectores de características completos para entrenamiento de modelos de IA.
- Clasificación de activos: Más rentables vs Candidatos a Poda.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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
    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cargar el dataset limpio canónico de 23 activos
    p_clean = PROJECT_ROOT / 'scratch' / 'msnr_complete_23_faithful_trades_clean.csv'
    df_clean = pd.read_csv(p_clean)
    df_clean['time'] = pd.to_datetime(df_clean['time'], utc=True)
    df_clean['exit_time'] = pd.to_datetime(df_clean['exit_time'], utc=True)

    # 2. Cargar los símbolos adicionales no canónicos de msnr_faithful_trades.csv (BTCUSD, US Tech 100, US Oil, Vol 10, Vol 25, Vol 75)
    p_orig = PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv'
    df_orig = pd.read_csv(p_orig)
    df_orig['time'] = pd.to_datetime(df_orig['time'], utc=True)
    df_orig['exit_time'] = df_orig['time'] + pd.to_timedelta(df_orig['bars'] * 15, unit='m')
    
    extra_syms = ['BTCUSD', 'US Tech 100', 'US Oil', 'Volatility 10 Index', 'Volatility 25 Index', 'Volatility 75 Index']
    df_extra = df_orig[df_orig['symbol'].isin(extra_syms)].copy()

    # Combinar en catálogo completo fiel
    df_all = pd.concat([df_clean, df_extra], ignore_index=True)
    df_all = df_all.sort_values('time').drop_duplicates(['symbol', 'time']).reset_index(drop=True)

    # Categorización
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

    def assign_class(s):
        if s in SYNTH_CORE: return 'SINTETICO'
        elif s in FOREX_ALL: return 'FOREX'
        elif s in METALS_INDICES_CRYPTO: return 'METALES_INDICES_CRYPTO'
        return 'OTRO'

    df_all['asset_class'] = df_all['symbol'].apply(assign_class)

    # =========================================================================
    # FASE 1: SINTÉTICOS (Replay 2 Años)
    # =========================================================================
    df_synth = df_all[df_all['asset_class'] == 'SINTETICO'].copy()
    
    # Filtro MSNR Experimental para Sintéticos: ADX >= 30, ATR <= 1.5, Body Ratio >= 0.50
    c_s = (df_synth['adx'] >= 30.0) & (df_synth['risk_atr'] <= 1.5) & (df_synth['body_ratio'] >= 0.50)
    df_synth_exp = df_synth[c_s].copy().sort_values('time').reset_index(drop=True)

    # Simular Cap=1 secuencial sobre Sintéticos
    open_pos = []
    synth_accepted = []
    synth_blocked = []
    for idx, row in df_synth_exp.iterrows():
        t_entry = row['time']
        open_pos = [t_exit for t_exit in open_pos if t_exit > t_entry]
        if len(open_pos) < 1:
            open_pos.append(row['exit_time'])
            synth_accepted.append(row)
        else:
            synth_blocked.append(row)

    df_phase1 = pd.DataFrame(synth_accepted)
    phase1_csv = out_dir / "replay_msnr_exp_fase1_sinteticos_2y.csv"
    df_phase1.to_csv(phase1_csv, index=False)

    # =========================================================================
    # FASE 2: FOREX, CRIPTOS, METALES, ÍNDICES (Máxima Historia Verificable)
    # =========================================================================
    df_trad = df_all[df_all['asset_class'].isin(['FOREX', 'METALES_INDICES_CRYPTO'])].copy()
    
    # Filtro MSNR Experimental para Tradicionales: ADX >= 30, ATR <= 1.2
    c_t = (df_trad['adx'] >= 30.0) & (df_trad['risk_atr'] <= 1.2)
    df_trad_exp = df_trad[c_t].copy().sort_values('time').reset_index(drop=True)

    # Simular Cap=1 secuencial sobre Tradicionales
    open_pos_t = []
    trad_accepted = []
    trad_blocked = []
    for idx, row in df_trad_exp.iterrows():
        t_entry = row['time']
        open_pos_t = [t_exit for t_exit in open_pos_t if t_exit > t_entry]
        if len(open_pos_t) < 1:
            open_pos_t.append(row['exit_time'])
            trad_accepted.append(row)
        else:
            trad_blocked.append(row)

    df_phase2 = pd.DataFrame(trad_accepted)
    phase2_csv = out_dir / "replay_msnr_exp_fase2_forex_metals_crypto.csv"
    df_phase2.to_csv(phase2_csv, index=False)

    print("=" * 125)
    print("ARCHIVOS ALMACENADOS LOCALMENTE PARA ENTRENAMIENTO DE IA:")
    print(f"  * Fase 1 (Sintéticos 2Y)       : {phase1_csv} ({len(df_phase1)} trades)")
    print(f"  * Fase 2 (Forex/Metales/Crypto): {phase2_csv} ({len(df_phase2)} trades)")
    print("=" * 125)

    # 3. Reporte de Estadísticas Fase 1
    print("\n" + "=" * 125)
    print("FASE 1: RESULTADOS POR ACTIVO SINTÉTICO (2 AÑOS) - CANDIDATOS RENTABLES VS PODA")
    print("=" * 125)
    p1_stats = []
    for sym, grp in df_phase1.groupby('symbol'):
        kp = compute_kpis(grp['rr'])
        estado = "RENTABLE (CONSERVAR)" if kp['net_r'] > 0 else ("NEUTRO" if kp['net_r'] == 0 else "NO RENTABLE (CANDIDATO A PODA)")
        p1_stats.append({
            "symbol": sym, "n": kp['n'], "w": kp['wins'], "l": kp['losses'], "wr": kp['wr'],
            "ci_95": kp['ci_95'], "net_r": kp['net_r'], "pf": kp['pf'], "payoff": kp['payoff'], "exp_r": kp['exp_r'],
            "max_dd": kp['max_dd'], "estado": estado
        })
    df_p1_rep = pd.DataFrame(p1_stats).sort_values('net_r', ascending=False)
    print(f"{'Activo Sintético':26s} | {'N':2s} | {'W':2s} | {'L':2s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Net PnL (R)':11s} | {'PF':5s} | {'Payoff':6s} | {'Exp (R)':8s} | {'MaxDD':6s} | {'Dictamen'}")
    print("-" * 135)
    for idx, r in df_p1_rep.iterrows():
        pf_str = f"{r['pf']:5.2f}" if r['pf'] < 100 else "  INF"
        print(f"{r['symbol']:26s} | {r['n']:2d} | {r['w']:2d} | {r['l']:2d} | {r['wr']:4.1f}% | {r['ci_95']:16s} | {r['net_r']:+10.2f} R | {pf_str} | {r['payoff']:6.2f} | {r['exp_r']:+7.4f}R | {r['max_dd']:5.2f}R | {r['estado']}")

    # 4. Reporte de Estadísticas Fase 2
    print("\n" + "=" * 125)
    print("FASE 2: RESULTADOS POR ACTIVO FOREX, METALES, CRIPTO E ÍNDICES (MÁXIMA HISTORIA VERIFICABLE)")
    print("=" * 125)
    p2_stats = []
    for sym, grp in df_phase2.groupby('symbol'):
        kp = compute_kpis(grp['rr'])
        estado = "RENTABLE (CONSERVAR)" if kp['net_r'] > 0 else ("NEUTRO" if kp['net_r'] == 0 else "NO RENTABLE (CANDIDATO A PODA)")
        p2_stats.append({
            "symbol": sym, "n": kp['n'], "w": kp['wins'], "l": kp['losses'], "wr": kp['wr'],
            "ci_95": kp['ci_95'], "net_r": kp['net_r'], "pf": kp['pf'], "payoff": kp['payoff'], "exp_r": kp['exp_r'],
            "max_dd": kp['max_dd'], "estado": estado
        })
    df_p2_rep = pd.DataFrame(p2_stats).sort_values('net_r', ascending=False)
    print(f"{'Activo Tradicional':26s} | {'N':2s} | {'W':2s} | {'L':2s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Net PnL (R)':11s} | {'PF':5s} | {'Payoff':6s} | {'Exp (R)':8s} | {'MaxDD':6s} | {'Dictamen'}")
    print("-" * 135)
    for idx, r in df_p2_rep.iterrows():
        pf_str = f"{r['pf']:5.2f}" if r['pf'] < 100 else "  INF"
        print(f"{r['symbol']:26s} | {r['n']:2d} | {r['w']:2d} | {r['l']:2d} | {r['wr']:4.1f}% | {r['ci_95']:16s} | {r['net_r']:+10.2f} R | {pf_str} | {r['payoff']:6.2f} | {r['exp_r']:+7.4f}R | {r['max_dd']:5.2f}R | {r['estado']}")

if __name__ == '__main__':
    main()
