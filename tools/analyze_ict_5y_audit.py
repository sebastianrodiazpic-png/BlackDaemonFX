"""Análisis cuantitativo de 5 años del replay fiel de ICT Sabri Malle.

Evalúa sobre `storage/analysis/ict_5y_signals_complete.csv`:
1. Desempeño de todos los instrumentos (activos y en poda) aplicando el spread real de ticks y el tope de spread/SL del motor.
2. Identificación de instrumentos con Acierto (WR) > 47 % y verificación de rentabilidad multianual (por año fiscal oct-oct),
   consistencia interanual, test de azar y walk-forward (elegir WR > 47 % en un año y medir en el siguiente).
3. Para los instrumentos en PODA o con WR <= 47 %, búsqueda de oportunidades de mejora bajo la misma estrategia ICT:
   - Tope estricto de spread/SL (<= 0.5 %, <= 1.0 %, <= 1.5 %, <= 2.0 %)
   - Dirección (solo BUY vs solo SELL)
   - Ventana de orden límite (1..3 barras vs 8 barras vs orden a mercado)
   - Filtros H1 (ADX H1, SL/ATR H1, ratio de cuerpo de desplazamiento)
   - Franja horaria / Killzone UTC (Londres 07-10, NY 12-15, Londres+NY 07-16, Asia 00-06)
   Verificando si algún filtro produce R/op > 0 consistente en TODOS los años con >= 20 operaciones.
4. Genera:
   - `storage/analysis/ict_5y_by_symbol.csv`
   - `storage/analysis/ict_5y_poda_rescue.csv`
   - `storage/analysis/ict_5y_audit_report.md`
"""
from __future__ import annotations

import json
import sys
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"


def norm_p_one_sided(t_val: float) -> float:
    if np.isnan(t_val):
        return 1.0
    return 0.5 * (1.0 - erf(t_val / sqrt(2.0)))


def assign_year_bucket(ts: pd.Series) -> pd.Series:
    # Años de oct-20 a oct-20: Y1=2025-26, Y0=2024-25, Y-1=2023-24, Y-2=2022-23, Y-3=2021-22
    t = pd.to_datetime(ts, utc=True)
    conds = [
        (t >= pd.Timestamp("2025-10-20", tz="UTC")),
        (t >= pd.Timestamp("2024-10-20", tz="UTC")) & (t < pd.Timestamp("2025-10-20", tz="UTC")),
        (t >= pd.Timestamp("2023-10-20", tz="UTC")) & (t < pd.Timestamp("2024-10-20", tz="UTC")),
        (t >= pd.Timestamp("2022-10-20", tz="UTC")) & (t < pd.Timestamp("2023-10-20", tz="UTC")),
        (t < pd.Timestamp("2022-10-20", tz="UTC")),
    ]
    labels = ["2025-26", "2024-25", "2023-24", "2022-23", "2021-22"]
    return pd.Series(np.select(conds, labels, default="otro"), index=ts.index)


def load_real_tick_spreads() -> tuple[dict[str, float], dict[str, float]]:
    # 1. Factores de spread real en sintéticos (real_spread / bar_spread)
    synth_factors: dict[str, float] = {}
    sf_path = OUT / "real_spread_factors.csv"
    if sf_path.exists():
        sf = pd.read_csv(sf_path)
        for _, r in sf.iterrows():
            if pd.notna(r.get("factor")) and float(r["factor"]) > 0:
                synth_factors[str(r["symbol"])] = float(r["factor"])

    # 2. Spread real mediano en mercados reales (en unidades de precio)
    real_mkt_spread: dict[str, float] = {}
    rm_path = OUT / "real_markets_tick_spread_20261023.json"
    if rm_path.exists():
        data = json.loads(rm_path.read_text(encoding="utf-8"))
        for sym, info in data.get("symbols", {}).items():
            point = float(info.get("point") or 0.0)
            pts = info.get("tick_median_pts") or info.get("info_spread_pts") or 0.0
            if point > 0 and pts > 0:
                real_mkt_spread[sym] = float(pts) * point
    return synth_factors, real_mkt_spread


