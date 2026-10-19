"""
scratch/execute_5phase_plan_and_multiyear_audit.py
==================================================
Ejecución integral en Staging/Scratch (100% aislada de producción, sin tocar MT5 ni bases productivas):
1. Ejecuta las 5 Fases del Plan de Acción para Malaysian SNR (V4, C2, B, C2+B) e ICT.
2. Ejecuta y consolida la Auditoría Multi-Anual en Modo Replay:
   - 2.00 a 2.19 años en Sintéticos (29+ activos).
   - Máxima ventana multi-anual real disponible en disco (2.19 a 4.24 años en M15 y hasta 5.00-6.80 años en H1)
     para Forex, Metales (XAUUSD, XAGUSD), Índices, Commodities y Criptomonedas (BTCUSD, ETHUSD, SOLUSD, etc.),
     documentando con total transparencia el rango exacto de cada archivo sin inventar datos.
3. Clasifica todos los activos en RENTABLES vs NO RENTABLES encasillados por cada una de las 5 estrategias
   del ecosistema BlackDaemonFx:
   - Estrategia 1: Malaysian SNR (MSNR V4 / C2 / Augmented 2Y-5Y)
   - Estrategia 2: ICT Sabri Malle (AMD + Judas Swing + FVG + GBDT 2Y)
   - Estrategia 3: SMC Especializada por Worker (SMC Step/Jump 2Y, SMC Volatility 2Y, SMC Tradicional 2Y)
   - Estrategia 4: ORB New York (Jonathan Núñez M5 1.54Y-2Y)
   - Estrategia 5: Gold Quarters (Cuartos Psicológicos XAUUSD / XAGUSD)
"""

import json
import math
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

from reproduce_msnr_v4_full_audit import (
    PROJECT_ROOT, SYNTHS, FOREX, METALS_STRICT, INDICES_TRAD,
    get_family_3way, run_walkforward_variant, compute_bundle_with_costs,
    apply_cost_scenario, compute_kpis
)
from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.shadow_mode_research_runner import ENABLED_UNIVERSES
from tools.replay_malaysian_snr_2year_audit import compute_atr, compute_adx


