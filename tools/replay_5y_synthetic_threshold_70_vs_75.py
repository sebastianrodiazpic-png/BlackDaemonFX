"""
tools/replay_5y_synthetic_threshold_70_vs_75.py
================================================
Replay cuantitativo y comparativa de 5 AÑOS (2021-2026) en ACTIVOS SINTÉTICOS:
Evaluación del impacto de reducir el umbral de Criterio Humano de 75.0 a 70.0 puntos.

Calcula:
1. Métricas Globales en Sintéticos: Umbral 75.0 vs Umbral 70.0 vs Grupo Delta (70-74.9 pts).
2. Desglose detallado por familia (Step, Jump, Boom, Crash, Volatility).
3. Detalle específico para Step Index 400.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if sys.path and ("tools" in sys.path[0] or sys.path[0].endswith("tools")):
    sys.path.pop(0)

import json
import numpy as np
import pandas as pd

ANALYSIS_DIR = PROJECT_ROOT / "storage" / "analysis"

from tools.analyze_ict_5y_audit import load_real_tick_spreads

def calc_metrics(r_series: pd.Series) -> dict:
    n = len(r_series)
    if n == 0:
        return {
            "trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
            "net_r": 0.0, "profit_factor": 0.0, "exp_r": 0.0
        }
    wins = int((r_series > 0.001).sum())
    losses = int((r_series < -0.001).sum())
    wr = (wins / n) * 100.0
    net_r = float(r_series.sum())
    gw = float(r_series[r_series > 0.0].sum()) if wins > 0 else 0.0
    gl = float(np.abs(r_series[r_series < 0.0].sum())) if losses > 0 else 0.0
    pf = (gw / gl) if gl > 0 else (99.0 if gw > 0 else 0.0)
    exp_r = net_r / n
    return {
        "trades": n, "wins": wins, "losses": losses,
        "win_rate": round(wr, 2), "net_r": round(net_r, 2),
        "profit_factor": round(pf, 2), "exp_r": round(exp_r, 4)
    }

def run_replay():
    cache_path = ANALYSIS_DIR / "ict_5y_signals_h1_enriched.csv"
    if not cache_path.exists():
        print(f"Error: {cache_path} no encontrado.")
        return

    df = pd.read_csv(cache_path, low_memory=False)
    df = df[df["synthetic"] == True].copy()
    df = df[~df["symbol"].str.lower().str.contains("micro")].copy()
    df = df[df["lim_fill"].isin(["LIMITE", "INMEDIATO"])].copy()

    synth_factors, _ = load_real_tick_spreads()
    real_sp_list = [float(sp) * synth_factors.get(str(s), 1.0) for s, sp in zip(df["symbol"], df["spread"])]
    df["real_spread"] = real_sp_list
    df["extra_spread"] = np.maximum(0.0, df["real_spread"] - df["spread"])
    df["lim_risk_price"] = (df["limit"] - df["stop_loss"]).abs()
    df["lim_rr_real"] = df["lim_rr"] - (df["extra_spread"] / df["lim_risk_price"].replace(0, np.nan))
    df["spread_sl_lim"] = df["real_spread"] / df["lim_risk_price"].replace(0, np.nan)
    df = df[df["lim_rr_real"].notna()].copy()

    syms = df["symbol"].astype(str)
    dirs = df["direction"].astype(str).str.upper()

    # 1. Asimetría Spike (Boom & Crash)
    is_crash_buy = syms.str.upper().str.contains("CRASH") & (dirs == "BUY")
    is_boom_sell = syms.str.upper().str.contains("BOOM") & (dirs == "SELL")
    spike_penalty = np.where(is_crash_buy | is_boom_sell, 20.0, 0.0)

    # 2. HTF Trend
    sl_atr = df["sl_atr_h1"].astype(float).fillna(1.0)
    score_htf = np.where(sl_atr >= 1.2, 30.0, np.where(sl_atr >= 1.0, 26.0, np.where(sl_atr >= 0.8, 20.0, 14.0)))

    # 3. Regime / ADX
    adx = df["adx_h1"].astype(float).fillna(22.0)
    is_step_jump = syms.str.lower().str.contains("step|jump")
    score_regime = np.where(
        adx >= 25.0, 25.0,
        np.where(adx >= 18.0, 18.0,
            np.where(is_step_jump, 12.5, 5.0)
        )
    )

    # 4. Candle Quality
    br = df["body_ratio"].astype(float)
    score_candle = np.where(
        br.isna(), 20.0,
        np.where((br >= 0.50) & (br <= 0.80), 25.0,
            np.where(br <= 0.85, 16.0, 8.0)
        )
    )

    # 5. Spread Friction
    sp_sl = df["spread_sl_lim"].fillna(0.02)
    score_spread = np.where(
        sp_sl <= 0.03, 10.0,
        np.where(sp_sl <= 0.08, 7.5,
            np.where(sp_sl <= 0.12, 5.0, 0.0)
        )
    )

    score_streak = 8.0

    total_score = np.round(score_htf + score_regime + score_candle + score_streak + score_spread - spike_penalty, 1)
    df["score"] = total_score
    df["r"] = df["lim_rr_real"]

    # Grupos
    mask_75 = df["score"] >= 75.0
    mask_70 = df["score"] >= 70.0
    mask_delta = (df["score"] >= 70.0) & (df["score"] < 75.0)

    m_base = calc_metrics(df["r"])
    m_75 = calc_metrics(df.loc[mask_75, "r"])
    m_70 = calc_metrics(df.loc[mask_70, "r"])
    m_delta = calc_metrics(df.loc[mask_delta, "r"])

    print("=" * 85)
    print("REPLAY AUDITADO DE 5 AÑOS (2021-2026): ÍNDICES SINTÉTICOS")
    print("Comparativa de Umbral de Criterio Humano: 75.0 pts vs 70.0 pts")
    print("=" * 85)

    print(f"\n1. Universo Sintético Base (Sin Filtro de Corte):")
    print(f"   Trades: {m_base['trades']:,} | WinRate: {m_base['win_rate']:.2f}% | PnL: {m_base['net_r']:+.2f} R | ProfitFactor: {m_base['profit_factor']:.2f} | Exp: {m_base['exp_r']:+.4f} R")

    print(f"\n2. Umbral Estricto Actual (Score >= 75.0 pts):")
    print(f"   Trades: {m_75['trades']:,} | WinRate: {m_75['win_rate']:.2f}% | PnL: {m_75['net_r']:+.2f} R | ProfitFactor: {m_75['profit_factor']:.2f} | Exp: {m_75['exp_r']:+.4f} R")

    print(f"\n3. Umbral Reducido Propuesto (Score >= 70.0 pts):")
    print(f"   Trades: {m_70['trades']:,} | WinRate: {m_70['win_rate']:.2f}% | PnL: {m_70['net_r']:+.2f} R | ProfitFactor: {m_70['profit_factor']:.2f} | Exp: {m_70['exp_r']:+.4f} R")

    print(f"\n4. IMPACTO DEL GRUPO DELTA (Señales que entran solo con 70.0 a 74.9 pts):")
    print(f"   Trades Adicionales: {m_delta['trades']:,}")
    print(f"   WinRate del Grupo Delta: {m_delta['win_rate']:.2f}%")
    print(f"   PnL Neto del Grupo Delta: {m_delta['net_r']:+.2f} R")
    print(f"   Profit Factor del Grupo Delta: {m_delta['profit_factor']:.2f}")
    print(f"   Expectativa Matemática: {m_delta['exp_r']:+.4f} R / trade")

    # Por familia
    print("\n" + "=" * 85)
    print("DESGLOSE POR FAMILIA DE SINTÉTICOS (DELTA 70.0 A 74.9 PTS)")
    print("=" * 85)

    def classify_family(sym: str) -> str:
        s = sym.lower()
        if "step" in s:
            return "STEP"
        if "jump" in s:
            return "JUMP"
        if "boom" in s:
            return "BOOM"
        if "crash" in s:
            return "CRASH"
        return "VOLATILITY"

    df["family"] = df["symbol"].apply(classify_family)

    records_fam = []
    for fam, grp in df.groupby("family"):
        grp_75 = grp[grp["score"] >= 75.0]
        grp_70 = grp[grp["score"] >= 70.0]
        grp_d = grp[(grp["score"] >= 70.0) & (grp["score"] < 75.0)]

        m75 = calc_metrics(grp_75["r"])
        m70 = calc_metrics(grp_70["r"])
        md = calc_metrics(grp_d["r"])

        print(f"\n>>> Familia {fam}:")
        print(f"    Umbral 75.0: Trades={m75['trades']:5d} | WR={m75['win_rate']:5.2f}% | PnL={m75['net_r']:+8.2f} R | PF={m75['profit_factor']:.2f}")
        print(f"    Umbral 70.0: Trades={m70['trades']:5d} | WR={m70['win_rate']:5.2f}% | PnL={m70['net_r']:+8.2f} R | PF={m70['profit_factor']:.2f}")
        print(f"    Delta [70-74.9]: Trades={md['trades']:4d} | WR={md['win_rate']:5.2f}% | PnL={md['net_r']:+8.2f} R | PF={md['profit_factor']:.2f} | Exp={md['exp_r']:+.4f} R")

        records_fam.append({
            "family": fam,
            "trades_75": m75["trades"], "wr_75": m75["win_rate"], "pnl_75": m75["net_r"],
            "trades_70": m70["trades"], "wr_70": m70["win_rate"], "pnl_70": m70["net_r"],
            "trades_delta": md["trades"], "wr_delta": md["win_rate"], "pnl_delta": md["net_r"],
            "pf_delta": md["profit_factor"], "exp_delta": md["exp_r"]
        })

    # Step Index 400 específicamente
    print("\n" + "=" * 85)
    print("DETALLE ESPECÍFICO: STEP INDEX 400 (5 AÑOS)")
    print("=" * 85)
    df_s400 = df[df["symbol"] == "Step Index 400"]
    s400_75 = calc_metrics(df_s400[df_s400["score"] >= 75.0]["r"])
    s400_70 = calc_metrics(df_s400[df_s400["score"] >= 70.0]["r"])
    s400_d = calc_metrics(df_s400[(df_s400["score"] >= 70.0) & (df_s400["score"] < 75.0)]["r"])

    print(f"Umbral 75.0 pts (Actual): Trades={s400_75['trades']} | WR={s400_75['win_rate']:.2f}% | PnL={s400_75['net_r']:+.2f} R | PF={s400_75['profit_factor']:.2f}")
    print(f"Umbral 70.0 pts (Prop.):  Trades={s400_70['trades']} | WR={s400_70['win_rate']:.2f}% | PnL={s400_70['net_r']:+.2f} R | PF={s400_70['profit_factor']:.2f}")
    print(f"Delta [70.0 a 74.9 pts]:  Trades={s400_d['trades']} | WR={s400_d['win_rate']:.2f}% | PnL={s400_d['net_r']:+.2f} R | PF={s400_d['profit_factor']:.2f} | Exp={s400_d['exp_r']:+.4f} R")

    # Guardar resultados para trazabilidad
    df_fam_res = pd.DataFrame(records_fam)
    df_fam_res.to_csv(ANALYSIS_DIR / "replay_5y_synthetic_threshold_70_vs_75_comparison.csv", index=False)
    print(f"\nReporte guardado en storage/analysis/replay_5y_synthetic_threshold_70_vs_75_comparison.csv")

if __name__ == "__main__":
    run_replay()
