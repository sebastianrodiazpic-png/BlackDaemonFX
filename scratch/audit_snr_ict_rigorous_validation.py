"""
scratch/audit_snr_ict_rigorous_validation.py
Auditoría forense completa y rigurosa para Malaysian SNR (V4) e ICT (Sabri Malle).
Calcula con exactitud matemática:
1. Desglose de 4 folds de V4 (ADX >= 30 + ATR <= 1.5 + Cap=1), métricas, payoff, Wilson 95% CI.
2. Análisis de Cap=1: señales aceptadas vs bloqueadas, contrafactuales, sensibilidad a orden.
3. Desglose de los 23 activos canónicos de SNR (positivos, negativos, sin operaciones, días de cobertura).
4. Desglose de ICT por ventanas temporales, impacto del premarket NY (07:00-09:00), sesión de Londres, y degradación OOS.
5. Fricción observada vs escenarios de estrés (slippage y gaps).
6. Evaluación estadística de la meta 60-70% WR.
"""

import sys
from pathlib import Path
import math
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows console encoding
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054  # 95% confidence
    p = k / n
    denominator = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denominator
    spread = (z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denominator
    return (max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0)

def compute_detailed_stats(df: pd.DataFrame, label: str = "") -> dict:
    if len(df) == 0:
        return {
            "label": label, "n": 0, "wins": 0, "losses": 0, "wr": 0.0, "wilson_ci": (0.0, 0.0),
            "net_r": 0.0, "exp_r": 0.0, "payoff": 0.0, "pf": 0.0, "max_dd": 0.0
        }
    n = len(df)
    wins_df = df[df['rr'] > 0]
    losses_df = df[df['rr'] <= 0]
    k = len(wins_df)
    losses_count = len(losses_df)
    wr = (k / n) * 100.0
    w_ci = wilson_ci(k, n)
    net_r = float(df['rr'].sum())
    exp_r = float(df['rr'].mean())
    avg_win = float(wins_df['rr'].mean()) if k > 0 else 0.0
    avg_loss = float(abs(losses_df['rr'].mean())) if losses_count > 0 else 0.0
    payoff = (avg_win / avg_loss) if avg_loss > 0 else (99.0 if avg_win > 0 else 0.0)
    gross_win = float(wins_df['rr'].sum())
    gross_loss = float(abs(losses_df['rr'].sum()))
    pf = (gross_win / gross_loss) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
    cum = df['rr'].cumsum()
    max_dd = float((cum.cummax() - cum).max()) if len(cum) > 0 else 0.0
    return {
        "label": label, "n": n, "wins": k, "losses": losses_count, "wr": round(wr, 1),
        "wilson_ci": (round(w_ci[0], 1), round(w_ci[1], 1)),
        "net_r": round(net_r, 2), "exp_r": round(exp_r, 4),
        "avg_win": round(avg_win, 2), "avg_loss": round(avg_loss, 2),
        "payoff": round(payoff, 2), "pf": round(pf, 2), "max_dd": round(max_dd, 2)
    }

def simulate_concurrency_cap_detailed(trades_df: pd.DataFrame, max_open: int = 1) -> tuple:
    accepted = []
    blocked = []
    open_positions = []
    for idx, row in trades_df.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < max_open:
            accepted.append(row)
            open_positions.append(row['exit_time'])
        else:
            blocked.append(row)
    return pd.DataFrame(accepted), pd.DataFrame(blocked)

def run_audit():
    print("=" * 100)
    print("AUDITORÍA FORENSE MATEMÁTICA Y REPRODUCCIÓN INDEPENDIENTE: SNR (V4) E ICT")
    print("=" * 100)

    # ---------------------------------------------------------
    # 1. REPRODUCCIÓN DE MALAYSIAN SNR V4 (4 FOLDS WALK-FORWARD)
    # ---------------------------------------------------------
    df_msnr = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv')
    df_msnr['time'] = pd.to_datetime(df_msnr['time'], utc=True)
    df_msnr = df_msnr.sort_values('time').reset_index(drop=True)
    df_msnr['exit_time'] = df_msnr['time'] + pd.to_timedelta(df_msnr['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    allowed_snr = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df_snr_canon = df_msnr[df_msnr['symbol'].isin(allowed_snr)].reset_index(drop=True)

    total_snr = len(df_snr_canon)
    n_folds = 4
    start_train = total_snr // (n_folds + 1)
    step = (total_snr - start_train) // n_folds

    fold_v4_list = []
    fold_v2_list = []
    fold_blocked_list = []
    fold_details = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total_snr, train_end + step)
        
        split_time = df_snr_canon['time'].iloc[train_end]
        train_slice = df_snr_canon.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        test_slice = df_snr_canon.iloc[train_end:test_end].copy().reset_index(drop=True)
        
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        
        v4, blocked = simulate_concurrency_cap_detailed(v2, max_open=1)
        
        fold_v4_list.append(v4)
        fold_v2_list.append(v2)
        fold_blocked_list.append(blocked)
        
        t_start = test_slice['time'].min().strftime('%Y-%m-%d')
        t_end = test_slice['time'].max().strftime('%Y-%m-%d')
        
        st_v4 = compute_detailed_stats(v4, f"Fold {f+1} ({t_start} a {t_end})")
        fold_details.append(st_v4)

    df_v4_all = pd.concat(fold_v4_list, ignore_index=True) if len(fold_v4_list) > 0 else pd.DataFrame()
    df_v2_all = pd.concat(fold_v2_list, ignore_index=True) if len(fold_v2_list) > 0 else pd.DataFrame()
    df_blocked_all = pd.concat(fold_blocked_list, ignore_index=True) if len(fold_blocked_list) > 0 else pd.DataFrame()

    st_v4_total = compute_detailed_stats(df_v4_all, "V4 Total Walk-Forward (4 Folds)")
    st_v2_total = compute_detailed_stats(df_v2_all, "V2 Total (Sin Cap=1)")
    st_blocked_total = compute_detailed_stats(df_blocked_all, "Señales Bloqueadas por Cap=1")

    print("\n--- 1. DESGLOSE EXACTO DE LOS 4 FOLDS DE MALAYSIAN SNR V4 ---")
    print(f"{'Fold / Período':32s} | {'N':2s} | {'W/L':5s} | {'WR (%)':7s} | {'Wilson 95% CI':15s} | {'Net R':7s} | {'Exp (R)':8s} | {'Payoff':6s} | {'PF':5s} | {'MaxDD':6s}")
    print("-" * 105)
    for fd in fold_details:
        wl = f"{fd['wins']}/{fd['losses']}"
        ci_str = f"[{fd['wilson_ci'][0]:4.1f}%, {fd['wilson_ci'][1]:4.1f}%]"
        print(f"{fd['label']:32s} | {fd['n']:2d} | {wl:5s} | {fd['wr']:5.1f}% | {ci_str:15s} | {fd['net_r']:+7.2f} | {fd['exp_r']:+8.4f} | {fd['payoff']:6.2f} | {fd['pf']:5.2f} | {fd['max_dd']:5.2f}R")
    
    wl_tot = f"{st_v4_total['wins']}/{st_v4_total['losses']}"
    ci_tot_str = f"[{st_v4_total['wilson_ci'][0]:4.1f}%, {st_v4_total['wilson_ci'][1]:4.1f}%]"
    print("-" * 105)
    print(f"{st_v4_total['label']:32s} | {st_v4_total['n']:2d} | {wl_tot:5s} | {st_v4_total['wr']:5.1f}% | {ci_tot_str:15s} | {st_v4_total['net_r']:+7.2f} | {st_v4_total['exp_r']:+8.4f} | {st_v4_total['payoff']:6.2f} | {st_v4_total['pf']:5.2f} | {st_v4_total['max_dd']:5.2f}R")

    # ---------------------------------------------------------
    # 2. AUDITORÍA DE CAP=1 Y CONTRAFACTUALES
    # ---------------------------------------------------------
    print("\n--- 2. AUDITORÍA DE CONCURRENCIA CAP=1 (ACEPTADAS VS BLOQUEADAS) ---")
    print(f"Total evaluadas antes de Cap=1 (V2): N={st_v2_total['n']}, Net R={st_v2_total['net_r']:+0.2f}R, WR={st_v2_total['wr']}%, PF={st_v2_total['pf']}, MaxDD={st_v2_total['max_dd']}R")
    print(f"Aceptadas bajo Cap=1 (V4)          : N={st_v4_total['n']}, Net R={st_v4_total['net_r']:+0.2f}R, WR={st_v4_total['wr']}%, PF={st_v4_total['pf']}, MaxDD={st_v4_total['max_dd']}R")
    print(f"Bloqueadas por Cap=1 (Contrafactual): N={st_blocked_total['n']}, Net R={st_blocked_total['net_r']:+0.2f}R, WR={st_blocked_total['wr']}%, PF={st_blocked_total['pf']}")
    if len(df_blocked_all) > 0:
        print("Detalle de señales bloqueadas:")
        for idx, brow in df_blocked_all.iterrows():
            print(f"  - Fecha: {brow['time'].strftime('%Y-%m-%d %H:%M')} | Activo: {brow['symbol']:18s} | Dir: {brow['direction']:4s} | Esc: {brow['scenario']} | RR: {brow['rr']:+5.2f}R")

    # ---------------------------------------------------------
    # 3. SENSIBILIDAD A FRICCIÓN (OBSERVADA VS ESCENARIOS SEVEROS)
    # ---------------------------------------------------------
    print("\n--- 3. SENSIBILIDAD A FRICCIÓN SOBRE V4 (N=40) ---")
    scenarios = [
        ("Base (Spread Real de MT5)", 0.0, 0.0),
        ("Fricción Baja (+0.025R slippage, 10% gap SL)", 0.025, 0.10),
        ("Fricción Moderada (+0.05R slippage, 15% gap SL)", 0.050, 0.15),
        ("Fricción Severa (+0.10R slippage, 20% gap SL)", 0.100, 0.20),
        ("Fricción Extrema (+0.15R slippage, 25% gap SL)", 0.150, 0.25)
    ]
    print(f"{'Escenario de Fricción':48s} | {'Net R':7s} | {'Exp (R)':8s} | {'PF':5s} | {'MaxDD':6s}")
    print("-" * 80)
    for sname, slip_r, gap_pct in scenarios:
        rr = df_v4_all['rr'].copy()
        if slip_r > 0:
            rr -= slip_r
        if gap_pct > 0:
            lmask = rr < 0
            rr[lmask] -= abs(rr[lmask]) * gap_pct
        n_sc = len(rr)
        net_sc = rr.sum()
        exp_sc = rr.mean()
        gw = rr[rr > 0].sum()
        gl = abs(rr[rr <= 0].sum())
        pf_sc = (gw / gl) if gl > 0 else 99.0
        cum_sc = rr.cumsum()
        dd_sc = float((cum_sc.cummax() - cum_sc).max()) if len(cum_sc) > 0 else 0.0
        print(f"{sname:48s} | {net_sc:+7.2f} | {exp_sc:+8.4f} | {pf_sc:5.2f} | {dd_sc:5.2f}R")

    # ---------------------------------------------------------
    # 4. DESGLOSE POR ACTIVO Y DIRECCIÓN DE V4
    # ---------------------------------------------------------
    print("\n--- 4. DESGLOSE DE V4 POR ACTIVO Y DIRECCIÓN ---")
    by_sym_v4 = df_v4_all.groupby('symbol').apply(lambda g: compute_detailed_stats(g, g.name)).tolist()
    print(f"{'Activo':22s} | {'N':2s} | {'W/L':5s} | {'WR (%)':7s} | {'Net R':7s} | {'Exp (R)':8s} | {'PF':5s} | {'MaxDD':6s}")
    print("-" * 75)
    for sa in sorted(by_sym_v4, key=lambda x: x['net_r'], reverse=True):
        wl = f"{sa['wins']}/{sa['losses']}"
        print(f"{sa['label']:22s} | {sa['n']:2d} | {wl:5s} | {sa['wr']:5.1f}% | {sa['net_r']:+7.2f} | {sa['exp_r']:+8.4f} | {sa['pf']:5.2f} | {sa['max_dd']:5.2f}R")

    by_dir_v4 = df_v4_all.groupby('direction').apply(lambda g: compute_detailed_stats(g, g.name)).tolist()
    print("\nPor Dirección:")
    for sd in by_dir_v4:
        wl = f"{sd['wins']}/{sd['losses']}"
        print(f"  {sd['label']:5s} | N={sd['n']:2d} | W/L: {wl:5s} | WR: {sd['wr']:5.1f}% | Net R: {sd['net_r']:+7.2f}R | Exp: {sd['exp_r']:+8.4f}R | PF: {sd['pf']:5.2f} | MaxDD: {sd['max_dd']:5.2f}R")

    # ---------------------------------------------------------
    # 5. DENOMINADOR INSTITUCIONAL: LOS 23 ACTIVOS CANÓNICOS DE SNR
    # ---------------------------------------------------------
    print("\n--- 5. DENOMINADOR INSTITUCIONAL DE LOS 23 ACTIVOS DE MALAYSIAN SNR ---")
    # Chequear días de cobertura para cada activo en local
    raw_pbar = PROJECT_ROOT / 'storage' / 'bars'
    cov_dict = {}
    for sym in sorted(list(allowed_snr)):
        # Buscar pkl
        clean_name = sym.replace(' ', '_').replace('(', '').replace(')', '')
        candidates = list(raw_pbar.glob(f"{clean_name}_M15.pkl")) + list(raw_pbar.glob(f"{sym}_M15.pkl"))
        if not candidates:
            # check M5
            candidates = list(raw_pbar.glob(f"{clean_name}_M5.pkl")) + list(raw_pbar.glob(f"{sym}_M5.pkl"))
        if candidates:
            import pickle
            try:
                with open(candidates[0], 'rb') as f:
                    bdata = pickle.load(f)
                if isinstance(bdata, pd.DataFrame) and len(bdata) > 0:
                    span_days = (bdata.index.max() - bdata.index.min()).days
                    cov_dict[sym] = f"{span_days} días ({len(bdata)} barras)"
                else:
                    cov_dict[sym] = "Vacío"
            except Exception as e:
                cov_dict[sym] = f"Error: {e}"
        else:
            cov_dict[sym] = "No existe archivo local"

    # En df_v4_all
    v4_syms = set(df_v4_all['symbol'].unique())
    pos_v4 = set(df_v4_all.groupby('symbol')['rr'].sum()[lambda x: x > 0].index)
    neg_v4 = set(df_v4_all.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    zero_v4 = set(df_v4_all.groupby('symbol')['rr'].sum()[lambda x: x == 0].index)
    no_trade_v4 = allowed_snr - v4_syms

    print(f"Total configurados: 23")
    print(f"Activos con PnL Positivo en V4 (N={len(pos_v4)}): {sorted(list(pos_v4))}")
    print(f"Activos con PnL Negativo en V4 (N={len(neg_v4)}): {sorted(list(neg_v4))}")
    print(f"Activos con PnL Neutro (0.0R) en V4 (N={len(zero_v4)}): {sorted(list(zero_v4))}")
    print(f"Activos Sin Operaciones en V4 (N={len(no_trade_v4)}): {sorted(list(no_trade_v4))}")
    print("\nDetalle de Cobertura de Datos Locales por Activo:")
    for sym in sorted(list(allowed_snr)):
        pnl = df_v4_all[df_v4_all['symbol'] == sym]['rr'].sum() if sym in v4_syms else 0.0
        n_ops = len(df_v4_all[df_v4_all['symbol'] == sym]) if sym in v4_syms else 0
        print(f"  {sym:24s} | Ops: {n_ops:2d} | Net R: {pnl:+6.2f}R | Cobertura: {cov_dict.get(sym, 'N/A')}")

    # ---------------------------------------------------------
    # 6. EVALUACIÓN FORENSE INDEPENDIENTE DE ICT (SABRI MALLE)
    # ---------------------------------------------------------
    print("\n--- 6. EVALUACIÓN FORENSE INDEPENDIENTE DE ICT (SABRI MALLE) ---")
    df_ict = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'ict_faithful_trades.csv')
    df_ict['time'] = pd.to_datetime(df_ict['time'], utc=True)
    df_ict = df_ict.sort_values('time').reset_index(drop=True)
    ict_canon = set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])
    df_ict_canon = df_ict[df_ict['symbol'].isin(ict_canon)].reset_index(drop=True)

    # Sesiones y horas: Premarket NY (07:00 y 08:00 NY)
    # Ver desglose de horas NY
    print("Desglose de ICT por Hora NY (Foco Premarket 07:00-09:00):")
    hr_pnl = df_ict_canon.groupby('ny_hour')['rr'].agg(['count', 'sum', 'mean']).reset_index()
    print(f"{'Hora NY':8s} | {'N':4s} | {'Net R':7s} | {'Exp (R)':8s}")
    print("-" * 35)
    for idx, r in hr_pnl.iterrows():
        print(f"Hora {int(r['ny_hour']):02d}    | {int(r['count']):4d} | {r['sum']:+7.2f} | {r['mean']:+8.4f}")

    # Separar Londres vs NY
    # Londres suele ser horas 02:00 a 05:00 NY; Premarket 07:00-09:00 NY; Core NY 09:30-16:00
    df_ict_canon['session_bucket'] = 'Other'
    df_ict_canon.loc[df_ict_canon['ny_hour'].isin([2, 3, 4, 5]), 'session_bucket'] = 'London (02-05 NY)'
    df_ict_canon.loc[df_ict_canon['ny_hour'].isin([7, 8]), 'session_bucket'] = 'Premarket NY (07-08 NY)'
    df_ict_canon.loc[df_ict_canon['ny_hour'].isin([9, 10, 11, 12, 13, 14, 15]), 'session_bucket'] = 'Core NY (09-15 NY)'

    print("\nDesglose de ICT por Bloque de Sesión:")
    for sess, sdf in df_ict_canon.groupby('session_bucket'):
        st_sess = compute_detailed_stats(sdf, sess)
        print(f"  {st_sess['label']:24s} | N={st_sess['n']:3d} | WR: {st_sess['wr']:4.1f}% | Net R: {st_sess['net_r']:+7.2f}R | Exp: {st_sess['exp_r']:+8.4f}R | PF: {st_sess['pf']:4.2f}")

    # Ventanas temporales de Londres (para ver cómo la ventana reciente fue negativa)
    df_london = df_ict_canon[df_ict_canon['session_bucket'] == 'London (02-05 NY)'].copy().reset_index(drop=True)
    if len(df_london) > 0:
        n_l = len(df_london)
        w_size = n_l // 3
        print("\nDesglose de Londres en 3 Ventanas Cronológicas:")
        for w_idx in range(3):
            sub_w = df_london.iloc[w_idx*w_size : (w_idx+1)*w_size if w_idx < 2 else n_l]
            t_s = sub_w['time'].min().strftime('%Y-%m-%d')
            t_e = sub_w['time'].max().strftime('%Y-%m-%d')
            st_lw = compute_detailed_stats(sub_w, f"Londres Ventana {w_idx+1} ({t_s} a {t_e})")
            print(f"  {st_lw['label']:36s} | N={st_lw['n']:2d} | Net R: {st_lw['net_r']:+6.2f}R | Exp: {st_lw['exp_r']:+7.4f}R | PF: {st_lw['pf']:4.2f}")

    # ---------------------------------------------------------
    # 7. EVALUACIÓN ESTADÍSTICA DE LA META 60-70% WIN RATE
    # ---------------------------------------------------------
    print("\n--- 7. EVALUACIÓN ESTADÍSTICA DE LA META DE WIN RATE (60-70%) ---")
    print(f"V4 Observado: N={st_v4_total['n']}, Aciertos={st_v4_total['wins']}, Fallos={st_v4_total['losses']}")
    print(f"Win Rate puntual: {st_v4_total['wr']:.1f}%")
    print(f"Intervalo Wilson al 95%: [{st_v4_total['wilson_ci'][0]:.1f}%, {st_v4_total['wilson_ci'][1]:.1f}%]")
    print(f"Expectativa por trade: {st_v4_total['exp_r']:+0.4f} R | Payoff: {st_v4_total['payoff']:.2f}")

if __name__ == '__main__':
    run_audit()
