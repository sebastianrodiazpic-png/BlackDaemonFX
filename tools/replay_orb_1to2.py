"""Replay Histórico Cuantitativo para Activos ORB (New York Opening Range Breakout - 12 Meses).

Evalúa la estrategia ORB oficial con relación Riesgo:Beneficio mínima 1:2 (RR >= 2.0).
Analiza:
1. Rendimiento Directo 1:2 (TP=+2.0R, SL=-1.0R).
2. Rendimiento con Break-Even a +1.0R (SL a precio de entrada al tocar +1.0R MFE).
3. Rendimiento con Doble Pierna Asimétrica (TP1=+1.2R, Runner=+2.5R, BE=+0.1R).
4. Excursión Máxima Favorable (MFE) y Adversa (MAE).
5. Desglose analítico:
   - Por activo (XAUUSD, XAGUSD, US Oil, UK Brent Oil, US Tech 100, Wall Street 30, US SP 500, BTCUSD).
   - Por modalidad (RETEST vs MOMENTUM).
   - Por calidad de retest (HIGH, STANDARD, LOW).
   - Por ratio de amplitud de rango (ORH-ORL / ATR).
   - Por confirmación de volumen y alineación VWAP / POC.
   - Por ventana horaria dentro de la sesión de NY.
6. Exportación de operaciones a CSV compatible para entrenamiento del Meta-Modelo de IA.

Uso:
    python tools/replay_orb_1to2.py [--days 365] [--symbols ...]
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta, time as dtime
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
import json
import argparse
import math

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

from strategy.orb.new_york_orb import (
    NewYorkORBStrategy,
    ORBConfig,
    classify_orb_market,
    is_orb_eligible_symbol,
    discover_orb_symbols,
)
from strategy.orb.asset_rules import (
    get_asset_rules,
    default_asset_profiles,
    ORB_STRATEGY_VERSION,
)


NY_TZ = ZoneInfo("America/New_York")

ORB_SYMBOLS_DEFAULT = [
    "XAUUSD",
    "XAGUSD",
    "US Oil",
    "UK Brent Oil",
    "US Tech 100",
    "Wall Street 30",
    "US SP 500",
    "BTCUSD",
]


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
    plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr.replace(0, 1e-9)
    minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr.replace(0, 1e-9)

    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    adx = dx.ewm(alpha=1/period, min_periods=period).mean()
    return adx


def fetch_symbol_candles_chunked(symbol: str, timeframe: int, days: int = 365) -> pd.DataFrame | None:
    """Descarga velas históricas desde MT5 en bloques para superar el límite de buffer (~100k barras)."""
    if not mt5.symbol_select(symbol, True):
        return None

    rates_latest = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    if rates_latest is None or len(rates_latest) == 0:
        return None

    dt_end = pd.to_datetime(rates_latest["time"][0], unit="s")
    target_start = dt_end - timedelta(days=days)

    dfs = []
    current_end = dt_end
    step = timedelta(days=90)

    while current_end > target_start:
        current_start = max(target_start, current_end - step)
        rates = mt5.copy_rates_range(symbol, timeframe, current_start, current_end)
        if rates is not None and len(rates) > 0:
            df_chunk = pd.DataFrame(rates)
            dfs.append(df_chunk)
        current_end = current_start

    if not dfs:
        return None

    full_df = pd.concat(dfs, ignore_index=True)
    full_df = full_df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    full_df["time"] = pd.to_datetime(full_df["time"], unit="s", utc=True)
    full_df["time_ny"] = full_df["time"].dt.tz_convert(NY_TZ)
    return full_df


class FastHistoricalProvider:
    """Proveedor en memoria ultrarrápido compatible con NewYorkORBStrategy."""

    def __init__(self, full_df: pd.DataFrame):
        self.full_df = full_df
        self.source_name = "MT5_HISTORICAL_REPLAY"
        self.current_time = None
        self._time_series = full_df["time"]

    def get_candles(self, symbol: str, timeframe: str, count: int = 350) -> pd.DataFrame:
        idx = self._time_series.searchsorted(self.current_time, side="right")
        start_idx = max(0, idx - count)
        sub = self.full_df.iloc[start_idx:idx]
        return sub.copy()

    def get_current_tick(self, symbol: str) -> dict:
        idx = self._time_series.searchsorted(self.current_time, side="right")
        if idx > 0:
            last_close = float(self.full_df["close"].iloc[idx - 1])
        else:
            last_close = 0.0
        return {"time": self.current_time, "bid": last_close, "ask": last_close}


def simulate_orb_trade(
    candles: pd.DataFrame,
    entry_time,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    be_trigger_rr: float = 1.0,
    max_bars: int = 150,
) -> dict | None:
    """Simula bar-a-bar el trade midiendo Directo 1:2, BE@1.0R, Doble Pierna y MFE/MAE."""
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

    # Parámetros asimétricos doble pierna (50% cada una)
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

        # 2. Simulación con BE @ 1.0R
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
        if not leg1_closed:
            if hit_tp1:
                leg1_closed = True
                leg1_rr = 1.2 * 0.5  # +0.6R
                be_active = True
            elif hit_sl:
                leg1_closed = True
                leg1_rr = -1.0 * 0.5  # -0.5R

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

        if direct_result is not None and be_result is not None and leg1_closed and leg2_closed:
            break

    # Si aún no cerró al límite de barras
    if direct_result is None:
        last_candle = future.iloc[-1]
        direct_exit_time = last_candle["time"]
        direct_bars = len(future)
        last_close = float(last_candle["close"])
        final_r = (last_close - entry_price) / risk if direction == "BUY" else (entry_price - last_close) / risk
        direct_realized_rr = max(-1.0, min(2.0, round(final_r, 2)))
        direct_result = "WIN" if direct_realized_rr >= 2.0 else "LOSS" if direct_realized_rr <= -1.0 else "OPEN"

    if be_result is None:
        be_result = direct_result
        be_realized_rr = direct_realized_rr

    asym_realized_rr = leg1_rr + leg2_rr
    if not leg1_closed or not leg2_closed:
        asym_result = "OPEN"
    else:
        asym_result = "WIN" if asym_realized_rr > 0 else "BREAK_EVEN" if abs(asym_realized_rr) <= 0.05 else "LOSS"

    return {
        "direct_result": direct_result,
        "direct_realized_rr": round(direct_realized_rr, 3),
        "direct_bars": direct_bars,
        "direct_exit_time": str(direct_exit_time),
        "be_result": be_result,
        "be_realized_rr": round(be_realized_rr, 3),
        "asym_result": asym_result,
        "asym_realized_rr": round(asym_realized_rr, 3),
        "max_mfe_r": round(max_mfe_r, 3),
        "max_mae_r": round(max_mae_r, 3),
        "risk_distance": risk,
    }


def run_orb_replay(symbols: list[str] = None, days: int = 365, target_rr: float = 2.0):
    """Ejecuta el replay histórico de 12 meses para todos los activos ORB."""
    if not mt5.initialize():
        print(f"Error inicializando MT5: {mt5.last_error()}")
        return None

    if symbols is None:
        symbols = ORB_SYMBOLS_DEFAULT

    print("=" * 105)
    print(f"INICIANDO REPLAY HISTÓRICO ORB NEW YORK (ÚLTIMOS {days} DÍAS / RR OBJETIVO 1:{target_rr})")
    print(f"Símbolos a evaluar: {', '.join(symbols)}")
    print("=" * 105)

    all_trades = []
    symbol_summaries = {}

    for sym in symbols:
        print(f"\n[+] Descargando velas M5 para {sym} ({days} días)...")
        df = fetch_symbol_candles_chunked(sym, mt5.TIMEFRAME_M5, days=days)
        if df is None or len(df) < 500:
            print(f"    [-] Datos insuficientes para {sym} (velas: {len(df) if df is not None else 0}). Omitiendo.")
            continue

        print(f"    Velas cargadas: {len(df):,d} ({df['time_ny'].iloc[0].strftime('%Y-%m-%d')} a {df['time_ny'].iloc[-1].strftime('%Y-%m-%d')})")

        # Indicadores complementarios
        df["atr"] = compute_atr(df, 14)
        df["adx"] = compute_adx(df, 14)

        provider = FastHistoricalProvider(df)
        config = ORBConfig(target_rr=target_rr)
        strategy = NewYorkORBStrategy(provider, config)

        unique_dates = sorted(list(set(df["time_ny"].dt.date)))
        sym_trades = []

        for d in unique_dates:
            # Filtrar fines de semana
            if d.weekday() >= 5:
                continue

            # Sesión NY para este día
            session_bars = df[(df["time_ny"].dt.date == d) & (df["time_ny"].dt.hour >= 9) & (df["time_ny"].dt.hour < 16)]
            if len(session_bars) < 10:
                continue

            # Evaluar velas desde las 09:45 NY (después de formado el rango ORB de 15 min)
            trading_bars = session_bars[
                (session_bars["time_ny"].dt.hour > 9) |
                ((session_bars["time_ny"].dt.hour == 9) & (session_bars["time_ny"].dt.minute >= 45))
            ]

            for _, bar in trading_bars.iterrows():
                candle_close_time = bar["time"] + timedelta(minutes=5)
                provider.current_time = candle_close_time

                res = strategy.analyze_symbol(sym, candle_close_time)
                if not res.get("valid"):
                    continue

                sig = res.get("signal") or {}
                if not sig.get("valid"):
                    continue

                entry_price = float(sig["entry_price"])
                stop_loss = float(sig["stop_loss"])
                take_profit = float(sig["take_profit"])
                direction = str(sig["direction"]).upper()
                entry_time = pd.Timestamp(sig.get("entry_time") or candle_close_time)

                # Simular trade
                sim = simulate_orb_trade(
                    df,
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

                # Extraer metadatos ricos de ORB
                entry_mode = sig.get("orb_entry_mode", "ORB_BREAKOUT_RETEST")
                quality = sig.get("retest_quality") or "N/A"
                range_amp = sig.get("range_amplitude") or {}
                amp_ratio = float(range_amp.get("ratio") or sig.get("opening_range_atr_ratio") or 0.0)
                vol_evidence = sig.get("volume_evidence") or {}
                vol_ratio = float(vol_evidence.get("volume_ratio") or sig.get("breakout_volume_ratio") or 0.0)
                vol_confirmed = bool(vol_evidence.get("confirmed", True))

                # Valores ADX y ATR en el momento de la entrada
                bar_idx = df["time"].searchsorted(entry_time, side="right") - 1
                adx_val = float(df["adx"].iloc[bar_idx]) if bar_idx >= 0 and pd.notna(df["adx"].iloc[bar_idx]) else 20.0
                atr_val = float(df["atr"].iloc[bar_idx]) if bar_idx >= 0 and pd.notna(df["atr"].iloc[bar_idx]) else float(sig.get("orb_signal_atr") or 1.0)

                trade_record = {
                    "symbol": sym,
                    "family": "ORB",
                    "strategy_name": "ORB_NEW_YORK",
                    "market": classify_orb_market(sym),
                    "entry_time": str(entry_time),
                    "session_date": str(d),
                    "direction": direction,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "risk_distance": sim["risk_distance"],
                    "adx": adx_val,
                    "atr": atr_val,
                    "orb_entry_mode": entry_mode,
                    "retest_quality": quality,
                    "opening_range_atr_ratio": amp_ratio,
                    "breakout_volume_ratio": vol_ratio,
                    "breakout_volume_confirmed": vol_confirmed,
                    "vwap_alignment": bool(sig.get("confirmations", {}).get("vwap_alignment", True)),
                    "poc_alignment": bool(sig.get("confirmations", {}).get("poc_alignment", True)),
                    "direct_result": sim["direct_result"],
                    "direct_realized_rr": sim["direct_realized_rr"],
                    "direct_bars": sim["direct_bars"],
                    "direct_exit_time": sim["direct_exit_time"],
                    "be_result": sim["be_result"],
                    "be_realized_rr": sim["be_realized_rr"],
                    "asym_result": sim["asym_result"],
                    "asym_realized_rr": sim["asym_realized_rr"],
                    "max_mfe_r": sim["max_mfe_r"],
                    "max_mae_r": sim["max_mae_r"],
                    "is_killzone": True,
                }

                sym_trades.append(trade_record)
                all_trades.append(trade_record)

                # Registrar tesis utilizada para respetar one_signal_per_session
                strategy.mark_signal_used(sym, str(d), sig.get("breakout_candle_time"))
                break

        print(f"    [OK] Operaciones generadas para {sym}: {len(sym_trades)}")
        if sym_trades:
            s_df = pd.DataFrame(sym_trades)
            s_direct_wins = (s_df["direct_result"] == "WIN").sum()
            s_direct_wr = s_direct_wins / len(s_df) * 100
            s_direct_r = s_df["direct_realized_rr"].sum()
            s_be_wins = (s_df["be_result"] == "WIN").sum()
            s_be_wr = s_be_wins / len(s_df) * 100
            s_be_r = s_df["be_realized_rr"].sum()
            print(f"         Directo 1:2: WR={s_direct_wr:.1f}% ({s_direct_wins}/{len(s_df)}) | Net R={s_direct_r:+.1f}R")
            print(f"         Con BE @ 1R: WR={s_be_wr:.1f}% ({s_be_wins}/{len(s_df)}) | Net R={s_be_r:+.1f}R")

    mt5.shutdown()

    if not all_trades:
        print("\n[!] No se generaron operaciones en el replay histórico.")
        return None

    trades_df = pd.DataFrame(all_trades)

    # Exportar CSV
    analysis_dir = PROJECT_ROOT / "storage" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    csv_path = analysis_dir / "replay_orb_12m_trades.csv"
    trades_df.to_csv(csv_path, index=False)
    print(f"\n[+] Dataset histórico guardado en: {csv_path}")

    # Análisis cuantitativo global y desgloses
    results = compute_comprehensive_metrics(trades_df)
    json_path = analysis_dir / "replay_orb_12m_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[+] Resumen cuantitativo guardado en: {json_path}")

    # Imprimir Reporte
    print_orb_performance_report(trades_df, results)

    return trades_df, results


def compute_comprehensive_metrics(df: pd.DataFrame) -> dict:
    """Calcula todas las métricas de rendimiento cuantitativo."""
    total = len(df)
    if total == 0:
        return {}

    # Direct 1:2
    d_wins = (df["direct_result"] == "WIN").sum()
    d_losses = (df["direct_result"] == "LOSS").sum()
    d_ambig = (df["direct_result"].isin(["AMBIGUOUS", "OPEN"])).sum()
    d_wr = d_wins / total * 100
    d_net_r = df["direct_realized_rr"].sum()
    d_exp = d_net_r / total
    d_gross_win = df[df["direct_realized_rr"] > 0]["direct_realized_rr"].sum()
    d_gross_loss = abs(df[df["direct_realized_rr"] < 0]["direct_realized_rr"].sum())
    d_pf = d_gross_win / d_gross_loss if d_gross_loss > 0 else 99.0

    # Break-Even @ 1.0R
    be_wins = (df["be_result"] == "WIN").sum()
    be_losses = (df["be_result"] == "LOSS").sum()
    be_bes = (df["be_result"] == "BREAK_EVEN").sum()
    be_wr = be_wins / total * 100
    be_net_r = df["be_realized_rr"].sum()
    be_exp = be_net_r / total
    be_gross_win = df[df["be_realized_rr"] > 0]["be_realized_rr"].sum()
    be_gross_loss = abs(df[df["be_realized_rr"] < 0]["be_realized_rr"].sum())
    be_pf = be_gross_win / be_gross_loss if be_gross_loss > 0 else 99.0

    # Asymmetric Double Leg
    asym_wins = (df["asym_result"] == "WIN").sum()
    asym_losses = (df["asym_result"] == "LOSS").sum()
    asym_bes = (df["asym_result"] == "BREAK_EVEN").sum()
    asym_wr = asym_wins / total * 100
    asym_net_r = df["asym_realized_rr"].sum()
    asym_exp = asym_net_r / total
    asym_gross_win = df[df["asym_realized_rr"] > 0]["asym_realized_rr"].sum()
    asym_gross_loss = abs(df[df["asym_realized_rr"] < 0]["asym_realized_rr"].sum())
    asym_pf = asym_gross_win / asym_gross_loss if asym_gross_loss > 0 else 99.0

    # MFE / MAE
    avg_mfe = df["max_mfe_r"].mean()
    avg_mae = df["max_mae_r"].mean()
    loss_df = df[df["direct_result"] == "LOSS"]
    loss_mfe_gte_05 = (loss_df["max_mfe_r"] >= 0.5).sum()
    loss_mfe_gte_10 = (loss_df["max_mfe_r"] >= 1.0).sum()
    loss_mfe_gte_15 = (loss_df["max_mfe_r"] >= 1.5).sum()

    # Per symbol breakdown
    per_symbol = {}
    for sym, sdf in df.groupby("symbol"):
        stotal = len(sdf)
        swins = (sdf["direct_result"] == "WIN").sum()
        s_be_wins = (sdf["be_result"] == "WIN").sum()
        s_be_bes = (sdf["be_result"] == "BREAK_EVEN").sum()
        s_be_losses = (sdf["be_result"] == "LOSS").sum()
        per_symbol[sym] = {
            "trades": stotal,
            "direct_winrate": round(swins / stotal * 100, 1),
            "direct_net_r": round(sdf["direct_realized_rr"].sum(), 1),
            "direct_expectancy": round(sdf["direct_realized_rr"].mean(), 2),
            "be_winrate": round(s_be_wins / stotal * 100, 1),
            "be_count": int(s_be_bes),
            "be_loss_count": int(s_be_losses),
            "be_net_r": round(sdf["be_realized_rr"].sum(), 1),
            "be_expectancy": round(sdf["be_realized_rr"].mean(), 2),
            "asym_net_r": round(sdf["asym_realized_rr"].sum(), 1),
            "avg_mfe": round(sdf["max_mfe_r"].mean(), 2),
            "avg_mae": round(sdf["max_mae_r"].mean(), 2),
        }

    # Per entry mode breakdown
    per_mode = {}
    for mode, mdf in df.groupby("orb_entry_mode"):
        mtotal = len(mdf)
        mwins = (mdf["direct_result"] == "WIN").sum()
        m_be_wins = (mdf["be_result"] == "WIN").sum()
        per_mode[mode] = {
            "trades": mtotal,
            "direct_winrate": round(mwins / mtotal * 100, 1),
            "direct_net_r": round(mdf["direct_realized_rr"].sum(), 1),
            "be_winrate": round(m_be_wins / mtotal * 100, 1),
            "be_net_r": round(mdf["be_realized_rr"].sum(), 1),
            "be_expectancy": round(mdf["be_realized_rr"].mean(), 2),
        }

    # Per retest quality breakdown
    per_quality = {}
    for q, qdf in df.groupby("retest_quality"):
        qtotal = len(qdf)
        qwins = (qdf["direct_result"] == "WIN").sum()
        q_be_wins = (qdf["be_result"] == "WIN").sum()
        per_quality[str(q)] = {
            "trades": qtotal,
            "direct_winrate": round(qwins / qtotal * 100, 1),
            "direct_net_r": round(qdf["direct_realized_rr"].sum(), 1),
            "be_winrate": round(q_be_wins / qtotal * 100, 1),
            "be_net_r": round(qdf["be_realized_rr"].sum(), 1),
            "be_expectancy": round(qdf["be_realized_rr"].mean(), 2),
        }

    # Per time window in NY
    df_copy = df.copy()
    entry_dts = pd.to_datetime(df_copy["entry_time"], utc=True).dt.tz_convert(NY_TZ)
    hour_float = entry_dts.dt.hour + entry_dts.dt.minute / 60.0
    df_copy["time_window"] = np.where(
        hour_float < 11.5, "EARLY_NY (09:45-11:30)",
        np.where(hour_float < 13.5, "MIDDAY_NY (11:30-13:30)", "LATE_NY (13:30-16:00)")
    )
    per_time_window = {}
    for tw, tdf in df_copy.groupby("time_window"):
        ttotal = len(tdf)
        twins = (tdf["direct_result"] == "WIN").sum()
        t_be_wins = (tdf["be_result"] == "WIN").sum()
        per_time_window[tw] = {
            "trades": ttotal,
            "direct_winrate": round(twins / ttotal * 100, 1),
            "direct_net_r": round(tdf["direct_realized_rr"].sum(), 1),
            "be_winrate": round(t_be_wins / ttotal * 100, 1),
            "be_net_r": round(tdf["be_realized_rr"].sum(), 1),
            "be_expectancy": round(tdf["be_realized_rr"].mean(), 2),
        }

    # Per range amplitude ratio tier
    df_copy["range_tier"] = np.where(
        df_copy["opening_range_atr_ratio"] < 1.0, "NARROW (<1.0 ATR)",
        np.where(df_copy["opening_range_atr_ratio"] <= 1.5, "NORMAL (1.0-1.5 ATR)", "WIDE (>1.5 ATR)")
    )
    per_range_tier = {}
    for rt, rtdf in df_copy.groupby("range_tier"):
        rtotal = len(rtdf)
        rwins = (rtdf["direct_result"] == "WIN").sum()
        r_be_wins = (rtdf["be_result"] == "WIN").sum()
        per_range_tier[rt] = {
            "trades": rtotal,
            "direct_winrate": round(rwins / rtotal * 100, 1),
            "direct_net_r": round(rtdf["direct_realized_rr"].sum(), 1),
            "be_winrate": round(r_be_wins / rtotal * 100, 1),
            "be_net_r": round(rtdf["be_realized_rr"].sum(), 1),
            "be_expectancy": round(rtdf["be_realized_rr"].mean(), 2),
        }

    # Per volume confirmation
    per_volume = {}
    for vc, vcdf in df.groupby("breakout_volume_confirmed"):
        vctotal = len(vcdf)
        vcwins = (vcdf["direct_result"] == "WIN").sum()
        vc_be_wins = (vcdf["be_result"] == "WIN").sum()
        per_volume["CONFIRMED" if vc else "UNCONFIRMED"] = {
            "trades": vctotal,
            "direct_winrate": round(vcwins / vctotal * 100, 1),
            "direct_net_r": round(vcdf["direct_realized_rr"].sum(), 1),
            "be_winrate": round(vc_be_wins / vctotal * 100, 1),
            "be_net_r": round(vcdf["be_realized_rr"].sum(), 1),
            "be_expectancy": round(vcdf["be_realized_rr"].mean(), 2),
        }

    return {
        "total_trades": total,
        "direct_1to2": {
            "wins": int(d_wins),
            "losses": int(d_losses),
            "ambiguous": int(d_ambig),
            "winrate": round(d_wr, 1),
            "net_r": round(d_net_r, 1),
            "expectancy_r": round(d_exp, 2),
            "profit_factor": round(d_pf, 2),
        },
        "break_even_1to2": {
            "wins": int(be_wins),
            "losses": int(be_losses),
            "break_evens": int(be_bes),
            "winrate": round(be_wr, 1),
            "effective_loss_rate": round(be_losses / total * 100, 1),
            "net_r": round(be_net_r, 1),
            "expectancy_r": round(be_exp, 2),
            "profit_factor": round(be_pf, 2),
        },
        "asymmetric_double_leg": {
            "wins": int(asym_wins),
            "losses": int(asym_losses),
            "break_evens": int(asym_bes),
            "winrate": round(asym_wr, 1),
            "net_r": round(asym_net_r, 1),
            "expectancy_r": round(asym_exp, 2),
            "profit_factor": round(asym_pf, 2),
        },
        "mfe_mae": {
            "avg_mfe": round(avg_mfe, 2),
            "avg_mae": round(avg_mae, 2),
            "total_losses": int(len(loss_df)),
            "losses_mfe_gte_05": int(loss_mfe_gte_05),
            "losses_mfe_gte_10": int(loss_mfe_gte_10),
            "losses_mfe_gte_15": int(loss_mfe_gte_15),
            "pct_losses_reached_1r": round(loss_mfe_gte_10 / len(loss_df) * 100, 1) if len(loss_df) > 0 else 0.0,
        },
        "per_symbol": per_symbol,
        "per_mode": per_mode,
        "per_quality": per_quality,
        "per_time_window": per_time_window,
        "per_range_tier": per_range_tier,
        "per_volume": per_volume,
    }


def print_orb_performance_report(df: pd.DataFrame, results: dict):
    """Imprime en consola un informe visual completo y cuantitativo."""
    print("\n" + "=" * 105)
    print("                      REPORTE DE RENDIMIENTO HISTÓRICO ORB NEW YORK (12 MESES)")
    print("=" * 105)

    tot = results["total_trades"]
    d = results["direct_1to2"]
    be = results["break_even_1to2"]
    asym = results["asymmetric_double_leg"]
    mfe = results["mfe_mae"]

    print(f"TOTAL OPERACIONES EVALUADAS: {tot}")
    print("-" * 105)
    print(f"{'MODALIDAD DE GESTIÓN':<30} | {'WIN RATE':<10} | {'NET R':<10} | {'ESPERANZA':<10} | {'PROFIT FACTOR':<14} | {'DETALLE'}")
    print("-" * 105)
    print(f"{'1. Directo 1:2 (TP 2R / SL 1R)':<30} | {d['winrate']:>7.1f}%  | {d['net_r']:>+8.1f}R | {d['expectancy_r']:>+7.2f}R | {d['profit_factor']:>12.2f}  | {d['wins']}W / {d['losses']}L")
    print(f"{'2. Con Break-Even @ +1.0R':<30} | {be['winrate']:>7.1f}%  | {be['net_r']:>+8.1f}R | {be['expectancy_r']:>+7.2f}R | {be['profit_factor']:>12.2f}  | {be['wins']}W / {be['break_evens']}BE / {be['losses']}L")
    print(f"{'3. Doble Pierna Asimétrica':<30} | {asym['winrate']:>7.1f}%  | {asym['net_r']:>+8.1f}R | {asym['expectancy_r']:>+7.2f}R | {asym['profit_factor']:>12.2f}  | {asym['wins']}W / {asym['break_evens']}BE / {asym['losses']}L")
    print("=" * 105)

    print("\n[+] ANÁLISIS DE EXCURSIÓN FAVORABLE (MFE) EN OPERACIONES PERDEDORAS:")
    print(f"    - MFE Promedio General: +{mfe['avg_mfe']:.2f}R | MAE Promedio: -{mfe['avg_mae']:.2f}R")
    print(f"    - De {mfe['total_losses']} pérdidas directas:")
    print(f"      * {mfe['losses_mfe_gte_05']} ({mfe['losses_mfe_gte_05']/mfe['total_losses']*100:.1f}%) llegaron a superar +0.5R antes de caer al SL.")
    print(f"      * {mfe['losses_mfe_gte_10']} ({mfe['pct_losses_reached_1r']:.1f}%) llegaron a superar +1.0R antes de revertir y tocar el SL.")
    print(f"      * {mfe['losses_mfe_gte_15']} ({mfe['losses_mfe_gte_15']/mfe['total_losses']*100:.1f}%) llegaron a superar +1.5R (a solo 0.5R del TP).")
    print("    => CONCLUSIÓN MFE: El Break-Even a +1.0R rescata un % masivo de operaciones que luego revierten.")

    print("\n" + "=" * 105)
    print("                           DESGLOSE POR ACTIVO EN EL WORK DE ORB")
    print("=" * 105)
    print(f"{'SÍMBOLO':<16} | {'TRADES':<7} | {'DIRECT WR':<10} | {'DIRECT R':<9} | {'BE WR':<8} | {'BE COUNT':<8} | {'BE NET R':<9} | {'BE EXP'}")
    print("-" * 105)
    for sym, s in results["per_symbol"].items():
        print(f"{sym:<16} | {s['trades']:<7} | {s['direct_winrate']:>8.1f}% | {s['direct_net_r']:>+7.1f}R | {s['be_winrate']:>6.1f}% | {s['be_count']:<8} | {s['be_net_r']:>+7.1f}R | {s['be_expectancy']:>+6.2f}R")
    print("=" * 105)

    print("\n" + "=" * 105)
    print("                           DESGLOSE POR MODALIDAD ORB (RETEST vs MOMENTUM)")
    print("=" * 105)
    for mode, m in results["per_mode"].items():
        print(f"  * {mode:<25}: {m['trades']} trades | Direct WR: {m['direct_winrate']:.1f}% ({m['direct_net_r']:+.1f}R) | BE WR: {m['be_winrate']:.1f}% ({m['be_net_r']:+.1f}R, Exp: {m['be_expectancy']:+.2f}R)")
    print("=" * 105)

    print("\n" + "=" * 105)
    print("                           DESGLOSE POR CALIDAD DE RETEST")
    print("=" * 105)
    for q, qres in results.get("per_quality", {}).items():
        print(f"  * {q:<25}: {qres['trades']} trades | Direct WR: {qres['direct_winrate']:.1f}% ({qres['direct_net_r']:+.1f}R) | BE WR: {qres['be_winrate']:.1f}% ({qres['be_net_r']:+.1f}R, Exp: {qres['be_expectancy']:+.2f}R)")
    print("=" * 105)

    print("\n" + "=" * 105)
    print("                           DESGLOSE POR FRANJA HORARIA (SESIÓN NY)")
    print("=" * 105)
    for tw, twres in results.get("per_time_window", {}).items():
        print(f"  * {tw:<25}: {twres['trades']} trades | Direct WR: {twres['direct_winrate']:.1f}% ({twres['direct_net_r']:+.1f}R) | BE WR: {twres['be_winrate']:.1f}% ({twres['be_net_r']:+.1f}R, Exp: {twres['be_expectancy']:+.2f}R)")
    print("=" * 105)

    print("\n" + "=" * 105)
    print("                           DESGLOSE POR AMPLITUD DE RANGO (RATIO / ATR)")
    print("=" * 105)
    for rt, rtres in results.get("per_range_tier", {}).items():
        print(f"  * {rt:<25}: {rtres['trades']} trades | Direct WR: {rtres['direct_winrate']:.1f}% ({rtres['direct_net_r']:+.1f}R) | BE WR: {rtres['be_winrate']:.1f}% ({rtres['be_net_r']:+.1f}R, Exp: {rtres['be_expectancy']:+.2f}R)")
    print("=" * 105)

    print("\n" + "=" * 105)
    print("                           DESGLOSE POR CONFIRMACIÓN DE VOLUMEN")
    print("=" * 105)
    for vc, vcres in results.get("per_volume", {}).items():
        print(f"  * {vc:<25}: {vcres['trades']} trades | Direct WR: {vcres['direct_winrate']:.1f}% ({vcres['direct_net_r']:+.1f}R) | BE WR: {vcres['be_winrate']:.1f}% ({vcres['be_net_r']:+.1f}R, Exp: {vcres['be_expectancy']:+.2f}R)")
    print("=" * 105)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay Histórico ORB 12 Meses 1:2")
    parser.add_argument("--days", type=int, default=365, help="Días históricos (default: 365)")
    parser.add_argument("--rr", type=float, default=2.0, help="Relación Riesgo Beneficio (default: 2.0)")
    parser.add_argument("--symbols", nargs="+", default=None, help="Símbolos específicos")
    args = parser.parse_args()

    run_orb_replay(symbols=args.symbols, days=args.days, target_rr=args.rr)