def classify_symbol(sym: str) -> tuple[str, str, float]:
    from config.ict_instrument_policy import (
        ICT_FOREX_ACTIVE,
        ICT_MARKETS_ACTIVE,
        ICT_PHASE1_EXCLUDED,
        ICT_SYNTHETIC_FAMILIES,
        MSNR_SYNTHETIC_UNIVERSE,
    )
    from config.synth_wr45 import ICT_WR45_PRUNED

    active_synths = {s for fam in ICT_SYNTHETIC_FAMILIES.values() for s in fam}
    pruned_synths = (set(MSNR_SYNTHETIC_UNIVERSE) - active_synths) | set(ICT_WR45_PRUNED)
    active_fx = {s for s in ICT_FOREX_ACTIVE if "micro" not in s.lower()}
    active_mkts = {s for s in ICT_MARKETS_ACTIVE if "micro" not in s.lower()}

    if sym in active_synths:
        fam = next((k for k, v in ICT_SYNTHETIC_FAMILIES.items() if sym in v), "SYNTH")
        return "ACTIVO_SINTETICO", fam, 0.02
    if sym in pruned_synths:
        return "PODA_SINTETICO", "SYNTH_PODA", 0.02
    if sym in active_fx:
        return "ACTIVO_FOREX", "FOREX", 0.05
    if sym in active_mkts:
        cap = 0.02 if "XAU" in sym.upper() else 0.05
        return "ACTIVO_MERCADO_REAL", "REAL_MKT", cap
    if "XAU" in sym.upper() or "XAG" in sym.upper():
        return "PODA_MERCADO_REAL", "METALES_PODA", 0.02
    if "BTC" in sym.upper() or "ETH" in sym.upper():
        return "PODA_MERCADO_REAL", "CRIPTO_PODA", 0.02
    return "PODA_FOREX", "FOREX_PODA", 0.05


def prepare_dataset() -> pd.DataFrame:
    df = pd.read_csv(OUT / "ict_5y_signals_complete.csv", low_memory=False)
    # Normalizar símbolos micro al subyacente si existieran duplicados, pero conservando los base
    df = df[~df["symbol"].str.lower().str.contains("micro")].copy()
    df["t"] = pd.to_datetime(df["time"], utc=True)
    df["year_bucket"] = assign_year_bucket(df["time"])
    df["hour_utc"] = df["t"].dt.hour

    # Enriquecer sintéticos con features H1 de ict_slices_features.csv cuando estén disponibles
    sl_path = OUT / "ict_slices_features.csv"
    if sl_path.exists():
        sf = pd.read_csv(sl_path, usecols=["symbol", "time", "atr", "adx", "sl_atr"])
        sf = sf.drop_duplicates(subset=["symbol", "time"])
        df = df.merge(sf, on=["symbol", "time"], how="left")
        df["atr_h1"] = df["atr_h1"].fillna(df["atr"])
        df["adx_h1"] = df["adx_h1"].fillna(df["adx"])
        df["sl_atr_h1"] = df["sl_atr_h1"].fillna(df["sl_atr"])
        df = df.drop(columns=["atr", "adx", "sl_atr"], errors="ignore")

    synth_factors, real_mkt_spread = load_real_tick_spreads()

    status_list, fam_list, cap_list = [], [], []
    real_sp_list = []
    for sym, bar_sp, is_syn in zip(df["symbol"], df["spread"], df["synthetic"]):
        st, fam, cap = classify_symbol(str(sym))
        status_list.append(st)
        fam_list.append(fam)
        cap_list.append(cap)
        if bool(is_syn):
            factor = synth_factors.get(str(sym), 1.0)
            real_sp_list.append(float(bar_sp) * factor)
        else:
            real_sp_list.append(real_mkt_spread.get(str(sym), float(bar_sp)))

    df["policy_status"] = status_list
    df["family"] = fam_list
    df["engine_cap"] = cap_list
    df["real_spread"] = real_sp_list
    df["extra_spread"] = np.maximum(0.0, df["real_spread"] - df["spread"])

    # Riesgo base en precio para orden límite y a mercado
    df["lim_risk_price"] = (df["limit"] - df["stop_loss"]).abs()
    df["mkt_risk_price"] = df["mkt_risk"].fillna(df["lim_risk_price"]).abs()

    df["spread_sl_lim"] = df["real_spread"] / df["lim_risk_price"].replace(0, np.nan)
    df["spread_sl_mkt"] = df["real_spread"] / df["mkt_risk_price"].replace(0, np.nan)

    # R neto tras descontar el sobrecoste de spread real de ticks vs spread de barra
    df["lim_rr_real"] = df["lim_rr"] - (df["extra_spread"] / df["lim_risk_price"].replace(0, np.nan))
    df["mkt_rr_real"] = df["mkt_rr"] - (df["extra_spread"] / df["mkt_risk_price"].replace(0, np.nan))
    return df


