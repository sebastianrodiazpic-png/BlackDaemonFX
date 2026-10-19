"""
scratch/audit_c2_comparability_and_concentration.py
===================================================
Script de solo lectura para cuantificar:
1. Las diferencias exactas trade por trade entre A (V4), B, C1 y C2 (incluyendo Wall Street 30).
2. El impacto de comparabilidad entre el universo canónico de 23 activos (MalaysianSNRConfig)
   y el universo de 19 activos del runner (ENABLED_UNIVERSES["MSNR"]).
3. La concentración de beneficios por activo y sensibilidad a costos de V4 y C2.
4. La deduplicación no destructiva (en memoria) de eventos únicos en las bases shadow (?mode=ro).
"""

import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

from reproduce_msnr_v4_full_audit import (
    PROJECT_ROOT, SYNTHS, FOREX, METALS_STRICT, INDICES_TRAD,
    get_family_3way, get_family_4way, run_walkforward_variant,
    compute_bundle_with_costs, apply_cost_scenario, compute_kpis
)
from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.shadow_mode_research_runner import ENABLED_UNIVERSES


def main():
    cfg = MalaysianSNRConfig()
    canonical_23 = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    runner_19 = sorted(list(set(ENABLED_UNIVERSES["MSNR"])))

    in_both_15 = sorted(list(set(canonical_23) & set(runner_19)))
    omitted_8 = sorted(list(set(canonical_23) - set(runner_19)))
    extra_4 = sorted(list(set(runner_19) - set(canonical_23)))

    lines = []
    lines.append("=" * 110)
    lines.append("1. DISCREPANCIA DE UNIVERSOS: ALLOWLIST CANÓNICA (23) VS SHADOW RUNNER (19)")
    lines.append("=" * 110)
    lines.append(f"Canónicos (23)         : {canonical_23}")
    lines.append(f"Runner ENABLED_19 (19) : {runner_19}")
    lines.append(f"Intersección (15)      : {in_both_15}")
    lines.append(f"Omitidos por Runner (8): {omitted_8}")
    lines.append(f"Extra en Runner (4)    : {extra_4}")

    csv_clean = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df_clean = pd.read_csv(csv_clean)
    df_clean['time'] = pd.to_datetime(df_clean['time'], utc=True)
    df_clean['exit_time'] = pd.to_datetime(df_clean['exit_time'], utc=True)
    df_clean['subfamily'] = df_clean['symbol'].apply(get_family_3way)
    df_clean = df_clean[df_clean['symbol'].isin(canonical_23)].sort_values('time').reset_index(drop=True)

    lines.append(f"\nRango temporal exacto de los 957 eventos evaluados:")
    lines.append(f"  Min entry_time: {df_clean['time'].min()} | Max entry_time: {df_clean['time'].max()} | Max exit_time: {df_clean['exit_time'].max()}")
    span_days = (df_clean['time'].max() - df_clean['time'].min()).total_seconds() / 86400.0
    lines.append(f"  Duración efectiva entre primera y última entrada: {span_days:.2f} días (~{span_days/30.4375:.2f} meses)")

    def f_a(d): return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]
    def f_b(d): return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5) & (d['symbol'] != 'Crash 1000 Index')]
    def f_c1(d):
        c_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_strict | c_synth]
    def f_c2(d):
        is_fx_or_pure_metal = d['symbol'].isin(FOREX | METALS_STRICT)
        c_strict = is_fx_or_pure_metal & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_other = (~is_fx_or_pure_metal) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_strict | c_other]

    res_a = run_walkforward_variant(df_clean, f_a, n_folds=4, cap=1)
    res_b = run_walkforward_variant(df_clean, f_b, n_folds=4, cap=1)
    res_c1 = run_walkforward_variant(df_clean, f_c1, n_folds=4, cap=1)
    res_c2 = run_walkforward_variant(df_clean, f_c2, n_folds=4, cap=1)

    # Cuantificar impacto de los 8 activos omitidos en el dataset de 957 eventos y en OOS
    raw_omitted = df_clean[df_clean['symbol'].isin(omitted_8)]
    lines.append(f"\nImpacto de los 8 activos canónicos omitidos por el runner en el Replay de 180 días:")
    lines.append(f"  Eventos brutos en los 8 activos omitidos: {len(raw_omitted)} / {len(df_clean)} ({len(raw_omitted)/len(df_clean)*100:.1f}%)")
    for s in omitted_8:
        cnt_raw = len(df_clean[df_clean['symbol'] == s])
        cnt_a = len(res_a['trades'][res_a['trades']['symbol'] == s])
        net_a = res_a['trades'][res_a['trades']['symbol'] == s]['rr'].sum() if cnt_a > 0 else 0.0
        cnt_c2 = len(res_c2['trades'][res_c2['trades']['symbol'] == s])
        net_c2 = res_c2['trades'][res_c2['trades']['symbol'] == s]['rr'].sum() if cnt_c2 > 0 else 0.0
        lines.append(f"    - {s:26s}: Brutos={cnt_raw:3d} | OOS V4(A)={cnt_a:2d} ({net_a:+.2f}R) | OOS C2={cnt_c2:2d} ({net_c2:+.2f}R)")

    # Qué ocurre si corremos walk-forward solo con los 15 activos de la intersección
    df_15 = df_clean[df_clean['symbol'].isin(in_both_15)].sort_values('time').reset_index(drop=True)
    res_a_15 = run_walkforward_variant(df_15, f_a, n_folds=4, cap=1)
    res_c2_15 = run_walkforward_variant(df_15, f_c2, n_folds=4, cap=1)
    lines.append(f"  Walk-Forward restringido a los 15 activos en común (23 ∩ 19):")
    lines.append(f"    - V4 (15 activos): N={res_a_15['total']['base']['n']}, WR={res_a_15['total']['base']['wr']}%, NetR Base={res_a_15['total']['base']['net_r']:+.2f}R, PF={res_a_15['total']['base']['pf']:.2f}")
    lines.append(f"    - C2 (15 activos): N={res_c2_15['total']['base']['n']}, WR={res_c2_15['total']['base']['wr']}%, NetR Base={res_c2_15['total']['base']['net_r']:+.2f}R, PF={res_c2_15['total']['base']['pf']:.2f}")

    # 2. Diferencias exactas trade por trade entre A, B, C1 y C2
    lines.append("\n" + "=" * 110)
    lines.append("2. TRAZABILIDAD OPERACIÓN POR OPERACIÓN DE DIFERENCIAS ENTRE V4 (A), B, C1 Y C2")
    lines.append("=" * 110)
    ta = res_a['trades'].copy()
    tb = res_b['trades'].copy()
    tc1 = res_c1['trades'].copy()
    tc2 = res_c2['trades'].copy()

    for label, other in [("B (Sin Crash 1000)", tb), ("C1 (ATR<=1.2 FX+Met+WS30)", tc1), ("C2 (ATR<=1.2 solo FX+XAU/XAG)", tc2)]:
        m = pd.merge(ta, other[['time', 'symbol']], on=['time', 'symbol'], how='left', indicator=True)
        diff = m[m['_merge'] == 'left_only']
        lines.append(f"\nOperaciones de V4 (A) excluidas en {label} (Total={len(diff)}, Suma R en V4={diff['rr'].sum():+.2f}R):")
        for _, r in diff.iterrows():
            lines.append(f"  Fold {r['fold']} | {r['time']} | Exit {r['exit_time']} | {r['symbol']:20s} | ADX={r['adx']:.2f} | ATR={r['risk_atr']:.3f} | outcome={r['outcome']:8s} | rr={r['rr']:+.2f}R")

    # También mostrar todas las operaciones de Wall Street 30 en V4/C2 vs C1
    lines.append("\nDetalle completo de las 5 operaciones OOS de Wall Street 30 en V4 y C2 (vs C1):")
    ws_a = ta[ta['symbol'] == 'Wall Street 30']
    ws_c1_keys = set(zip(tc1['time'], tc1['symbol']))
    for _, r in ws_a.iterrows():
        in_c1 = (r['time'], r['symbol']) in ws_c1_keys
        lines.append(f"  Fold {r['fold']} | {r['time']} | {r['symbol']:16s} | ADX={r['adx']:.2f} | ATR={r['risk_atr']:.3f} | outcome={r['outcome']:8s} | rr={r['rr']:+.2f}R | En C1: {'SÍ' if in_c1 else 'NO (FILTRADA POR ATR>1.2)'}")

    # 3. Concentración de beneficios y sensibilidad a costos
    lines.append("\n" + "=" * 110)
    lines.append("3. CONCENTRACIÓN DE BENEFICIOS Y SENSIBILIDAD A COSTOS (V4 vs B vs C1 vs C2)")
    lines.append("=" * 110)
    for vname, vres in [("A (V4 Base)", res_a), ("B (Sin Crash 1000)", res_b), ("C1 (ATR<=1.2 FX+Met+WS30)", res_c1), ("C2 (ATR<=1.2 solo FX+Met)", res_c2)]:
        tdf = vres['trades']
        sym_net = tdf.groupby('symbol')['rr'].sum().sort_values(ascending=False)
        total_net = sym_net.sum()
        pos_sum = sym_net[sym_net > 0].sum()
        top1_sym, top1_val = sym_net.index[0], sym_net.iloc[0]
        top2_sym, top2_val = sym_net.index[1], sym_net.iloc[1]
        top3_sym, top3_val = sym_net.index[2], sym_net.iloc[2]
        # HHI sobre contribución al beneficio positivo entre activos ganadores
        shares_pos = (sym_net[sym_net > 0] / pos_sum)
        hhi_pos = float((shares_pos ** 2).sum())
        # Sin el activo Top-1 y sin Top-2
        without_top1 = tdf[tdf['symbol'] != top1_sym]['rr']
        without_top2 = tdf[~tdf['symbol'].isin([top1_sym, top2_sym])]['rr']
        k_no1 = compute_kpis(without_top1)
        k_no2 = compute_kpis(without_top2)
        lines.append(f"\n[{vname}] Net R Total = {total_net:+.2f}R | Suma Activos Positivos = {pos_sum:+.2f}R | HHI (activos ganadores) = {hhi_pos:.3f}")
        lines.append(f"  * Top 1: {top1_sym:18s} ({top1_val:+.2f}R = {top1_val/total_net*100:5.1f}% del Net R total | {top1_val/pos_sum*100:5.1f}% del beneficio positivo)")
        lines.append(f"  * Top 2: {top2_sym:18s} ({top2_val:+.2f}R = {(top1_val+top2_val)/total_net*100:5.1f}% acumulado Top-2 | {(top1_val+top2_val)/pos_sum*100:5.1f}% del beneficio positivo)")
        lines.append(f"  * Top 3: {top3_sym:18s} ({top3_val:+.2f}R = {(top1_val+top2_val+top3_val)/total_net*100:5.1f}% acumulado Top-3 | {(top1_val+top2_val+top3_val)/pos_sum*100:5.1f}% del beneficio positivo)")
        lines.append(f"  * Sin Top-1 ({top1_sym}): N={k_no1['n']}, WR={k_no1['wr']}%, NetR={k_no1['net_r']:+.2f}R, PF={k_no1['pf']:.2f}, MaxDD={k_no1['max_dd']:.2f}R")
        lines.append(f"  * Sin Top-1 ni Top-2 ({top1_sym}, {top2_sym}): N={k_no2['n']}, WR={k_no2['wr']}%, NetR={k_no2['net_r']:+.2f}R, PF={k_no2['pf']:.2f}, MaxDD={k_no2['max_dd']:.2f}R")

    # Sensibilidad paramétrica a costos adicionales para V4 y C2
    lines.append("\n Curva de Sensibilidad a Fricción (V4 vs C2):")
    lines.append(f"  {'Escenario de Costo':34s} | {'V4 NetR':8s} | {'V4 PF':6s} | {'V4 DD':6s} | {'C2 NetR':8s} | {'C2 PF':6s} | {'C2 DD':6s}")
    lines.append("  " + "-" * 86)
    for scen_lbl, slp, gp in [
        ("Base (Spread MT5 incluido, +0.00R)", 0.00, 0.00),
        ("Leve (+0.03R slip, +10% gap SL)", 0.03, 0.10),
        ("Moderado (+0.05R slip, +15% gap SL)", 0.05, 0.15),
        ("Severo 20% (+0.10R slip, +20% gap)", 0.10, 0.20),
        ("Severo 25% (+0.10R slip, +25% gap)", 0.10, 0.25),
        ("Extremo 35% (+0.15R slip, +35% gap)", 0.15, 0.35),
        ("Catastrófico (+0.20R slip, +50% gap)", 0.20, 0.50),
    ]:
        ka = compute_kpis(apply_cost_scenario(res_a['trades']['rr'], slp, gp))
        kc2 = compute_kpis(apply_cost_scenario(res_c2['trades']['rr'], slp, gp))
        lines.append(f"  {scen_lbl:34s} | {ka['net_r']:+7.2f}R | {ka['pf']:6.2f} | {ka['max_dd']:5.2f}R | {kc2['net_r']:+7.2f}R | {kc2['pf']:6.2f} | {kc2['max_dd']:5.2f}R")

    # 4. Auditoría de eventos únicos y filtro canónico no destructivo en bases shadow (?mode=ro)
    lines.append("\n" + "=" * 110)
    lines.append("4. AUDITORÍA NO DESTRUCTIVA DE COHORTES SHADOW: EVENTOS BRUTOS VS ÚNICOS Y ALLOWLIST 23")
    lines.append("=" * 110)
    for db_name, db_rel in [
        ("PROSPECTIVA SELLADA (shadow_research.sqlite3)", "storage/runtime/shadow_research.sqlite3"),
        ("STAGING (shadow_research_staging.sqlite3)", "storage/runtime/shadow_research_staging.sqlite3"),
    ]:
        db_path = PROJECT_ROOT / db_rel
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        df_s = pd.read_sql_query("SELECT * FROM shadow_signals WHERE strategy='MSNR' ORDER BY id ASC", con)
        con.close()
        df_s['is_synthetic_fixture'] = df_s['variant'].isin(['h4_fresh_level', 'enabled_19_only'])
        df_s['is_canonical_23'] = df_s['symbol'].isin(canonical_23)
        # Clave de evento único por (symbol, direction, round(stop_loss, 2)) o ventana de 4h
        df_s['sl_round'] = df_s['stop_loss'].round(2)
        df_real = df_s[~df_s['is_synthetic_fixture']].copy()
        df_real_can = df_real[df_real['is_canonical_23']].copy()
        df_real_dedup = df_real.drop_duplicates(subset=['symbol', 'direction', 'sl_round'], keep='first')
        df_real_can_dedup = df_real_can.drop_duplicates(subset=['symbol', 'direction', 'sl_round'], keep='first')

        lines.append(f"\n[{db_name}]")
        lines.append(f"  * Filas totales MSNR                      : {len(df_s)}")
        lines.append(f"  * Filas fixture sintético (--test-suite)  : {int(df_s['is_synthetic_fixture'].sum())}")
        lines.append(f"  * Filas reales sincronizadas              : {len(df_real)}")
        lines.append(f"  * Filas reales en símbolos NO canónicos   : {len(df_real) - len(df_real_can)} ({sorted(df_real[~df_real['is_canonical_23']]['symbol'].unique().tolist())})")
        lines.append(f"  * Filas reales en allowlist canónica (23) : {len(df_real_can)}")
        lines.append(f"  * Eventos reales únicos (dedup nivel SL)  : {len(df_real_dedup)} (de {len(df_real)} filas reales)")
        lines.append(f"  * Eventos canónicos únicos (dedup SL)     : {len(df_real_can_dedup)} (de {len(df_real_can)} filas canónicas)")
        acc_can_dedup = df_real_can_dedup[df_real_can_dedup['final_action'] == 'ACCEPTED_EXECUTION']
        lines.append(f"  * Aceptados canónicos únicos (dedup SL)   : {len(acc_can_dedup)}")
        for _, r in acc_can_dedup.iterrows():
            lines.append(f"      - ID {r['id']:3d} | {r['timestamp']} | {r['symbol']:18s} | {r['direction']:4s} | sim={r['simulated_outcome']:18s} ({r['simulated_rr']:+.4f}R) | mkt={r['market_outcome']:18s} ({r['market_rr']:+.4f}R)")

    out_path = PROJECT_ROOT / "scratch" / "audit_c2_comparability_and_concentration_output.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
