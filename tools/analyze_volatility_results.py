import sqlite3
import pandas as pd
import numpy as np

def run_deep_analysis():
    conn = sqlite3.connect(r'storage/analysis/volatility_smc_analysis.db')
    df = pd.read_sql_query('SELECT * FROM smc_historical_trades WHERE trade1_result IN ("WIN", "LOSS")', conn)
    conn.close()

    print("=" * 90)
    print("ANÁLISIS PROFUNDO DE LOS TRADES HISTÓRICOS (2 AÑOS - ESTRATEGIA SMC 1:2 + RUNNER)")
    print(f"Total Oportunidades Cerradas: {len(df)}")
    print("=" * 90)

    # 1. Performance by Worker
    print("\n" + "=" * 90)
    print("1. DESGLOSE POR WORKER (VOLATILITY_1, VOLATILITY_2, VOLATILITY_3, VOLATILITY_4):")
    print("=" * 90)
    worker_stats = []
    for worker, grp in df.groupby('worker'):
        n = len(grp)
        t1_w = (grp['trade1_result'] == 'WIN').sum()
        t1_wr = t1_w / n * 100
        t1_pnl = grp['trade1_pnl_pct'].sum()
        t2_3r_w = (grp['trade2_3r_result'] == 'WIN_TP2').sum()
        t2_3r_be = (grp['trade2_3r_result'] == 'BREAK_EVEN').sum()
        t2_3r_pnl = grp['trade2_3r_pnl_pct'].sum()
        comb_3r = grp['combined_3r_pct'].sum()
        gross_win = grp[grp['combined_3r_pct'] > 0]['combined_3r_pct'].sum()
        gross_loss = abs(grp[grp['combined_3r_pct'] < 0]['combined_3r_pct'].sum())
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        worker_stats.append({
            'Worker': worker, 'Trades': n,
            'T1_WinRate%': round(t1_wr, 2), 'T1_PnL%': round(t1_pnl, 2),
            'T2_3r_Wins': t2_3r_w, 'T2_3r_BE': t2_3r_be, 'T2_PnL%': round(t2_3r_pnl, 2),
            'Combined_3R%': round(comb_3r, 2),
            'Profit_Factor': pf,
            'Expectancy%': round(comb_3r / n, 3)
        })
    print(pd.DataFrame(worker_stats).to_string(index=False))

    # 2. Performance by Individual Instrument
    print("\n" + "=" * 90)
    print("2. DESGLOSE Y RANKING POR INSTRUMENTO (TOP PERFORMERS vs UNDERPERFORMERS):")
    print("=" * 90)
    sym_stats = []
    for (sym, worker), grp in df.groupby(['symbol', 'worker']):
        n = len(grp)
        t1_w = (grp['trade1_result'] == 'WIN').sum()
        t1_wr = t1_w / n * 100
        t1_pnl = grp['trade1_pnl_pct'].sum()
        t2_3r_w = (grp['trade2_3r_result'] == 'WIN_TP2').sum()
        t2_3r_be = (grp['trade2_3r_result'] == 'BREAK_EVEN').sum()
        comb_3r = grp['combined_3r_pct'].sum()
        gross_win = grp[grp['combined_3r_pct'] > 0]['combined_3r_pct'].sum()
        gross_loss = abs(grp[grp['combined_3r_pct'] < 0]['combined_3r_pct'].sum())
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        sym_stats.append({
            'Symbol': sym, 'Worker': worker, 'Trades': n,
            'T1_WR%': round(t1_wr, 1),
            'T1_PnL%': round(t1_pnl, 1),
            'T2_Wins': t2_3r_w, 'T2_BE': t2_3r_be,
            'Net_PnL%': round(comb_3r, 1),
            'Profit_Factor': pf,
            'Exp%': round(comb_3r / n, 3)
        })
    sym_df = pd.DataFrame(sym_stats).sort_values(by='Net_PnL%', ascending=False)
    print(sym_df.to_string(index=False))

    # 3. Performance by SMC Quality Score Threshold
    print("\n" + "=" * 90)
    print("3. DESGLOSE POR SCORE DE CALIDAD SMC (IMPACTO EN FRECUENCIA Y RENTABILIDAD):")
    print("=" * 90)
    score_stats = []
    for min_s in [75.0, 78.0, 80.0, 82.0, 85.0, 88.0, 90.0]:
        sub = df[df['smc_score'] >= min_s]
        n = len(sub)
        if n == 0: continue
        t1_w = (sub['trade1_result'] == 'WIN').sum()
        t1_wr = t1_w / n * 100
        comb_3r = sub['combined_3r_pct'].sum()
        gross_win = sub[sub['combined_3r_pct'] > 0]['combined_3r_pct'].sum()
        gross_loss = abs(sub[sub['combined_3r_pct'] < 0]['combined_3r_pct'].sum())
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        score_stats.append({
            'Min_Score': min_s, 'Trades': n, 'T1_WR%': round(t1_wr, 2),
            'Combined_PnL%': round(comb_3r, 2), 'Profit_Factor': pf,
            'Expectancy%': round(comb_3r / n, 3)
        })
    print(pd.DataFrame(score_stats).to_string(index=False))

    # 4. Performance by ADX Regime (Trend Strength)
    print("\n" + "=" * 90)
    print("4. DESGLOSE POR RÉGIMEN DE MERCADO (ADX / FUERZA TENDENCIAL):")
    print("=" * 90)
    adx_bins = [
        (0, 15, 'Rango / Choppy (< 15)'),
        (15, 22, 'Transición Débil (15 - 22)'),
        (22, 30, 'Tendencia Confirmada (22 - 30)'),
        (30, 45, 'Tendencia Fuerte (30 - 45)'),
        (45, 100, 'Momento Extremo (> 45)')
    ]
    adx_stats = []
    for low, high, lbl in adx_bins:
        sub = df[(df['adx'] >= low) & (df['adx'] < high)]
        n = len(sub)
        if n == 0: continue
        t1_w = (sub['trade1_result'] == 'WIN').sum()
        t1_wr = t1_w / n * 100
        comb_3r = sub['combined_3r_pct'].sum()
        gross_win = sub[sub['combined_3r_pct'] > 0]['combined_3r_pct'].sum()
        gross_loss = abs(sub[sub['combined_3r_pct'] < 0]['combined_3r_pct'].sum())
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        adx_stats.append({
            'Regime': lbl, 'Trades': n, 'T1_WR%': round(t1_wr, 2),
            'Combined_PnL%': round(comb_3r, 2), 'Profit_Factor': pf,
            'Expectancy%': round(comb_3r / n, 3)
        })
    print(pd.DataFrame(adx_stats).to_string(index=False))

    # 5. Performance by Session / Hour (UTC)
    print("\n" + "=" * 90)
    print("5. DESGLOSE POR HORARIOS DE ENTRADA (UTC):")
    print("=" * 90)
    hour_stats = []
    for h, grp in df.groupby('entry_hour'):
        n = len(grp)
        t1_w = (grp['trade1_result'] == 'WIN').sum()
        t1_wr = t1_w / n * 100
        comb_3r = grp['combined_3r_pct'].sum()
        gross_win = grp[grp['combined_3r_pct'] > 0]['combined_3r_pct'].sum()
        gross_loss = abs(grp[grp['combined_3r_pct'] < 0]['combined_3r_pct'].sum())
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        hour_stats.append({
            'Hour_UTC': h, 'Trades': n, 'T1_WR%': round(t1_wr, 1),
            'Net_PnL%': round(comb_3r, 1), 'Profit_Factor': pf,
            'Exp%': round(comb_3r / n, 3)
        })
    h_df = pd.DataFrame(hour_stats).sort_values(by='Net_PnL%', ascending=False)
    print(h_df.to_string(index=False))

    # 6. Evaluation of Runner Strategy (BE Trigger at TP1 vs BE at +1.0R, and TP2 targets)
    print("\n" + "=" * 90)
    print("6. COMPARATIVA DE GESTIÓN DE LA CORREDORA (RUNNER):")
    print("=" * 90)
    print(f"Total Oportunidades: {len(df)}")
    t1_wins = (df['trade1_result'] == 'WIN').sum()
    print(f"Oportunidades donde TP1 (+2.0R) fue alcanzado: {t1_wins} ({t1_wins/len(df)*100:.2f}%)")

    # When BE is triggered at TP1:
    t2_3r_hit = (df['trade2_3r_result'] == 'WIN_TP2').sum()
    t2_3r_be = (df['trade2_3r_result'] == 'BREAK_EVEN').sum()
    print(f"\n[A] Activando BE al llegar a TP1 (+2.0R) con objetivo TP2 = 1:3 RR:")
    print(f"    - Runner alcanza TP2 (+3.0R = +1.5% capital): {t2_3r_hit} trades ({t2_3r_hit/t1_wins*100:.1f}% de las ganadoras)")
    print(f"    - Runner sacada en Break-Even cubriendo spread: {t2_3r_be} trades ({t2_3r_be/t1_wins*100:.1f}% de las ganadoras)")
    print(f"    - PnL Neto Total de la Corredora: {df['trade2_3r_pnl_pct'].sum():.2f}%")

    t2_4r_hit = (df['trade2_4r_result'] == 'WIN_TP2').sum()
    t2_4r_be = (df['trade2_4r_result'] == 'BREAK_EVEN').sum()
    print(f"\n[B] Activando BE al llegar a TP1 (+2.0R) con objetivo TP2 = 1:4 RR:")
    print(f"    - Runner alcanza TP2 (+4.0R = +2.0% capital): {t2_4r_hit} trades ({t2_4r_hit/t1_wins*100:.1f}% de las ganadoras)")
    print(f"    - Runner sacada en Break-Even cubriendo spread: {t2_4r_be} trades ({t2_4r_be/t1_wins*100:.1f}% de las ganadoras)")
    print(f"    - PnL Neto Total de la Corredora: {df['trade2_4r_pnl_pct'].sum():.2f}%")

    # Early BE at 1.0R
    t2_early_hit = (df['trade2_early_1r_result'] == 'WIN_TP2').sum()
    t2_early_be = (df['trade2_early_1r_result'] == 'BREAK_EVEN').sum()
    t2_early_loss = (df['trade2_early_1r_result'] == 'LOSS').sum()
    print(f"\n[C] Activando BE tempranamente a +1.0R (con objetivo TP2 = 1:3 RR):")
    print(f"    - Runner alcanza TP2: {t2_early_hit} trades")
    print(f"    - Runner sacada en BE a +1.0R: {t2_early_be} trades")
    print(f"    - Pérdidas directas (nunca llegó a +1.0R): {t2_early_loss} trades")
    print(f"    - PnL Neto Total de esta Corredora Temprana: {df['trade2_early_1r_pnl_pct'].sum():.2f}%")
    print(f"    - PnL Combinado con Trade 1: {df['combined_early_1r_pct'].sum():.2f}%")

    # 7. MFE Analysis on Losses (Direct Trade 1 Losses)
    print("\n" + "=" * 90)
    print("7. ANÁLISIS DE EXCURSIÓN MÁXIMA FAVORABLE (MFE) EN PÉRDIDAS:")
    print("=" * 90)
    losses_df = df[df['trade1_result'] == 'LOSS']
    n_loss = len(losses_df)
    mfe_05 = (losses_df['max_mfe_r'] >= 0.5).sum()
    mfe_10 = (losses_df['max_mfe_r'] >= 1.0).sum()
    mfe_15 = (losses_df['max_mfe_r'] >= 1.5).sum()
    print(f"Pérdidas totales analizadas: {n_loss}")
    print(f"  - Llegaron a +0.5R a favor antes de tocar SL: {mfe_05} ({mfe_05/n_loss*100:.1f}%)")
    print(f"  - Llegaron a +1.0R a favor antes de tocar SL: {mfe_10} ({mfe_10/n_loss*100:.1f}%)")
    print(f"  - Llegaron a +1.5R a favor antes de tocar SL: {mfe_15} ({mfe_15/n_loss*100:.1f}%)")


if __name__ == '__main__':
    run_deep_analysis()