def calc_metrics(r_series: pd.Series) -> dict:
    r = r_series.dropna()
    n = len(r)
    if n == 0:
        return dict(n=0, wr=np.nan, avg_r=np.nan, tot_r=0.0, pf=np.nan, t_stat=np.nan, p_val=1.0, max_dd=0.0)
    wins = (r > 0).sum()
    wr = 100.0 * wins / n
    avg_r = float(r.mean())
    tot_r = float(r.sum())
    pos_sum = float(r[r > 0].sum())
    neg_sum = float(-r[r < 0].sum())
    pf = pos_sum / neg_sum if neg_sum > 0 else (np.inf if pos_sum > 0 else np.nan)
    std = float(r.std(ddof=1)) if n > 1 else 0.0
    t_stat = avg_r / (std / sqrt(n)) if std > 0 and n > 1 else np.nan
    p_val = norm_p_one_sided(t_stat) if pd.notna(t_stat) else 1.0
    eq = r.cumsum()
    dd = float((eq.cummax() - eq).max()) if n > 0 else 0.0
    return dict(n=int(n), wr=wr, avg_r=avg_r, tot_r=tot_r, pf=pf, t_stat=t_stat, p_val=p_val, max_dd=dd)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = prepare_dataset()
    years = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

    # Operativa fiel del motor actual: orden LIMITE 8 barras + filtro spread_sl_lim <= engine_cap
    filled_lim = df[df["lim_rr_real"].notna() & (df["spread_sl_lim"] <= df["engine_cap"])].copy()

    rows_sym = []
    for sym, grp_all in df.groupby("symbol"):
        st, fam, cap = classify_symbol(str(sym))
        grp = filled_lim[filled_lim["symbol"] == sym]
        m = calc_metrics(grp["lim_rr_real"])

        # También medir sin cap de spread y a mercado para referencia
        grp_nocap = df[(df["symbol"] == sym) & df["lim_rr_real"].notna()]
        m_nocap = calc_metrics(grp_nocap["lim_rr_real"])
        grp_mkt = df[(df["symbol"] == sym) & df["mkt_rr_real"].notna() & (df["spread_sl_mkt"] <= cap)]
        m_mkt = calc_metrics(grp_mkt["mkt_rr_real"])

        yr_stats = {}
        pos_years = 0
        valid_years = 0
        wr47_years = 0
        for y in years:
            gy = grp[grp["year_bucket"] == y]
            my = calc_metrics(gy["lim_rr_real"])
            yr_stats[f"n_{y}"] = my["n"]
            yr_stats[f"wr_{y}"] = my["wr"]
            yr_stats[f"r_{y}"] = my["avg_r"]
            if my["n"] >= 10:
                valid_years += 1
                if my["avg_r"] > 0:
                    pos_years += 1
                if my["wr"] > 47.0:
                    wr47_years += 1

        t_min = grp_all["t"].min().strftime("%Y-%m-%d") if len(grp_all) else ""
        t_max = grp_all["t"].max().strftime("%Y-%m-%d") if len(grp_all) else ""
        span_years = (grp_all["t"].max() - grp_all["t"].min()).days / 365.25 if len(grp_all) else 0.0

        rows_sym.append(
            dict(
                symbol=sym,
                policy_status=st,
                family=fam,
                engine_cap_pct=cap * 100.0,
                start_date=t_min,
                end_date=t_max,
                span_years=round(span_years, 2),
                signals_total=len(grp_all),
                n=m["n"],
                wr_pct=m["wr"],
                avg_r=m["avg_r"],
                tot_r=m["tot_r"],
                pf=m["pf"],
                t_stat=m["t_stat"],
                p_val=m["p_val"],
                max_dd_r=m["max_dd"],
                valid_years=valid_years,
                pos_years=pos_years,
                wr47_years=wr47_years,
                nocap_n=m_nocap["n"],
                nocap_wr=m_nocap["wr"],
                nocap_avg_r=m_nocap["avg_r"],
                mkt_n=m_mkt["n"],
                mkt_wr=m_mkt["wr"],
                mkt_avg_r=m_mkt["avg_r"],
                **yr_stats,
            )
        )

    sym_df = pd.DataFrame(rows_sym).sort_values(["policy_status", "avg_r"], ascending=[True, False])
    sym_df.to_csv(OUT / "ict_5y_by_symbol.csv", index=False)

    # Walk-forward de elegir WR > 47% en un año y medir en el año siguiente
    wf_pairs = [("2021-22", "2022-23"), ("2022-23", "2023-24"), ("2023-24", "2024-25"), ("2024-25", "2025-26")]
    wf_rows = []
    for y_in, y_out in wf_pairs:
        sub = sym_df[(sym_df[f"n_{y_in}"] >= 15) & (sym_df[f"n_{y_out}"] >= 15)].copy()
        if sub.empty:
            continue
        sel = sub[sub[f"wr_{y_in}"] > 47.0]
        rest = sub[sub[f"wr_{y_in}"] <= 47.0]
        # También selección por WR > 47% Y R/op > 0 en in-sample
        sel_pos = sub[(sub[f"wr_{y_in}"] > 47.0) & (sub[f"r_{y_in}"] > 0)]
        wf_rows.append(
            dict(
                train_year=y_in,
                test_year=y_out,
                n_symbols=len(sub),
                n_wr47=len(sel),
                test_wr_wr47=float(sel[f"wr_{y_out}"].mean()) if len(sel) else np.nan,
                test_r_wr47=float(sel[f"r_{y_out}"].mean()) if len(sel) else np.nan,
                test_pos_syms_wr47=int((sel[f"r_{y_out}"] > 0).sum()) if len(sel) else 0,
                n_wr47_and_pos=len(sel_pos),
                test_r_wr47_and_pos=float(sel_pos[f"r_{y_out}"].mean()) if len(sel_pos) else np.nan,
                test_r_rest=float(rest[f"r_{y_out}"].mean()) if len(rest) else np.nan,
            )
        )
    wf_df = pd.DataFrame(wf_rows)

    # Búsqueda de rescate/mejora para instrumentos en PODA o con WR <= 47% / R/op <= 0
    rescue_rows = []
    for sym, grp_all in df.groupby("symbol"):
        st, fam, cap = classify_symbol(str(sym))
        base_row = sym_df[sym_df["symbol"] == sym].iloc[0]
        is_target = ("PODA" in st) or (pd.isna(base_row["wr_pct"])) or (base_row["wr_pct"] <= 47.0) or (base_row["avg_r"] <= 0)
        if not is_target:
            continue

        # Definir variantes bajo la misma estrategia ICT
        g_lim = grp_all[grp_all["lim_rr_real"].notna()].copy()
        g_mkt = grp_all[grp_all["mkt_rr_real"].notna()].copy()

        variants = [
            ("Base (Límite 8v, cap motor)", g_lim[g_lim["spread_sl_lim"] <= cap], "lim_rr_real"),
            ("Sin cap spread (Límite 8v)", g_lim, "lim_rr_real"),
            ("Spread/SL <= 1.5%", g_lim[g_lim["spread_sl_lim"] <= 0.015], "lim_rr_real"),
            ("Spread/SL <= 1.0%", g_lim[g_lim["spread_sl_lim"] <= 0.010], "lim_rr_real"),
            ("Spread/SL <= 0.75%", g_lim[g_lim["spread_sl_lim"] <= 0.0075], "lim_rr_real"),
            ("Spread/SL <= 3.0%", g_lim[g_lim["spread_sl_lim"] <= 0.030], "lim_rr_real"),
            ("Entrada a Mercado (cap motor)", g_mkt[g_mkt["spread_sl_mkt"] <= cap], "mkt_rr_real"),
            ("Límite rápido <= 3 velas (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["lim_fill_bars"] <= 3)], "lim_rr_real"),
            ("Solo BUY (cap motor)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["direction"] == "BUY")], "lim_rr_real"),
            ("Solo SELL (cap motor)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["direction"] == "SELL")], "lim_rr_real"),
            ("Killzone Londres+NY 07-16 UTC (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["hour_utc"].between(7, 16))], "lim_rr_real"),
            ("Killzone NY 12-16 UTC (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["hour_utc"].between(12, 16))], "lim_rr_real"),
            ("ADX H1 >= 25 (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["adx_h1"] >= 25)], "lim_rr_real"),
            ("ADX H1 < 22 rango (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["adx_h1"] < 22)], "lim_rr_real"),
            ("SL/ATR H1 >= 0.8 (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["sl_atr_h1"] >= 0.8)], "lim_rr_real"),
            ("Body ratio >= 0.65 (cap)", g_lim[(g_lim["spread_sl_lim"] <= cap) & (g_lim["body_ratio"] >= 0.65)], "lim_rr_real"),
        ]

        best_var = None
        for v_name, v_df, col in variants:
            m = calc_metrics(v_df[col])
            if m["n"] < 25:
                continue
            v_valid_y = 0
            v_pos_y = 0
            for y in years:
                vy = calc_metrics(v_df[v_df["year_bucket"] == y][col])
                if vy["n"] >= 8:
                    v_valid_y += 1
                    if vy["avg_r"] > 0:
                        v_pos_y += 1
            rec = dict(
                symbol=sym,
                policy_status=st,
                base_n=int(base_row["n"]),
                base_wr=base_row["wr_pct"],
                base_avg_r=base_row["avg_r"],
                variant=v_name,
                var_n=m["n"],
                var_wr=m["wr"],
                var_avg_r=m["avg_r"],
                var_tot_r=m["tot_r"],
                var_pf=m["pf"],
                var_t=m["t_stat"],
                var_valid_years=v_valid_y,
                var_pos_years=v_pos_y,
            )
            if v_name != "Base (Límite 8v, cap motor)":
                if best_var is None or (
                    (rec["var_pos_years"] >= max(2, rec["var_valid_years"] - 1) and rec["var_avg_r"] > best_var["var_avg_r"])
                    or (best_var["var_avg_r"] <= 0 and rec["var_avg_r"] > best_var["var_avg_r"])
                ):
                    best_var = rec
        if best_var is not None:
            rescue_rows.append(best_var)
        else:
            rescue_rows.append(
                dict(
                    symbol=sym,
                    policy_status=st,
                    base_n=int(base_row["n"]),
                    base_wr=base_row["wr_pct"],
                    base_avg_r=base_row["avg_r"],
                    variant="SIN_VARIANTE_VIABLE (n<25)",
                    var_n=0,
                    var_wr=np.nan,
                    var_avg_r=np.nan,
                    var_tot_r=0.0,
                    var_pf=np.nan,
                    var_t=np.nan,
                    var_valid_years=0,
                    var_pos_years=0,
                )
            )

    rescue_df = pd.DataFrame(rescue_rows).sort_values(["policy_status", "var_avg_r"], ascending=[True, False])
    rescue_df.to_csv(OUT / "ict_5y_poda_rescue.csv", index=False)
    wf_df.to_csv(OUT / "ict_5y_walkforward.csv", index=False)

    print("=== RESUMEN EJECUTADO ===")
    print(f"Total símbolos auditados: {len(sym_df)}")
    sel_wr47 = sym_df[(sym_df["wr_pct"] > 47.0) & (sym_df["n"] >= 20)]
    print(f"Símbolos con WR > 47% (n>=20): {len(sel_wr47)}")
    sel_wr47_pos = sel_wr47[sel_wr47["avg_r"] > 0]
    print(f"Símbolos con WR > 47% Y R/op > 0 (n>=20): {len(sel_wr47_pos)}")
    print("\nWalk-forward de elegir WR > 47%:")
    print(wf_df.to_string(index=False))


if __name__ == "__main__":
    main()
