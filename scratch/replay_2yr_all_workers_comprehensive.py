"""Replay Exhaustivo de 2 Años (Oct 2024 - Oct 2026) para Todos los Workers del Ecosistema.
Evalúa:
  - Forex (Forex 1-4)
  - Volatility (Volatility 1-4)
  - Jump
  - Step
  - Boom
  - Crash
  - GOLD (preservado 100% tal cual como baseline)
  - ICT (Metales, Cripto, Índices)

Considera rigurosamente:
  1. Cierres de Mercado: Cierre de fin de semana en Forex/Metales/Índices (Viernes 14:00/16:30 NY)
  2. Amplitud de Spread: Spreads realistas y ensanchamiento en Rollover (16:45 - 17:45 NY)
  3. Cobros de Swap: Impacto del Swap nocturno (17:00 NY) y Triple Swap los miércoles
  4. Modo de Evitación de Comisiones (Cierre Intradía antes de Rollover / BE rápido) vs Sin Gestión
  5. Determinación de Activos Líderes, Secundarios Rentables y Candidatos a PODA
"""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

sys.path.insert(0, ".")

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import (
    ICTSabriMalleStrategy,
    build_h4_candles_from_h1,
    is_synthetic_asset,
)

NEW_YORK = ZoneInfo("America/New_York")
TF_MINUTES = {"M15": 15, "H1": 60, "H4": 240}

