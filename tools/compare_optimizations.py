import sqlite3
import pandas as pd
import numpy as np

def run_comparison():
    conn = sqlite3.connect(r'storage/analysis/volatility_smc_analysis.db')
    df = pd.read_sql_query('SELECT * FROM smc_historical_trades WHERE trade1_result IN ("WIN", "LOSS")', conn)
    conn.close()

    bad_symbols = {
        'Vol over Crash 400', 'Vol over Boom 750', 'Spot Up - Volatility Up Index',
        'Volatility 100 Index', 'Volatility Crash 750 Index', 'Vol over Crash 750',
        'High Frequency Vol 75 Index', 'High Frequency Vol 25 Index', 'Volatility 50 Index', 'VolSwitch Medium Vol Index'
    }
    df_good_sym = df[~df['symbol'].isin(bad_symbols)].copy()

    # Horas toxicas con rentabilidad negativa sistematica
    toxic_hours = {0, 1, 2, 4, 5, 6, 7, 8, 12, 13, 15, 16, 20}
    df_good_hours = df[~df['entry_hour'].isin(toxic_hours)].copy()

    # Combinado
    df_optimized = df[(~df['symbol'].isin(bad_symbols)) & (~df['entry_hour'].isin(toxic_hours))].copy()

    # Top Alpha Symbols Only (PF >= 1.10)
    top_alpha_symbols = {
        'Volatility 50 (1s) Index', 'Volatility 75 Index', 'Volatility 75 (1s) Index',
        'VolSwitch High Vol Index', 'High Frequency Vol 50 Index', 'Vol over Crash 550',
        'Volatility 15 Index', 'Volatility 150 (1s) Index', 'Volatility 250 (1s) Index'
    }
    df_top_alpha = df[df['symbol'].isin(top_alpha_symbols)].copy()
    df_top_alpha_timed = df[(df['symbol'].isin(top_alpha_symbols)) & (~df['entry_hour'].isin(toxic_hours))].copy()

    def evaluate(subset, name):
        n = len(subset)
        if n == 0: return
        t1_w = (subset['trade1_result'] == 'WIN').sum()
        t1_wr = t1_w / n * 100
        t1_pnl = subset['trade1_pnl_pct'].sum()
        t2_w = (subset['trade2_3r_result'] == 'WIN_TP2').sum()
        t2_be = (subset['trade2_3r_result'] == 'BREAK_EVEN').sum()
        t2_pnl = subset['trade2_3r_pnl_pct'].sum()
        comb = subset['combined_3r_pct'].sum()
        gross_win = subset[subset['combined_3r_pct'] > 0]['combined_3r_pct'].sum()
        gross_loss = abs(subset[subset['combined_3r_pct'] < 0]['combined_3r_pct'].sum())
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        exp = round(comb / n, 3)
        print(f"=== {name} ===")
        print(f"Trades Ejecutados: {n}")
        print(f"Trade 1 (TP1 1:2): Win Rate = {t1_wr:.2f}% | PnL = {t1_pnl:+.1f}%")
        print(f"Trade 2 (Runner 1:3 + BE): TP2 = {t2_w} ({t2_w/n*100:.1f}%) | BE cubriendo Spread = {t2_be} ({t2_be/n*100:.1f}%) | PnL = {t2_pnl:+.1f}%")
        print(f"RETORNO NETO COMBINADO: {comb:+.1f}% (+${comb*100:,.2f})")
        print(f"PROFIT FACTOR: {pf} | ESPERANZA MATEMATICA: {exp:+.3f}% por trade\n")

    print("=" * 80)
    print("COMPARATIVA DE ESCENARIOS DE OPTIMIZACIÓN:")
    print("=" * 80)
    evaluate(df, "ESCENARIO 1: BASE SIN FILTROS (36 Activos, 24h)")
    evaluate(df_good_sym, "ESCENARIO 2: PODA DE ACTIVOS TÓXICOS (Excluye 10 activos con sesgo negativo)")
    evaluate(df_good_hours, "ESCENARIO 3: FILTRO HORARIO (Solo Ventanas de Alta Liquidez/Confluencia)")
    evaluate(df_optimized, "ESCENARIO 4: PODA DE ACTIVOS + FILTRO HORARIO")
    evaluate(df_top_alpha, "ESCENARIO 5: SOLO ACTIVOS TOP ALPHA (9 Activos Líderes, 24h)")
    evaluate(df_top_alpha_timed, "ESCENARIO 6: MÁXIMA RENTABILIDAD (Activos Top Alpha + Ventanas Horarias Premium)")

if __name__ == "__main__":
    run_comparison()
