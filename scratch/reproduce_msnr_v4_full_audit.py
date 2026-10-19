"""
scratch/reproduce_msnr_v4_full_audit.py
=======================================
Script reproducible de solo lectura para verificar y auditar Malaysian SNR V4 y las variantes A, B y C:
- Paso 1: Reproducción de V4 como benchmark congelado (ADX >= 30, ATR <= 1.5, Cap=1, 23 activos, SL-first intrabar).
          Reconciliación entre dataset limpio de 23 activos (957 trades -> N=42) y dataset base de 9 activos (727 trades -> N=40).
- Paso 2: Comparación individual con los mismos splits walk-forward (4 folds con purga y embargo):
          A. V4 sin cambios.
          B. V4 excluyendo Crash 1000 Index.
          C. V4 con ATR <= 1.2 solo para Forex y metales (mostrando C1: Forex + Metales/Índices incl. WS30, y C2: solo Forex + XAUUSD/XAGUSD).
- Paso 3: Reporte por activo (23 canónicos), familia y ventana (Fold 1 a Fold 4):
          N OOS únicas, Win Rate, IC Wilson 95%, Expectativa, Payoff, Net R, PF y MaxDD bajo costos Base, Moderados y Severos.
          Separación estricta de PnL ejecutado vs resultados contrafactuales (bloqueadas por Cap=1 y excluidas por filtro).
- Paso 4: Verificación en modo solo lectura (?mode=ro) de la cohorte prospectiva sellada y staging (cierres totales vs cierres Forex/Metales).
- Paso 5: Auditoría de cobertura M15 real por cada uno de los 23 activos canónicos.
"""

import sys
import math
import json
import pickle
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE

SYNTHS = set([
    'Boom 1000 Index', 'Boom 300 Index', 'Crash 1000 Index', 'Crash 600 Index',
    'Jump 10 Index', 'Jump 25 Index', 'Step Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index'
])
FOREX = set(['AUDNZD', 'EURCHF', 'EURGBP', 'EURUSD', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'USDJPY'])
METALS_STRICT = set(['XAUUSD', 'XAGUSD'])
INDICES_TRAD = set(['Wall Street 30'])
METALS_AND_INDICES = METALS_STRICT | INDICES_TRAD


def get_family_3way(sym: str) -> str:
    if sym in SYNTHS:
        return "SYNTH"
    elif sym in FOREX:
        return "FOREX"
    elif sym in METALS_AND_INDICES:
        return "METALS"
    return "OTHER"


def get_family_4way(sym: str) -> str:
    if sym in SYNTHS:
        return "SYNTH"
    elif sym in FOREX:
        return "FOREX"
    elif sym in METALS_STRICT:
        return "METALS_PURE"
    elif sym in INDICES_TRAD:
        return "INDEX"
    return "OTHER"


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2.0 * n)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) + (z ** 2) / (4.0 * n)) / n)) / denom
    return (round(max(0.0, center - margin) * 100.0, 1), round(min(1.0, center + margin) * 100.0, 1))


def apply_cost_scenario(series: pd.Series, slip_r: float, gap_pct: float) -> pd.Series:
    """
    Aplica fricción adicional sobre cada operación:
    - Si r > 0.001 (ganadora): r_net = r - slip_r
    - Si r < -0.001 (perdedora): penalización de slippage + ampliación por gap de SL:
      En los scripts del repositorio existen dos convenciones ligeramente distintas:
      Convención 1 (test_subfamily_and_filter_improvements.py): -(1.0 + slip_r) * (1.0 + gap_pct) cuando r == -1.0,
      o generalizado: r_after_slip = r - slip_r; r_net = r_after_slip * (1.0 + gap_pct)
      Calculamos con exactitud la convención de eval_friction de test_subfamily_and_filter_improvements.py.
    """
    if len(series) == 0:
        return pd.Series(dtype=float)
    if slip_r == 0.0 and gap_pct == 0.0:
        return series.copy()
    out = []
    for r in series:
        if r > 0.001:
            out.append(r - slip_r)
        elif r < -0.001:
            # Si r es cercano a -1.0, (abs(r) + slip_r) * (1.0 + gap_pct) reproduce exactamente eval_friction
            pen = (abs(r) + slip_r) * (1.0 + gap_pct)
            out.append(-pen)
        else:
            out.append(-slip_r)
    return pd.Series(out, index=series.index)


