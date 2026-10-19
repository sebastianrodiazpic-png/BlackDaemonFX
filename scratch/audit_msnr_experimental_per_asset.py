"""
scratch/audit_msnr_experimental_per_asset.py
============================================
Auditoría y desglose exhaustivo por activo de la estrategia:
MSNR Variante Experimental (ATR Met/Fx <= 1.2 + Body Ratio >= 0.50 en Sintéticos, ADX >= 30, Cap=1)
sobre el universo completo canónico y análisis de cobertura de datos disponible.
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

def main():
    csv_path = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)

    synths = set([
        'Boom 1000 Index', 'Boom 300 Index', 'Crash 1000 Index', 'Crash 600 Index',
        'Jump 10 Index', 'Jump 25 Index', 'Step Index', 'Step Index 200',
        'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
        'Volatility 90 Index'
    ])
    forex = set(['AUDNZD', 'EURCHF', 'EURGBP', 'EURUSD', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'USDJPY'])
    metals_indices = set(['XAUUSD', 'XAGUSD', 'Wall Street 30'])

    def get_subfamily(sym):
        if sym in synths:
            return 'SINTÉTICOS'
        elif sym in forex:
            return 'FOREX'
        elif sym in metals_indices:
            return 'METALES/ÍNDICES'
        return 'OTROS'

    df['subfamily'] = df['symbol'].apply(get_subfamily)

    # Filtros de MSNR Experimental (Combinación 1)
    c_mf = (df['subfamily'].isin(['FOREX', 'METALES/ÍNDICES'])) & (df['adx'] >= 30.0) & (df['risk_atr'] <= 1.2)
    c_s = (df['subfamily'] == 'SINTÉTICOS') & (df['adx'] >= 30.0) & (df['risk_atr'] <= 1.5) & (df['body_ratio'] >= 0.50)
    df_exp = df[c_mf | c_s].copy()

    # Simulación Cap=1 estricta secuencial
    open_positions = []
    accepted = []
    blocked = []
    for idx, row in df_exp.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < 1:
            open_positions.append(row['exit_time'])
            accepted.append(row)
        else:
            blocked.append(row)

    df_cap1 = pd.DataFrame(accepted)
    df_blocked = pd.DataFrame(blocked)

    print("=" * 120)
    print("ESTADÍSTICAS GLOBALES: MSNR VARIANTE EXPERIMENTAL (ATR Met/Fx<=1.2, Body>=0.50, Cap=1)")
    print("=" * 120)
    n_tot = len(df_cap1)
    wins = (df_cap1['rr'] > 0).sum()
    losses = (df_cap1['rr'] < 0).sum()
    net_pnl = df_cap1['rr'].sum()
    wr = 100.0 * wins / n_tot if n_tot > 0 else 0.0
    ci_w = wilson_score_interval(wins, n_tot)
    gross_w = df_cap1[df_cap1['rr'] > 0]['rr'].sum()
    gross_l = abs(df_cap1[df_cap1['rr'] < 0]['rr'].sum())
    pf = gross_w / gross_l if gross_l > 0 else 999.0
    payoff = (gross_w / wins) / (gross_l / losses) if (wins > 0 and losses > 0 and gross_l > 0) else 0.0
    exp_r = net_pnl / n_tot if n_tot > 0 else 0.0

    # Max Drawdown
    equity = df_cap1['rr'].cumsum()
    peak = equity.cummax()
    dd = peak - equity
    max_dd = dd.max()

    print(f"Total Operaciones (N):      {n_tot}")
    print(f"Ganadoras (W) / Perdedoras: {wins} / {losses}")
    print(f"Win Rate:                   {wr:.1f}% (IC Wilson 95%: [{ci_w[0]}%, {ci_w[1]}%])")
    print(f"Profit Factor (PF):         {pf:.2f}")
    print(f"Payoff (Ratio Gan/Pérd):    {payoff:.2f}")
    print(f"Expectativa por Operación:  {exp_r:+.4f} R/op")
    print(f"PnL Neto Total:             {net_pnl:+.2f} R")
    print(f"Máximo Drawdown (MaxDD):    {max_dd:.2f} R")
    print(f"Señales Bloqueadas (Cap=1): {len(df_blocked)} señales (PnL Contrafactual: {df_blocked['rr'].sum():+.2f} R)")

    print("\n" + "=" * 120)
    print("DESGLOSE POR ACTIVO: RANKING DE RENTABILIDAD")
    print("=" * 120)
    print(f"{'Activo':26s} | {'Familia':15s} | {'N':2s} | {'W':2s} | {'L':2s} | {'Win%':5s} | {'Net PnL (R)':11s} | {'PF':5s} | {'Payoff':6s} | {'Exp (R)':8s} | {'MaxDD':6s} | {'Estado'}")
    print("-" * 120)

    sym_stats = []
    for sym, grp in df_cap1.groupby('symbol'):
        n = len(grp)
        w = (grp['rr'] > 0).sum()
        l = (grp['rr'] < 0).sum()
        s_wr = 100.0 * w / n if n > 0 else 0.0
        s_pnl = grp['rr'].sum()
        gw = grp[grp['rr'] > 0]['rr'].sum()
        gl = abs(grp[grp['rr'] < 0]['rr'].sum())
        s_pf = gw / gl if gl > 0 else (999.0 if gw > 0 else 0.0)
        s_payoff = (gw / w) / (gl / l) if (w > 0 and l > 0 and gl > 0) else (gw / w if w > 0 else 0.0)
        s_exp = s_pnl / n if n > 0 else 0.0
        
        # MaxDD
        eq = grp['rr'].cumsum()
        pk = eq.cummax()
        s_dd = (pk - eq).max()
        
        fam = grp['subfamily'].iloc[0]
        estado = "RENTABLE" if s_pnl > 0 else ("NEUTRO" if s_pnl == 0 else "NO RENTABLE (PÉRDIDAS)")
        sym_stats.append({
            'symbol': sym, 'family': fam, 'n': n, 'w': w, 'l': l,
            'wr': s_wr, 'net_r': s_pnl, 'pf': s_pf, 'payoff': s_payoff,
            'exp_r': s_exp, 'max_dd': s_dd, 'estado': estado
        })

    df_sym = pd.DataFrame(sym_stats).sort_values('net_r', ascending=False)
    for idx, r in df_sym.iterrows():
        pf_str = f"{r['pf']:5.2f}" if r['pf'] < 100 else "  INF"
        print(f"{r['symbol']:26s} | {r['family']:15s} | {r['n']:2d} | {r['w']:2d} | {r['l']:2d} | {r['wr']:4.1f}% | {r['net_r']:+10.2f} R | {pf_str} | {r['payoff']:6.2f} | {r['exp_r']:+7.4f}R | {r['max_dd']:5.2f}R | {r['estado']}")

    print("\n" + "=" * 120)
    print("DESGLOSE POR FAMILIA DE ACTIVOS")
    print("=" * 120)
    for fam, grp in df_cap1.groupby('subfamily'):
        fn = len(grp)
        fw = (grp['rr'] > 0).sum()
        fl = (grp['rr'] < 0).sum()
        f_wr = 100.0 * fw / fn if fn > 0 else 0.0
        f_pnl = grp['rr'].sum()
        fgw = grp[grp['rr'] > 0]['rr'].sum()
        fgl = abs(grp[grp['rr'] < 0]['rr'].sum())
        f_pf = fgw / fgl if fgl > 0 else 999.0
        f_exp = f_pnl / fn if fn > 0 else 0.0
        pf_str = f"{f_pf:5.2f}" if f_pf < 100 else "  INF"
        print(f"Familia {fam:16s} | N={fn:2d} (W:{fw:2d}, L:{fl:2d}) | WR: {f_wr:4.1f}% | Net: {f_pnl:+7.2f} R | PF: {pf_str} | Exp: {f_exp:+7.4f} R/op")

    print("\n" + "=" * 120)
    print("ACTIVOS CANÓNICOS SIN OPERACIONES FILTRADAS (N=0 tras filtros ADX/ATR/Body y Cap=1)")
    print("=" * 120)
    all_23 = sorted(df['symbol'].unique())
    traded = set(df_cap1['symbol'].unique())
    zero_trades = [s for s in all_23 if s not in traded]
    for s in zero_trades:
        raw_s = df[df['symbol'] == s]
        print(f"  * {s:26s} (Señales brutas: {len(raw_s):2d} | PnL bruto sin filtro: {raw_s['rr'].sum():+6.2f} R -> Bloqueado por filtros de régimen)")

if __name__ == '__main__':
    main()
