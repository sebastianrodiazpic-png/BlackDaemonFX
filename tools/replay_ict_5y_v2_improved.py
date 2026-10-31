"""Replay y evaluación multianual de 5 años (2021-2026) de ICT Sabri Malle v2 con las 6 mejoras aplicadas.

Enriquece el 100 % de las señales de 5 años (79 instrumentos) con el contexto H1 exacto (ATR H1 y ADX H1 de velas
cerradas en MT5 sin lookahead) cuando faltaba en los cortes Y0/Y1 previos, aplica las 6 mejoras estructurales y de
ejecución implementadas en `ICTSabriMalleStrategy` y `LiveTradingEngine`, y selecciona todos los instrumentos con
efectividad (Win Rate) > 47 % en el replay de 5 años.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
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


def enrich_missing_h1_features(df: pd.DataFrame) -> pd.DataFrame:
    """Completa atr_h1, adx_h1 y sl_atr_h1 desde MT5 para las filas de Y0/Y1 que no los tenían."""
    cache_path = OUT / "ict_5y_signals_h1_enriched.csv"
    if cache_path.exists():
        cached = pd.read_csv(cache_path, low_memory=False)
        if len(cached) >= len(df) and cached["adx_h1"].notna().mean() > 0.95:
            return cached

    missing_syms = sorted(df[df["adx_h1"].isna() | df["atr_h1"].isna()]["symbol"].unique())
    if not missing_syms:
        return df

    try:
        import MetaTrader5 as mt5
        from strategy.ict.ict_strategy import compute_atr
        from strategy.indicators import calculate_adx

        if mt5.initialize():
            print(f"Enriqueciendo H1 (ATR/ADX) desde MT5 para {len(missing_syms)} símbolos...", flush=True)
            parts = []
            for sym, grp in df.groupby("symbol", sort=False):
                g = grp.sort_values("t").copy()
                if g["adx_h1"].isna().any() or g["atr_h1"].isna().any():
                    mt5.symbol_select(str(sym), True)
                    t_min = (g["t"].min() - pd.Timedelta(days=15)).to_pydatetime()
                    t_max = (g["t"].max() + pd.Timedelta(days=2)).to_pydatetime()
                    chunks = []
                    a = t_min
                    while a < t_max:
                        b = min(t_max, a + timedelta(days=300))
                        rates = mt5.copy_rates_range(str(sym), mt5.TIMEFRAME_H1, a, b)
                        if rates is not None and len(rates):
                            chunks.append(pd.DataFrame(rates))
                        a = b
                    if chunks:
                        h1 = pd.concat(chunks, ignore_index=True).drop_duplicates("time").sort_values("time").reset_index(drop=True)
                        h1["time"] = pd.to_datetime(h1["time"], unit="s", utc=True)
                        h1["atr_calc"] = compute_atr(h1, period=14)
                        h1["adx_calc"] = calculate_adx(h1, 14).values
                        h1["avail_t"] = h1["time"] + pd.Timedelta(hours=1)
                        h1_ctx = h1[["avail_t", "atr_calc", "adx_calc"]].sort_values("avail_t")
                        merged = pd.merge_asof(
                            g,
                            h1_ctx,
                            left_on="t",
                            right_on="avail_t",
                            direction="backward",
                        )
                        merged["atr_h1"] = merged["atr_h1"].fillna(merged["atr_calc"])
                        merged["adx_h1"] = merged["adx_h1"].fillna(merged["adx_calc"])
                        risk_p = (merged["limit"] - merged["stop_loss"]).abs()
                        merged["sl_atr_h1"] = merged["sl_atr_h1"].fillna(
                            risk_p / merged["atr_h1"].replace(0, np.nan)
                        )
                        g = merged.drop(columns=["avail_t", "atr_calc", "adx_calc"], errors="ignore")
                parts.append(g)
            mt5.shutdown()
            df = pd.concat(parts, ignore_index=True)
            df.to_csv(cache_path, index=False)
            print(f"Guardado {cache_path.name} (cobertura adx_h1: {df['adx_h1'].notna().mean():.1%})", flush=True)
    except Exception as exc:
        print(f"Aviso MT5 H1 enrich: {exc}", flush=True)
    return df


def calc_metrics(r_series: pd.Series) -> dict:
    r = r_series.dropna()
    n = len(r)
    if n == 0:
        return dict(n=0, wr=np.nan, avg_r=np.nan, tot_r=0.0, pf=np.nan, t_stat=np.nan, p_val=1.0, max_dd=0.0)
    wins = int((r > 0).sum())
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


def classify_market_group(sym: str, is_syn: bool) -> tuple[str, float]:
    if is_syn:
        s_up = sym.upper()
        if "BOOM" in s_up and "VOL OVER" not in s_up:
            return "BOOM", 0.02
        if "CRASH" in s_up and "VOL OVER" not in s_up:
            return "CRASH", 0.02
        if "STEP" in s_up:
            return "STEP", 0.02
        if "JUMP" in s_up:
            return "JUMP", 0.02
        return "VOLATILITY", 0.02
    s_up = sym.upper()
    if any(k in s_up for k in ("XAU", "XAG", "GOLD", "SILVER")):
        return "METALS", 0.02
    if any(k in s_up for k in ("BTC", "ETH", "CRYPTO")):
        return "CRYPTO", 0.02
    if any(k in s_up for k in ("OIL", "TECH", "SP 500", "SP500", "WALL", "NAS", "US ")):
        return "INDEX_ENERGY", 0.025
    return "FOREX", 0.025


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from tools.analyze_ict_5y_audit import load_real_tick_spreads

    raw = pd.read_csv(OUT / "ict_5y_signals_complete.csv", low_memory=False)
    raw = raw[~raw["symbol"].str.lower().str.contains("micro")].copy()
    raw["t"] = pd.to_datetime(raw["time"], utc=True)

    # Mergear features previas de ict_slices_features.csv si existen
    sl_path = OUT / "ict_slices_features.csv"
    if sl_path.exists():
        sf = pd.read_csv(sl_path, usecols=["symbol", "time", "atr", "adx", "sl_atr"]).drop_duplicates(subset=["symbol", "time"])
        raw = raw.merge(sf, on=["symbol", "time"], how="left")
        raw["atr_h1"] = raw["atr_h1"].fillna(raw["atr"])
        raw["adx_h1"] = raw["adx_h1"].fillna(raw["adx"])
        raw["sl_atr_h1"] = raw["sl_atr_h1"].fillna(raw["sl_atr"])
        raw = raw.drop(columns=["atr", "adx", "sl_atr"], errors="ignore")

    df = enrich_missing_h1_features(raw)
    df["t"] = pd.to_datetime(df["time"], utc=True)
    df["year_bucket"] = assign_year_bucket(df["time"])
    df["t_ny"] = df["t"].dt.tz_convert("America/New_York")
    df["ny_hour"] = df["t_ny"].dt.hour

    synth_factors, real_mkt_spread = load_real_tick_spreads()

    fam_list, cap_v1_list, cap_v2_list, real_sp_list = [], [], [], []
    for sym, bar_sp, is_syn in zip(df["symbol"], df["spread"], df["synthetic"]):
        fam, cap_v2 = classify_market_group(str(sym), bool(is_syn))
        cap_v1 = 0.02 if (bool(is_syn) or fam in ("METALS", "CRYPTO")) else 0.05
        fam_list.append(fam)
        cap_v1_list.append(cap_v1)
        cap_v2_list.append(cap_v2)
        if bool(is_syn):
            real_sp_list.append(float(bar_sp) * synth_factors.get(str(sym), 1.0))
        else:
            real_sp_list.append(real_mkt_spread.get(str(sym), float(bar_sp)))

    df["family"] = fam_list
    df["cap_v1"] = cap_v1_list
    df["cap_v2"] = cap_v2_list
    df["real_spread"] = real_sp_list
    df["extra_spread"] = np.maximum(0.0, df["real_spread"] - df["spread"])

    df["lim_risk_price"] = (df["limit"] - df["stop_loss"]).abs()
    df["mkt_risk_price"] = df["mkt_risk"].fillna(df["lim_risk_price"]).abs()
    df["spread_sl_lim"] = df["real_spread"] / df["lim_risk_price"].replace(0, np.nan)
    df["spread_sl_mkt"] = df["real_spread"] / df["mkt_risk_price"].replace(0, np.nan)

    df["lim_rr_real"] = df["lim_rr"] - (df["extra_spread"] / df["lim_risk_price"].replace(0, np.nan))
    df["mkt_rr_real"] = df["mkt_rr"] - (df["extra_spread"] / df["mkt_risk_price"].replace(0, np.nan))

    sign = np.where(df["direction"] == "BUY", 1.0, -1.0)
    df["signed_pullback_r"] = sign * (df["close"] - df["limit"]) / df["lim_risk_price"].replace(0, np.nan)

    # Aplicación de las 6 mejoras sobre el flujo de señales de 5 años:
    # 1. Mejora 1: en sintéticos, sl_atr_h1 >= 1.0
    m1_ok = (~df["synthetic"]) | (df["sl_atr_h1"].isna()) | (df["sl_atr_h1"] >= 1.0)
    # 2. Mejora 2: profundidad máxima de retroceso <= 0.35 R
    m2_ok = df["signed_pullback_r"].isna() | (df["signed_pullback_r"] <= 0.35)
    # 3. Mejora 3: en mercados reales, London Killzone 03:00-05:00 NY (sin 02:00 NY ni 14:00 NY)
    m3_kz_ok = df["synthetic"] | df["ny_hour"].isin([3, 4, 5])
    # 4. Mejora 4: especialización direccional en Jump 50/75 (solo BUY) y Step Index (solo SELL)
    m4_dir_ok = ~(
        (df["symbol"].isin(["Jump 50 Index", "Jump 75 Index"]) & (df["direction"] != "BUY"))
        | ((df["symbol"] == "Step Index") & (df["direction"] != "SELL"))
    )
    # 5. Mejora 5: filtro de régimen ADX H1 >= 20.0
    m5_adx_ok = df["adx_h1"].isna() | (df["adx_h1"] >= 20.0)

    df["v2_signal_valid"] = m1_ok & m2_ok & m3_kz_ok & m4_dir_ok & m5_adx_ok

    # Para US Oil se ejecuta a mercado con spread_sl_mkt <= 0.05; para todos los demás (sintéticos y reales) orden limitada virtual con cap_v2
    is_us_oil = df["symbol"] == "US Oil"
    df["v2_rr"] = np.where(is_us_oil, df["mkt_rr_real"], df["lim_rr_real"])
    df["v2_spread_sl"] = np.where(is_us_oil, df["spread_sl_mkt"], df["spread_sl_lim"])
    df["v2_cap"] = np.where(is_us_oil, 0.05, df["cap_v2"])

    # Baseline v1 (antes de las 6 mejoras): sintéticos con límite (2%), mercados reales con límite/mercado según v1
    df["v1_rr"] = np.where(is_us_oil, df["mkt_rr_real"], df["lim_rr_real"])
    df["v1_spread_sl"] = np.where(is_us_oil, df["spread_sl_mkt"], df["spread_sl_lim"])

    years = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
    rows = []
    for sym, grp_all in df.groupby("symbol"):
        is_syn = bool(grp_all["synthetic"].iloc[0])
        fam = str(grp_all["family"].iloc[0])

        # Métricas V1 (Antes)
        g_v1 = grp_all[grp_all["v1_rr"].notna() & (grp_all["v1_spread_sl"] <= grp_all["cap_v1"])]
        m_v1 = calc_metrics(g_v1["v1_rr"])

        # Métricas V2 (Con las 6 mejoras aplicadas)
        g_v2 = grp_all[grp_all["v2_signal_valid"] & grp_all["v2_rr"].notna() & (grp_all["v2_spread_sl"] <= grp_v2_cap if False else (grp_all["v2_spread_sl"] <= grp_all["v2_cap"]))]
        m_v2 = calc_metrics(g_v2["v2_rr"])

        pos_years_v2 = 0
        valid_years_v2 = 0
        yr_cols = {}
        for y in years:
            gy = g_v2[g_v2["year_bucket"] == y]
            my = calc_metrics(gy["v2_rr"])
            yr_cols[f"n_{y}"] = my["n"]
            yr_cols[f"wr_{y}"] = my["wr"]
            yr_cols[f"r_{y}"] = my["avg_r"]
            if my["n"] >= 5:
                valid_years_v2 += 1
                if my["avg_r"] > 0:
                    pos_years_v2 += 1

        span_years = (grp_all["t"].max() - grp_all["t"].min()).days / 365.25 if len(grp_all) else 0.0
        rows.append(
            dict(
                symbol=sym,
                synthetic=is_syn,
                family=fam,
                span_years=round(span_years, 2),
                v1_n=m_v1["n"],
                v1_wr=m_v1["wr"],
                v1_avg_r=m_v1["avg_r"],
                v1_tot_r=m_v1["tot_r"],
                v1_pf=m_v1["pf"],
                v2_n=m_v2["n"],
                v2_wr=m_v2["wr"],
                v2_avg_r=m_v2["avg_r"],
                v2_tot_r=m_v2["tot_r"],
                v2_pf=m_v2["pf"],
                v2_t_stat=m_v2["t_stat"],
                v2_p_val=m_v2["p_val"],
                v2_max_dd=m_v2["max_dd"],
                v2_valid_years=valid_years_v2,
                v2_pos_years=pos_years_v2,
                delta_wr=(m_v2["wr"] - m_v1["wr"]) if (pd.notna(m_v2["wr"]) and pd.notna(m_v1["wr"])) else np.nan,
                delta_avg_r=(m_v2["avg_r"] - m_v1["avg_r"]) if (pd.notna(m_v2["avg_r"]) and pd.notna(m_v1["avg_r"])) else np.nan,
                delta_tot_r=m_v2["tot_r"] - m_v1["tot_r"],
                wr_gt_47=bool(pd.notna(m_v2["wr"]) and m_v2["wr"] > 47.0 and m_v2["n"] >= 10),
                wr_gt_47_and_pos_r=bool(pd.notna(m_v2["wr"]) and m_v2["wr"] > 47.0 and pd.notna(m_v2["avg_r"]) and m_v2["avg_r"] > 0 and m_v2["n"] >= 10),
                **yr_cols,
            )
        )

    res_df = pd.DataFrame(rows).sort_values(["synthetic", "v2_wr"], ascending=[False, False])
    res_df.to_csv(OUT / "ict_5y_v2_improved_by_symbol.csv", index=False)
    print(f"Guardado ict_5y_v2_improved_by_symbol.csv con {len(res_df)} instrumentos.", flush=True)


if __name__ == "__main__":
    main()