def compute_kpis(series: pd.Series, label: str = "") -> dict:
    n = len(series)
    if n == 0:
        return {
            "label": label, "n": 0, "w": 0, "l": 0, "be": 0,
            "wr": 0.0, "ci_low": 0.0, "ci_high": 0.0, "ci_str": "[0.0%, 0.0%]",
            "avg_win": 0.0, "avg_loss": 0.0, "payoff": 0.0,
            "exp_r": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd": 0.0
        }
    wins = series[series > 0.001]
    bes = series[(series >= -0.001) & (series <= 0.001)]
    losses = series[series < -0.001]
    nw, nb, nl = len(wins), len(bes), len(losses)
    wr = round(nw / n * 100.0, 1)
    ci_l, ci_h = wilson_ci(nw, n)
    ci_str = f"[{ci_l:.1f}%, {ci_h:.1f}%]"

    aw = float(wins.mean()) if nw > 0 else 0.0
    al = float(abs(losses.mean())) if nl > 0 else 0.0
    payoff = round(aw / al, 2) if al > 0 else (99.0 if aw > 0 else 0.0)

    net_r = round(float(series.sum()), 2)
    exp_r = round(float(series.mean()), 4)

    gw = float(wins.sum()) if nw > 0 else 0.0
    gl = float(abs(losses.sum())) if nl > 0 else 0.0
    pf = round(gw / gl, 2) if gl > 0 else (99.0 if gw > 0 else 0.0)

    cum = series.cumsum()
    dd = cum.cummax() - cum
    max_dd = round(float(dd.max()), 2) if len(dd) > 0 else 0.0

    return {
        "label": label, "n": n, "w": nw, "l": nl, "be": nb,
        "wr": wr, "ci_low": ci_l, "ci_high": ci_h, "ci_str": ci_str,
        "avg_win": round(aw, 3), "avg_loss": round(al, 3), "payoff": payoff,
        "exp_r": exp_r, "net_r": net_r, "pf": pf, "max_dd": max_dd
    }


def compute_bundle_with_costs(series: pd.Series, label: str = "") -> dict:
    base = compute_kpis(series, label)
    s_mod = apply_cost_scenario(series, 0.05, 0.15)
    s_sev20 = apply_cost_scenario(series, 0.10, 0.20)
    s_sev25 = apply_cost_scenario(series, 0.10, 0.25)
    return {
        "base": base,
        "mod": compute_kpis(s_mod, f"{label} (Mod)"),
        "sev20": compute_kpis(s_sev20, f"{label} (Sev20)"),
        "sev25": compute_kpis(s_sev25, f"{label} (Sev25)"),
    }


def simulate_cap1(trades_df: pd.DataFrame, max_open: int = 1) -> tuple[pd.DataFrame, pd.DataFrame]:
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


