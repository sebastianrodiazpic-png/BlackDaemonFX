"""Analisis cuantitativo profundo de resultados de 2 años en STEP y JUMP.

Procesa la base de datos storage/analysis/step_jump_smc_analysis.db y evalua:
1. Rendimiento global y por Worker (STEP vs JUMP, Primarios vs Extendidos).
2. Ranking individual por instrumento.
3. Evaluacion detallada de la Corredora (Runner): TP2 @ 1:3 vs 1:4 vs 1:5 vs Trailing.
4. Analisis de mecanica de Break-Even (BE a TP1 vs BE Temprano).
5. Excursion MFE/MAE de perdidas.
6. Optimizacion: Curva de Score SMC y Raw Score (impacto en frecuencia y rentabilidad).
7. Optimizacion: Porcentaje de confirmacion y Grado de Trade (A+, A, B).
8. Optimizacion: Tipo de quiebre estructural (BOS vs CHoCH).
9. Optimizacion: Regimenes de ADX / Volatilidad.
10. Optimizacion: Horarios UTC de mayor probabilidad y rentabilidad.
11. Optimizacion: Tipos de Setup y Direccion (BUY vs SELL).
12. Impacto del Spread sobre el riesgo (Spread Ratio).
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "storage" / "analysis" / "step_jump_smc_analysis.db"
OUTPUT_REPORT = PROJECT_ROOT / "storage" / "analysis" / "step_jump_analysis_report.json"


def safe_json_default(o):
    if isinstance(o, (np.integer, int)):
        return int(o)
    elif isinstance(o, (np.floating, float)):
        return float(o)
    elif isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def run_analysis():
    if not DB_PATH.exists():
        print(f"Error: Base de datos no encontrada en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM smc_step_jump_trades WHERE trade1_result IN ('WIN', 'LOSS')", conn)
    conn.close()

    total_closed = len(df)
    if total_closed == 0:
        print("No hay operaciones cerradas para analizar.")
        return

    print("=" * 105)
    print("INFORME CUANTITATIVO HISTÓRICO - 2 AÑOS (WORKERS STEP & JUMP)")
    print(f"Total Operaciones Evaluadas: {total_closed} | Capital Base: $10,000 | Riesgo: 1.0% ($100/trade)")
    print("Estructura: Trade 1 (0.5% riesgo, TP1=1:2) + Trade 2 Runner (0.5% riesgo, BE+spread al tocar TP1)")
    print("=" * 105)

    # 1. Rendimiento Global
    t1_wins = int((df["trade1_result"] == "WIN").sum())
    t1_losses = int((df["trade1_result"] == "LOSS").sum())
    t1_wr = t1_wins / total_closed * 100
    t1_pnl_pct = float(df["trade1_pnl_pct"].sum())

    t2_3r_wins = int((df["trade2_3r_result"] == "WIN_TP2").sum())
    t2_3r_be = int((df["trade2_3r_result"] == "BREAK_EVEN").sum())
    t2_3r_losses = int((df["trade2_3r_result"] == "LOSS").sum())
    t2_3r_pnl_pct = float(df["trade2_3r_pnl_pct"].sum())

    comb_3r_pnl = float(df["combined_3r_pct"].sum())
    comb_4r_pnl = float(df["combined_4r_pct"].sum())
    comb_5r_pnl = float(df["combined_5r_pct"].sum())
    comb_trail_pnl = float(df["combined_trail_pct"].sum())

    gross_win = float(df[df["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
    gross_loss = abs(float(df[df["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
    pf_3r = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0

    print("\n" + "=" * 105)
    print("1. RESUMEN GLOBAL CONSOLIDADO:")
    print("=" * 105)
    print(f"  Trades Totales:           {total_closed}")
    print(f"  Trade 1 (Scalp 1:2 RR):   Wins={t1_wins} | Losses={t1_losses} | Win Rate={t1_wr:.2f}% | PnL={t1_pnl_pct:+.2f}% (+${t1_pnl_pct*100:,.0f})")
    print(f"  Trade 2 (Runner TP2 1:3): Wins={t2_3r_wins} | BreakEven={t2_3r_be} | Losses={t2_3r_losses} | PnL={t2_3r_pnl_pct:+.2f}% (+${t2_3r_pnl_pct*100:,.0f})")
    print(f"  --------------------------------------------------------------------------------------------------")
    print(f"  RESULTADO COMBINADO 1:2 + RUNNER 1:3:")
    print(f"    Rendimiento Neto Total: {comb_3r_pnl:+.2f}% (+${comb_3r_pnl*100:,.2f})")
    print(f"    Profit Factor:          {pf_3r:.2f}")
    print(f"    Expectativa Matemática: {comb_3r_pnl / total_closed:+.3f}% por trade (+${(comb_3r_pnl / total_closed)*100:+.2f})")
    print(f"    Otras variantes de Runner:")
    print(f"      - Con TP2 @ 1:4 RR:   {comb_4r_pnl:+.2f}% (+${comb_4r_pnl*100:,.0f})")
    print(f"      - Con TP2 @ 1:5 RR:   {comb_5r_pnl:+.2f}% (+${comb_5r_pnl*100:,.0f})")
    print(f"      - Con Trailing Stop:  {comb_trail_pnl:+.2f}% (+${comb_trail_pnl*100:,.0f})")

    # 2. Rendimiento por Worker (STEP vs JUMP) y Universo (Primario vs Extendido)
    print("\n" + "=" * 105)
    print("2. DESGLOSE POR WORKER Y UNIVERSO:")
    print("=" * 105)
    worker_rows = []
    for (worker, is_prim), grp in df.groupby(["worker", "is_primary"]):
        n = int(len(grp))
        w = int((grp["trade1_result"] == "WIN").sum())
        wr = w / n * 100
        pnl_1 = float(grp["trade1_pnl_pct"].sum())
        t2_w = int((grp["trade2_3r_result"] == "WIN_TP2").sum())
        t2_be = int((grp["trade2_3r_result"] == "BREAK_EVEN").sum())
        comb_pnl = float(grp["combined_3r_pct"].sum())
        gw = float(grp[grp["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
        gl = abs(float(grp[grp["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
        pf = round(gw / gl, 2) if gl > 0 else 999.0
        exp = comb_pnl / n
        universe_lbl = "PRIMARIO (Worker)" if is_prim == 1 else "EXTENDIDO (Familia)"
        worker_rows.append({
            "Worker": str(worker),
            "Universo": universe_lbl,
            "Trades": n,
            "T1_WR%": round(wr, 1),
            "T1_PnL%": round(pnl_1, 1),
            "T2_Wins": t2_w,
            "T2_BE": t2_be,
            "Net_PnL%": round(comb_pnl, 1),
            "Profit_Factor": pf,
            "Exp%": round(exp, 3),
        })
    print(pd.DataFrame(worker_rows).to_string(index=False))

    # 3. Ranking por Instrumento Individual
    print("\n" + "=" * 105)
    print("3. RANKING POR INSTRUMENTO (ORDENADO POR RENDIMIENTO NETO):")
    print("=" * 105)
    sym_rows = []
    for (sym, worker, is_prim), grp in df.groupby(["symbol", "worker", "is_primary"]):
        n = int(len(grp))
        w = int((grp["trade1_result"] == "WIN").sum())
        wr = w / n * 100
        pnl_1 = float(grp["trade1_pnl_pct"].sum())
        t2_w = int((grp["trade2_3r_result"] == "WIN_TP2").sum())
        t2_be = int((grp["trade2_3r_result"] == "BREAK_EVEN").sum())
        comb_pnl = float(grp["combined_3r_pct"].sum())
        gw = float(grp[grp["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
        gl = abs(float(grp[grp["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
        pf = round(gw / gl, 2) if gl > 0 else 999.0
        exp = comb_pnl / n
        avg_spread_ratio = float(grp["spread_ratio"].mean())
        sym_rows.append({
            "Symbol": str(sym),
            "Worker": str(worker),
            "Tipo": "Primario" if is_prim == 1 else "Extendido",
            "Trades": n,
            "T1_WR%": round(wr, 1),
            "T2_Wins": t2_w,
            "T2_BE": t2_be,
            "Net_PnL%": round(comb_pnl, 1),
            "Profit_Factor": pf,
            "Exp%": round(exp, 3),
            "Avg_Spread_Ratio%": round(avg_spread_ratio * 100, 2),
        })
    sym_df = pd.DataFrame(sym_rows).sort_values(by="Net_PnL%", ascending=False)
    print(sym_df.to_string(index=False))

    # 4. Evaluación de la Corredora y Activación de Break-Even
    print("\n" + "=" * 105)
    print("4. COMPARATIVA DE GESTIÓN DE CORREDORA Y BREAK-EVEN:")
    print("=" * 105)
    print(f"Oportunidades donde TP1 (+2.0R) fue alcanzado: {t1_wins} de {total_closed} ({t1_wins/total_closed*100:.1f}%)")
    
    sub_tp1 = df[df["trade1_result"] == "WIN"]
    hit_tp2_3r_count = int((sub_tp1["trade2_3r_result"] == "WIN_TP2").sum())
    hit_tp2_4r_count = int((sub_tp1["trade2_4r_result"] == "WIN_TP2").sum())
    hit_tp2_5r_count = int((sub_tp1["trade2_5r_result"] == "WIN_TP2").sum())
    hit_be_3r_count = int((sub_tp1["trade2_3r_result"] == "BREAK_EVEN").sum())

    print(f"  De las operaciones que alcanzaron TP1 (+2.0R):")
    print(f"    - Alcanzaron TP2 @ 1:3 RR (+3.0R): {hit_tp2_3r_count} ({hit_tp2_3r_count/len(sub_tp1)*100:.1f}%) -> Retorno Trade 2: +1.5%")
    print(f"    - Alcanzaron TP2 @ 1:4 RR (+4.0R): {hit_tp2_4r_count} ({hit_tp2_4r_count/len(sub_tp1)*100:.1f}%) -> Retorno Trade 2: +2.0%")
    print(f"    - Alcanzaron TP2 @ 1:5 RR (+5.0R): {hit_tp2_5r_count} ({hit_tp2_5r_count/len(sub_tp1)*100:.1f}%) -> Retorno Trade 2: +2.5%")
    print(f"    - Retrocedieron a Break-Even:      {hit_be_3r_count} ({hit_be_3r_count/len(sub_tp1)*100:.1f}%) -> Retorno Trade 2: 0.0% (spread cubierto)")

    early_1r_pnl = float(df["combined_early_1r_pct"].sum())
    early_15r_pnl = float(df["combined_early_15r_pct"].sum())
    print(f"\n  Comparativa de Timing de Break-Even:")
    print(f"    - BE al llegar a TP1 (+2.0R) [Estrategia Actual]: PnL = {comb_3r_pnl:+.2f}% | PF = {pf_3r:.2f}")
    print(f"    - BE Temprano a +1.0R:                           PnL = {early_1r_pnl:+.2f}%")
    print(f"    - BE Intermedio a +1.5R:                         PnL = {early_15r_pnl:+.2f}%")

    # 5. Análisis MFE en Operaciones Perdedoras
    print("\n" + "=" * 105)
    print("5. ANÁLISIS DE MFE (EXCURSIÓN FAVORABLE MÁXIMA) EN PÉRDIDAS:")
    print("=" * 105)
    losses_df = df[df["trade1_result"] == "LOSS"]
    total_l = int(len(losses_df))
    mfe_05 = int((losses_df["max_mfe_r"] >= 0.5).sum())
    mfe_10 = int((losses_df["max_mfe_r"] >= 1.0).sum())
    mfe_15 = int((losses_df["max_mfe_r"] >= 1.5).sum())
    print(f"  Total Pérdidas Directas: {total_l}")
    print(f"    - Avanzaron >= +0.5R antes de caer al SL: {mfe_05} ({mfe_05/total_l*100:.1f}%)")
    print(f"    - Avanzaron >= +1.0R antes de caer al SL: {mfe_10} ({mfe_10/total_l*100:.1f}%)")
    print(f"    - Avanzaron >= +1.5R antes de caer al SL: {mfe_15} ({mfe_15/total_l*100:.1f}%)")

    # 6. Optimización: Curva de Raw Trade Score
    raw_score_rows = []
    if "raw_trade_score" in df.columns and df["raw_trade_score"].notna().any():
        print("\n" + "=" * 105)
        print("6. OPTIMIZACIÓN: CURVA DE RAW TRADE SCORE (CONFIRMACIONES SMC):")
        print("=" * 105)
        for s_th in [90.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0]:
            sub = df[df["raw_trade_score"] >= s_th]
            n = int(len(sub))
            if n == 0:
                continue
            w = int((sub["trade1_result"] == "WIN").sum())
            wr = w / n * 100
            pnl = float(sub["combined_3r_pct"].sum())
            gw = float(sub[sub["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
            gl = abs(float(sub[sub["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
            pf = round(gw / gl, 2) if gl > 0 else 999.0
            exp = pnl / n
            raw_score_rows.append({
                "Min_Raw_Score": s_th,
                "Trades": n,
                "Trades/Mes": round(n / 24, 1),
                "T1_WR%": round(wr, 1),
                "Net_PnL%": round(pnl, 1),
                "Profit_Factor": pf,
                "Exp%": round(exp, 3),
            })
        print(pd.DataFrame(raw_score_rows).to_string(index=False))

    # 7. Optimización: Porcentaje de Confirmación SMC
    conf_pct_rows = []
    if "confirmation_percentage" in df.columns and df["confirmation_percentage"].notna().any():
        print("\n" + "=" * 105)
        print("7. OPTIMIZACIÓN: PORCENTAJE DE CONFIRMACIÓN (%):")
        print("=" * 105)
        for c_th in [80.0, 85.0, 90.0, 92.0]:
            sub = df[df["confirmation_percentage"] >= c_th]
            n = int(len(sub))
            if n == 0:
                continue
            w = int((sub["trade1_result"] == "WIN").sum())
            wr = w / n * 100
            pnl = float(sub["combined_3r_pct"].sum())
            gw = float(sub[sub["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
            gl = abs(float(sub[sub["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
            pf = round(gw / gl, 2) if gl > 0 else 999.0
            exp = pnl / n
            conf_pct_rows.append({
                "Min_Conf_Pct": c_th,
                "Trades": n,
                "Trades/Mes": round(n / 24, 1),
                "T1_WR%": round(wr, 1),
                "Net_PnL%": round(pnl, 1),
                "Profit_Factor": pf,
                "Exp%": round(exp, 3),
            })
        print(pd.DataFrame(conf_pct_rows).to_string(index=False))

    # 8. Optimización: Quiebre Estructural (BOS vs CHoCH)
    break_rows = []
    if "structure_break_type" in df.columns and df["structure_break_type"].notna().any():
        print("\n" + "=" * 105)
        print("8. OPTIMIZACIÓN: TIPO DE QUIEBRE ESTRUCTURAL (BOS vs CHOCH):")
        print("=" * 105)
        for b_type, grp in df.groupby("structure_break_type"):
            n = int(len(grp))
            w = int((grp["trade1_result"] == "WIN").sum())
            wr = w / n * 100
            pnl = float(grp["combined_3r_pct"].sum())
            gw = float(grp[grp["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
            gl = abs(float(grp[grp["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
            pf = round(gw / gl, 2) if gl > 0 else 999.0
            break_rows.append({
                "Estructura": str(b_type),
                "Trades": n,
                "T1_WR%": round(wr, 1),
                "Net_PnL%": round(pnl, 1),
                "Profit_Factor": pf,
                "Exp%": round(pnl / n, 3),
            })
        print(pd.DataFrame(break_rows).to_string(index=False))

    # 9. Optimización: Régimen de Mercado (ADX)
    print("\n" + "=" * 105)
    print("9. OPTIMIZACIÓN: RÉGIMEN DE FUERZA DE TENDENCIA (ADX):")
    print("=" * 105)
    adx_bins = [
        (0, 18, "Rango / Sin Tendencia (< 18)"),
        (18, 25, "Inicio de Tendencia (18 - 25)"),
        (25, 35, "Tendencia Confirmada (25 - 35)"),
        (35, 100, "Tendencia Extrema / Impulso (> 35)"),
    ]
    adx_rows = []
    for low, high, lbl in adx_bins:
        sub = df[(df["adx"] >= low) & (df["adx"] < high)]
        n = int(len(sub))
        if n == 0:
            continue
        w = int((sub["trade1_result"] == "WIN").sum())
        wr = w / n * 100
        pnl = float(sub["combined_3r_pct"].sum())
        gw = float(sub[sub["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
        gl = abs(float(sub[sub["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
        pf = round(gw / gl, 2) if gl > 0 else 999.0
        exp = pnl / n
        adx_rows.append({
            "Regimen_ADX": lbl,
            "Trades": n,
            "T1_WR%": round(wr, 1),
            "Net_PnL%": round(pnl, 1),
            "Profit_Factor": pf,
            "Exp%": round(exp, 3),
        })
    print(pd.DataFrame(adx_rows).to_string(index=False))

    # 10. Optimización: Horarios UTC
    print("\n" + "=" * 105)
    print("10. OPTIMIZACIÓN: DISTRIBUCIÓN POR HORARIOS (UTC):")
    print("=" * 105)
    hour_rows = []
    for h, grp in df.groupby("entry_hour"):
        n = int(len(grp))
        w = int((grp["trade1_result"] == "WIN").sum())
        wr = w / n * 100
        pnl = float(grp["combined_3r_pct"].sum())
        gw = float(grp[grp["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
        gl = abs(float(grp[grp["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
        pf = round(gw / gl, 2) if gl > 0 else 999.0
        exp = pnl / n
        hour_rows.append({
            "Hour_UTC": int(h),
            "Trades": n,
            "T1_WR%": round(wr, 1),
            "Net_PnL%": round(pnl, 1),
            "Profit_Factor": pf,
            "Exp%": round(exp, 3),
        })
    hour_df = pd.DataFrame(hour_rows).sort_values(by="Net_PnL%", ascending=False)
    print(hour_df.to_string(index=False))

    # 11. Optimización: Dirección (BUY vs SELL)
    print("\n" + "=" * 105)
    print("11. OPTIMIZACIÓN: DIRECCIÓN (BUY vs SELL):")
    print("=" * 105)
    dir_rows = []
    for d, grp in df.groupby("direction"):
        n = int(len(grp))
        w = int((grp["trade1_result"] == "WIN").sum())
        wr = w / n * 100
        pnl = float(grp["combined_3r_pct"].sum())
        gw = float(grp[grp["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
        gl = abs(float(grp[grp["combined_3r_pct"] < 0]["combined_3r_pct"].sum()))
        pf = round(gw / gl, 2) if gl > 0 else 999.0
        dir_rows.append({
            "Direccion": str(d),
            "Trades": n,
            "T1_WR%": round(wr, 1),
            "Net_PnL%": round(pnl, 1),
            "Profit_Factor": pf,
            "Exp%": round(pnl / n, 3),
        })
    print(pd.DataFrame(dir_rows).to_string(index=False))

    # 12. Optimización: Impacto del Spread (Spread Ratio)
    print("\n" + "=" * 105)
    print("12. OPTIMIZACIÓN: IMPACTO DEL SPREAD (SPREAD / STOP LOSS):")
    print("=" * 105)
    spread_bins = [
        (0.0, 0.05, "Despreciable (< 5% del SL)"),
        (0.05, 0.15, "Moderado (5% - 15% del SL)"),
        (0.15, 0.30, "Alto (15% - 30% del SL)"),
        (0.30, 2.00, "Crítico (> 30% del SL)"),
    ]
    spread_rows = []
    for low, high, lbl in spread_bins:
        sub = df[(df["spread_ratio"] >= low) & (df["spread_ratio"] < high)]
        n = int(len(sub))
        if n == 0:
            continue
        w = int((sub["trade1_result"] == "WIN").sum())
        wr = w / n * 100
        pnl = float(sub["combined_3r_pct"].sum())
        gw = float(sub[sub["combined_3r_pct"] > 0]["combined_3r_pct"].sum())
        gl = abs(sub[sub["combined_3r_pct"] < 0]["combined_3r_pct"].sum())
        pf = round(gw / gl, 2) if gl > 0 else 999.0
        spread_rows.append({
            "Impacto_Spread": lbl,
            "Trades": n,
            "T1_WR%": round(wr, 1),
            "Net_PnL%": round(pnl, 1),
            "Profit_Factor": pf,
            "Exp%": round(pnl / n, 3),
        })
    print(pd.DataFrame(spread_rows).to_string(index=False))

    # Guardar resumen en JSON con safe_json_default
    report_data = {
        "total_trades": total_closed,
        "trade1_win_rate": round(t1_wr, 2),
        "combined_3r_pnl": round(comb_3r_pnl, 2),
        "combined_4r_pnl": round(comb_4r_pnl, 2),
        "combined_5r_pnl": round(comb_5r_pnl, 2),
        "profit_factor_3r": pf_3r,
        "workers": worker_rows,
        "top_symbols": sym_rows,
        "raw_score_curve": raw_score_rows,
        "conf_pct_curve": conf_pct_rows,
        "structure_breaks": break_rows,
        "adx_curve": adx_rows,
        "hourly_distribution": hour_rows,
        "direction_distribution": dir_rows,
    }
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=safe_json_default)
    print(f"\nReporte JSON guardado en: {OUTPUT_REPORT}")


if __name__ == "__main__":
    run_analysis()