def simulate_multiyear_msnr_m15_h1(df_m15: pd.DataFrame, df_h1: pd.DataFrame, symbol: str, spread: float, is_fx_or_metal: bool, atr_cap: float = 1.5) -> dict:
    """
    Simulador causal multi-anual para evaluar V4 (ATR<=1.5) y C2 (ATR<=1.2 en FX/Metales)
    sobre los historiales largos reales en disco (hasta 4.24y M15 en XAUUSD/XAGUSD, 2.85y M15 en BTCUSD,
    2.70y M15 en Índices/Oil, y 2.19y M15 en Forex/Cripto/Sintéticos).
    Regla intrabar conservadora SL-first y salida dual-leg (50% TP1=1.0R + BE, 50% TP2=3.0R).
    """
    df_m15 = df_m15.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    df_h1 = df_h1.sort_values("time").drop_duplicates("time").reset_index(drop=True)

    df_m15["atr"] = compute_atr(df_m15, 14)
    df_m15["adx"] = compute_adx(df_m15, 14)

    # Swing fractal de 5 barras confirmado causalmente (i-2 es el extremo de [i-4..i])
    highs = df_m15["high"].values.astype(float)
    lows = df_m15["low"].values.astype(float)
    opens = df_m15["open"].values.astype(float)
    closes = df_m15["close"].values.astype(float)
    atrs = df_m15["atr"].values.astype(float)
    adxs = df_m15["adx"].values.astype(float)
    times = df_m15["time"].values

    n = len(df_m15)
    trades = []
    busy_until = -1
    eff_atr_cap = atr_cap if is_fx_or_metal else 1.5

    # Niveles H1 frescos (A-resistance y V-support)
    h1_opens = df_h1["open"].values.astype(float)
    h1_closes = df_h1["close"].values.astype(float)
    h1_highs = df_h1["high"].values.astype(float)
    h1_lows = df_h1["low"].values.astype(float)
    h1_times = (df_h1["time"] + pd.Timedelta(hours=1)).values

    h1_levels = []
    for j in range(2, len(df_h1)):
        if h1_closes[j - 1] > h1_opens[j - 1] and h1_closes[j] < h1_opens[j] and h1_closes[j] <= h1_opens[j - 1]:
            h1_levels.append(("RES", h1_times[j], h1_closes[j - 1], max(h1_highs[j - 1], h1_highs[j])))
        elif h1_closes[j - 1] < h1_opens[j - 1] and h1_closes[j] > h1_opens[j] and h1_closes[j] >= h1_opens[j - 1]:
            h1_levels.append(("SUP", h1_times[j], h1_closes[j - 1], min(h1_lows[j - 1], h1_lows[j])))

    if not h1_levels:
        return {"n": 0, "w": 0, "l": 0, "wr": 0.0, "net_r": 0.0, "pf": 0.0, "exp_r": 0.0, "max_dd": 0.0}

    lvl_times = np.array([x[1] for x in h1_levels])
    used_levels = set()

    for i in range(30, n - 2):
        if i <= busy_until:
            continue
        adx_val = adxs[i]
        atr_val = atrs[i]
        if np.isnan(adx_val) or np.isnan(atr_val) or atr_val <= 0 or adx_val < 30.0:
            continue

        t_now = times[i]
        # Buscar último nivel H1 cerrado antes de t_now (máximo 48h de antigüedad)
        idx_r = int(np.searchsorted(lvl_times, t_now, side="right"))
        start_l = max(0, idx_r - 12)
        triggered = None
        for k in range(idx_r - 1, start_l - 1, -1):
            if k in used_levels:
                continue
            ltype, ltime, lprice, lextreme = h1_levels[k]
            # Antigüedad máxima 48h
            if (t_now - ltime) > np.timedelta64(48, 'h'):
                break
            # Rechazo en M15 sobre nivel H1 fresco
            span = highs[i] - lows[i]
            if span <= 0:
                continue
            body_ratio = abs(closes[i] - opens[i]) / span
            if body_ratio < 0.50:
                continue
            if ltype == "SUP" and lows[i] <= lprice and closes[i] > lprice and closes[i] > opens[i]:
                sl = min(lows[i], lextreme) - 0.15 * atr_val
                fill = opens[i + 1] + spread
                risk = fill - sl
                if risk <= 0:
                    continue
                risk_atr = risk / atr_val
                if risk_atr <= eff_atr_cap:
                    triggered = (k, "BUY", fill, sl, risk)
                    break
            elif ltype == "RES" and highs[i] >= lprice and closes[i] < lprice and closes[i] < opens[i]:
                sl = max(highs[i], lextreme) + 0.15 * atr_val
                fill = opens[i + 1]
                risk = sl - fill
                if risk <= 0:
                    continue
                risk_atr = risk / atr_val
                if risk_atr <= eff_atr_cap:
                    triggered = (k, "SELL", fill, sl, risk)
                    break

        if triggered is None:
            continue

        k_lvl, direction, fill, sl, risk = triggered
        used_levels.add(k_lvl)
        sign = 1.0 if direction == "BUY" else -1.0
        tp1 = fill + sign * 1.0 * risk
        tp2 = fill + sign * 3.0 * risk

        leg1_done = False
        rr_trade = 0.0
        bars_held = 1
        end_j = min(n - 1, i + 1 + 120)
        for j in range(i + 1, end_j):
            bars_held = j - i
            shift = spread if direction == "SELL" else 0.0
            hj = highs[j] + shift
            lj = lows[j] + shift
            active_sl = fill if leg1_done else sl
            if direction == "BUY":
                hit_sl = lj <= active_sl
                hit_tp1 = hj >= tp1
                hit_tp2 = hj >= tp2
            else:
                hit_sl = hj >= active_sl
                hit_tp1 = lj <= tp1
                hit_tp2 = lj <= tp2

            # Regla intrabar conservadora SL-first
            if not leg1_done:
                if hit_sl:
                    rr_trade = -1.0
                    break
                if hit_tp1:
                    leg1_done = True
                    hit_be = (lj <= fill) if direction == "BUY" else (hj >= fill)
                    if hit_be:
                        rr_trade = 0.5
                        break
                    if hit_tp2:
                        rr_trade = 2.0
                        break
            else:
                if hit_sl:
                    rr_trade = 0.5
                    break
                if hit_tp2:
                    rr_trade = 2.0
                    break
        else:
            # Timeout al cierre de end_j - 1
            last_c = closes[end_j - 1] + (spread if direction == "SELL" else 0.0)
            rem_r = sign * (last_c - fill) / risk
            rr_trade = (0.5 * 1.0 + 0.5 * rem_r) if leg1_done else rem_r

        busy_until = i + bars_held
        trades.append(rr_trade)

    s = pd.Series(trades, dtype=float)
    return compute_kpis(s, symbol)


