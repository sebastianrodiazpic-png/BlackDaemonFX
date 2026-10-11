"""Replay Histórico Cuantitativo - Estrategia ORB (2 Entradas / Gestión Asimétrica).

Implementa la estrategia ORB :
1. Rango de apertura de Nueva York (09:30 - 09:45 NY, 15 minutos / 3 velas M5).
2. Niveles clave: ORH, ORL y 50% Equilibrium (Midpoint).
3. Stop Loss estructural al 50% del ORB.
4. Gestión de Riesgo (1.0% total dividido en 2 entradas al 0.5% cada una):
   - Entrada 1 (Pierna 1 - 0.5% riesgo): Cierra en TP1 (1:1 / 1.0R de proyección).
   - Entrada 2 (Pierna 2 - 0.5% riesgo): Al tocar TP1, su SL se mueve a Break-Even (precio de entrada).
     Continúa buscando TP2 (2:1 / 2.0R de proyección).
5. Instrumentos evaluados:
   - Índices: US30 (Wall Street 30), NAS100 (US Tech 100), SPX500 (US SP 500).
   - Materias Primas: XAUUSD (Oro), XAGUSD (Plata), US Oil (Petróleo WTI).
   - Divisas: EURUSD (Euro/Dólar).
   - Cripto: BTCUSD (Bitcoin).
6. Comparativas de rendimiento:
   - Sistema Núñez 2-Leg (TP1 1:1, TP2 1:2 con BE).
   - Sistema Núñez Asimétrico (TP1 1.2R, TP2 2.5R con BE).
   - Sistema Directo 1:2 (1 posición al 1.0% fija).
   - Sistema Directo 1:1 (1 posición al 1.0% fija - Regla del 70%).
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import json
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
)
from strategy.orb.asset_rules import default_asset_profiles


NY_TZ = ZoneInfo("America/New_York")

SYMBOLS_TO_EVALUATE = [
    "Wall Street 30",  # US30
    "US Tech 100",     # NAS100
    "US SP 500",       # SPX500
    "XAUUSD",          # Oro
    "XAGUSD",          # Plata
    "US Oil",          # Petróleo WTI
    "EURUSD",          # Euro / Dólar
    "BTCUSD",          # Bitcoin
]


def fetch_symbol_candles_chunked(symbol: str, timeframe: int, days: int = 730) -> pd.DataFrame | None:
    """Descarga el máximo de velas M5 históricas desde MT5 en bloques de 90 días."""
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


def simulate_nunez_dual_trade(
    candles: pd.DataFrame,
    entry_time,
    direction: str,
    entry_price: float,
    stop_loss: float,
    max_bars: int = 150,
) -> dict | None:
    """Simula barra a barra el modelo exacto de benchmarks.

    Reglas Núñez 2-Leg:
    - Riesgo total: 1.0% (Pierna 1 = 0.5%, Pierna 2 = 0.5%).
    - SL inicial al 50% del ORB.
    - TP1 a 1.0R (distancia del riesgo). Pierna 1 cierra al 100%.
    - Al tocar TP1, Pierna 2 pasa su SL a Break-Even (entry_price).
    - Pierna 2 busca TP2 a 2.0R (distancia 2.0 * riesgo).
    """
    direction = str(direction).upper()
    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    risk = abs(entry_price - stop_loss)
    if risk <= 1e-9:
        return None

    future = candles[candles["time"] > entry_time].head(max_bars)
    if future.empty:
        return None

    # Niveles exactos Núñez
    sign = 1.0 if direction == "BUY" else -1.0
    tp1_price = entry_price + sign * 1.0 * risk   # 1:1
    tp2_price = entry_price + sign * 2.0 * risk   # 1:2
    be_price = entry_price                        # Break Even exacto

    # Niveles variante asimétrica alternativa (1.2R y 2.5R)
    alt_tp1_price = entry_price + sign * 1.2 * risk
    alt_tp2_price = entry_price + sign * 2.5 * risk

    # Estado Núñez 2-Leg (0.5% c/u)
    leg1_status = "OPEN"  # "WIN_TP1", "LOSS"
    leg2_status = "OPEN"  # "WIN_TP2", "BREAK_EVEN", "LOSS"
    leg1_return_r = 0.0   # en múltiplos de R total (0.5R max)
    leg2_return_r = 0.0   # en múltiplos de R total (1.0R max)
    leg2_be_active = False

    # Estado Directo 1:2 (100% posición)
    direct_1to2_status = None
    direct_1to2_r = 0.0

    # Estado Directo 1:1 (100% posición)
    direct_1to1_status = None
    direct_1to1_r = 0.0

    max_mfe_r = 0.0
    max_mae_r = 0.0
    exit_bars = 0
    exit_time = None

    for bar_num, (_, candle) in enumerate(future.iterrows(), start=1):
        high = float(candle["high"])
        low = float(candle["low"])
        c_time = candle["time"]

        # Medición MFE / MAE
        if direction == "BUY":
            bar_mfe = (high - entry_price) / risk
            bar_mae = (entry_price - low) / risk
            hit_initial_sl = low <= stop_loss
            hit_tp1 = high >= tp1_price
            hit_tp2 = high >= tp2_price
            hit_be = leg2_be_active and (low <= be_price)
        else:
            bar_mfe = (entry_price - low) / risk
            bar_mae = (high - entry_price) / risk
            hit_initial_sl = high >= stop_loss
            hit_tp1 = low <= tp1_price
            hit_tp2 = low <= tp2_price
            hit_be = leg2_be_active and (high >= be_price)

        max_mfe_r = max(max_mfe_r, bar_mfe)
        max_mae_r = max(max_mae_r, bar_mae)

        # ----------------------------------------------------
        # 1. Simulación Directa 1:1
        # ----------------------------------------------------
        if direct_1to1_status is None:
            if hit_initial_sl and hit_tp1:
                # Caso ambiguo en misma barra: conservadoramente pérdida
                direct_1to1_status = "LOSS"
                direct_1to1_r = -1.0
            elif hit_initial_sl:
                direct_1to1_status = "LOSS"
                direct_1to1_r = -1.0
            elif hit_tp1:
                direct_1to1_status = "WIN"
                direct_1to1_r = 1.0

        # ----------------------------------------------------
        # 2. Simulación Directa 1:2
        # ----------------------------------------------------
        if direct_1to2_status is None:
            if hit_initial_sl and hit_tp2:
                direct_1to2_status = "LOSS"
                direct_1to2_r = -1.0
            elif hit_initial_sl:
                direct_1to2_status = "LOSS"
                direct_1to2_r = -1.0
            elif hit_tp2:
                direct_1to2_status = "WIN"
                direct_1to2_r = 2.0

        # ----------------------------------------------------
        # 3. Simulación Núñez 2-Leg (0.5% + 0.5% = 1.0% total)
        # ----------------------------------------------------
        # Pierna 1
        if leg1_status == "OPEN":
            if hit_initial_sl and hit_tp1:
                # Ambiguo: conservador
                leg1_status = "LOSS"
                leg1_return_r = -0.5
                leg2_status = "LOSS"
                leg2_return_r = -0.5
            elif hit_initial_sl:
                leg1_status = "LOSS"
                leg1_return_r = -0.5
                leg2_status = "LOSS"
                leg2_return_r = -0.5
            elif hit_tp1:
                leg1_status = "WIN_TP1"
                leg1_return_r = 0.5  # +1.0R en su 50% de asignación = +0.5R neto
                leg2_be_active = True

        # Pierna 2 (si no cayó en SL inicial)
        if leg2_status == "OPEN":
            if leg2_be_active:
                if hit_tp2:
                    leg2_status = "WIN_TP2"
                    leg2_return_r = 1.0  # +2.0R en su 50% de asignación = +1.0R neto
                elif hit_be:
                    leg2_status = "BREAK_EVEN"
                    leg2_return_r = 0.0
            else:
                if hit_initial_sl:
                    leg2_status = "LOSS"
                    leg2_return_r = -0.5

        if leg1_status != "OPEN" and leg2_status != "OPEN" and direct_1to1_status is not None and direct_1to2_status is not None:
            exit_bars = bar_num
            exit_time = c_time
            break

    # Si terminó la ventana y no cerró
    if leg1_status == "OPEN":
        last_close = float(future.iloc[-1]["close"])
        final_r = sign * (last_close - entry_price) / risk
        leg1_status = "TIMEOUT"
        leg1_return_r = round(max(-0.5, min(0.5, final_r * 0.5)), 3)
    if leg2_status == "OPEN":
        last_close = float(future.iloc[-1]["close"])
        final_r = sign * (last_close - entry_price) / risk
        leg2_status = "TIMEOUT"
        leg2_return_r = round(max(-0.5, min(1.0, final_r * 0.5)), 3)
    if direct_1to1_status is None:
        direct_1to1_status = "TIMEOUT"
        direct_1to1_r = 0.0
    if direct_1to2_status is None:
        direct_1to2_status = "TIMEOUT"
        direct_1to2_r = 0.0

    total_nunez_r = round(leg1_return_r + leg2_return_r, 3)
    total_nunez_capital_pct = total_nunez_r  # Porque 1.0R = 1.0% del capital de la cuenta

    if leg1_status == "WIN_TP1" and leg2_status == "WIN_TP2":
        nunez_outcome = "FULL_WIN (+1.5%)"
    elif leg1_status == "WIN_TP1" and leg2_status == "BREAK_EVEN":
        nunez_outcome = "PARTIAL_WIN_BE (+0.5%)"
    elif leg1_status == "LOSS" and leg2_status == "LOSS":
        nunez_outcome = "FULL_LOSS (-1.0%)"
    else:
        nunez_outcome = f"OTHER ({total_nunez_r:+.2f}R)"

    return {
        "nunez_outcome": nunez_outcome,
        "nunez_net_r": total_nunez_r,
        "nunez_net_capital_pct": total_nunez_capital_pct,
        "leg1_status": leg1_status,
        "leg1_return_r": leg1_return_r,
        "leg2_status": leg2_status,
        "leg2_return_r": leg2_return_r,
        "direct_1to1_status": direct_1to1_status,
        "direct_1to1_r": direct_1to1_r,
        "direct_1to2_status": direct_1to2_status,
        "direct_1to2_r": direct_1to2_r,
        "max_mfe_r": round(max_mfe_r, 3),
        "max_mae_r": round(max_mae_r, 3),
        "risk_distance": risk,
        "exit_bars": exit_bars or len(future),
        "exit_time": str(exit_time or future.iloc[-1]["time"]),
    }


def run_comprehensive_nunez_replay(days: int = 730):
    """Ejecuta el replay histórico completo de ORB"""
    if not mt5.initialize():
        print(f"Error inicializando MT5: {mt5.last_error()}")
        return None

    print("=" * 110)
    print(" INICIANDO REPLAY HISTÓRICO: ESTRATEGIA ORB (MODELO 2 ENTRADAS AL 0.5%)")
    print(f" Periodo: Hasta {days} días (Máximo histórico M5 disponible en broker)")
    print(f" Instrumentos: {', '.join(SYMBOLS_TO_EVALUATE)}")
    print("=" * 110)

    # Perfiles con EURUSD y USOIL autorizados para el replay
    custom_profiles = default_asset_profiles()
    custom_profiles["EURUSD"] = dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False)
    custom_profiles["USOIL"] = dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.07, max_range_atr_ratio=2.0, require_volume=False)

    all_trades = []
    symbol_stats = {}

    for sym in SYMBOLS_TO_EVALUATE:
        print(f"\n[+] Cargando velas M5 para {sym}...")
        df = fetch_symbol_candles_chunked(sym, mt5.TIMEFRAME_M5, days=days)
        if df is None or len(df) < 500:
            print(f"    [-] Datos insuficientes para {sym} (velas: {len(df) if df is not None else 0}). Omitiendo.")
            continue

        first_date = df['time_ny'].iloc[0].strftime('%Y-%m-%d')
        last_date = df['time_ny'].iloc[-1].strftime('%Y-%m-%d')
        days_span = (df['time_ny'].iloc[-1] - df['time_ny'].iloc[0]).days
        print(f"    [OK] Velas cargadas: {len(df):,d} | Rango: {first_date} a {last_date} ({days_span} días / {days_span/365.25:.2f} años)")

        provider = FastHistoricalProvider(df)
        config = ORBConfig(
            asset_profiles=custom_profiles,
            target_rr=2.0,
            break_even_enabled=True,
            one_signal_per_session=True,
        )
        strategy = NewYorkORBStrategy(provider, config)

        unique_dates = sorted(list(set(df["time_ny"].dt.date)))
        sym_trades = []

        for d in unique_dates:
            if d.weekday() >= 5:
                continue

            session_bars = df[(df["time_ny"].dt.date == d) & (df["time_ny"].dt.hour >= 9) & (df["time_ny"].dt.hour < 16)]
            if len(session_bars) < 10:
                continue

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
                direction = str(sig["direction"]).upper()
                entry_time = pd.Timestamp(sig.get("entry_time") or candle_close_time)

                # Simular trade con modelo exacto de Núñez
                sim = simulate_nunez_dual_trade(
                    df,
                    entry_time=entry_time,
                    direction=direction,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    max_bars=150,
                )

                if sim is None:
                    continue

                trade_record = {
                    "symbol": sym,
                    "market": classify_orb_market(sym),
                    "entry_time": str(entry_time),
                    "session_date": str(d),
                    "direction": direction,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "risk_distance": sim["risk_distance"],
                    "orb_entry_mode": sig.get("orb_entry_mode", "ORB_BREAKOUT_RETEST"),
                    "retest_quality": sig.get("retest_quality") or "N/A",
                    "nunez_outcome": sim["nunez_outcome"],
                    "nunez_net_r": sim["nunez_net_r"],
                    "nunez_net_capital_pct": sim["nunez_net_capital_pct"],
                    "leg1_status": sim["leg1_status"],
                    "leg1_return_r": sim["leg1_return_r"],
                    "leg2_status": sim["leg2_status"],
                    "leg2_return_r": sim["leg2_return_r"],
                    "direct_1to1_status": sim["direct_1to1_status"],
                    "direct_1to1_r": sim["direct_1to1_r"],
                    "direct_1to2_status": sim["direct_1to2_status"],
                    "direct_1to2_r": sim["direct_1to2_r"],
                    "max_mfe_r": sim["max_mfe_r"],
                    "max_mae_r": sim["max_mae_r"],
                    "exit_bars": sim["exit_bars"],
                    "exit_time": sim["exit_time"],
                }

                sym_trades.append(trade_record)
                all_trades.append(trade_record)

                strategy.mark_signal_used(sym, str(d), sig.get("breakout_candle_time"))
                break

        print(f"    --> Trades completados para {sym}: {len(sym_trades)}")
        if sym_trades:
            stdf = pd.DataFrame(sym_trades)
            full_wins = (stdf["nunez_outcome"] == "FULL_WIN (+1.5%)").sum()
            partial_wins = (stdf["nunez_outcome"] == "PARTIAL_WIN_BE (+0.5%)").sum()
            full_losses = (stdf["nunez_outcome"] == "FULL_LOSS (-1.0%)").sum()
            tp1_hits = (stdf["leg1_status"] == "WIN_TP1").sum()
            tp1_rate = (tp1_hits / len(stdf)) * 100
            total_net_r = stdf["nunez_net_r"].sum()
            print(f"        Aciertos TP1 (Regla 70%): {tp1_rate:.1f}% ({tp1_hits}/{len(stdf)})")
            print(f"        Full Win (+1.5%): {full_wins} | Parcial BE (+0.5%): {partial_wins} | Pérdida (-1.0%): {full_losses}")
            print(f"        Retorno Neto Núñez: {total_net_r:+.2f}R ({total_net_r:+.2f}% de capital)")

    mt5.shutdown()

    if not all_trades:
        print("\n[!] No se generaron operaciones en el replay.")
        return None

    trades_df = pd.DataFrame(all_trades)

    # Exportar datos a CSV y JSON
    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_file = out_dir / "replay_orb_nunez_trades.csv"
    trades_df.to_csv(csv_file, index=False)
    print(f"\n[+] Operaciones exportadas exitosamente a: {csv_file}")

    # Métricas agregadas
    results = compute_nunez_metrics(trades_df)
    json_file = out_dir / "replay_orb_nunez_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[+] Resumen cuantitativo guardado en: {json_file}")

    return trades_df, results


def compute_nunez_metrics(df: pd.DataFrame) -> dict:
    """Calcula estadísticas detalladas del modelo de 2 entradas de Núñez y sus benchmarks."""
    total = len(df)
    if total == 0:
        return {}

    # 1. Modelo Núñez 2-Leg
    full_wins = (df["nunez_outcome"] == "FULL_WIN (+1.5%)").sum()
    partial_wins = (df["nunez_outcome"] == "PARTIAL_WIN_BE (+0.5%)").sum()
    full_losses = (df["nunez_outcome"] == "FULL_LOSS (-1.0%)").sum()
    other_outcomes = total - (full_wins + partial_wins + full_losses)

    tp1_hits = (df["leg1_status"] == "WIN_TP1").sum()
    tp1_winrate = (tp1_hits / total) * 100.0

    tp2_hits = (df["leg2_status"] == "WIN_TP2").sum()
    tp2_winrate = (tp2_hits / total) * 100.0

    be_saves = (df["leg2_status"] == "BREAK_EVEN").sum()
    be_save_rate = (be_saves / total) * 100.0

    nunez_net_r = df["nunez_net_r"].sum()
    nunez_net_pct = df["nunez_net_capital_pct"].sum()
    nunez_gross_win = df[df["nunez_net_r"] > 0]["nunez_net_r"].sum()
    nunez_gross_loss = abs(df[df["nunez_net_r"] < 0]["nunez_net_r"].sum())
    nunez_pf = nunez_gross_win / nunez_gross_loss if nunez_gross_loss > 0 else 99.0

    # Drawdown Núñez
    equity_curve = df["nunez_net_capital_pct"].cumsum()
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = running_max - equity_curve
    max_drawdown_pct = drawdowns.max()

    # 2. Benchmark Directo 1:2
    d12_wins = (df["direct_1to2_status"] == "WIN").sum()
    d12_losses = (df["direct_1to2_status"] == "LOSS").sum()
    d12_wr = (d12_wins / total) * 100.0
    d12_net_r = df["direct_1to2_r"].sum()
    d12_gross_win = df[df["direct_1to2_r"] > 0]["direct_1to2_r"].sum()
    d12_gross_loss = abs(df[df["direct_1to2_r"] < 0]["direct_1to2_r"].sum())
    d12_pf = d12_gross_win / d12_gross_loss if d12_gross_loss > 0 else 99.0

    # 3. Benchmark Directo 1:1
    d11_wins = (df["direct_1to1_status"] == "WIN").sum()
    d11_losses = (df["direct_1to1_status"] == "LOSS").sum()
    d11_wr = (d11_wins / total) * 100.0
    d11_net_r = df["direct_1to1_r"].sum()
    d11_gross_win = df[df["direct_1to1_r"] > 0]["direct_1to1_r"].sum()
    d11_gross_loss = abs(df[df["direct_1to1_r"] < 0]["direct_1to1_r"].sum())
    d11_pf = d11_gross_win / d11_gross_loss if d11_gross_loss > 0 else 99.0

    # Desglose por símbolo
    by_symbol = {}
    for sym, sdf in df.groupby("symbol"):
        s_total = len(sdf)
        s_fw = (sdf["nunez_outcome"] == "FULL_WIN (+1.5%)").sum()
        s_pw = (sdf["nunez_outcome"] == "PARTIAL_WIN_BE (+0.5%)").sum()
        s_fl = (sdf["nunez_outcome"] == "FULL_LOSS (-1.0%)").sum()
        s_tp1 = (sdf["leg1_status"] == "WIN_TP1").sum()
        s_tp2 = (sdf["leg2_status"] == "WIN_TP2").sum()
        s_be = (sdf["leg2_status"] == "BREAK_EVEN").sum()
        s_net_r = sdf["nunez_net_r"].sum()
        s_gw = sdf[sdf["nunez_net_r"] > 0]["nunez_net_r"].sum()
        s_gl = abs(sdf[sdf["nunez_net_r"] < 0]["nunez_net_r"].sum())
        s_pf = s_gw / s_gl if s_gl > 0 else 99.0

        # Drawdown del símbolo
        s_eq = sdf["nunez_net_capital_pct"].cumsum()
        s_dd = (np.maximum.accumulate(s_eq) - s_eq).max()

        by_symbol[sym] = {
            "trades": s_total,
            "tp1_winrate": round((s_tp1 / s_total) * 100.0, 1),
            "tp2_winrate": round((s_tp2 / s_total) * 100.0, 1),
            "be_save_rate": round((s_be / s_total) * 100.0, 1),
            "full_wins": int(s_fw),
            "partial_wins": int(s_pw),
            "full_losses": int(s_fl),
            "nunez_net_r": round(s_net_r, 2),
            "nunez_net_pct": round(s_net_r, 2),
            "profit_factor": round(s_pf, 2),
            "max_drawdown_pct": round(s_dd, 2),
            "direct_1to2_net_r": round(sdf["direct_1to2_r"].sum(), 2),
            "direct_1to1_net_r": round(sdf["direct_1to1_r"].sum(), 2),
            "direct_1to2_winrate": round((sdf["direct_1to2_status"] == "WIN").sum() / s_total * 100.0, 1),
            "direct_1to1_winrate": round((sdf["direct_1to1_status"] == "WIN").sum() / s_total * 100.0, 1),
            "avg_mfe": round(sdf["max_mfe_r"].mean(), 2),
            "avg_mae": round(sdf["max_mae_r"].mean(), 2),
        }

    return {
        "global_summary": {
            "total_trades": total,
            "nunez_2leg": {
                "tp1_winrate_pct": round(tp1_winrate, 1),
                "tp2_winrate_pct": round(tp2_winrate, 1),
                "be_save_rate_pct": round(be_save_rate, 1),
                "full_wins_count": int(full_wins),
                "partial_wins_count": int(partial_wins),
                "full_losses_count": int(full_losses),
                "profitable_trades_pct": round(((full_wins + partial_wins) / total) * 100.0, 1),
                "total_net_r": round(nunez_net_r, 2),
                "total_return_capital_pct": round(nunez_net_pct, 2),
                "profit_factor": round(nunez_pf, 2),
                "max_drawdown_pct": round(max_drawdown_pct, 2),
                "expectancy_per_trade_pct": round(nunez_net_pct / total, 3),
            },
            "benchmark_direct_1to2": {
                "winrate_pct": round(d12_wr, 1),
                "total_net_r": round(d12_net_r, 2),
                "profit_factor": round(d12_pf, 2),
            },
            "benchmark_direct_1to1": {
                "winrate_pct": round(d11_wr, 1),
                "total_net_r": round(d11_net_r, 2),
                "profit_factor": round(d11_pf, 2),
            },
            "mfe_mae": {
                "avg_mfe": round(df["max_mfe_r"].mean(), 2),
                "avg_mae": round(df["max_mae_r"].mean(), 2),
            }
        },
        "by_symbol": by_symbol,
    }


if __name__ == "__main__":
    run_comprehensive_nunez_replay(days=730)
