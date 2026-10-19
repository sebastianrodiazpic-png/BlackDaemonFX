import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig
from scratch.reproduce_msnr_v4_full_audit import (
    FOREX,
    METALS_STRICT,
    get_family_3way,
    run_walkforward_variant,
)


def main():
    out = []
    out.append("=" * 125)
    out.append("FRONTERA DE CANTIDAD DE TRADES (N) vs RENTABILIDAD NETA: MSNR + ICT + ORB")
    out.append("=" * 125)

    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace("micro", "") for s in cfg.allowed_symbols)))

    csv_clean = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df_clean = pd.read_csv(csv_clean)
    df_clean["time"] = pd.to_datetime(df_clean["time"], utc=True)
    df_clean["exit_time"] = pd.to_datetime(df_clean["exit_time"], utc=True)
    df_clean["subfamily"] = df_clean["symbol"].apply(get_family_3way)
    df_clean = df_clean[df_clean["symbol"].isin(canonical_symbols)].sort_values("time").reset_index(drop=True)

    out.append("\n[1. MALAYSIAN SNR (MSNR): PALANCAS PARA AUMENTAR CANTIDAD DE TRADES Y RENTABILIDAD (180d WF, 957 señales base)]")
    out.append(f"  {'Configuración MSNR Evaluada en Walk-Forward (4 Folds)':66s} | {'N':4s} | {'W/L':7s} | {'WR%':6s} | {'Payoff':6s} | {'Exp(R)':8s} | {'Net R':8s} | {'PF Base/Sev':13s} | {'MaxDD'}")
    out.append("  " + "-" * 138)

    is_fx_or_metal = lambda d: d["symbol"].isin(FOREX | METALS_STRICT)

    variants = [
        (
            "Benchmark V4 (ADX>=30, ATR<=1.5, 23 act, Cap=1)",
            lambda d: d[(d["adx"] >= 30.0) & (d["risk_atr"] <= 1.5)],
            1,
        ),
        (
            "Fase 1: C2 (ADX>=30, ATR<=1.2 FX/Met, 23 act, Cap=1)",
            lambda d: d[
                (is_fx_or_metal(d) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.2))
                | ((~is_fx_or_metal(d)) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.5))
            ],
            1,
        ),
        (
            "Fase 2: C2+B (ADX>=30, ATR<=1.2 FX/Met, Sin Crash1000, Cap=1)",
            lambda d: d[
                (d["symbol"] != "Crash 1000 Index")
                & (
                    (is_fx_or_metal(d) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.2))
                    | ((~is_fx_or_metal(d)) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.5))
                )
            ],
            1,
        ),
        (
            "Palanca MSNR-1: C2+B con Cap=2 (hasta 2 trades/activo)",
            lambda d: d[
                (d["symbol"] != "Crash 1000 Index")
                & (
                    (is_fx_or_metal(d) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.2))
                    | ((~is_fx_or_metal(d)) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.5))
                )
            ],
            2,
        ),
        (
            "Palanca MSNR-2: C2+B con ADX>=25 en Sint/WS30 y ADX>=30 FX/Met",
            lambda d: d[
                (d["symbol"] != "Crash 1000 Index")
                & (
                    (is_fx_or_metal(d) & (d["adx"] >= 30.0) & (d["risk_atr"] <= 1.2))
                    | ((~is_fx_or_metal(d)) & (d["adx"] >= 25.0) & (d["risk_atr"] <= 1.5))
                )
            ],
            1,
        ),
        (
            "Palanca MSNR-3: C2+B con ADX>=25 Global (ATR<=1.2 FX/Met)",
            lambda d: d[
                (d["symbol"] != "Crash 1000 Index")
                & (
                    (is_fx_or_metal(d) & (d["adx"] >= 25.0) & (d["risk_atr"] <= 1.2))
                    | ((~is_fx_or_metal(d)) & (d["adx"] >= 25.0) & (d["risk_atr"] <= 1.5))
                )
            ],
            1,
        ),
        (
            "Palanca MSNR-4: C2+B con ADX>=22 en Sint/WS30 y ADX>=25 FX/Met",
            lambda d: d[
                (d["symbol"] != "Crash 1000 Index")
                & (
                    (is_fx_or_metal(d) & (d["adx"] >= 25.0) & (d["risk_atr"] <= 1.2))
                    | ((~is_fx_or_metal(d)) & (d["adx"] >= 22.0) & (d["risk_atr"] <= 1.5))
                )
            ],
            1,
        ),
        (
            "Palanca MSNR-5: C2+B con ADX>=20 Global + ATR<=1.2 FX/Met + Cap=2",
            lambda d: d[
                (d["symbol"] != "Crash 1000 Index")
                & (
                    (is_fx_or_metal(d) & (d["adx"] >= 20.0) & (d["risk_atr"] <= 1.2))
                    | ((~is_fx_or_metal(d)) & (d["adx"] >= 20.0) & (d["risk_atr"] <= 1.5))
                )
            ],
            2,
        ),
    ]

    for label, fn, cap_val in variants:
        res = run_walkforward_variant(df_clean, fn, n_folds=4, cap=cap_val)
        kb = res["total"]["base"]
        ks = res["total"]["sev25"]
        wl = f"{kb['w']}/{kb['l']}"
        pfs = f"{kb['pf']:4.2f} / {ks['pf']:4.2f}"
        out.append(f"  {label:66s} | {kb['n']:4d} | {wl:7s} | {kb['wr']:5.1f}% | {kb['payoff']:6.2f} | {kb['exp_r']:+7.3f}R | {kb['net_r']:+7.2f}R | {pfs:13s} | {kb['max_dd']:4.1f}R")

    # 2. ICT SABRI MALLE: Análisis de Volumen vs Rentabilidad en 2 Años y en Staging
    out.append("\n[2. ICT SABRI MALLE: ESCALADO DE CANTIDAD DE TRADES Y RENTABILIDAD (2 AÑOS: replay_ict_60_assets_2y_summary.csv)]")
    ict_df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "replay_ict_60_assets_2y_summary.csv")
    ict_active = ict_df[ict_df["recommendation"] == "ACTIVE"].copy()
    ict_top19 = ict_df[ict_df["aug_net_r"] >= 10.0].copy()
    ict_top10 = ict_df.sort_values("aug_net_r", ascending=False).head(10).copy()
    ict_pos = ict_df[ict_df["aug_net_r"] > 0].copy()

    for name, sub in [
        ("ICT Universo Completo Sin Poda (60 activos, 2Y)", ict_df),
        ("ICT Todos los Activos Positivos (35 activos, 2Y)", ict_pos),
        ("ICT Selección Oficial ACTIVE (22 activos, 2Y)", ict_active),
        ("ICT Élite Alta Expectativa (NetR >= +10R: 20 activos, 2Y)", ict_top19),
        ("ICT Top 10 Activos Líderes (10 activos, 2Y)", ict_top10),
    ]:
        tot_t = int(sub["aug_trades"].sum())
        tot_r = float(sub["aug_net_r"].sum())
        tp1_h = int(sub["aug_tp1_hits"].sum())
        wr_tp1 = (tp1_h / tot_t * 100.0) if tot_t > 0 else 0.0
        exp_r = tot_r / tot_t if tot_t > 0 else 0.0
        trades_per_month = tot_t / 24.0
        out.append(f"  * {name:56s} | N(2Y)={tot_t:4d} ({trades_per_month:5.1f}/mes) | WR_TP1={wr_tp1:5.1f}% | Exp={exp_r:+6.3f}R | NetR(2Y)={tot_r:+7.2f}R")

    # 3. ORB NEW YORK: Optimización de Volumen y Rentabilidad en orb_nunez_2y/trades.csv
    out.append("\n[3. ORB NEW YORK (Jonathan Núñez M5): FILTRADO INTELIGENTE PARA MULTIPLICAR RENTABILIDAD Y TRADES]")
    orb_df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "orb_nunez_2y" / "trades.csv")
    orb_sweep_gold_btc = orb_df[(orb_df["variant"] == "SWEEP") & (orb_df["symbol"].isin(["XAUUSD", "BTCUSD"]))]
    orb_htf_sweep_xag_oil = orb_df[(orb_df["variant"] == "HTF_SWEEP") & (orb_df["symbol"].isin(["XAGUSD", "US Oil"]))]
    orb_combined_elite = pd.concat([orb_sweep_gold_btc, orb_htf_sweep_xag_oil], ignore_index=True)

    for name, sub in [
        ("ORB CURRENT (Sin filtro Sweep - 6 activos)", orb_df[orb_df["variant"] == "CURRENT"]),
        ("ORB SWEEP (Todos los 9 activos sin seleccionar)", orb_df[orb_df["variant"] == "SWEEP"]),
        ("ORB SWEEP Élite (XAUUSD + BTCUSD)", orb_sweep_gold_btc),
        ("ORB HTF_SWEEP Élite (XAGUSD + US Oil)", orb_htf_sweep_xag_oil),
        ("ORB Portafolio Combinado Élite (XAU + BTC [SWEEP] + XAG + Oil [HTF_SWEEP])", orb_combined_elite),
    ]:
        n = len(sub)
        wins = int((sub["net_r"] > 0).sum())
        wr = (wins / n * 100.0) if n > 0 else 0.0
        net_r = float(sub["net_r"].sum())
        exp_r = net_r / n if n > 0 else 0.0
        gw = float(sub.loc[sub["net_r"] > 0, "net_r"].sum())
        gl = float(abs(sub.loc[sub["net_r"] < 0, "net_r"].sum()))
        pf = gw / gl if gl > 0 else 0.0
        t_col = "entry_time" if "entry_time" in sub.columns else sub.columns[0]
        eq = sub.sort_values(t_col)["net_r"].cumsum()
        dd = float((eq.cummax() - eq).max()) if n > 0 else 0.0
        out.append(f"  * {name:73s} | N={n:4d} | WR={wr:5.1f}% | Exp={exp_r:+6.3f}R | NetR={net_r:+7.2f}R | PF={pf:4.2f} | MaxDD={dd:5.2f}R")

    out_path = PROJECT_ROOT / "scratch" / "optimize_trade_frequency_and_profitability_output.txt"
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
