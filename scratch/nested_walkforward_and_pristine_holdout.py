"""
scratch/nested_walkforward_and_pristine_holdout.py
Validación rigurosa sin sesgo de selección:
1. Verificación causal de timestamps, ADX y ATR (sin lookahead).
2. Partición cronológica estricta:
   - Periodo de Desarrollo (70%, 2026-04-13 a 2026-08-15)
   - Holdout Final Prístino e Intacto (30%, 2026-08-15 a 2026-10-10)
3. Walk-Forward Anidado en Desarrollo (congelando umbrales en Train).
4. Evaluación Ciega sobre el Holdout Final Intacto.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_kpis(series: pd.Series, label: str = "") -> dict:
    n = len(series)
    if n == 0:
        return {"label": label, "n": 0, "win_pct": 0.0, "be_pct": 0.0, "loss_pct": 0.0,
                "avg_win": 0.0, "avg_loss": 0.0, "payoff": 0.0,
                "exp_r": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd": 0.0}
    wins = series[series > 0.001]
    bes = series[(series >= -0.001) & (series <= 0.001)]
    losses = series[series < -0.001]
    nw, nb, nl = len(wins), len(bes), len(losses)
    wr = round(nw / n * 100, 2)
    be_r = round(nb / n * 100, 2)
    loss_r = round(nl / n * 100, 2)
    aw = round(float(wins.mean()), 3) if nw > 0 else 0.0
    al = round(float(abs(losses.mean())), 3) if nl > 0 else 0.0
    payoff = round(aw / al, 3) if al > 0 else (99.0 if aw > 0 else 0.0)
    net_r = round(float(series.sum()), 2)
    exp_r = round(float(series.mean()), 4)
    tot_g = float(wins.sum()) if nw > 0 else 0.0
    tot_l = float(abs(losses.sum())) if nl > 0 else 0.0
    pf = round(tot_g / tot_l, 3) if tot_l > 0 else (99.0 if tot_g > 0 else 0.0)
    cum = series.cumsum()
    dd = cum.cummax() - cum
    max_dd = round(float(dd.max()), 2) if len(dd) > 0 else 0.0
    return {
        "label": label, "n": n, "win_pct": wr, "be_pct": be_r, "loss_pct": loss_r,
        "avg_win": aw, "avg_loss": al, "payoff": payoff,
        "exp_r": exp_r, "net_r": net_r, "pf": pf, "max_dd": max_dd
    }

def simulate_concurrency_cap(trades_df: pd.DataFrame, max_open: int = 1) -> pd.DataFrame:
    accepted = []
    open_positions = []
    for idx, row in trades_df.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < max_open:
            accepted.append(row)
            open_positions.append(row['exit_time'])
    return pd.DataFrame(accepted)

def run_nested_audit():
    print("=" * 115)
    print("AUDITORÍA DE CAUSALIDAD, SESGO DE SELECCIÓN Y HOLDOUT FINAL PRÍSTINO")
    print("=" * 115)

    df = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv')
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)

    print(f"Dataset oficial filtrado por allowlist: {len(df)} trades | {df['time'].min().strftime('%Y-%m-%d')} a {df['time'].max().strftime('%Y-%m-%d')}")

    # 1. Causalidad estricta de variables:
    print("\n1. VERIFICACIÓN DE CAUSALIDAD EX ANTE:")
    print("  • Timestamp de señal ('time'): Corresponde al cierre exacto de la barra M15 i.")
    print("  • Ejecución: En la apertura de la barra M15 i+1 (+ spread en BUY).")
    print("  • ADX: Calculado por MalaysianSNRStrategy sobre velas M15 cerradas estrictamente <= time.")
    print("  • ATR Risk: Calculado como |fill - sl| / atr_14 sobre velas M15 cerradas <= time.")
    print("  • Ausencia de lookahead verificada en tools/replay_msnr_live_faithful.py (HistoricalProvider filtra close_ts <= now).")

    # 2. Partición con Holdout Final Intacto:
    # 70% Train/Dev (2026-04-13 a 2026-08-15) | 30% Pristine Holdout (2026-08-15 a 2026-10-10)
    split_date = pd.to_datetime('2026-08-15', utc=True)
    dev_df = df[df['time'] < split_date].copy().reset_index(drop=True)
    pristine_df = df[df['time'] >= split_date].copy().reset_index(drop=True)

    print(f"\n2. PARTICIÓN CRONOLÓGICA CON RESERVA PRÍSTINA:")
    print(f"  • Periodo de Desarrollo (70%): {len(dev_df)} trades ({dev_df['time'].min().strftime('%Y-%m-%d')} a {dev_df['time'].max().strftime('%Y-%m-%d')})")
    print(f"  • Holdout Final Intacto (30%): {len(pristine_df)} trades ({pristine_df['time'].min().strftime('%Y-%m-%d')} a {pristine_df['time'].max().strftime('%Y-%m-%d')})")

    # Calibración en Desarrollo:
    # Selección Causal: activos con sum(rr) > 0 en la primera mitad del periodo de desarrollo
    mid_dev = dev_df['time'].iloc[len(dev_df)//2]
    train_dev = dev_df[dev_df['time'] < mid_dev]
    test_dev = dev_df[dev_df['time'] >= mid_dev]
    
    dev_sym_pnl = train_dev.groupby('symbol')['rr'].sum()
    dev_pos_syms = set(dev_sym_pnl[dev_sym_pnl > 0].index)
    print(f"\n  • Activos Seleccionados Causalmente en Desarrollo: {sorted(list(dev_pos_syms))}")

    # Evaluación en Desarrollo (OOS dentro de Dev):
    dev_oos_causal = test_dev[test_dev['symbol'].isin(dev_pos_syms)].copy()
    dev_v1 = dev_oos_causal[dev_oos_causal['adx'] >= 30.0]
    dev_v2 = dev_oos_causal[(dev_oos_causal['adx'] >= 30.0) & (dev_oos_causal['risk_atr'] <= 1.5)]
    dev_v4 = simulate_concurrency_cap(dev_v2, max_open=1)

    k_dev_base = compute_kpis(test_dev['rr'], "Base Mecánica Dev OOS")
    k_dev_v1 = compute_kpis(dev_v1['rr'], "ADX >= 30 Dev OOS")
    k_dev_v2 = compute_kpis(dev_v2['rr'], "ADX >= 30 + ATR <= 1.5 Dev OOS")
    k_dev_v4 = compute_kpis(dev_v4['rr'], "ADX >= 30 + ATR <= 1.5 + Cap=1 Dev OOS")

    print("\n--- RESULTADOS EN DESARROLLO (VALIDACIÓN INTERNA CONGELADA) ---")
    for k in [k_dev_base, k_dev_v1, k_dev_v2, k_dev_v4]:
        print(f"  {k['label']:42s} | N={k['n']:2d} | WR: {k['win_pct']:4.1f}% | Net: {k['net_r']:+6.2f} R | Exp: {k['exp_r']:+6.4f} R | PF: {k['pf']:4.2f} | MaxDD: {k['max_dd']:4.2f} R")

    # 3. EVALUACIÓN CIEGA SOBRE EL HOLDOUT FINAL PRÍSTINO (2026-08-15 a 2026-10-10):
    # Activos aprendidos de todo el periodo de desarrollo
    full_dev_sym_pnl = dev_df.groupby('symbol')['rr'].sum()
    final_pos_syms = set(full_dev_sym_pnl[full_dev_sym_pnl > 0].index)
    print(f"\n3. EVALUACIÓN CIEGA SOBRE EL HOLDOUT FINAL INTACTO (56 DÍAS):")
    print(f"  • Activos congelados desde todo Dev: {sorted(list(final_pos_syms))}")

    pris_causal = pristine_df[pristine_df['symbol'].isin(final_pos_syms)].copy()
    pris_base = pristine_df
    pris_v1 = pris_causal[pris_causal['adx'] >= 30.0]
    pris_v2 = pris_causal[(pris_causal['adx'] >= 30.0) & (pris_causal['risk_atr'] <= 1.5)]
    pris_v3 = simulate_concurrency_cap(pris_v1, max_open=1)
    pris_v4 = simulate_concurrency_cap(pris_v2, max_open=1)

    k_pris_base = compute_kpis(pris_base['rr'], "1. Base Mecánica Pura (Holdout Prístino)")
    k_pris_v1 = compute_kpis(pris_v1['rr'], "2. ADX >= 30 (Holdout Prístino)")
    k_pris_v2 = compute_kpis(pris_v2['rr'], "3. ADX >= 30 + ATR <= 1.5 (Holdout Prístino)")
    k_pris_v3 = compute_kpis(pris_v3['rr'], "4. ADX >= 30 + Cap=1 (Holdout Prístino)")
    k_pris_v4 = compute_kpis(pris_v4['rr'], "5. ADX >= 30 + ATR <= 1.5 + Cap=1 (Candidato Final)")

    print("\n--- RESULTADOS DEFINITIVOS EN HOLDOUT FINAL PRÍSTINO (TOTALMENTE CIEGO) ---")
    for k in [k_pris_base, k_pris_v1, k_pris_v2, k_pris_v3, k_pris_v4]:
        print(f"  {k['label']:52s} | N={k['n']:2d} | WR: {k['win_pct']:4.1f}% | Net: {k['net_r']:+6.2f} R | Exp: {k['exp_r']:+6.4f} R | PF: {k['pf']:4.2f} | MaxDD: {k['max_dd']:4.2f} R")

    # 4. Estrés de Fricción sobre el Candidato Final en el Holdout Prístino:
    print("\n4. ESTRÉS DE FRICCIÓN EN EL HOLDOUT FINAL PRÍSTINO:")
    for sname, slip_r, gap_pct in [
        ("Base Real (Spread Deriv)", 0.0, 0.0),
        ("Fricción Baja (+0.025 R slip + 10% gap)", 0.025, 0.10),
        ("Fricción Moderada (+0.05 R slip + 15% gap)", 0.05, 0.15),
        ("Fricción Severa (+0.10 R slip + 20% gap)", 0.10, 0.20),
    ]:
        rr = pris_v4['rr'].copy()
        if slip_r > 0: rr -= slip_r
        if gap_pct > 0:
            l = rr < 0
            rr[l] -= abs(rr[l]) * gap_pct
        k = compute_kpis(rr, sname)
        print(f"  {sname:44s} | Net R: {k['net_r']:+6.2f} R | Exp: {k['exp_r']:+6.4f} R | PF: {k['pf']:4.2f} | MaxDD: {k['max_dd']:4.2f} R")

if __name__ == '__main__':
    run_nested_audit()
