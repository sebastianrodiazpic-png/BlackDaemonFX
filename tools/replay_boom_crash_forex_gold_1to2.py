"""Replay Histórico Cuantitativo para BOOM, CRASH, FOREX y GOLD (6 Meses / 180 Días).

Evalúa la estrategia SMC con relación Riesgo:Beneficio mínima 1:2 (RR >= 2.0).
Analiza:
1. Rendimiento Directo 1:2 (TP=+2.0R, SL=-1.0R).
2. Rendimiento con Break-Even a +1.0R.
3. Rendimiento con Doble Pierna Asimétrica (TP1=+1.2R, Runner=+2.5R, BE=+0.1R).
4. Excursión Máxima Favorable (MFE) y Adversa (MAE).
5. Filtros institucionales por familia:
   - BOOM: BUY (a favor de spikes) vs SELL; filtro de mínimo de 24h.
   - CRASH: SELL (a favor de caídas) vs BUY; filtro de máximo de 24h.
   - FOREX: Killzones Londres (07:00-10:00 UTC) y NY (12:00-16:00 UTC).
   - GOLD: Killzone Solapamiento Londres/NY (12:00-17:00 UTC).
   - Régimen tendencial ADX (ADX >= 20).

Uso:
    python tools/replay_boom_crash_forex_gold_1to2.py [--days 180] [--family BOOM|CRASH|FOREX|GOLD|ALL]
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
import json
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8 configuration
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import pandas as pd
import MetaTrader5 as mt5

from strategy.execution.trade_pipeline import run_trade_pipeline, PipelineConfig


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula Average True Range (ATR) clásico."""
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula Average Directional Index (ADX)."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = pd.Series(tr).ewm(alpha=1/period, min_periods=period).mean()
    plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr

    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    adx = dx.ewm(alpha=1/period, min_periods=period).mean()
    return adx


CORE_ASSETS = {
    "BOOM": [
        "Boom 1000 Index",
        "Boom 500 Index",
        "Boom 300 Index",
        "Boom 600 Index",
        "Boom 900 Index",
    ],
    "CRASH": [
        "Crash 1000 Index",
        "Crash 500 Index",
        "Crash 300 Index",
        "Crash 600 Index",
        "Crash 900 Index",
    ],
    "FOREX": [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
        "USDCHF",
        "EURJPY",
        "GBPJPY",
    ],
    "GOLD": [
        "XAUUSD",
    ],
}


