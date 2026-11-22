"""
Replay Cuantitativo Multianual desde el Nacimiento (~2.2 años / 801 días)
Instrumentos: Multi Step 2 Index, Multi Step 3 Index, Multi Step 4 Index
Estrategia: MultiEstrategia (ICT + Malaysian SNR) con Subasta Competitiva
Objetivo: Evaluar viabilidad para 1 a 2 trades/día con máxima rentabilidad.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import json

HISTORY_DIR = Path("storage/analysis/msnr_v21_two_years_20261011/history")

INSTRUMENTS = [
    ("Multi Step 2 Index", "Multi_Step_2_Index", 2.0),
    ("Multi Step 3 Index", "Multi_Step_3_Index", 3.0),
    ("Multi Step 4 Index", "Multi_Step_4_Index", 4.0),
]


def simulate_contract(highs, lows, direction, entry, sl, spread=0.0, max_bars=120):
    sign = 1 if direction == "BUY" else -1
    risk = sign * (entry - sl)
    if risk <= 0:
        return -1.0, "INVALID", 1

    tp1 = entry + sign * 1.0 * risk
    tp2 = entry + sign * 2.0 * risk
    tp3 = entry + sign * 3.0 * risk
    tp4 = entry + sign * 4.0 * risk

    leg1_done = False
    leg1_r = 0.0
    runner_sl = sl
    n = min(len(highs), len(lows), max_bars)

    for i in range(n):
        h = highs[i]
        l = lows[i]

        # Stop loss check
        sl_hit = (l <= runner_sl) if sign > 0 else (h + spread >= runner_sl)
        if sl_hit:
            if not leg1_done:
                return -1.0, "SL", i + 1
            else:
                p2_r = 0.5 * (sign * (runner_sl - entry) / risk)
                return leg1_r + p2_r, "BE", i + 1

        # TP1 check
        if not leg1_done:
            tp1_hit = (h >= tp1) if sign > 0 else (l <= tp1)
            if tp1_hit:
                leg1_done = True
                leg1_r = 0.50
                runner_sl = entry + (spread if sign > 0 else -spread)

        # Runner management
        if leg1_done:
            if (h >= tp4 if sign > 0 else l <= tp4):
                return leg1_r + 2.0, "TP4", i + 1
            elif (h >= tp3 if sign > 0 else l <= tp3):
                runner_sl = entry + sign * 2.5 * risk
            elif (h >= tp2 if sign > 0 else l <= tp2):
                runner_sl = entry + sign * 1.0 * risk

    if leg1_done:
        return leg1_r, "TIME_P1", n
    return -1.0, "TIME_SL", n


def run_analysis_for_instrument(name, file_prefix, step_size):
    # Load M15 and H1
    with open(HISTORY_DIR / f"{file_prefix}_M15.pkl", "rb") as f:
        df_m15 = pickle.load(f)
    with open(HISTORY_DIR / f"{file_prefix}_H1.pkl", "rb") as f:
        df_h1 = pickle.load(f)

    # Sort and clean
    df_m15 = df_m15.sort_values("time").reset_index(drop=True)
    df_h1 = df_h1.sort_values("time").reset_index(drop=True)

    times = pd.to_datetime(df_m15["time"])
    days_count = (times.iloc[-1] - times.iloc[0]).total_seconds() / 86400.0
    n_bars = len(df_m15)

    # Precalculate ATR, EMA, Highs, Lows
    highs = df_m15["high"].values
    lows = df_m15["low"].values
    closes = df_m15["close"].values
    opens = df_m15["open"].values
    spreads = df_m15["spread"].values if "spread" in df_m15.columns else np.zeros(n_bars)

    # Simple ATR 14
    tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
    atr = np.zeros(n_bars)
    atr[1:15] = tr[:14].mean()
    for i in range(15, n_bars):
        atr[i] = (atr[i-1] * 13 + tr[i-1]) / 14

    # EMA 20 & EMA 50 for H1 trend alignment
    h1_closes = df_h1["close"].values
    h1_ema20 = pd.Series(h1_closes).ewm(span=20).mean().values
    h1_ema50 = pd.Series(h1_closes).ewm(span=50).mean().values
    h1_times = pd.to_datetime(df_h1["time"]).values

    # Map H1 trend to M15
    h1_idx = 0
    h1_len = len(h1_times)
    m15_h1_trend = np.zeros(n_bars)
    for i in range(n_bars):
        t = times.iloc[i].to_datetime64()
        while h1_idx + 1 < h1_len and h1_times[h1_idx + 1] <= t:
            h1_idx += 1
        m15_h1_trend[i] = 1 if h1_ema20[h1_idx] > h1_ema50[h1_idx] else -1

    # Configurations to test:
    # 1. Baseline Mono-Strategy (MSNR puro sin filtro de step, 2024-2026)
    # 2. MultiStrategia Moderada (ICT + MSNR con filtro de step estricto)
    # 3. MultiStrategia Alta Frecuencia (1 a 2 trades/día objetivo del usuario)
    configs = [
        {"name": "Mono-Estrategia Baseline (MSNR puro sin calibrar)", "freq_target": "Baja", "fvg_sens": 0.0, "step_filter": False, "cooldown": 48},
        {"name": "MultiStrategia Moderada (Alta Convicción)", "freq_target": "Media (~0.5/día)", "fvg_sens": 1.5, "step_filter": True, "cooldown": 16},
        {"name": "MultiStrategia Alta Frecuencia (1-2 trades/día)", "freq_target": "Objetivo Usuario (~1.2 - 1.6/día)", "fvg_sens": 0.8, "step_filter": True, "cooldown": 6},
    ]

    results = []

    for cfg in configs:
        trades = []
        last_trade_bar = -999
        fvg_mult = cfg["fvg_sens"]
        use_step_filter = cfg["step_filter"]
        cooldown = cfg["cooldown"]

        for i in range(50, n_bars - 120):
            if i - last_trade_bar < cooldown:
                continue

            current_atr = atr[i]
            if current_atr <= 0:
                continue

            h1_dir = m15_h1_trend[i]
            close_i = closes[i]
            high_i = highs[i]
            low_i = lows[i]

            signal = None
            entry_p = close_i
            sl_p = None

            # ICT Signal: FVG Detection (3-bar pattern)
            # Bullish FVG: low[i] > high[i-2]
            fvg_bull = (lows[i] - highs[i-2]) > (fvg_mult * step_size) if i >= 2 else False
            # Bearish FVG: high[i] < low[i-2]
            fvg_bear = (lows[i-2] - highs[i]) > (fvg_mult * step_size) if i >= 2 else False

            # Malaysian SNR Signal: Breakout of 20-bar local extreme + Retest
            local_high = np.max(highs[i-20:i-1])
            local_low = np.min(lows[i-20:i-1])
            msnr_bull = (close_i > local_high) and (opens[i] <= local_high)
            msnr_bear = (close_i < local_low) and (opens[i] >= local_low)

            if cfg["name"].startswith("Mono-Estrategia"):
                # Solo quiebre puro sin filtro
                if msnr_bull and close_i > local_high:
                    signal = "BUY"
                    sl_p = close_i - 1.5 * current_atr
                elif msnr_bear and close_i < local_low:
                    signal = "SELL"
                    sl_p = close_i + 1.5 * current_atr
            else:
                # Subasta MultiEstrategia
                if (fvg_bull or msnr_bull) and (h1_dir > 0 or not use_step_filter):
                    # Filtro de micro-absorción de escalón: vela debe cerrar con cuerpo > 0.8 * step_size
                    if not use_step_filter or (close_i - opens[i] >= 0.8 * step_size):
                        signal = "BUY"
                        # SL técnico debajo del mínimo de la vela de quiebre o swing low + buffer ATR
                        sl_dist = max(1.2 * current_atr, 2.5 * step_size)
                        sl_p = close_i - sl_dist

                elif (fvg_bear or msnr_bear) and (h1_dir < 0 or not use_step_filter):
                    if not use_step_filter or (opens[i] - close_i >= 0.8 * step_size):
                        signal = "SELL"
                        sl_dist = max(1.2 * current_atr, 2.5 * step_size)
                        sl_p = close_i + sl_dist

            if signal and sl_p is not None:
                spread = (spreads[i] * 0.001) if spreads[i] > 0 else (0.1 * step_size)
                fut_h = highs[i+1:i+121]
                fut_l = lows[i+1:i+121]
                r_res, outcome, bars_dur = simulate_contract(fut_h, fut_l, signal, entry_p, sl_p, spread=spread)
                trades.append({
                    "bar": i,
                    "time": str(times.iloc[i]),
                    "direction": signal,
                    "r": r_res,
                    "outcome": outcome,
                    "bars": bars_dur
                })
                last_trade_bar = i

        n_t = len(trades)
        if n_t > 0:
            wins = sum(1 for t in trades if t["r"] > 0)
            be_trades = sum(1 for t in trades if t["outcome"] == "BE")
            wr = (wins / n_t) * 100.0
            tot_r = sum(t["r"] for t in trades)
            trades_per_day = n_t / days_count
            profit_usd = tot_r * 100.0  # en base de $100/R ($10,000 base 1.0%)
            gross_win = sum(t["r"] for t in trades if t["r"] > 0)
            gross_loss = abs(sum(t["r"] for t in trades if t["r"] < 0))
            pf = (gross_win / gross_loss) if gross_loss > 0 else 99.9

            # Max drawdown
            cum_r = np.cumsum([t["r"] for t in trades])
            peak = np.maximum.accumulate(cum_r)
            dd = peak - cum_r
            max_dd = np.max(dd) if len(dd) > 0 else 0.0

            results.append({
                "config": cfg["name"],
                "trades": n_t,
                "days": round(days_count, 1),
                "trades_per_day": round(trades_per_day, 2),
                "win_rate": round(wr, 1),
                "net_r": round(tot_r, 1),
                "pnl_usd": round(profit_usd, 2),
                "profit_factor": round(pf, 2),
                "max_drawdown_r": round(max_dd, 1),
                "be_count": be_trades,
            })

    return name, results


if __name__ == "__main__":
    summary_report = {}
    for name, prefix, step in INSTRUMENTS:
        sym_name, res = run_analysis_for_instrument(name, prefix, step)
        summary_report[sym_name] = res

    print("\n" + "="*80)
    print("REPORTE OFICIAL DEL REPLAY MULTI STEP 2, 3 Y 4 (HISTORIA COMPLETA ~2.2 AÑOS)")
    print("="*80)
    for sym, res_list in summary_report.items():
        print(f"\n>>> {sym.upper()} <<<")
        for r in res_list:
            print(f"  * {r['config']}:")
            print(f"      Trades: {r['trades']} ({r['trades_per_day']} trades/día en {r['days']} días)")
            print(f"      Win Rate: {r['win_rate']}% | PnL: +{r['net_r']} R (+${r['pnl_usd']:,.2f} USD)")
            print(f"      Profit Factor: {r['profit_factor']} | Max Drawdown: {r['max_drawdown_r']} R | BEs: {r['be_count']}")

    with open("storage/analysis/replay_multi_step_2_3_4_report.json", "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print("\nGuardado en storage/analysis/replay_multi_step_2_3_4_report.json")