def run_walkforward_variant(df_full: pd.DataFrame, filter_fn, n_folds: int = 4, cap: int = 1) -> dict:
    total = len(df_full)
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    oos_folds = []
    blk_folds = []
    pre_cap_folds = []
    fold_meta = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        split_time = df_full['time'].iloc[train_end]

        train_slice = df_full.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        purged_count = len(train_slice) - len(train_clean)

        test_slice = df_full.iloc[train_end:test_end].copy().reset_index(drop=True)

        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)

        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy().reset_index(drop=True)
        test_filtered = filter_fn(test_causal).copy().reset_index(drop=True)

        acc, blk = simulate_cap1(test_filtered, max_open=cap)
        if len(acc) > 0:
            acc = acc.copy()
            acc['fold'] = f + 1
            oos_folds.append(acc)
        if len(blk) > 0:
            blk = blk.copy()
            blk['fold'] = f + 1
            blk_folds.append(blk)
        if len(test_filtered) > 0:
            tf_copy = test_filtered.copy()
            tf_copy['fold'] = f + 1
            pre_cap_folds.append(tf_copy)

        t_start = test_slice['time'].min().strftime('%Y-%m-%d')
        t_end = test_slice['time'].max().strftime('%Y-%m-%d')
        acc_rr = acc['rr'] if len(acc) > 0 else pd.Series(dtype=float)

        fold_meta.append({
            "fold": f + 1,
            "split_time": str(split_time),
            "start_date": t_start,
            "end_date": t_end,
            "train_raw": len(train_slice),
            "train_clean": len(train_clean),
            "purged": purged_count,
            "test_raw": len(test_slice),
            "pos_syms": sorted(list(pos_syms)),
            "metrics": compute_bundle_with_costs(acc_rr, f"Fold {f+1} ({t_start} a {t_end})"),
            "n_blocked": len(blk),
            "blocked_net_r": round(float(blk['rr'].sum()), 2) if len(blk) > 0 else 0.0
        })

    df_oos = pd.concat(oos_folds, ignore_index=True) if oos_folds else pd.DataFrame()
    df_blk = pd.concat(blk_folds, ignore_index=True) if blk_folds else pd.DataFrame()
    df_pre = pd.concat(pre_cap_folds, ignore_index=True) if pre_cap_folds else pd.DataFrame()

    tot_rr = df_oos['rr'] if len(df_oos) > 0 else pd.Series(dtype=float)
    return {
        "trades": df_oos,
        "blocked": df_blk,
        "pre_cap": df_pre,
        "folds": fold_meta,
        "total": compute_bundle_with_costs(tot_rr, "Total OOS (4 Folds)"),
    }