def fetch_symbol_candles(symbol: str, timeframe: int, days: int):
    """Descarga velas históricas desde MT5 para el período solicitado."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    mt5.symbol_select(symbol, True)
    rates = mt5.copy_rates_range(symbol, timeframe, start_time, now)
    if rates is None or len(rates) == 0:
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def is_forex_killzone(timestamp) -> bool:
    """Verifica si la hora UTC está en Killzone de Londres (07-10 UTC) o NY (12-16 UTC)."""
    try:
        ts = pd.to_datetime(timestamp, utc=True)
        h = ts.hour
        m = ts.minute
        t_float = h + m / 60.0
        # Londres: 07:00 a 10:00 UTC
        if 7.0 <= t_float <= 10.0:
            return True
        # NY: 12:00 a 16:00 UTC
        if 12.0 <= t_float <= 16.0:
            return True
        return False
    except Exception:
        return False


def is_gold_killzone(timestamp) -> bool:
    """Verifica si la hora UTC está en la ventana de solapamiento Londres/NY (12-17 UTC)."""
    try:
        ts = pd.to_datetime(timestamp, utc=True)
        h = ts.hour
        m = ts.minute
        t_float = h + m / 60.0
        return 12.0 <= t_float <= 17.0
    except Exception:
        return False


def simulate_trade_comprehensive(
    candles: pd.DataFrame,
    entry_time,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    be_trigger_rr: float = 1.0,
    max_bars: int = 200,
):
    """Simula bar-a-bar el trade midiendo:
    1. Directo 1:2 (TP=+2.0R, SL=-1.0R)
    2. Con Break-Even a 1.0R (SL movido a entry)
    3. Doble Pierna Asimétrica (Pierna 1 TP=+1.2R, Pierna 2 TP=+2.5R con BE a +0.1R al tocar 1.0R)
    4. MFE y MAE
    """
    direction = str(direction).upper()
    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    take_profit = float(take_profit)
    risk = abs(entry_price - stop_loss)
    if risk <= 1e-9:
        return None

    future = candles[candles["time"] > entry_time].head(max_bars)
    if future.empty:
        return None

    # Parámetros asimétricos doble pierna
    tp1_price = entry_price + (1.2 * risk if direction == "BUY" else -1.2 * risk)
    tp2_price = entry_price + (2.5 * risk if direction == "BUY" else -2.5 * risk)
    be_price = entry_price + (0.1 * risk if direction == "BUY" else -0.1 * risk)

    be_active = False
    max_mfe_r = 0.0
    max_mae_r = 0.0

    direct_result = None
    direct_bars = 0
    direct_realized_rr = 0.0
    direct_exit_time = None

    be_result = None
    be_realized_rr = 0.0

    # Piernas asimétricas (50% cada una)
    leg1_closed = False
    leg1_rr = 0.0
    leg2_closed = False
    leg2_rr = 0.0

    for bars_held, (_, candle) in enumerate(future.iterrows(), start=1):
        high = float(candle["high"])
        low = float(candle["low"])
        c_time = candle["time"]

        # Medir MFE / MAE
        if direction == "BUY":
            bar_mfe = (high - entry_price) / risk
            bar_mae = (entry_price - low) / risk
            hit_tp = high >= take_profit
            hit_sl = low <= stop_loss
            hit_be = be_active and (low <= entry_price)

            hit_tp1 = high >= tp1_price
            hit_tp2 = high >= tp2_price
            hit_asym_be = be_active and (low <= be_price)
            if bar_mfe >= be_trigger_rr:
                be_active = True
        else:
            bar_mfe = (entry_price - low) / risk
            bar_mae = (high - entry_price) / risk
            hit_tp = low <= take_profit
            hit_sl = high >= stop_loss
            hit_be = be_active and (high >= entry_price)

            hit_tp1 = low <= tp1_price
            hit_tp2 = low <= tp2_price
            hit_asym_be = be_active and (high >= be_price)
            if bar_mfe >= be_trigger_rr:
                be_active = True

        max_mfe_r = max(max_mfe_r, bar_mfe)
        max_mae_r = max(max_mae_r, bar_mae)

        # 1. Simulación Directa 1:2
        if direct_result is None:
            if hit_sl and hit_tp:
                direct_result = "AMBIGUOUS"
                direct_realized_rr = 0.0
                direct_bars = bars_held
                direct_exit_time = c_time
            elif hit_sl:
                direct_result = "LOSS"
                direct_realized_rr = -1.0
                direct_bars = bars_held
                direct_exit_time = c_time
            elif hit_tp:
                direct_result = "WIN"
                direct_realized_rr = 2.0
                direct_bars = bars_held
                direct_exit_time = c_time

        # 2. Simulación con BE @ 1R
        if be_result is None:
            if hit_tp:
                be_result = "WIN"
                be_realized_rr = 2.0
            elif be_active and hit_be:
                be_result = "BREAK_EVEN"
                be_realized_rr = 0.0
            elif hit_sl:
                be_result = "LOSS"
                be_realized_rr = -1.0

        # 3. Simulación Doble Pierna Asimétrica (0.5% + 0.5%)
        # Pierna 1 (TP1 @ 1.2R)
        if not leg1_closed:
            if hit_tp1:
                leg1_closed = True
                leg1_rr = 1.2 * 0.5  # +0.6R
                be_active = True     # Al cerrar TP1, BE inmediato en Pierna 2
            elif hit_sl:
                leg1_closed = True
                leg1_rr = -1.0 * 0.5  # -0.5R

        # Pierna 2 (Runner @ 2.5R con BE a +0.1R)
        if not leg2_closed:
            if hit_tp2:
                leg2_closed = True
                leg2_rr = 2.5 * 0.5  # +1.25R
            elif be_active and hit_asym_be:
                leg2_closed = True
                leg2_rr = 0.1 * 0.5  # +0.05R
            elif hit_sl:
                leg2_closed = True
                leg2_rr = -1.0 * 0.5  # -0.5R

        # Si todo cerró, terminar simulación
        if direct_result is not None and be_result is not None and leg1_closed and leg2_closed:
            break

    # Si expira por tiempo (max_bars)
    if direct_result is None:
        direct_result = "OPEN"
        direct_realized_rr = 0.0
        direct_bars = len(future)
        direct_exit_time = future.iloc[-1]["time"]
    if be_result is None:
        be_result = "OPEN"
        be_realized_rr = 0.0

    asym_total_rr = round(leg1_rr + leg2_rr, 4)
    asym_result = "WIN" if asym_total_rr > 0 else ("BREAK_EVEN" if asym_total_rr == 0 else "LOSS")

    return {
        "direct_result": direct_result,
        "direct_realized_rr": direct_realized_rr,
        "direct_bars": direct_bars,
        "direct_exit_time": str(direct_exit_time),
        "be_result": be_result,
        "be_realized_rr": be_realized_rr,
        "asym_result": asym_result,
        "asym_realized_rr": asym_total_rr,
        "max_mfe_r": round(max_mfe_r, 3),
        "max_mae_r": round(max_mae_r, 3),
    }


def analyze_asset_replay(symbol: str, family: str, days: int = 180):
    """Ejecuta el replay histórico de 180 días para un activo específico."""
    print(f"\n[{family}] Analizando {symbol} ({days} días)...", flush=True)

    candles = fetch_symbol_candles(symbol, mt5.TIMEFRAME_M15, days=days)
    if candles is None or len(candles) < 200:
        print(f"  Datos insuficientes para {symbol}")
        return None

    # Cálculo de indicadores contextuales
    candles["adx"] = compute_adx(candles, period=14)
    candles["atr"] = compute_atr(candles, period=14)

    # Configuración de pipeline SMC con RR 1:2
    cfg = PipelineConfig(
        risk_reward_ratio=2.0,
        chart_patterns_enabled=False,
        harmonic_enabled=False,
        divergence_enabled=False,
        fvg_enabled=True,
        fvg_min_displacement_atr_multiplier=1.5,
        minimum_trade_score=80.0,
    )

    t0 = time.time()
    chunk_size = 4000
    overlap = 200
    total_len = len(candles)

    all_setups = []
    all_confirmations = []

    for start_idx in range(0, total_len, chunk_size - overlap):
        end_idx = min(start_idx + chunk_size, total_len)
        chunk = candles.iloc[start_idx:end_idx].copy()
        if len(chunk) < 200:
            break
        try:
            res = run_trade_pipeline(chunk, config=cfg, symbol=symbol)
            if not res["setups"].empty:
                all_setups.append(res["setups"])
            if not res["confirmations"].empty:
                all_confirmations.append(res["confirmations"])
        except Exception as e:
            print(f"    Error en chunk {start_idx}-{end_idx}: {e}")

        if end_idx >= total_len:
            break

    setups = (
        pd.concat(all_setups, ignore_index=True).drop_duplicates(subset=["setup_time", "ob_high", "ob_low"])
        if all_setups else pd.DataFrame()
    )
    confirmations = (
        pd.concat(all_confirmations, ignore_index=True).drop_duplicates(subset=["entry_time", "direction"])
        if all_confirmations else pd.DataFrame()
    )

    elapsed = time.time() - t0
    print(f"  Velas: {len(candles)} (M15) | Setups: {len(setups)} | Confirmaciones: {len(confirmations)} (Tiempo: {elapsed:.1f}s)", flush=True)

    if confirmations.empty:
        return None

    # Simular confirmaciones
    trade_records = []
    for _, conf in confirmations.iterrows():
        entry_time = conf["entry_time"]
        direction = conf["direction"]
        entry_price = float(conf["entry_price"])
        stop_loss = float(conf["stop_loss"])
        take_profit = float(conf["take_profit"])

        sim = simulate_trade_comprehensive(
            candles=candles,
            entry_time=entry_time,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            be_trigger_rr=1.0,
            max_bars=150,
        )
        if sim is None:
            continue

        conf_row = candles[candles["time"] == entry_time]
        adx_val = float(conf_row["adx"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["adx"].iloc[0]) else 0.0
        atr_val = float(conf_row["atr"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["atr"].iloc[0]) else 0.0

        # Filtros de sesión
        in_kz = is_gold_killzone(entry_time) if family == "GOLD" else (is_forex_killzone(entry_time) if family == "FOREX" else True)

        rec = {
            "symbol": symbol,
            "family": family,
            "entry_time": str(entry_time),
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "adx": adx_val,
            "atr": atr_val,
            "is_killzone": in_kz,
            **sim,
        }
        trade_records.append(rec)

    if not trade_records:
        return None

    df_trades = pd.DataFrame(trade_records)

    # 1. Estadísticas Directas 1:2
    direct_closed = df_trades[df_trades["direct_result"].isin(["WIN", "LOSS"])]
    direct_total = len(direct_closed)
    direct_wins = len(direct_closed[direct_closed["direct_result"] == "WIN"])
    direct_losses = len(direct_closed[direct_closed["direct_result"] == "LOSS"])
    direct_wr = round(direct_wins / direct_total * 100, 2) if direct_total > 0 else 0.0
    direct_tot_r = round(float(direct_closed["direct_realized_rr"].sum()), 2)
    direct_exp = round(direct_tot_r / direct_total, 3) if direct_total > 0 else 0.0

    # 2. Estadísticas con BE @ 1.0R
    be_closed = df_trades[df_trades["be_result"].isin(["WIN", "LOSS", "BREAK_EVEN"])]
    be_total = len(be_closed)
    be_wins = len(be_closed[be_closed["be_result"] == "WIN"])
    be_losses = len(be_closed[be_closed["be_result"] == "LOSS"])
    be_bes = len(be_closed[be_closed["be_result"] == "BREAK_EVEN"])
    be_decided = be_wins + be_losses
    be_wr = round(be_wins / be_decided * 100, 2) if be_decided > 0 else 0.0
    be_tot_r = round(float(be_closed["be_realized_rr"].sum()), 2)
    be_exp = round(be_tot_r / be_total, 3) if be_total > 0 else 0.0

    # 3. Estadísticas Doble Pierna Asimétrica (0.5% TP1 @ 1.2R + 0.5% Runner @ 2.5R)
    asym_closed = df_trades[df_trades["asym_result"].isin(["WIN", "LOSS", "BREAK_EVEN"])]
    asym_total = len(asym_closed)
    asym_wins = len(asym_closed[asym_closed["asym_result"] == "WIN"])
    asym_losses = len(asym_closed[asym_closed["asym_result"] == "LOSS"])
    asym_bes = len(asym_closed[asym_closed["asym_result"] == "BREAK_EVEN"])
    asym_tot_r = round(float(asym_closed["asym_realized_rr"].sum()), 2)
    asym_wr = round(asym_wins / asym_total * 100, 2) if asym_total > 0 else 0.0
    asym_exp = round(asym_tot_r / asym_total, 3) if asym_total > 0 else 0.0

    # 4. MFE en Pérdidas Directas
    losses_df = direct_closed[direct_closed["direct_result"] == "LOSS"]
    mfe_reached_05 = len(losses_df[losses_df["max_mfe_r"] >= 0.5])
    mfe_reached_10 = len(losses_df[losses_df["max_mfe_r"] >= 1.0])
    mfe_reached_15 = len(losses_df[losses_df["max_mfe_r"] >= 1.5])

    # 5. Régimen ADX
    win_trades = direct_closed[direct_closed["direct_result"] == "WIN"]
    loss_trades = direct_closed[direct_closed["direct_result"] == "LOSS"]
    mean_adx_win = round(float(win_trades["adx"].mean()), 1) if not win_trades.empty else 0.0
    mean_adx_loss = round(float(loss_trades["adx"].mean()), 1) if not loss_trades.empty else 0.0

    # 6. Filtros Específicos
    # Para BOOM: BUY vs SELL
    # Para CRASH: SELL vs BUY
    # Para FOREX/GOLD: Killzone vs Fuera de Killzone
    extra_filter_analysis = {}
    if family == "BOOM":
        buy_trades = direct_closed[direct_closed["direction"] == "BUY"]
        sell_trades = direct_closed[direct_closed["direction"] == "SELL"]
        extra_filter_analysis["BUY_only_WR"] = round(len(buy_trades[buy_trades["direct_result"] == "WIN"]) / len(buy_trades) * 100, 1) if len(buy_trades) > 0 else 0.0
        extra_filter_analysis["BUY_only_R"] = round(float(buy_trades["direct_realized_rr"].sum()), 2) if len(buy_trades) > 0 else 0.0
        extra_filter_analysis["SELL_only_WR"] = round(len(sell_trades[sell_trades["direct_result"] == "WIN"]) / len(sell_trades) * 100, 1) if len(sell_trades) > 0 else 0.0
        extra_filter_analysis["SELL_only_R"] = round(float(sell_trades["direct_realized_rr"].sum()), 2) if len(sell_trades) > 0 else 0.0
    elif family == "CRASH":
        sell_trades = direct_closed[direct_closed["direction"] == "SELL"]
        buy_trades = direct_closed[direct_closed["direction"] == "BUY"]
        extra_filter_analysis["SELL_only_WR"] = round(len(sell_trades[sell_trades["direct_result"] == "WIN"]) / len(sell_trades) * 100, 1) if len(sell_trades) > 0 else 0.0
        extra_filter_analysis["SELL_only_R"] = round(float(sell_trades["direct_realized_rr"].sum()), 2) if len(sell_trades) > 0 else 0.0
        extra_filter_analysis["BUY_only_WR"] = round(len(buy_trades[buy_trades["direct_result"] == "WIN"]) / len(buy_trades) * 100, 1) if len(buy_trades) > 0 else 0.0
        extra_filter_analysis["BUY_only_R"] = round(float(buy_trades["direct_realized_rr"].sum()), 2) if len(buy_trades) > 0 else 0.0
    elif family in ("FOREX", "GOLD"):
        kz_trades = direct_closed[direct_closed["is_killzone"] == True]
        nokz_trades = direct_closed[direct_closed["is_killzone"] == False]
        extra_filter_analysis["KZ_WR"] = round(len(kz_trades[kz_trades["direct_result"] == "WIN"]) / len(kz_trades) * 100, 1) if len(kz_trades) > 0 else 0.0
        extra_filter_analysis["KZ_R"] = round(float(kz_trades["direct_realized_rr"].sum()), 2) if len(kz_trades) > 0 else 0.0
        extra_filter_analysis["NO_KZ_WR"] = round(len(nokz_trades[nokz_trades["direct_result"] == "WIN"]) / len(nokz_trades) * 100, 1) if len(nokz_trades) > 0 else 0.0
        extra_filter_analysis["NO_KZ_R"] = round(float(nokz_trades["direct_realized_rr"].sum()), 2) if len(nokz_trades) > 0 else 0.0

    result_summary = {
        "symbol": symbol,
        "family": family,
        "direct": {
            "trades": direct_total,
            "wins": direct_wins,
            "losses": direct_losses,
            "win_rate": direct_wr,
            "total_r": direct_tot_r,
            "expectancy_r": direct_exp,
        },
        "with_be": {
            "trades": be_total,
            "wins": be_wins,
            "losses": be_losses,
            "break_evens": be_bes,
            "win_rate_excluding_be": be_wr,
            "total_r": be_tot_r,
            "expectancy_r": be_exp,
            "losses_saved_by_be": be_bes,
        },
        "asym_dual_leg": {
            "trades": asym_total,
            "wins": asym_wins,
            "losses": asym_losses,
            "break_evens": asym_bes,
            "win_rate": asym_wr,
            "total_r": asym_tot_r,
            "expectancy_r": asym_exp,
        },
        "mfe_loss_analysis": {
            "total_losses": len(losses_df),
            "reached_0_5r_before_loss": mfe_reached_05,
            "reached_1_0r_before_loss": mfe_reached_10,
            "reached_1_5r_before_loss": mfe_reached_15,
        },
        "regime_analysis": {
            "mean_adx_wins": mean_adx_win,
            "mean_adx_losses": mean_adx_loss,
        },
        "extra_filter_analysis": extra_filter_analysis,
        "trades": trade_records,
    }

    print(f"  [RESULTADOS {symbol}]")
    print(f"    Directo 1:2:      Trades={direct_total} | Wins={direct_wins} | Losses={direct_losses} | WR={direct_wr}% | Total R={direct_tot_r:+.2f}R | Exp={direct_exp:+.3f}R")
    print(f"    Con BE @ 1R:      Trades={be_total} | Wins={be_wins} | BE={be_bes} | Losses={be_losses} | Total R={be_tot_r:+.2f}R | Exp={be_exp:+.3f}R")
    print(f"    Doble Pierna 1:2.5: Trades={asym_total} | Wins={asym_wins} | Losses={asym_losses} | WR={asym_wr}% | Total R={asym_tot_r:+.2f}R | Exp={asym_exp:+.3f}R")
    if extra_filter_analysis:
        print(f"    Filtros Específicos: {extra_filter_analysis}")
    print(f"    Pérdidas con MFE >= 1.0R: {mfe_reached_10} de {len(losses_df)} ({round(mfe_reached_10/len(losses_df)*100, 1) if len(losses_df) > 0 else 0}%)")
    print(f"    ADX Promedio: Wins={mean_adx_win} vs Losses={mean_adx_loss}", flush=True)

    return result_summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Replay histórico BOOM, CRASH, FOREX, GOLD (1:2 RR)")
    parser.add_argument("--days", type=int, default=180, help="Días históricos (default: 180)")
    parser.add_argument("--family", type=str, default="ALL", help="Familia (BOOM, CRASH, FOREX, GOLD, ALL)")
    args = parser.parse_args()

    if not mt5.initialize():
        print("Error al inicializar MetaTrader 5:", mt5.last_error())
        sys.exit(1)

    print("=" * 85)
    print(f"REPLAY HISTÓRICO SMC 1:2 RR - BOOM, CRASH, FOREX, GOLD ({args.days} DÍAS / {args.days//30} MESES)")
    print("=" * 85)

    selected_families = {}
    if args.family.upper() == "ALL":
        selected_families = CORE_ASSETS
    elif args.family.upper() in CORE_ASSETS:
        selected_families = {args.family.upper(): CORE_ASSETS[args.family.upper()]}
    else:
        print(f"Familia desconocida: {args.family}")
        mt5.shutdown()
        sys.exit(1)

    all_results = {}
    all_trades = []
    asset_rows = []

    for fam, symbols in selected_families.items():
        print(f"\n=======================================================")
        print(f">>> INICIANDO FAMILIA {fam} ({len(symbols)} activos) <<<")
        print(f"=======================================================")
        for sym in symbols:
            res = analyze_asset_replay(sym, fam, days=args.days)
            if res:
                all_results[sym] = res
                trades = res.pop("trades", [])
                all_trades.extend(trades)

                d = res["direct"]
                b = res["with_be"]
                a = res["asym_dual_leg"]
                mfe = res["mfe_loss_analysis"]
                reg = res["regime_analysis"]

                asset_rows.append({
                    "family": fam,
                    "symbol": sym,
                    "direct_trades": d["trades"],
                    "direct_wins": d["wins"],
                    "direct_losses": d["losses"],
                    "direct_wr": d["win_rate"],
                    "direct_r": d["total_r"],
                    "direct_exp": d["expectancy_r"],
                    "be_trades": b["trades"],
                    "be_wins": b["wins"],
                    "be_bes": b["break_evens"],
                    "be_losses": b["losses"],
                    "be_r": b["total_r"],
                    "be_exp": b["expectancy_r"],
                    "asym_trades": a["trades"],
                    "asym_wins": a["wins"],
                    "asym_losses": a["losses"],
                    "asym_wr": a["win_rate"],
                    "asym_r": a["total_r"],
                    "asym_exp": a["expectancy_r"],
                    "losses_reaching_1r": mfe["reached_1_0r_before_loss"],
                    "total_losses": mfe["total_losses"],
                    "adx_wins": reg["mean_adx_wins"],
                    "adx_losses": reg["mean_adx_losses"],
                })

    mt5.shutdown()

    # Guardar resultados
    output_dir = PROJECT_ROOT / "storage" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"replay_boom_crash_forex_gold_{args.days}d_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        csv_path = output_dir / f"replay_boom_crash_forex_gold_{args.days}d_trades.csv"
        if csv_path.exists() and args.family.upper() != "ALL":
            try:
                prev_df = pd.read_csv(csv_path)
                curr_families = set(trades_df["family"].unique())
                retained_df = prev_df[~prev_df["family"].isin(curr_families)]
                trades_df = pd.concat([retained_df, trades_df], ignore_index=True)
            except Exception as e:
                print(f"Aviso al combinar CSV: {e}")
        trades_df.to_csv(csv_path, index=False)
        print(f"\nOperaciones guardadas en: {csv_path} (Total operaciones: {len(trades_df)})")

    if asset_rows:
        summary_df = pd.DataFrame(asset_rows)
        consolidated_csv = output_dir / f"consolidated_replay_boom_crash_forex_gold_{args.days}d.csv"
        if consolidated_csv.exists() and args.family.upper() != "ALL":
            try:
                prev_sum = pd.read_csv(consolidated_csv)
                curr_fams = set(summary_df["family"].unique())
                retained_sum = prev_sum[~prev_sum["family"].isin(curr_fams)]
                summary_df = pd.concat([retained_sum, summary_df], ignore_index=True)
            except Exception:
                pass
        summary_df.to_csv(consolidated_csv, index=False)

        print("\n" + "=" * 115)
        print("RESUMEN CONSOLIDADO POR ACTIVO - REPLAY SMC 1:2 RR (180 DÍAS)")
        print("=" * 115)
        print(f"{'FAMILIA':<10} | {'ACTIVO':<20} | {'TRADES':<6} | {'DIR WR':<7} | {'DIR R':<8} | {'BE R':<8} | {'ASYM R':<8} | {'ASYM WR':<7} | {'MFE>=1R'}")
        print("-" * 115)
        for _, r in summary_df.iterrows():
            mfe_str = f"{r['losses_reaching_1r']}/{r['total_losses']}"
            print(f"{r['family']:<10} | {r['symbol']:<20} | {r['direct_trades']:<6} | {r['direct_wr']:>5.1f}% | {r['direct_r']:>+7.2f}R | {r['be_r']:>+7.2f}R | {r['asym_r']:>+7.2f}R | {r['asym_wr']:>5.1f}% | {mfe_str:<8}")
        print("=" * 115)


if __name__ == "__main__":
    main()