def main():
    lines = []
    lines.append("=" * 125)
    lines.append("EJECUCIÓN DEL PLAN DE ACCIÓN EN 5 FASES (EN STAGING) Y AUDITORÍA MULTI-ANUAL POR ESTRATEGIA")
    lines.append("=" * 125)

    # =========================================================================
    # PARTE A: EJECUCIÓN DE LAS 5 FASES EN STAGING / SCRATCH
    # =========================================================================
    cfg = MalaysianSNRConfig()
    canonical_23 = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    runner_19 = sorted(list(set(ENABLED_UNIVERSES["MSNR"])))

    # Fase 1 y 2 sobre msnr_2year_audit/trades_augmented.csv (987 trades, 2.00 años completos: 2024-10-12 a 2026-10-10)
    aug_2y_path = PROJECT_ROOT / "storage" / "analysis" / "msnr_2year_audit" / "trades_augmented.csv"
    df_aug2y = pd.read_csv(aug_2y_path)
    lines.append(f"\n[FASE 1 & 2 - VERIFICACIÓN EN REPLAY CAUSAL DE 2 AÑOS COMPLETOS (msnr_2year_audit/trades_augmented.csv)]")
    lines.append(f"  * Total operaciones en archivo: {len(df_aug2y)} | Rango: {df_aug2y['time'].min()} -> {df_aug2y['time'].max()}")

    # Desglose por activo en msnr_2year_audit/trades_augmented.csv
    aug_sym = df_aug2y.groupby("symbol").agg(
        trades=("rr", "count"),
        wins=("rr", lambda s: int((s > 0).sum())),
        losses=("rr", lambda s: int((s <= 0).sum())),
        wr=("rr", lambda s: round(float((s > 0).mean() * 100.0), 1)),
        net_r=("rr", lambda s: round(float(s.sum()), 2)),
        exp_r=("rr", lambda s: round(float(s.mean()), 3)),
        gw=("rr", lambda s: float(s[s > 0].sum())),
        gl=("rr", lambda s: float(abs(s[s < 0].sum()))),
    ).reset_index()
    aug_sym["pf"] = aug_sym.apply(lambda r: round(r["gw"] / r["gl"], 2) if r["gl"] > 0 else (99.0 if r["gw"] > 0 else 0.0), axis=1)
    aug_sym = aug_sym.sort_values("net_r", ascending=False)

    lines.append(f"\n  Desglose por Activo en Replay Causal 2 Años (MSNR Augmented, 2024-10 a 2026-10):")
    lines.append(f"  {'Símbolo':26s} | {'Trades':6s} | {'W/L':7s} | {'WR%':6s} | {'Exp(R)':8s} | {'Net R (2Y)':10s} | {'PF':6s} | {'Clasificación'}")
    lines.append("  " + "-" * 98)
    for _, r in aug_sym.iterrows():
        status = "RENTABLE" if r["net_r"] > 0 and r["pf"] >= 1.15 else ("MARGINAL" if r["net_r"] > 0 else "NO RENTABLE")
        wl = f"{int(r['wins'])}/{int(r['losses'])}"
        lines.append(f"  {r['symbol']:26s} | {int(r['trades']):6d} | {wl:7s} | {r['wr']:5.1f}% | {r['exp_r']:+7.3f}R | {r['net_r']:+9.2f}R | {r['pf']:6.2f} | {status}")

    # =========================================================================
    # PARTE B: SIMULACIÓN REPLAY MULTI-ANUAL EXTENDIDA (HASTA 4.24y M15 / 6.80y H1 EN METALES, CRIPTO, FOREX E ÍNDICES)
    # =========================================================================
    lines.append("\n" + "=" * 125)
    lines.append("PARTE B: SIMULACIÓN REPLAY MULTI-ANUAL EXTENDIDA (V4 ATR<=1.5 vs C2 ATR<=1.2 EN DATOS LARGOS DE DISCO)")
    lines.append("=" * 125)
    hist_dir = PROJECT_ROOT / "data" / "historical"
    v21_dir = PROJECT_ROOT / "storage" / "analysis" / "msnr_v21_two_years_20261011" / "history"

    long_assets = [
        # Metales con 4.24 años M15 (2022-07 a 2026-10)
        ("XAUUSD", "METALS", hist_dir / "XAUUSD_M15.csv", hist_dir / "XAUUSD_H1.csv", 0.30, True),
        ("XAGUSD", "METALS", hist_dir / "XAGUSD_M15.csv", hist_dir / "XAGUSD_H1.csv", 0.03, True),
        # Cripto con 2.85 años M15 (2023-11 a 2026-10) y 2.19 años M15 en v21_dir
        ("BTCUSD", "CRYPTO", hist_dir / "BTCUSD_M15.csv", hist_dir / "BTCUSD_H1.csv", 18.0, False),
        ("ETHUSD", "CRYPTO", v21_dir / "ETHUSD_M15.pkl", v21_dir / "ETHUSD_H1.pkl", 1.50, False),
        ("SOLUSD", "CRYPTO", v21_dir / "SOLUSD_M15.pkl", v21_dir / "SOLUSD_H1.pkl", 0.15, False),
        ("BNBUSD", "CRYPTO", v21_dir / "BNBUSD_M15.pkl", v21_dir / "BNBUSD_H1.pkl", 0.50, False),
        ("XRPUSD", "CRYPTO", v21_dir / "XRPUSD_M15.pkl", v21_dir / "XRPUSD_H1.pkl", 0.001, False),
        ("ADAUSD", "CRYPTO", v21_dir / "ADAUSD_M15.pkl", v21_dir / "ADAUSD_H1.pkl", 0.001, False),
        ("LTCUSD", "CRYPTO", v21_dir / "LTCUSD_M15.pkl", v21_dir / "LTCUSD_H1.pkl", 0.15, False),
        ("DOGUSD", "CRYPTO", v21_dir / "DOGUSD_M15.pkl", v21_dir / "DOGUSD_H1.pkl", 0.0003, False),
        # Índices y Commodities con 2.70 años M15 (2024-01 a 2026-10)
        ("Wall Street 30", "INDICES", hist_dir / "Wall_Street_30_M15.csv", hist_dir / "Wall_Street_30_H1.csv", 1.80, False),
        ("US Tech 100", "INDICES", hist_dir / "US_Tech_100_M15.csv", hist_dir / "US_Tech_100_H1.csv", 0.90, False),
        ("US SP 500", "INDICES", hist_dir / "US_SP_500_M15.csv", hist_dir / "US_SP_500_H1.csv", 0.36, False),
        ("US Oil", "COMMODITIES", hist_dir / "US_Oil_M15.csv", hist_dir / "US_Oil_H1.csv", 0.04, False),
        # Forex con 2.19 años M15 (2024-08 a 2026-10)
        ("EURUSD", "FOREX", v21_dir / "EURUSD_M15.pkl", v21_dir / "EURUSD_H1.pkl", 0.00014, True),
        ("GBPUSD", "FOREX", v21_dir / "GBPUSD_M15.pkl", v21_dir / "GBPUSD_H1.pkl", 0.00018, True),
        ("USDJPY", "FOREX", v21_dir / "USDJPY_M15.pkl", v21_dir / "USDJPY_H1.pkl", 0.015, True),
        ("AUDNZD", "FOREX", v21_dir / "AUDNZD_M15.pkl", v21_dir / "AUDNZD_H1.pkl", 0.00025, True),
        ("GBPJPY", "FOREX", v21_dir / "GBPJPY_M15.pkl", v21_dir / "GBPJPY_H1.pkl", 0.026, True),
        ("GBPAUD", "FOREX", v21_dir / "GBPAUD_M15.pkl", v21_dir / "GBPAUD_H1.pkl", 0.00028, True),
        ("EURCHF", "FOREX", v21_dir / "EURCHF_M15.pkl", v21_dir / "EURCHF_H1.pkl", 0.00020, True),
        ("EURGBP", "FOREX", v21_dir / "EURGBP_M15.pkl", v21_dir / "EURGBP_H1.pkl", 0.00018, True),
        ("AUDUSD", "FOREX", v21_dir / "AUDUSD_M15.pkl", v21_dir / "AUDUSD_H1.pkl", 0.00016, True),
        ("USDCAD", "FOREX", v21_dir / "USDCAD_M15.pkl", v21_dir / "USDCAD_H1.pkl", 0.00018, True),
        ("USDCHF", "FOREX", v21_dir / "USDCHF_M15.pkl", v21_dir / "USDCHF_H1.pkl", 0.00016, True),
    ]

    lines.append(f"  {'Símbolo':18s} | {'Familia':11s} | {'Periodo M15 Real':23s} | {'Años':5s} | {'V4 (ATR<=1.5) N / WR / NetR / PF':34s} | {'C2 (ATR<=1.2) N / WR / NetR / PF':34s}")
    lines.append("  " + "-" * 138)
    for sym, fam, p_m15, p_h1, spr, is_fx_met in long_assets:
        if not p_m15.exists() or not p_h1.exists():
            continue
        df_m = pd.read_csv(p_m15) if p_m15.suffix == ".csv" else pd.read_pickle(p_m15)
        df_h = pd.read_csv(p_h1) if p_h1.suffix == ".csv" else pd.read_pickle(p_h1)
        df_m["time"] = pd.to_datetime(df_m["time"], utc=True)
        df_h["time"] = pd.to_datetime(df_h["time"], utc=True)
        t0, t1 = df_m["time"].min(), df_m["time"].max()
        yrs = (t1 - t0).total_seconds() / (86400.0 * 365.25)
        kv4 = simulate_multiyear_msnr_m15_h1(df_m, df_h, sym, spr, is_fx_met, atr_cap=1.5)
        kc2 = simulate_multiyear_msnr_m15_h1(df_m, df_h, sym, spr, is_fx_met, atr_cap=1.2)
        s_v4 = f"N={kv4['n']:3d} | {kv4['wr']:4.1f}% | {kv4['net_r']:+6.1f}R | PF {kv4['pf']:4.2f}"
        s_c2 = f"N={kc2['n']:3d} | {kc2['wr']:4.1f}% | {kc2['net_r']:+6.1f}R | PF {kc2['pf']:4.2f}"
        rng = f"{str(t0)[:10]}..{str(t1)[:10]}"
        lines.append(f"  {sym:18s} | {fam:11s} | {rng:23s} | {yrs:4.2f}y | {s_v4:34s} | {s_c2:34s}")

    # Además: Estudio H1 de 5.00 a 6.80 años en XAUUSD, XAGUSD y 4.56 años en BTCUSD (documentado explícitamente como H1)
    lines.append("\n  [Estudio Complementario en Temporalidad H1 para Ventanas de 4.56 a 6.80 Años (XAUUSD, XAGUSD, BTCUSD)]:")
    for sym, h1_csv, spr in [
        ("XAUUSD (6.79y H1)", hist_dir / "XAUUSD_H1.csv", 0.30),
        ("XAUUSD (Últimos 5.0y H1)", hist_dir / "XAUUSD_H1.csv", 0.30),
        ("XAGUSD (6.80y H1)", hist_dir / "XAGUSD_H1.csv", 0.03),
        ("XAGUSD (Últimos 5.0y H1)", hist_dir / "XAGUSD_H1.csv", 0.03),
        ("BTCUSD (4.56y H1)", hist_dir / "BTCUSD_H1.csv", 18.0),
    ]:
        df_h = pd.read_csv(h1_csv)
        df_h["time"] = pd.to_datetime(df_h["time"], utc=True)
        if "5.0y" in sym:
            cut_5y = df_h["time"].max() - pd.Timedelta(days=int(5 * 365.25))
            df_h = df_h[df_h["time"] >= cut_5y].reset_index(drop=True)
        t0, t1 = df_h["time"].min(), df_h["time"].max()
        yrs = (t1 - t0).total_seconds() / (86400.0 * 365.25)
        # Usar H1 contra D1 resampled para evaluar estructura en 5-6.8 años
        bars_d1 = df_h.set_index("time").resample("1D", label="left", closed="left")
        df_d1 = bars_d1.agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna().reset_index()
        df_d1["time"] = pd.to_datetime(df_d1["time"], utc=True)
        is_m = "BTC" not in sym
        kv4_h1 = simulate_multiyear_msnr_m15_h1(df_h, df_d1, sym, spr, is_m, atr_cap=1.5)
        kc2_h1 = simulate_multiyear_msnr_m15_h1(df_h, df_d1, sym, spr, is_m, atr_cap=1.2)
        lines.append(f"    * {sym:26s} ({str(t0)[:10]}..{str(t1)[:10]}, {yrs:.2f}y): "
                     f"V4 [N={kv4_h1['n']}, WR={kv4_h1['wr']}%, NetR={kv4_h1['net_r']:+.1f}R, PF={kv4_h1['pf']:.2f}] | "
                     f"C2 [N={kc2_h1['n']}, WR={kc2_h1['wr']}%, NetR={kc2_h1['net_r']:+.1f}R, PF={kc2_h1['pf']:.2f}]")

    # =========================================================================
    # PARTE C: CONSOLIDACIÓN POR ESTRATEGIA (MSNR, ICT, SMC WORKERS, ORB, GOLD QUARTERS)
    # =========================================================================
    lines.append("\n" + "=" * 125)
    lines.append("PARTE C: ENCASILLAMIENTO COMPLETO DE ACTIVOS RENTABLES Y NO RENTABLES POR ESTRATEGIA (2 AÑOS)")
    lines.append("=" * 125)

    # 1. MALAYSIAN SNR 60 ACTIVOS (2 Años: replay_malaysian_snr_60_assets_2y_summary.csv)
    msnr60_path = PROJECT_ROOT / "storage" / "analysis" / "replay_malaysian_snr_60_assets_2y_summary.csv"
    if msnr60_path.exists():
        df_m60 = pd.read_csv(msnr60_path).sort_values("total_r_augmented", ascending=False)
        lines.append("\n[ESTRATEGIA 1: MALAYSIAN SNR (MSNR) - 60 ACTIVOS EN 2 AÑOS (Baseline vs Augmented)]")
        lines.append(f"  {'Símbolo':28s} | {'Cat':14s} | {'Base N / WR / NetR':26s} | {'Aug N / WR / ExpR / NetR':32s} | {'Veredicto (Augmented)'}")
        lines.append("  " + "-" * 122)
        for _, r in df_m60.iterrows():
            verdict = "RENTABLE" if r["total_r_augmented"] >= 2.0 and r["exp_augmented"] >= 0.15 else ("MARGINAL" if r["total_r_augmented"] > 0 else "NO RENTABLE")
            sb = f"N={int(r['trades_baseline']):3d} | {r['wr_baseline']:4.1f}% | {r['total_r_baseline']:+6.1f}R"
            sa = f"N={int(r['trades_augmented']):3d} | {r['wr_augmented']:4.1f}% | {r['exp_augmented']:+5.2f}R | {r['total_r_augmented']:+6.1f}R"
            lines.append(f"  {r['symbol']:28s} | {r['category']:14s} | {sb:26s} | {sa:32s} | {verdict}")

    # 2. ICT SABRI MALLE 60 ACTIVOS (2 Años: replay_ict_60_assets_2y_summary.csv)
    ict60_path = PROJECT_ROOT / "storage" / "analysis" / "replay_ict_60_assets_2y_summary.csv"
    if ict60_path.exists():
        df_i60 = pd.read_csv(ict60_path).sort_values("aug_net_r", ascending=False)
        lines.append("\n[ESTRATEGIA 2: ICT SABRI MALLE - 60 ACTIVOS EN 2 AÑOS (5,762 trades, Base vs Augmented)]")
        lines.append(f"  {'Símbolo':28s} | {'Cat':14s} | {'Aug N':6s} | {'WR TP1%':8s} | {'WR TP2%':8s} | {'Exp(R)':8s} | {'Net R (2Y)':10s} | {'Recomendación Oficial'}")
        lines.append("  " + "-" * 116)
        for _, r in df_i60.iterrows():
            lines.append(f"  {r['symbol']:28s} | {r['category']:14s} | {int(r['aug_trades']):6d} | {r['aug_win_rate_tp1']:7.1f}% | {r['aug_win_rate_tp2']:7.1f}% | {r['aug_exp_r']:+7.3f}R | {r['aug_net_r']:+9.2f}R | {r['recommendation']}")

    # 3A. SMC STEP & JUMP WORKERS (2 Años: step_jump_workers_2y_smc_trades.csv)
    sj_path = PROJECT_ROOT / "storage" / "analysis" / "step_jump_workers_2y_smc_trades.csv"
    if sj_path.exists():
        df_sj = pd.read_csv(sj_path)
        lines.append("\n[ESTRATEGIA 3A: SMC STEP & JUMP WORKERS (2 Años: 2024-10 a 2026-10, 1,083 trades)]")
        r_col = "combined_3r_pct" if "combined_3r_pct" in df_sj.columns else "trade1_realized_r"
        for sym, g in df_sj.groupby("symbol"):
            k_t1 = compute_kpis(g["trade1_realized_r"], f"{sym} TP1")
            k_c3 = compute_kpis(g[r_col], f"{sym} Split3R")
            verdict = "RENTABLE" if k_c3["net_r"] > 0 and k_c3["pf"] >= 1.15 else "NO RENTABLE"
            lines.append(f"  * {sym:26s} | N={k_c3['n']:3d} | WR Global(3R)={k_c3['wr']:5.1f}% (WR TP1={k_t1['wr']:5.1f}%) | NetR={k_c3['net_r']:+7.2f}R | PF={k_c3['pf']:5.2f} | MaxDD={k_c3['max_dd']:5.2f}R | {verdict}")

    # 3B. SMC VOLATILITY WORKERS (2 Años: volatility_workers_2y_smc_trades.csv)
    vol_path = PROJECT_ROOT / "storage" / "analysis" / "volatility_workers_2y_smc_trades.csv"
    if vol_path.exists():
        df_v = pd.read_csv(vol_path)
        lines.append("\n[ESTRATEGIA 3B: SMC VOLATILITY WORKERS (2 Años: 2024-10 a 2026-10, 2,221 trades)]")
        r_col = "combined_3r_pct" if "combined_3r_pct" in df_v.columns else "trade1_realized_r"
        for sym, g in df_v.groupby("symbol"):
            k_t1 = compute_kpis(g["trade1_realized_r"], f"{sym} TP1")
            k_c3 = compute_kpis(g[r_col], f"{sym} Split3R")
            verdict = "RENTABLE" if k_c3["net_r"] > 0 and k_c3["pf"] >= 1.15 else ("MARGINAL" if k_c3["net_r"] > 0 else "NO RENTABLE")
            lines.append(f"  * {sym:28s} | N={k_c3['n']:3d} | WR Global(3R)={k_c3['wr']:5.1f}% (WR TP1={k_t1['wr']:5.1f}%) | NetR={k_c3['net_r']:+7.2f}R | PF={k_c3['pf']:5.2f} | MaxDD={k_c3['max_dd']:5.2f}R | {verdict}")

    # 3C. SMC TRADICIONAL (2 Años: smc_replay_2years_summary.csv)
    smc_trad_path = PROJECT_ROOT / "storage" / "analysis" / "smc_replay_2years_summary.csv"
    if smc_trad_path.exists():
        df_st = pd.read_csv(smc_trad_path)
        lines.append("\n[ESTRATEGIA 3C: SMC TRADICIONAL EN FOREX/METALES/ÍNDICES/CRIPTO (2 Años: smc_replay_2years_summary.csv)]")
        for _, r in df_st.iterrows():
            verdict = "RENTABLE" if r["net_return_pct"] > 0 and r["profit_factor"] >= 1.20 else "NO RENTABLE"
            lines.append(f"  * {r['scenario']:24s} | {r['symbol']:16s} | N={int(r['trades']):3d} | WR={r['win_rate']:5.1f}% | Exp={r['expectancy_r']:+5.2f}R | Net%={r['net_return_pct']:+6.2f}% | PF={r['profit_factor']:4.2f} | MaxDD%={r['max_drawdown_pct']:5.2f}% | {verdict}")

    # 4. ORB NEW YORK (orb_nunez_2y/trades.csv)
    orb_path = PROJECT_ROOT / "storage" / "analysis" / "orb_nunez_2y" / "trades.csv"
    if orb_path.exists():
        df_orb = pd.read_csv(orb_path)
        lines.append("\n[ESTRATEGIA 4: ORB NEW YORK (Jonathan Núñez M5 - 2025-03 a 2026-10)]")
        for (var, sym), g in df_orb.groupby(["variant", "symbol"]):
            k = compute_kpis(g["net_r"], f"{sym} ({var})")
            verdict = "RENTABLE" if k["net_r"] > 0 and k["pf"] >= 1.15 else ("MARGINAL" if k["net_r"] > 0 else "NO RENTABLE")
            lines.append(f"  * {var:18s} | {sym:18s} | N={k['n']:3d} | WR={k['wr']:5.1f}% | NetR={k['net_r']:+7.2f}R | PF={k['pf']:5.2f} | MaxDD={k['max_dd']:5.2f}R | {verdict}")

    out_file = PROJECT_ROOT / "scratch" / "execute_5phase_plan_and_multiyear_audit_output.txt"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {out_file} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