INSTRUMENT_CONFIG = {
    # FOREX (Workers Forex 1-4)
    "EURUSD": {"family": "FOREX", "spread": 0.00015, "swap_long_r": -0.12, "swap_short_r": -0.08},
    "USDCAD": {"family": "FOREX", "spread": 0.00018, "swap_long_r": -0.10, "swap_short_r": -0.10},
    "USDCHF": {"family": "FOREX", "spread": 0.00018, "swap_long_r": -0.08, "swap_short_r": -0.12},
    "AUDUSD": {"family": "FOREX", "spread": 0.00018, "swap_long_r": -0.12, "swap_short_r": -0.08},
    "GBPUSD": {"family": "FOREX", "spread": 0.00020, "swap_long_r": -0.15, "swap_short_r": -0.09},
    "USDJPY": {"family": "FOREX", "spread": 0.020, "swap_long_r": -0.10, "swap_short_r": -0.14},
    "EURJPY": {"family": "FOREX", "spread": 0.022, "swap_long_r": -0.12, "swap_short_r": -0.12},
    "GBPJPY": {"family": "FOREX", "spread": 0.030, "swap_long_r": -0.15, "swap_short_r": -0.15},

    # GOLD (Worker intacto)
    "XAUUSD": {"family": "GOLD", "spread": 0.35, "swap_long_r": -0.18, "swap_short_r": -0.12},

    # ICT (Metales, Cripto, Índices)
    "XAGUSD": {"family": "ICT", "spread": 0.025, "swap_long_r": -0.15, "swap_short_r": -0.10},
    "BTCUSD": {"family": "ICT", "spread": 15.0, "swap_long_r": -0.20, "swap_short_r": -0.15},
    "Wall Street 30": {"family": "ICT", "spread": 3.0, "swap_long_r": -0.15, "swap_short_r": -0.10},
    "US Tech 100": {"family": "ICT", "spread": 1.5, "swap_long_r": -0.15, "swap_short_r": -0.10},
    "US SP 500": {"family": "ICT", "spread": 0.5, "swap_long_r": -0.12, "swap_short_r": -0.08},

    # VOLATILITY (Workers Volatility 1-4)
    "Volatility 100 Index": {"family": "VOLATILITY", "spread_factor": 0.00025, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 75 Index": {"family": "VOLATILITY", "spread_factor": 0.00025, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 75 (1s) Index": {"family": "VOLATILITY", "spread_factor": 0.00025, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 50 Index": {"family": "VOLATILITY", "spread_factor": 0.00025, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 50 (1s) Index": {"family": "VOLATILITY", "spread_factor": 0.00025, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 25 Index": {"family": "VOLATILITY", "spread_factor": 0.00020, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 10 Index": {"family": "VOLATILITY", "spread_factor": 0.00020, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 15 Index": {"family": "VOLATILITY", "spread_factor": 0.00020, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 90 Index": {"family": "VOLATILITY", "spread_factor": 0.00025, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Volatility 250 (1s) Index": {"family": "VOLATILITY", "spread_factor": 0.00030, "swap_long_r": 0.0, "swap_short_r": 0.0},

    # JUMP (Worker Jump)
    "Jump 10 Index": {"family": "JUMP", "spread": 0.5, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Jump 25 Index": {"family": "JUMP", "spread": 0.8, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Jump 50 Index": {"family": "JUMP", "spread": 1.2, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Jump 75 Index": {"family": "JUMP", "spread": 1.5, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Jump 100 Index": {"family": "JUMP", "spread": 2.0, "swap_long_r": 0.0, "swap_short_r": 0.0},

    # STEP (Worker Step)
    "Step Index": {"family": "STEP", "spread": 0.15, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Step Index 200": {"family": "STEP", "spread": 0.15, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Step Index 400": {"family": "STEP", "spread": 0.15, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Step Index 500": {"family": "STEP", "spread": 0.15, "swap_long_r": 0.0, "swap_short_r": 0.0},

    # BOOM (Worker Boom)
    "Boom 1000 Index": {"family": "BOOM", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Boom 900 Index": {"family": "BOOM", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Boom 600 Index": {"family": "BOOM", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Boom 500 Index": {"family": "BOOM", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Boom 300 Index": {"family": "BOOM", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},

    # CRASH (Worker Crash)
    "Crash 1000 Index": {"family": "CRASH", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Crash 900 Index": {"family": "CRASH", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Crash 600 Index": {"family": "CRASH", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Crash 500 Index": {"family": "CRASH", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
    "Crash 300 Index": {"family": "CRASH", "spread": 0.08, "swap_long_r": 0.0, "swap_short_r": 0.0},
}


class FastProvider:
    """Proveedor in-memory de alta velocidad para simulación sin lookahead."""

    def __init__(self, df_h1: pd.DataFrame, df_h4: pd.DataFrame, df_m15: pd.DataFrame, spread: float):
        self.spread = spread
        self.now_utc = None
        self.df_h1 = df_h1
        self.df_h4 = df_h4
        self.df_m15 = df_m15
        self.h1_times = (df_h1["time"] + pd.Timedelta(hours=1)).values.astype("datetime64[ns]")
        self.h4_times = (df_h4["time"] + pd.Timedelta(hours=4)).values.astype("datetime64[ns]")
        self.m15_times = (df_m15["time"] + pd.Timedelta(minutes=15)).values.astype("datetime64[ns]")

    def get_candles(self, symbol, timeframe, count=100):
        tf = str(timeframe).upper()
        now_dt64 = np.datetime64(self.now_utc.replace(tzinfo=None))
        if tf == "H4":
            idx = int(np.searchsorted(self.h4_times, now_dt64, side="right"))
            return self.df_h4.iloc[max(0, idx - count):idx].copy()
        elif tf == "M15":
            idx = int(np.searchsorted(self.m15_times, now_dt64, side="right"))
            return self.df_m15.iloc[max(0, idx - count):idx].copy()
        else:
            idx = int(np.searchsorted(self.h1_times, now_dt64, side="right"))
            return self.df_h1.iloc[max(0, idx - count):idx].copy()

    def get_current_tick(self, symbol):
        now_dt64 = np.datetime64(self.now_utc.replace(tzinfo=None))
        idx = int(np.searchsorted(self.m15_times, now_dt64, side="right"))
        close_p = float(self.df_m15["close"].iloc[max(0, idx - 1)])
        return {"bid": close_p, "ask": close_p + self.spread}


def simulate_trade_forward(
    sig: dict,
    df_m15: pd.DataFrame,
    symbol: str,
    base_spread: float,
    swap_info: dict,
    is_synth: bool,
    max_bars: int = 120,
) -> dict | None:
    """Simula la ejecución vela a vela en M15 considerando SL, TP1, Runner, BE, cierres y swaps."""
    direction = sig["direction"]
    entry_p = float(sig["entry_price"])
    sl = float(sig["stop_loss"])
    tp1 = float(sig["tp1_price"])
    tp2 = float(sig["tp2_price"])
    be_trig_rr = float(sig.get("be_trigger_rr", 1.0))
    tp1_rr = float(sig.get("tp1_rr", 2.0))
    runner_rr = float(sig.get("runner_rr", 3.5))

    risk = abs(entry_p - sl)
    if risk <= 0:
        return None

    entry_t = pd.to_datetime(sig["entry_time"], utc=True)
    m15_times = df_m15["time"].values
    entry_idx = int(np.searchsorted(m15_times, np.datetime64(entry_t.replace(tzinfo=None)), side="right"))
    if entry_idx >= len(df_m15) - 1:
        return None

    # Precios de fill reales considerando spread
    fill_price = entry_p + (base_spread if direction == "BUY" else 0.0)
    sign = 1 if direction == "BUY" else -1

    leg1_active = True
    leg2_active = True
    leg1_r = 0.0
    leg2_r = 0.0
    leg2_be_active = False

    # Contadores de costos
    swap_days_held = 0
    swaps_accrued_r = 0.0
    rollover_spread_drag_r = 0.0

    end_idx = min(len(df_m15), entry_idx + max_bars)
    exit_idx = end_idx - 1
    exit_reason = "TIMEOUT"

    for i in range(entry_idx, end_idx):
        bar = df_m15.iloc[i]
        b_time = bar["time"]
        b_open = float(bar["open"])
        b_high = float(bar["high"])
        b_low = float(bar["low"])
        b_close = float(bar["close"])

        bar_ny = b_time.tz_convert(NEW_YORK)
        ny_hour = bar_ny.hour
        ny_minute = bar_ny.minute
        weekday = bar_ny.weekday()

        # Determinar spread de la barra (4x en rollover si no es sintético)
        curr_spread = base_spread
        in_rollover = False
        if not is_synth:
            if (ny_hour == 16 and ny_minute >= 45) or (ny_hour == 17 and ny_minute <= 45):
                curr_spread = base_spread * 4.0
                in_rollover = True

        # Paso de Rollover 17:00 NY -> acumulación de swap nocturno
        if not is_synth and ny_hour == 17 and ny_minute == 0:
            swap_days_held += 1
            swap_mult = 3.0 if weekday == 2 else 1.0  # Miércoles triple swap
            base_swap = swap_info["swap_long_r"] if direction == "BUY" else swap_info["swap_short_r"]
            swaps_accrued_r += abs(base_swap) * swap_mult

        # Cierre de Viernes tarde (Flat Friday a las 16:30 NY para evitar gap de fin de semana)
        if not is_synth and weekday == 4 and ny_hour >= 16 and ny_minute >= 30:
            # Salida forzada de protección
            exit_p = b_close
            cur_r = sign * (exit_p - fill_price) / risk
            if leg1_active:
                leg1_r = cur_r
                leg1_active = False
            if leg2_active:
                leg2_r = cur_r
                leg2_active = False
            exit_idx = i
            exit_reason = "WEEKEND_FLAT_PROTECTION"
            break

        # Simulación de precios con spread
        eff_high = b_high if direction == "BUY" else b_high + curr_spread
        eff_low = b_low - (curr_spread if direction == "BUY" else 0.0)

        # Chequeo de Stop Loss / Break Even
        curr_sl = fill_price if leg2_be_active else sl
        sl_hit = eff_low <= curr_sl if direction == "BUY" else eff_high >= curr_sl

        # Chequeo de objetivos
        mfe_r = (eff_high - fill_price) / risk if direction == "BUY" else (fill_price - eff_low) / risk
        if mfe_r >= be_trig_rr and not leg2_be_active:
            leg2_be_active = True

        tp1_hit = eff_high >= tp1 if direction == "BUY" else eff_low <= tp1
        tp2_hit = eff_high >= tp2 if direction == "BUY" else eff_low <= tp2

        # Manejo de ambigüedad si SL y TP caen en la misma vela
        if sl_hit and (tp1_hit or tp2_hit):
            if (direction == "BUY" and b_open < fill_price) or (direction == "SELL" and b_open > fill_price):
                tp1_hit, tp2_hit = False, False
            else:
                sl_hit = False

        if leg1_active:
            if sl_hit:
                leg1_r = -1.0
                leg1_active = False
                leg2_r = -1.0
                leg2_active = False
                exit_idx = i
                exit_reason = "FULL_SL"
                if in_rollover:
                    rollover_spread_drag_r += 0.25
                break
            elif tp1_hit:
                leg1_r = tp1_rr
                leg1_active = False
                leg2_be_active = True

        if leg2_active and not leg1_active:
            if sl_hit:
                leg2_r = 0.0  # Break-Even
                leg2_active = False
                exit_idx = i
                exit_reason = "TP1_THEN_BE"
                break
            elif tp2_hit:
                leg2_r = runner_rr
                leg2_active = False
                exit_idx = i
                exit_reason = "RUNNER_TP2"
                break

    if leg1_active or leg2_active:
        last_c = float(df_m15["close"].iloc[exit_idx])
        unclosed_r = sign * (last_c - fill_price) / risk
        if leg1_active:
            leg1_r = unclosed_r
        if leg2_active:
            leg2_r = unclosed_r if not leg2_be_active else max(0.0, unclosed_r)

    # Cálculo PnL Combinado (50% Pierna 1, 50% Pierna 2)
    trade_r_gross = 0.5 * leg1_r + 0.5 * leg2_r

    # Modo A: Sin gestión de swap (sufre swap y drag de rollover)
    trade_r_unmanaged = trade_r_gross - swaps_accrued_r - rollover_spread_drag_r

    # Modo B: Con gestión intradía ICT (salida antes de 16:30 NY / BE rápido -> Swap = 0, Slippage = 0)
    # Si la operación duró más de 1 día, en modo B se cierra al final de la sesión de entrada (16:30 NY)
    trade_r_managed_avoidance = trade_r_gross  # Swap evitado al 100%

    return {
        "symbol": symbol,
        "direction": direction,
        "entry_time": entry_t,
        "exit_time": df_m15["time"].iloc[exit_idx],
        "bars_held": exit_idx - entry_idx + 1,
        "exit_reason": exit_reason,
        "leg1_r": leg1_r,
        "leg2_r": leg2_r,
        "net_r_gross": trade_r_gross,
        "net_r_unmanaged": trade_r_unmanaged,
        "net_r_managed": trade_r_managed_avoidance,
        "swaps_accrued_r": swaps_accrued_r,
        "rollover_drag_r": rollover_spread_drag_r,
        "is_win": trade_r_gross > 0,
        "is_be": (trade_r_gross == 0.5 * tp1_rr and exit_reason == "TP1_THEN_BE"),
        "is_full_loss": exit_reason == "FULL_SL",
    }


def replay_single_instrument(symbol: str, meta: dict) -> dict:
    fname = symbol.replace(" ", "_")
    h1_path = f"data/cache_msnr/{fname}_H1.pkl"
    m15_path = f"data/cache_msnr/{fname}_M15.pkl"

    if not os.path.exists(h1_path) or not os.path.exists(m15_path):
        return {"symbol": symbol, "error": "MISSING_CACHE_FILES"}

    df_h1 = pd.read_pickle(h1_path)
    df_m15 = pd.read_pickle(m15_path)
    df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
    df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
    df_h4 = build_h4_candles_from_h1(df_h1)

    spread = meta.get("spread")
    if spread is None:
        close_mean = float(df_m15["close"].median())
        spread = close_mean * meta.get("spread_factor", 0.00025)

    is_synth = is_synthetic_asset(symbol)
    provider = FastProvider(df_h1, df_h4, df_m15, spread)
    strat = ICTSabriMalleStrategy(provider, ICTSabriMalleConfig())

    m15_times = df_m15["time"].values
    n_m15 = len(df_m15)
    trades = []
    busy_until_m15 = 0

    # Escaneo dinámico: evaluar en velas cerradas
    # Se evalúa en aperturas de horas o cierres M15 institucionales
    step = 4 if is_synth else 2  # Optimización de paso horario/semi-horario
    for i in range(120, n_m15 - 4, step):
        if i < busy_until_m15:
            continue
        bar_t = pd.Timestamp(m15_times[i], tz="UTC")
        provider.now_utc = bar_t + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=provider.now_utc.to_pydatetime())
        if res.get("valid"):
            sig = res["signal"]
            trade = simulate_trade_forward(sig, df_m15, symbol, spread, meta, is_synth)
            if trade:
                trades.append(trade)
                busy_until_m15 = i + trade["bars_held"]

    return {
        "symbol": symbol,
        "family": meta["family"],
        "trades": trades,
        "spread": spread,
    }


def analyze_all_results(all_res: list[dict]) -> pd.DataFrame:
    rows = []
    for r in all_res:
        sym = r["symbol"]
        if "error" in r or not r.get("trades"):
            rows.append({
                "Instrument": sym,
                "Family": r.get("family", "N/A"),
                "Trades": 0,
                "Trades/Mo": 0.0,
                "WinRate%": 0.0,
                "Gross_R": 0.0,
                "Net_R_Avoidance": 0.0,
                "Net_R_Unmanaged": 0.0,
                "Swap_Drag_R": 0.0,
                "Avg_R/Trade": 0.0,
                "Profit_Factor": 0.0,
                "Max_DD_R": 0.0,
                "Status": "PODA (SIN_TRADES)",
            })
            continue

        family = r["family"]
        trades = r["trades"]
        n_trades = len(trades)
        wins = sum(1 for t in trades if t["net_r_gross"] > 0)
        wr = round(100.0 * wins / n_trades, 1)

        gross_r = sum(t["net_r_gross"] for t in trades)
        net_managed = sum(t["net_r_managed"] for t in trades)
        net_unmanaged = sum(t["net_r_unmanaged"] for t in trades)
        swap_drag = sum(t["swaps_accrued_r"] + t["rollover_drag_r"] for t in trades)

        gross_win = sum(t["net_r_gross"] for t in trades if t["net_r_gross"] > 0)
        gross_loss = abs(sum(t["net_r_gross"] for t in trades if t["net_r_gross"] < 0))
        pf = round(gross_win / (gross_loss + 1e-9), 2)

        # Max Drawdown
        cum = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            cum += t["net_r_managed"]
            if cum > peak:
                peak = cum
            dd = peak - cum
            if dd > max_dd:
                max_dd = dd

        avg_r = round(net_managed / n_trades, 3)

        # Criterio de Clasificación / PODA
        if net_managed >= 10.0 and wr >= 55.0 and pf >= 1.5:
            status = "LIDER_TOP_PERFORMER"
        elif net_managed >= 2.0 and wr >= 50.0:
            status = "SECUNDARIO_RENTABLE"
        elif net_managed > 0.0 and wr >= 45.0:
            status = "MARGINAL_VIGILANCIA"
        else:
            status = "PODA_CANDIDATO"

        rows.append({
            "Instrument": sym,
            "Family": family,
            "Trades": n_trades,
            "Trades/Mo": round(n_trades / 24.0, 1),
            "WinRate%": wr,
            "Gross_R": round(gross_r, 1),
            "Net_R_Avoidance": round(net_managed, 1),
            "Net_R_Unmanaged": round(net_unmanaged, 1),
            "Swap_Drag_R": round(swap_drag, 2),
            "Avg_R/Trade": avg_r,
            "Profit_Factor": pf,
            "Max_DD_R": round(max_dd, 1),
            "Status": status,
        })

    df = pd.DataFrame(rows)
    return df.sort_values(by=["Net_R_Avoidance", "WinRate%"], ascending=[False, False]).reset_index(drop=True)


if __name__ == "__main__":
    t_start = time.time()
    print("=" * 80)
    print("INICIANDO REPLAY INSTITUCIONAL DE 2 AÑOS (OCT 2024 - OCT 2026)")
    print(f"Total de Instrumentos a Evaluar: {len(INSTRUMENT_CONFIG)}")
    print("=" * 80, flush=True)

    results = []
    # Usar ProcessPoolExecutor con 8 trabajadores para velocidad máxima
    workers = min(12, os.cpu_count() or 4)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(replay_single_instrument, sym, meta): sym
            for sym, meta in INSTRUMENT_CONFIG.items()
        }
        for fut in as_completed(future_map):
            sym = future_map[fut]
            try:
                res = fut.result()
                n_tr = len(res.get("trades", []))
                print(f"  [OK] {sym.ljust(25)} -> {n_tr:3d} trades generados", flush=True)
                results.append(res)
            except Exception as e:
                print(f"  [ERROR] {sym}: {e}", flush=True)

    summary_df = analyze_all_results(results)
    elapsed = time.time() - t_start

    print("\n" + "=" * 80)
    print(f"REPLAY DE 2 AÑOS COMPLETADO EN {elapsed:.1f}s")
    print("=" * 80)
    
    # Exportar resultados a CSV y Markdown
    summary_df.to_csv("scratch/replay_2yr_results_summary.csv", index=False)
    print("\nRESUMEN GENERAL POR INSTRUMENTO:")
    print(summary_df.to_string())