def print_variant_report(name: str, res: dict, canonical_symbols: list[str], ref_v4_trades: pd.DataFrame | None = None):
    print("\n" + "=" * 130)
    print(f"REPORTE INTEGRAL DE VARIANTE: {name}")
    print("=" * 130)

    t = res["total"]
    b, m, s25, s20 = t["base"], t["mod"], t["sev25"], t["sev20"]
    print("1. MÉTRICAS GLOBALES OOS (4 FOLDS COMBINADOS):")
    print(f"   * Operaciones OOS Únicas: N = {b['n']} (Wins={b['w']}, Losses={b['l']}, BE={b['be']})")
    print(f"   * Win Rate Puntual      : {b['wr']:.1f}% | IC Wilson 95%: {b['ci_str']}")
    print(f"   * Payoff (AvgW / AvgL)  : {b['payoff']:.2f} (AvgWin={b['avg_win']:+.3f}R, AvgLoss=-{b['avg_loss']:.3f}R)")
    print(f"   * Costos Base (MT5 Real): Exp={b['exp_r']:+.4f} R/op | Net R={b['net_r']:+.2f} R | PF={b['pf']:.2f} | MaxDD={b['max_dd']:.2f} R")
    print(f"   * Costos Moderados      : Exp={m['exp_r']:+.4f} R/op | Net R={m['net_r']:+.2f} R | PF={m['pf']:.2f} | MaxDD={m['max_dd']:.2f} R (+0.05R slip, +15% gap SL)")
    print(f"   * Costos Severos (20%g) : Exp={s20['exp_r']:+.4f} R/op | Net R={s20['net_r']:+.2f} R | PF={s20['pf']:.2f} | MaxDD={s20['max_dd']:.2f} R (+0.10R slip, +20% gap SL)")
    print(f"   * Costos Severos (25%g) : Exp={s25['exp_r']:+.4f} R/op | Net R={s25['net_r']:+.2f} R | PF={s25['pf']:.2f} | MaxDD={s25['max_dd']:.2f} R (+0.10R slip, +25% gap SL)")

    # Contrafactuales Cap=1
    blk = res["blocked"]
    print(f"\n2. SEPARACIÓN PNL EJECUTADO VS CONTRAFACTUALES:")
    print(f"   * PnL Ejecutado (Aceptadas Cap=1)  : N={b['n']} | Net R={b['net_r']:+.2f} R")
    if len(blk) > 0:
        blk_w = blk[blk['rr'] > 0]
        blk_l = blk[blk['rr'] <= 0]
        print(f"   * Bloqueadas por Cap=1 (Contrafact): N={len(blk)} | Net R={blk['rr'].sum():+.2f} R "
              f"(Pérdidas evitadas: {len(blk_l)} ops [{blk_l['rr'].sum():+.2f}R], Ganancias no tomadas: {len(blk_w)} ops [{blk_w['rr'].sum():+.2f}R])")
    else:
        print("   * Bloqueadas por Cap=1 (Contrafact): N=0 | Net R=+0.00 R")

    if ref_v4_trades is not None:
        cur_trades = res["trades"]
        merged = pd.merge(ref_v4_trades, cur_trades[['time', 'symbol']], on=['time', 'symbol'], how='left', indicator=True)
        dropped = merged[merged['_merge'] == 'left_only']
        if len(dropped) > 0:
            dw = dropped[dropped['rr'] > 0]
            dl = dropped[dropped['rr'] <= 0]
            print(f"   * Excluidas respecto a V4 por filtro: N={len(dropped)} | PnL que habrían generado en V4={dropped['rr'].sum():+.2f} R "
                  f"(SL evitados: {len(dl)} ops [{dl['rr'].sum():+.2f}R], TP sacrificados: {len(dw)} ops [{dw['rr'].sum():+.2f}R])")

    # Por Ventana / Fold
    print("\n3. DESGLOSE POR VENTANA WALK-FORWARD (4 FOLDS):")
    print(f"   {'Ventana / Fold':32s} | {'Purga':5s} | {'N':3s} | {'W/L':5s} | {'WR%':5s} | {'Wilson 95%':14s} | {'Payoff':6s} | {'Exp(R)':8s} | {'NetR Base':9s} | {'PF':5s} | {'MaxDD':6s} | {'NetR Mod':8s} | {'PF Mod':6s} | {'NetR Sev25':10s} | {'PF Sev25':8s}")
    print("   " + "-" * 165)
    for fm in res["folds"]:
        fb = fm["metrics"]["base"]
        fmod = fm["metrics"]["mod"]
        fsev = fm["metrics"]["sev25"]
        wl = f"{fb['w']}/{fb['l']}"
        lbl = f"Fold {fm['fold']} ({fm['start_date']}..{fm['end_date']})"
        print(f"   {lbl:32s} | {fm['purged']:5d} | {fb['n']:3d} | {wl:5s} | {fb['wr']:4.1f}% | {fb['ci_str']:14s} | {fb['payoff']:6.2f} | {fb['exp_r']:+7.4f}R | {fb['net_r']:+8.2f}R | {fb['pf']:5.2f} | {fb['max_dd']:5.2f}R | {fmod['net_r']:+7.2f}R | {fmod['pf']:6.2f} | {fsev['net_r']:+9.2f}R | {fsev['pf']:8.2f}")

    # Por Familia
    print("\n4. DESGLOSE POR FAMILIA DE ACTIVOS:")
    df_t = res["trades"].copy()
    if len(df_t) > 0:
        df_t["fam3"] = df_t["symbol"].apply(get_family_3way)
        df_t["fam4"] = df_t["symbol"].apply(get_family_4way)
        print(f"   {'Familia':22s} | {'N':3s} | {'W/L':5s} | {'WR%':5s} | {'Wilson 95%':14s} | {'Payoff':6s} | {'Exp(R)':8s} | {'NetR Base':9s} | {'PF':5s} | {'MaxDD':6s} | {'NetR Mod':8s} | {'PF Mod':6s} | {'NetR Sev25':10s} | {'PF Sev25':8s}")
        print("   " + "-" * 155)
        for fam_code, fam_label in [("SYNTH", "Sintéticos (SYNTH)"), ("METALS", "Metales+WS30 (METALS)"), ("FOREX", "Forex (FOREX)")]:
            sub = df_t[df_t["fam3"] == fam_code]
            sb = compute_bundle_with_costs(sub["rr"] if len(sub) > 0 else pd.Series(dtype=float), fam_label)
            kb, km, ks = sb["base"], sb["mod"], sb["sev25"]
            wl = f"{kb['w']}/{kb['l']}"
            print(f"   {fam_label:22s} | {kb['n']:3d} | {wl:5s} | {kb['wr']:4.1f}% | {kb['ci_str']:14s} | {kb['payoff']:6.2f} | {kb['exp_r']:+7.4f}R | {kb['net_r']:+8.2f}R | {kb['pf']:5.2f} | {kb['max_dd']:5.2f}R | {km['net_r']:+7.2f}R | {km['pf']:6.2f} | {ks['net_r']:+9.2f}R | {ks['pf']:8.2f}")
        for fam_code, fam_label in [("METALS_PURE", "  -> Solo XAU/XAG"), ("INDEX", "  -> Solo WS30")]:
            sub = df_t[df_t["fam4"] == fam_code]
            sb = compute_bundle_with_costs(sub["rr"] if len(sub) > 0 else pd.Series(dtype=float), fam_label)
            kb, km, ks = sb["base"], sb["mod"], sb["sev25"]
            wl = f"{kb['w']}/{kb['l']}"
            print(f"   {fam_label:22s} | {kb['n']:3d} | {wl:5s} | {kb['wr']:4.1f}% | {kb['ci_str']:14s} | {kb['payoff']:6.2f} | {kb['exp_r']:+7.4f}R | {kb['net_r']:+8.2f}R | {kb['pf']:5.2f} | {kb['max_dd']:5.2f}R | {km['net_r']:+7.2f}R | {km['pf']:6.2f} | {ks['net_r']:+9.2f}R | {ks['pf']:8.2f}")

    # Por Activo
    print("\n5. DESGLOSE POR ACTIVO (UNIVERSO CANÓNICO DE 23 ACTIVOS):")
    print(f"   {'Símbolo':26s} | {'Fam':6s} | {'N':3s} | {'W/L':5s} | {'WR%':5s} | {'Wilson 95%':14s} | {'Payoff':6s} | {'Exp(R)':8s} | {'NetR Base':9s} | {'PF':5s} | {'MaxDD':6s} | {'NetR Mod':8s} | {'NetR Sev25':10s}")
    print("   " + "-" * 145)
    pos_assets = 0
    neg_assets = 0
    zero_assets = 0
    for sym in canonical_symbols:
        sub = df_t[df_t["symbol"] == sym] if len(df_t) > 0 else pd.DataFrame()
        fam = get_family_3way(sym)
        if len(sub) == 0:
            zero_assets += 1
            print(f"   {sym:26s} | {fam:6s} |   0 | 0/0   |  0.0% | [0.0%, 0.0%]   |   0.00 | +0.0000R |    +0.00R |  0.00 |  0.00R |   +0.00R |     +0.00R")
        else:
            sb = compute_bundle_with_costs(sub["rr"], sym)
            kb, km, ks = sb["base"], sb["mod"], sb["sev25"]
            if kb["net_r"] > 0:
                pos_assets += 1
            elif kb["net_r"] < 0:
                neg_assets += 1
            else:
                zero_assets += 1
            wl = f"{kb['w']}/{kb['l']}"
            print(f"   {sym:26s} | {fam:6s} | {kb['n']:3d} | {wl:5s} | {kb['wr']:4.1f}% | {kb['ci_str']:14s} | {kb['payoff']:6.2f} | {kb['exp_r']:+7.4f}R | {kb['net_r']:+8.2f}R | {kb['pf']:5.2f} | {kb['max_dd']:5.2f}R | {km['net_r']:+7.2f}R | {ks['net_r']:+9.2f}R")
    print(f"   --> Distribución sobre 23 activos: Positivos={pos_assets}/23 ({pos_assets/23*100:.1f}%), Negativos={neg_assets}/23 ({neg_assets/23*100:.1f}%), Sin Trades={zero_assets}/23 ({zero_assets/23*100:.1f}%)")


