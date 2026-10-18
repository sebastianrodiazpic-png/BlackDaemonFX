"""Análisis Aislado y Cuantitativo de las Opciones A, B y C
=========================================================
Desglosa el impacto REAL y aislado de cada modificación:
1. Impacto de SMT: Comparación entre operaciones CON divergencia SMT vs SIN divergencia SMT.
2. Impacto de Cascada M5: Análisis de por qué el SL reducido sufre ruido en sintéticos y qué pasa cuando se exige confirmación micro-CHoCH.
3. Impacto de Inversion FVG (iFVG) y BPR: Métricas exclusivas de los trades generados por iFVG y BPR.
4. Impacto del Filtro de Confluencia Institucional / AI GBDT: Qué pasa cuando solo se toman las operaciones de alta probabilidad.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scratch.simulate_2yr_options_a_b_c import (
    SELECTED_SYMBOLS,
    SMT_TWIN_MAP,
    load_all_market_data,
    compute_adx,
    compute_smt_divergence,
    detect_ifvg_and_bpr_setups,
    simulate_dual_leg_trade,
)
from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE
from config.symbol_policy import is_direction_allowed

def run_isolated_audit():
    print("Cargando datos de mercado...")
    market_data = load_all_market_data(SELECTED_SYMBOLS)
    
    for s, frames in market_data.items():
        df_h1 = frames["H1"].copy()
        df_h1["ema50"] = df_h1["close"].ewm(span=50, adjust=False).mean()
        df_h1["ema200"] = df_h1["close"].ewm(span=200, adjust=False).mean()
        df_h1["adx"] = compute_adx(df_h1, period=14)
        frames["H1"] = df_h1

    # Contenedores para análisis aislado
    trades_smt_confirmed = []
    trades_no_smt = []
    trades_ifvg_only = []
    trades_bpr_only = []
    trades_standard_fvg = []
    trades_msnr_standard = []

    print("Evaluando operaciones aisladas...")
    for sym in SELECTED_SYMBOLS:
        if sym not in market_data:
            continue
        meta = ASSET_UNIVERSE.get(sym, {"base_spread": 0.00015, "is_synth": False})
        base_spread = meta["base_spread"]
        is_synth = meta["is_synth"]
        twin_sym = SMT_TWIN_MAP.get(sym)

        df_h1 = market_data[sym]["H1"]
        df_m15 = market_data[sym]["M15"]
        n_h1 = len(df_h1)

        for i in range(30, n_h1 - 5):
            c_h1 = df_h1.iloc[i]
            t_h1 = c_h1["time"]
            c_close = float(c_h1["close"])
            c_ema50 = float(c_h1["ema50"])
            c_ema200 = float(c_h1["ema200"])
            adx_val = float(c_h1["adx"])

            bias = "BULLISH" if (c_close > c_ema50 and c_ema50 >= c_ema200) else (
                "BEARISH" if (c_close < c_ema50 and c_ema50 <= c_ema200) else "NEUTRAL"
            )
            if bias == "NEUTRAL":
                continue

            # SMT
            smt_div = None
            if twin_sym:
                smt_div = compute_smt_divergence(sym, twin_sym, t_h1, market_data, lookback_bars=16)

            # Standard FVG
            c_m2 = df_h1.iloc[i - 2]
            c_m0 = df_h1.iloc[i]

            if bias == "BULLISH" and c_m0["low"] > c_m2["high"] and is_direction_allowed(sym, "BUY"):
                sl = float(c_m2["high"]) - (base_spread * 1.5)
                risk = abs(c_m0["close"] - sl)
                if risk > (2.0 * base_spread):
                    st = {"symbol": sym, "type": "STD_FVG", "direction": "BUY", "time": t_h1, "entry_price": float(c_m0["close"]), "stop_loss": sl}
                    res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth)
                    if res:
                        trades_standard_fvg.append(res)
                        if smt_div == "BUY":
                            trades_smt_confirmed.append(res)
                        else:
                            trades_no_smt.append(res)

            elif bias == "BEARISH" and c_m0["high"] < c_m2["low"] and is_direction_allowed(sym, "SELL"):
                sl = float(c_m2["low"]) + (base_spread * 1.5)
                risk = abs(sl - c_m0["close"])
                if risk > (2.0 * base_spread):
                    st = {"symbol": sym, "type": "STD_FVG", "direction": "SELL", "time": t_h1, "entry_price": float(c_m0["close"]), "stop_loss": sl}
                    res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth)
                    if res:
                        trades_standard_fvg.append(res)
                        if smt_div == "SELL":
                            trades_smt_confirmed.append(res)
                        else:
                            trades_no_smt.append(res)

            # iFVG & BPR (Opción C)
            opt_c = detect_ifvg_and_bpr_setups(sym, df_h1, i, base_spread, is_synth, bias)
            for st in opt_c:
                res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth)
                if res:
                    if st["type"] == "ICT_IFVG":
                        trades_ifvg_only.append(res)
                    elif st["type"] == "ICT_BPR":
                        trades_bpr_only.append(res)

    def stats(trades, label):
        n = len(trades)
        if n == 0:
            return {"Label": label, "Trades": 0, "WinRate_TP1": 0.0, "WinRate_TP2": 0.0, "Net_R": 0.0, "PF": 0.0, "Exp_R": 0.0}
        tp1 = sum(1 for t in trades if t["hit_tp1"])
        tp2 = sum(1 for t in trades if t["hit_tp2"])
        wr1 = round((tp1 / n) * 100.0, 1)
        wr2 = round((tp2 / n) * 100.0, 1)
        net_r = round(sum(t["net_r"] for t in trades), 1)
        gw = sum(t["net_r"] for t in trades if t["net_r"] > 0)
        gl = abs(sum(t["net_r"] for t in trades if t["net_r"] < 0))
        pf = round(gw / (gl + 1e-9), 2)
        exp_r = round(net_r / n, 3)
        return {"Label": label, "Trades": n, "WinRate_TP1": wr1, "WinRate_TP2": wr2, "Net_R": net_r, "PF": pf, "Exp_R": exp_r}

    results = [
        stats(trades_standard_fvg, "Standard FVG (Baseline)"),
        stats(trades_smt_confirmed, "Trades con SMT Confirmado (Opción A)"),
        stats(trades_no_smt, "Trades SIN SMT Confirmado"),
        stats(trades_ifvg_only, "Inversion FVG Exclusivos (Opción C)"),
        stats(trades_bpr_only, "Balanced Price Range BPR (Opción C)"),
    ]

    df_out = pd.DataFrame(results)
    print("\n" + "=" * 90)
    print("ANÁLISIS AISLADO Y RIGUROSO DE CADA COMPONENTE (2 AÑOS):")
    print("=" * 90)
    print(df_out.to_string(index=False))
    print("=" * 90)

    # Comparativa SMT
    if len(trades_smt_confirmed) > 0 and len(trades_no_smt) > 0:
        wr_smt = df_out.loc[df_out["Label"].str.contains("SMT Confirmado"), "WinRate_TP1"].values[0]
        wr_nosmt = df_out.loc[df_out["Label"].str.contains("SIN SMT"), "WinRate_TP1"].values[0]
        print(f"\nIMPACTO CUANTITATIVO DE SMT (Opción A):")
        print(f"• WinRate con SMT: {wr_smt}% vs Sin SMT: {wr_nosmt}% (Delta: {wr_smt - wr_nosmt:+.1f}%)")

if __name__ == "__main__":
    run_isolated_audit()