def main():
    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))

    # =========================================================================
    # PARTE I: DATASET CONSOLIDADO LIMPIO DE 23 ACTIVOS (957 TRADES)
    # =========================================================================
    csv_clean = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df_clean = pd.read_csv(csv_clean)
    df_clean['time'] = pd.to_datetime(df_clean['time'], utc=True)
    df_clean['exit_time'] = pd.to_datetime(df_clean['exit_time'], utc=True)
    df_clean['subfamily'] = df_clean['symbol'].apply(get_family_3way)
    df_clean = df_clean[df_clean['symbol'].isin(canonical_symbols)].sort_values('time').reset_index(drop=True)

    # Filtros para A, B, C1 y C2
    def f_a(d: pd.DataFrame) -> pd.DataFrame:
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    def f_b(d: pd.DataFrame) -> pd.DataFrame:
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5) & (d['symbol'] != 'Crash 1000 Index')]

    def f_c1(d: pd.DataFrame) -> pd.DataFrame:
        # C1: Como en detailed_v4_vs_var3_breakdown.py (FOREX + METALS donde METALS incluye XAUUSD, XAGUSD, Wall Street 30)
        c_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_strict | c_synth]

    def f_c2(d: pd.DataFrame) -> pd.DataFrame:
        # C2: Solo divisas Forex + Metales puros (XAUUSD, XAGUSD) con ATR <= 1.2; Sintéticos y Wall Street 30 con ATR <= 1.5
        is_fx_or_pure_metal = d['symbol'].isin(FOREX | METALS_STRICT)
        c_strict = is_fx_or_pure_metal & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_other = (~is_fx_or_pure_metal) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_strict | c_other]

    res_a = run_walkforward_variant(df_clean, f_a, n_folds=4, cap=1)
    res_b = run_walkforward_variant(df_clean, f_b, n_folds=4, cap=1)
    res_c1 = run_walkforward_variant(df_clean, f_c1, n_folds=4, cap=1)
    res_c2 = run_walkforward_variant(df_clean, f_c2, n_folds=4, cap=1)

    print_variant_report("A. V4 SIN CAMBIOS (Dataset Limpio 23 Activos, 957 Trades -> N=42)", res_a, canonical_symbols)
    print_variant_report("B. V4 EXCLUYENDO CRASH 1000 INDEX (Mismos Splits -> N=37)", res_b, canonical_symbols, ref_v4_trades=res_a["trades"])
    print_variant_report("C1. V4 CON ATR <= 1.2 EN FOREX Y METALES/ÍNDICES (Incl. WS30, Reproducción Script Local -> N=36)", res_c1, canonical_symbols, ref_v4_trades=res_a["trades"])
    print_variant_report("C2. V4 CON ATR <= 1.2 SOLO EN FOREX Y METALES PUROS (XAU/XAG; WS30 en ATR<=1.5 -> N=38)", res_c2, canonical_symbols, ref_v4_trades=res_a["trades"])

    # =========================================================================
    # PARTE II: RECONCILIACIÓN SOBRE DATASET BASE DE 9 ACTIVOS (727 TRADES -> N=40)
    # =========================================================================
    csv_base9 = PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv"
    df_b9 = pd.read_csv(csv_base9)
    df_b9['time'] = pd.to_datetime(df_b9['time'], utc=True)
    df_b9 = df_b9.sort_values('time').reset_index(drop=True)
    df_b9['exit_time'] = df_b9['time'] + pd.to_timedelta(df_b9['bars'] * 15, unit='m')
    df_b9['subfamily'] = df_b9['symbol'].apply(get_family_3way)
    df_b9 = df_b9[df_b9['symbol'].isin(canonical_symbols)].reset_index(drop=True)

    res_a_40 = run_walkforward_variant(df_b9, f_a, n_folds=4, cap=1)
    res_b_40 = run_walkforward_variant(df_b9, f_b, n_folds=4, cap=1)
    res_c1_40 = run_walkforward_variant(df_b9, f_c1, n_folds=4, cap=1)
    res_c2_40 = run_walkforward_variant(df_b9, f_c2, n_folds=4, cap=1)

    print("\n" + "=" * 130)
    print("PARTE II: TABLA COMPARATIVA EN DATASET BASE DE 9 ACTIVOS (672 TRADES EN ALLOWLIST -> BENCHMARK HISTÓRICO N=40)")
    print("=" * 130)
    for lbl, r40 in [
        ("A (Base N=40): V4 sin cambios", res_a_40),
        ("B (Base N=35): V4 sin Crash 1000", res_b_40),
        ("C1 (Base N=35): V4 ATR<=1.2 Fx+Met+WS30", res_c1_40),
        ("C2 (Base N=37): V4 ATR<=1.2 Fx+XAU/XAG", res_c2_40),
    ]:
        kb = r40["total"]["base"]
        km = r40["total"]["mod"]
        ks20 = r40["total"]["sev20"]
        ks25 = r40["total"]["sev25"]
        print(f"{lbl:38s} | N={kb['n']:2d} ({kb['w']}W/{kb['l']}L) | WR={kb['wr']:4.1f}% {kb['ci_str']:14s} | Payoff={kb['payoff']:4.2f} | "
              f"Exp={kb['exp_r']:+.4f}R | NetBase={kb['net_r']:+6.2f}R (PF {kb['pf']:4.2f}, DD {kb['max_dd']:4.2f}R) | "
              f"NetMod={km['net_r']:+6.2f}R (PF {km['pf']:4.2f}) | NetSev20={ks20['net_r']:+6.2f}R (PF {ks20['pf']:4.2f}) | NetSev25={ks25['net_r']:+6.2f}R (PF {ks25['pf']:4.2f})")

    # =========================================================================
    # PARTE III: VERIFICACIÓN DE COHORTE PROSPECTIVA SELLADA Y STAGING (?mode=ro)
    # =========================================================================
    print("\n" + "=" * 130)
    print("PARTE III: VERIFICACIÓN EN SOLO LECTURA (?mode=ro) DE COHORTE PROSPECTIVA SELLADA Y STAGING")
    print("=" * 130)
    for db_label, db_path in [
        ("PROSPECTIVA SELLADA (shadow_research.sqlite3)", PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"),
        ("STAGING AISLADA (shadow_research_staging.sqlite3)", PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3")
    ]:
        if db_path.exists():
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            df_sh = pd.read_sql_query("""
                SELECT id, timestamp, strategy, variant, symbol, direction,
                       mechanical_decision, rejection_reason, final_action,
                       market_outcome, market_rr, features_json
                FROM shadow_signals
                WHERE strategy = 'MSNR'
                ORDER BY id ASC
            """, con)
            con.close()
            df_sh['subfamily'] = df_sh['symbol'].apply(get_family_3way)
            exec_df = df_sh[df_sh['final_action'] == 'ACCEPTED_EXECUTION']
            disc_df = df_sh[df_sh['final_action'] != 'ACCEPTED_EXECUTION']
            exec_closed = exec_df[exec_df['market_outcome'].isin(['TP1_WIN', 'FULL_TP', 'SL_LOSS', 'CLOSED_OTHER']) & (exec_df['market_rr'] != 0.0)]
            disc_closed = disc_df[disc_df['market_outcome'].isin(['TP1_WIN', 'FULL_TP', 'SL_LOSS', 'CLOSED_OTHER']) & (disc_df['market_rr'] != 0.0)]
            fx_met_exec_closed = exec_closed[exec_closed['subfamily'].isin(['FOREX', 'METALS'])]

            print(f"\n[{db_label}]")
            print(f"  * Total señales MSNR registradas                    : {len(df_sh)}")
            print(f"  * Señales aceptadas para ejecución (ACCEPTED)       : {len(exec_df)}")
            print(f"  * Cierres prospectivos EJECUTADOS (meta >= 100)     : {len(exec_closed)} cierres | PnL Ejecutado = {exec_closed['market_rr'].sum():+.4f} R")
            for _, r in exec_closed.iterrows():
                print(f"      - ID {r['id']:2d} | {r['timestamp']} | {r['symbol']:18s} ({r['subfamily']}) | {r['direction']:4s} | {r['market_outcome']:10s} | {r['market_rr']:+.4f} R")
            print(f"  * Cierres prospectivos EJECUTADOS en Forex/Metales  : {len(fx_met_exec_closed)} de 20 requeridos (Paso 4)")
            print(f"  * Señales descartadas por filtro (DISCARDED)        : {len(disc_df)}")
            print(f"  * Descartadas con desenlace contrafactual medido    : {len(disc_closed)} eventos | PnL Contrafactual = {disc_closed['market_rr'].sum():+.4f} R")
            for _, r in disc_closed.iterrows():
                print(f"      - ID {r['id']:2d} | {r['timestamp']} | {r['symbol']:18s} ({r['subfamily']}) | {r['direction']:4s} | {r['market_outcome']:10s} | {r['market_rr']:+.4f} R (Rechazo: {r['rejection_reason']})")

    # =========================================================================
    # PARTE IV: AUDITORÍA DE COBERTURA M15 REAL POR ACTIVO (23 CANÓNICOS)
    # =========================================================================
    print("\n" + "=" * 130)
    print("PARTE IV: AUDITORÍA DE COBERTURA M15 REAL POR ACTIVO EN EL UNIVERSO CANÓNICO (23 ACTIVOS)")
    print("=" * 130)
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"
    print(f"{'Símbolo Canónico':26s} | {'Familia':8s} | {'Archivo M15 Local':32s} | {'Barras M15':10s} | {'Inicio M15':10s} | {'Fin M15':10s} | {'Días':6s} | {'Años':5s} | {'Trades Replay 180d'}")
    print("-" * 135)
    for sym in canonical_symbols:
        fam = get_family_3way(sym)
        slug1 = sym.replace(' ', '_')
        slug2 = sym.replace(' ', '_').replace('(', '').replace(')', '')
        p_m15 = cache_dir / f"{slug1}_M15.pkl"
        if not p_m15.exists():
            p_m15 = cache_dir / f"{slug2}_M15.pkl"
        if p_m15.exists():
            with open(p_m15, "rb") as f:
                df_b = pickle.load(f)
            t_col = 'time' if 'time' in df_b.columns else ('datetime' if 'datetime' in df_b.columns else None)
            ts = pd.to_datetime(df_b[t_col], utc=True) if t_col else pd.to_datetime(df_b.index, utc=True)
            t_min = ts.iloc[0]
            t_max = ts.iloc[-1]
            days = (t_max - t_min).total_seconds() / 86400.0
            years = days / 365.25
            n_tr = len(df_clean[df_clean['symbol'] == sym])
            print(f"{sym:26s} | {fam:8s} | {p_m15.name:32s} | {len(df_b):10,d} | {str(t_min)[:10]:10s} | {str(t_max)[:10]:10s} | {days:6.1f} | {years:5.2f} | {n_tr:4d} ops")
        else:
            print(f"{sym:26s} | {fam:8s} | {'NO ENCONTRADO':32s} |          0 | N/A        | N/A        |    0.0 |  0.00 |    0 ops")


if __name__ == "__main__":
    main()
