"""Analisis Historico Cuantitativo de 2 Años en Workers de STEP y JUMP

Estrategia: Smart Money Concepts (SMC)
- Riesgo total por oportunidad: 1.0% del capital ($100 en base $10,000)
- Dividido en 2 trades (50% / 50% = 0.5% cada uno):
    1. Trade 1: Riesgo 0.5%, Objetivo TP1 con relacion Riesgo:Beneficio 1:2 (+2.0R = +1.0% capital).
    2. Trade 2: Riesgo 0.5%, Corredora (Runner) a TP2 (evaluando 1:3, 1:4, 1:5 RR y Trailing),
       con Break-Even (BE) dinamico considerando el spread exacto del activo.
       Al alcanzar TP1 (+2.0R), el SL de Trade 2 se traslada a BE + spread para garantizar 0% riesgo restante.
- Variantes comparativas:
    a) BE activado al llegar a TP1 (+2.0R) [Estrategia Principal Solicitada]
    b) BE activado tempranamente a +1.0R
    c) BE activado intermedio a +1.5R
    d) Trailing Stop tras tocar TP1
- Cobertura de activos:
    - STEP: Step Index, Step Index 500 (Primarios del Worker), Step Index 200, 300, 400 (Familia extendida).
    - JUMP: Jump 10 Index, Jump 50 Index (Primarios del Worker), Jump 25, 75, 100 (Familia extendida).

Persistencia:
- SQLite: storage/analysis/step_jump_smc_analysis.db
- CSV: storage/analysis/step_jump_workers_2y_smc_trades.csv
- JSON: storage/analysis/step_jump_workers_2y_smc_summary.json
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
import json
import time
import sqlite3
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

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
    """Calcula Average True Range (ATR)."""
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
    return dx.ewm(alpha=1/period, min_periods=period).mean()


def simulate_two_leg_smc_trade(
    candles: pd.DataFrame,
    entry_time,
    direction: str,
    entry_price: float,
    stop_loss: float,
    spread_price: float,
    point: float,
    digits: int,
    max_bars: int = 250,
):
    """Simula bar-a-bar la ejecucion de la oportunidad SMC dividida en 2 trades:
    - Riesgo total oportunidad: 1.0% de capital ($100 en $10,000 base)
    - Trade 1: Riesgo 0.5% ($50), TP1 fijo a 1:2 RR (+2.0R = +1.0% / +$100).
    - Trade 2 (Corredora): Riesgo 0.5% ($50).
        - Al llegar el precio a TP1 (+2.0R), SL se mueve a Break-Even considerando spread:
            BUY: entry_price + spread_price + 2 * point
            SELL: entry_price - spread_price - 2 * point
        - Objetivos de corredora evaluados:
            TP2 @ 1:3 RR (+1.5% capital / +$150)
            TP2 @ 1:4 RR (+2.0% capital / +$200)
            TP2 @ 1:5 RR (+2.5% capital / +$250)
            Trailing Stop (tras TP1, trailing a 1.0R)
        - Si retrocede y toca BE, sale en 0% neto (spread completamente cubierto).
        - Si no alcanza TP1 y toca SL inicial, ambas posiciones pierden 0.5% (total -1.0%).
    """
    direction = str(direction).upper()
    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    risk_price = abs(entry_price - stop_loss)
    if risk_price <= 1e-9:
        return None

    # Niveles teoricos
    side = 1.0 if direction == "BUY" else -1.0
    tp1_price = entry_price + side * (risk_price * 2.0)
    tp2_3r_price = entry_price + side * (risk_price * 3.0)
    tp2_4r_price = entry_price + side * (risk_price * 4.0)
    tp2_5r_price = entry_price + side * (risk_price * 5.0)

    # Offset para BE considerando spread
    offset_be = spread_price + 2.0 * point
    be_price = entry_price + side * offset_be
    if digits is not None:
        be_price = round(be_price, digits)
        tp1_price = round(tp1_price, digits)
        tp2_3r_price = round(tp2_3r_price, digits)
        tp2_4r_price = round(tp2_4r_price, digits)
        tp2_5r_price = round(tp2_5r_price, digits)

    future = candles[candles["time"] > entry_time].head(max_bars)
    if future.empty:
        return None

    # Estados de la simulacion
    trade1_closed = False
    trade1_result = None
    trade1_exit_price = None
    trade1_exit_time = None
    trade1_bars = 0
    trade1_realized_r = 0.0

    be_activated = False
    be_activation_time = None
    
    trade2_3r_closed = False
    trade2_3r_result = None
    trade2_3r_exit_price = None
    trade2_3r_realized_r = 0.0

    trade2_4r_closed = False
    trade2_4r_result = None
    trade2_4r_exit_price = None
    trade2_4r_realized_r = 0.0

    trade2_5r_closed = False
    trade2_5r_result = None
    trade2_5r_exit_price = None
    trade2_5r_realized_r = 0.0

    # Variantes alternativas
    be_early_1r_activated = False
    trade2_early_1r_closed = False
    trade2_early_1r_result = None
    trade2_early_1r_realized_r = 0.0

    be_early_15r_activated = False
    trade2_early_15r_closed = False
    trade2_early_15r_result = None
    trade2_early_15r_realized_r = 0.0

    # Trailing Stop tras TP1
    trailing_sl = be_price
    trade2_trail_closed = False
    trade2_trail_result = None
    trade2_trail_realized_r = 0.0

    max_mfe_r = 0.0
    max_mae_r = 0.0

    for bars_held, (_, candle) in enumerate(future.iterrows(), start=1):
        high = float(candle["high"])
        low = float(candle["low"])
        c_time = candle["time"]

        # Medir MFE / MAE
        if direction == "BUY":
            bar_mfe = (high - entry_price) / risk_price
            bar_mae = (entry_price - low) / risk_price
            hit_tp1 = high >= tp1_price
            hit_initial_sl = low <= stop_loss
            hit_be = be_activated and (low <= be_price)
            hit_be_early_1r = be_early_1r_activated and (low <= be_price)
            hit_be_early_15r = be_early_15r_activated and (low <= be_price)
            hit_tp2_3r = high >= tp2_3r_price
            hit_tp2_4r = high >= tp2_4r_price
            hit_tp2_5r = high >= tp2_5r_price
        else:
            bar_mfe = (entry_price - low) / risk_price
            bar_mae = (high - entry_price) / risk_price
            hit_tp1 = low <= tp1_price
            hit_initial_sl = high >= stop_loss
            hit_be = be_activated and (high >= be_price)
            hit_be_early_1r = be_early_1r_activated and (high >= be_price)
            hit_be_early_15r = be_early_15r_activated and (high >= be_price)
            hit_tp2_3r = low <= tp2_3r_price
            hit_tp2_4r = low <= tp2_4r_price
            hit_tp2_5r = low <= tp2_5r_price

        max_mfe_r = max(max_mfe_r, bar_mfe)
        max_mae_r = max(max_mae_r, bar_mae)

        if bar_mfe >= 1.0:
            be_early_1r_activated = True
        if bar_mfe >= 1.5:
            be_early_15r_activated = True

        # Actualizar trailing SL si TP1 ya fue tocado
        if be_activated:
            if direction == "BUY":
                new_trail = high - (1.0 * risk_price)
                if new_trail > trailing_sl:
                    trailing_sl = new_trail
            else:
                new_trail = low + (1.0 * risk_price)
                if new_trail < trailing_sl:
                    trailing_sl = new_trail

        # 1. Evaluacion de Trade 1 (Fixed TP1 a 1:2)
        if not trade1_closed:
            if hit_initial_sl and hit_tp1:
                # Caso ambiguo en la misma vela: ser conservador y asumir perdida
                trade1_closed = True
                trade1_result = "LOSS"
                trade1_exit_price = stop_loss
                trade1_exit_time = c_time
                trade1_bars = bars_held
                trade1_realized_r = -1.0
            elif hit_initial_sl:
                trade1_closed = True
                trade1_result = "LOSS"
                trade1_exit_price = stop_loss
                trade1_exit_time = c_time
                trade1_bars = bars_held
                trade1_realized_r = -1.0
            elif hit_tp1:
                trade1_closed = True
                trade1_result = "WIN"
                trade1_exit_price = tp1_price
                trade1_exit_time = c_time
                trade1_bars = bars_held
                trade1_realized_r = 2.0
                # Activar BE para Trade 2 al tocar TP1 (+2.0R)
                be_activated = True
                be_activation_time = c_time

        # 2. Evaluacion de Trade 2 Variante TP2 = 1:3 RR (BE a TP1)
        if not trade2_3r_closed:
            if not be_activated:
                if hit_initial_sl:
                    trade2_3r_closed = True
                    trade2_3r_result = "LOSS"
                    trade2_3r_exit_price = stop_loss
                    trade2_3r_realized_r = -1.0
            else:
                if hit_tp2_3r:
                    trade2_3r_closed = True
                    trade2_3r_result = "WIN_TP2"
                    trade2_3r_exit_price = tp2_3r_price
                    trade2_3r_realized_r = 3.0
                elif hit_be:
                    trade2_3r_closed = True
                    trade2_3r_result = "BREAK_EVEN"
                    trade2_3r_exit_price = be_price
                    trade2_3r_realized_r = 0.0

        # 3. Evaluacion de Trade 2 Variante TP2 = 1:4 RR (BE a TP1)
        if not trade2_4r_closed:
            if not be_activated:
                if hit_initial_sl:
                    trade2_4r_closed = True
                    trade2_4r_result = "LOSS"
                    trade2_4r_exit_price = stop_loss
                    trade2_4r_realized_r = -1.0
            else:
                if hit_tp2_4r:
                    trade2_4r_closed = True
                    trade2_4r_result = "WIN_TP2"
                    trade2_4r_exit_price = tp2_4r_price
                    trade2_4r_realized_r = 4.0
                elif hit_be:
                    trade2_4r_closed = True
                    trade2_4r_result = "BREAK_EVEN"
                    trade2_4r_exit_price = be_price
                    trade2_4r_realized_r = 0.0

        # 4. Evaluacion de Trade 2 Variante TP2 = 1:5 RR (BE a TP1)
        if not trade2_5r_closed:
            if not be_activated:
                if hit_initial_sl:
                    trade2_5r_closed = True
                    trade2_5r_result = "LOSS"
                    trade2_5r_exit_price = stop_loss
                    trade2_5r_realized_r = -1.0
            else:
                if hit_tp2_5r:
                    trade2_5r_closed = True
                    trade2_5r_result = "WIN_TP2"
                    trade2_5r_exit_price = tp2_5r_price
                    trade2_5r_realized_r = 5.0
                elif hit_be:
                    trade2_5r_closed = True
                    trade2_5r_result = "BREAK_EVEN"
                    trade2_5r_exit_price = be_price
                    trade2_5r_realized_r = 0.0

        # 5. Evaluacion de Corredora con BE temprano a +1.0R (objetivo 1:3 RR)
        if not trade2_early_1r_closed:
            if not be_early_1r_activated:
                if hit_initial_sl:
                    trade2_early_1r_closed = True
                    trade2_early_1r_result = "LOSS"
                    trade2_early_1r_realized_r = -1.0
            else:
                if hit_tp2_3r:
                    trade2_early_1r_closed = True
                    trade2_early_1r_result = "WIN_TP2"
                    trade2_early_1r_realized_r = 3.0
                elif hit_be_early_1r:
                    trade2_early_1r_closed = True
                    trade2_early_1r_result = "BREAK_EVEN"
                    trade2_early_1r_realized_r = 0.0

        # 6. Evaluacion de Corredora con BE temprano a +1.5R (objetivo 1:3 RR)
        if not trade2_early_15r_closed:
            if not be_early_15r_activated:
                if hit_initial_sl:
                    trade2_early_15r_closed = True
                    trade2_early_15r_result = "LOSS"
                    trade2_early_15r_realized_r = -1.0
            else:
                if hit_tp2_3r:
                    trade2_early_15r_closed = True
                    trade2_early_15r_result = "WIN_TP2"
                    trade2_early_15r_realized_r = 3.0
                elif hit_be_early_15r:
                    trade2_early_15r_closed = True
                    trade2_early_15r_result = "BREAK_EVEN"
                    trade2_early_15r_realized_r = 0.0

        # 7. Evaluacion Trailing Stop
        if not trade2_trail_closed:
            if not be_activated:
                if hit_initial_sl:
                    trade2_trail_closed = True
                    trade2_trail_result = "LOSS"
                    trade2_trail_realized_r = -1.0
            else:
                hit_trail = (low <= trailing_sl) if direction == "BUY" else (high >= trailing_sl)
                if hit_trail:
                    trade2_trail_closed = True
                    # Calcular R alcanzado en trailing
                    trail_r = max(0.0, (trailing_sl - entry_price) / risk_price if direction == "BUY" else (entry_price - trailing_sl) / risk_price)
                    trade2_trail_result = "TRAILING_EXIT" if trail_r > 0.1 else "BREAK_EVEN"
                    trade2_trail_realized_r = round(trail_r, 2)

        if (
            trade1_closed
            and trade2_3r_closed
            and trade2_4r_closed
            and trade2_5r_closed
            and trade2_early_1r_closed
            and trade2_early_15r_closed
            and trade2_trail_closed
        ):
            break

    # Si expiro la ventana temporal sin tocar SL/TP
    if not trade1_closed:
        trade1_result = "OPEN"
        trade1_bars = len(future)
    if not trade2_3r_closed:
        trade2_3r_result = "OPEN"
    if not trade2_4r_closed:
        trade2_4r_result = "OPEN"
    if not trade2_5r_closed:
        trade2_5r_result = "OPEN"
    if not trade2_early_1r_closed:
        trade2_early_1r_result = "OPEN"
    if not trade2_early_15r_closed:
        trade2_early_15r_result = "OPEN"
    if not trade2_trail_closed:
        trade2_trail_result = "OPEN"

    # Calculo monetario normalizado sobre base $10,000 (Riesgo total 1% = $100)
    # Trade 1 arriesga 0.5% ($50). WIN (+2R) = +$100 (+1.0%), LOSS (-1R) = -$50 (-0.5%)
    t1_pnl_pct = (trade1_realized_r * 0.5) if trade1_closed and trade1_result in ("WIN", "LOSS") else 0.0
    t1_pnl_usd = t1_pnl_pct * 100.0

    # Trade 2 (TP2 1:3) arriesga 0.5% ($50). WIN (+3R) = +$150 (+1.5%), BE (0R) = $0, LOSS (-1R) = -$50 (-0.5%)
    t2_3r_pnl_pct = (trade2_3r_realized_r * 0.5) if trade2_3r_closed and trade2_3r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_3r_pnl_usd = t2_3r_pnl_pct * 100.0

    # Trade 2 (TP2 1:4) arriesga 0.5% ($50). WIN (+4R) = +$200 (+2.0%), BE (0R) = $0, LOSS (-1R) = -$50 (-0.5%)
    t2_4r_pnl_pct = (trade2_4r_realized_r * 0.5) if trade2_4r_closed and trade2_4r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_4r_pnl_usd = t2_4r_pnl_pct * 100.0

    # Trade 2 (TP2 1:5) arriesga 0.5% ($50). WIN (+5R) = +$250 (+2.5%), BE (0R) = $0, LOSS (-1R) = -$50 (-0.5%)
    t2_5r_pnl_pct = (trade2_5r_realized_r * 0.5) if trade2_5r_closed and trade2_5r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_5r_pnl_usd = t2_5r_pnl_pct * 100.0

    # Trade 2 Trailing
    t2_trail_pnl_pct = (trade2_trail_realized_r * 0.5) if trade2_trail_closed and trade2_trail_result in ("TRAILING_EXIT", "BREAK_EVEN", "LOSS") else 0.0
    t2_trail_pnl_usd = t2_trail_pnl_pct * 100.0

    # Corredora con BE temprano a 1.0R
    t2_early_1r_pnl_pct = (trade2_early_1r_realized_r * 0.5) if trade2_early_1r_closed and trade2_early_1r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_early_1r_pnl_usd = t2_early_1r_pnl_pct * 100.0

    # Corredora con BE temprano a 1.5R
    t2_early_15r_pnl_pct = (trade2_early_15r_realized_r * 0.5) if trade2_early_15r_closed and trade2_early_15r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_early_15r_pnl_usd = t2_early_15r_pnl_pct * 100.0

    combined_3r_pct = round(t1_pnl_pct + t2_3r_pnl_pct, 4)
    combined_3r_usd = round(t1_pnl_usd + t2_3r_pnl_usd, 2)
    combined_4r_pct = round(t1_pnl_pct + t2_4r_pnl_pct, 4)
    combined_4r_usd = round(t1_pnl_usd + t2_4r_pnl_usd, 2)
    combined_5r_pct = round(t1_pnl_pct + t2_5r_pnl_pct, 4)
    combined_5r_usd = round(t1_pnl_usd + t2_5r_pnl_usd, 2)
    combined_trail_pct = round(t1_pnl_pct + t2_trail_pnl_pct, 4)
    combined_trail_usd = round(t1_pnl_usd + t2_trail_pnl_usd, 2)
    combined_early_1r_pct = round(t1_pnl_pct + t2_early_1r_pnl_pct, 4)
    combined_early_15r_pct = round(t1_pnl_pct + t2_early_15r_pnl_pct, 4)

    spread_ratio = round(spread_price / risk_price, 4) if risk_price > 0 else 0.0

    return {
        "risk_price": round(risk_price, digits if digits else 4),
        "spread_price": round(spread_price, digits if digits else 4),
        "spread_ratio": spread_ratio,
        "be_price": be_price,
        "tp1_price": tp1_price,
        "tp2_3r_price": tp2_3r_price,
        "tp2_4r_price": tp2_4r_price,
        "tp2_5r_price": tp2_5r_price,
        "trade1_result": trade1_result,
        "trade1_realized_r": trade1_realized_r,
        "trade1_bars": trade1_bars,
        "trade1_exit_time": str(trade1_exit_time) if trade1_exit_time is not None else None,
        "trade1_pnl_pct": t1_pnl_pct,
        "trade1_pnl_usd": t1_pnl_usd,
        "trade2_3r_result": trade2_3r_result,
        "trade2_3r_realized_r": trade2_3r_realized_r,
        "trade2_3r_pnl_pct": t2_3r_pnl_pct,
        "trade2_3r_pnl_usd": t2_3r_pnl_usd,
        "trade2_4r_result": trade2_4r_result,
        "trade2_4r_realized_r": trade2_4r_realized_r,
        "trade2_4r_pnl_pct": t2_4r_pnl_pct,
        "trade2_4r_pnl_usd": t2_4r_pnl_usd,
        "trade2_5r_result": trade2_5r_result,
        "trade2_5r_realized_r": trade2_5r_realized_r,
        "trade2_5r_pnl_pct": t2_5r_pnl_pct,
        "trade2_5r_pnl_usd": t2_5r_pnl_usd,
        "trade2_trail_result": trade2_trail_result,
        "trade2_trail_realized_r": trade2_trail_realized_r,
        "trade2_trail_pnl_pct": t2_trail_pnl_pct,
        "trade2_trail_pnl_usd": t2_trail_pnl_usd,
        "trade2_early_1r_result": trade2_early_1r_result,
        "trade2_early_1r_realized_r": trade2_early_1r_realized_r,
        "trade2_early_1r_pnl_pct": t2_early_1r_pnl_pct,
        "trade2_early_15r_result": trade2_early_15r_result,
        "trade2_early_15r_realized_r": trade2_early_15r_realized_r,
        "trade2_early_15r_pnl_pct": t2_early_15r_pnl_pct,
        "combined_3r_pct": combined_3r_pct,
        "combined_3r_usd": combined_3r_usd,
        "combined_4r_pct": combined_4r_pct,
        "combined_4r_usd": combined_4r_usd,
        "combined_5r_pct": combined_5r_pct,
        "combined_5r_usd": combined_5r_usd,
        "combined_trail_pct": combined_trail_pct,
        "combined_trail_usd": combined_trail_usd,
        "combined_early_1r_pct": combined_early_1r_pct,
        "combined_early_15r_pct": combined_early_15r_pct,
        "max_mfe_r": round(max_mfe_r, 3),
        "max_mae_r": round(max_mae_r, 3),
    }


def analyze_single_instrument(
    symbol: str,
    worker: str,
    family: str,
    is_primary: bool,
    candles: pd.DataFrame,
    spread_price: float,
    point: float,
    digits: int,
    min_trade_score: float = 70.0,
):
    """Ejecuta el pipeline SMC y la simulacion para un unico instrumento."""
    t0 = time.time()
    total_candles = len(candles)
    if total_candles < 200:
        return [], None

    # Calculo de indicadores contextuales
    candles = candles.copy()
    candles["adx"] = compute_adx(candles, period=14)
    candles["atr"] = compute_atr(candles, period=14)

    # Configuracion del pipeline SMC
    cfg = PipelineConfig(
        risk_reward_ratio=2.0,
        chart_patterns_enabled=False,
        harmonic_enabled=False,
        divergence_enabled=False,
        fvg_enabled=True,
        fvg_min_displacement_atr_multiplier=1.5,
        minimum_trade_score=min_trade_score,
    )

    chunk_size = 4000
    overlap = 200
    all_setups = []
    all_confirmations = []

    for start_idx in range(0, total_candles, chunk_size - overlap):
        end_idx = min(start_idx + chunk_size, total_candles)
        chunk = candles.iloc[start_idx:end_idx].copy()
        if len(chunk) < 200:
            break
        try:
            res = run_trade_pipeline(chunk, config=cfg, symbol=symbol)
            if not res["setups"].empty:
                all_setups.append(res["setups"])
            if not res["confirmations"].empty:
                all_confirmations.append(res["confirmations"])
        except Exception:
            pass

        if end_idx >= total_candles:
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

    if confirmations.empty:
        summary = {
            "symbol": symbol,
            "worker": worker,
            "family": family,
            "is_primary": is_primary,
            "total_candles": total_candles,
            "setups_count": len(setups),
            "confirmations_count": 0,
            "closed_trades": 0,
            "elapsed_seconds": round(elapsed, 2),
        }
        return [], summary

    trade_records = []
    for _, conf in confirmations.iterrows():
        entry_time = conf["entry_time"]
        direction = conf["direction"]
        entry_price = float(conf["entry_price"])
        stop_loss = float(conf["stop_loss"])
        score = float(conf.get("trade_score", 0.0))
        raw_score = float(conf.get("raw_trade_score", score))
        conf_pct = float(conf.get("confirmation_percentage", 0.0))
        grade = str(conf.get("trade_grade", "N/A"))
        break_type = str(conf.get("structure_break_type", "N/A"))
        fvg_conf = 1 if bool(conf.get("fvg_confirmed", False)) else 0
        pattern_conf = 1 if bool(conf.get("chart_pattern_confirmed", False)) else 0
        div_conf = 1 if bool(conf.get("divergence_confirmation", False)) else 0
        vol_conf = 1 if bool(conf.get("volume_confirmed", False)) else 0
        body_rat = round(float(conf.get("body_ratio", 0.0)), 3)

        sim = simulate_two_leg_smc_trade(
            candles=candles,
            entry_time=entry_time,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            spread_price=spread_price,
            point=point,
            digits=digits,
            max_bars=250,
        )
        if sim is None:
            continue

        conf_row = candles[candles["time"] == entry_time]
        adx_val = float(conf_row["adx"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["adx"].iloc[0]) else 0.0
        atr_val = float(conf_row["atr"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["atr"].iloc[0]) else 0.0
        
        # Temporal metadata
        dt_entry = pd.to_datetime(entry_time)
        entry_hour = dt_entry.hour
        entry_day = dt_entry.day_name()

        rec = {
            "symbol": symbol,
            "worker": worker,
            "family": family,
            "is_primary": 1 if is_primary else 0,
            "entry_time": str(entry_time),
            "entry_hour": entry_hour,
            "entry_day": entry_day,
            "direction": direction,
            "setup_type": break_type,
            "smc_score": score,
            "raw_trade_score": raw_score,
            "confirmation_percentage": conf_pct,
            "trade_grade": grade,
            "structure_break_type": break_type,
            "fvg_confirmed": fvg_conf,
            "chart_pattern_confirmed": pattern_conf,
            "divergence_confirmation": div_conf,
            "volume_confirmed": vol_conf,
            "body_ratio": body_rat,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "adx": round(adx_val, 2),
            "atr": round(atr_val, 4),
            **sim
        }
        trade_records.append(rec)

    summary = {
        "symbol": symbol,
        "worker": worker,
        "family": family,
        "is_primary": is_primary,
        "total_candles": total_candles,
        "setups_count": len(setups),
        "confirmations_count": len(confirmations),
        "closed_trades": len(trade_records),
        "elapsed_seconds": round(elapsed, 2),
    }

    return trade_records, summary


def init_database(db_path: Path):
    """Crea la tabla en SQLite si no existe."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS smc_step_jump_trades")
    cur.execute("""
        CREATE TABLE smc_step_jump_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            worker TEXT,
            family TEXT,
            is_primary INTEGER,
            entry_time TEXT,
            entry_hour INTEGER,
            entry_day TEXT,
            direction TEXT,
            setup_type TEXT,
            smc_score REAL,
            raw_trade_score REAL,
            confirmation_percentage REAL,
            trade_grade TEXT,
            structure_break_type TEXT,
            fvg_confirmed INTEGER,
            chart_pattern_confirmed INTEGER,
            divergence_confirmation INTEGER,
            volume_confirmed INTEGER,
            body_ratio REAL,
            entry_price REAL,
            stop_loss REAL,
            risk_price REAL,
            spread_price REAL,
            spread_ratio REAL,
            be_price REAL,
            tp1_price REAL,
            tp2_3r_price REAL,
            tp2_4r_price REAL,
            tp2_5r_price REAL,
            trade1_result TEXT,
            trade1_realized_r REAL,
            trade1_pnl_pct REAL,
            trade1_pnl_usd REAL,
            trade1_bars INTEGER,
            trade2_3r_result TEXT,
            trade2_3r_realized_r REAL,
            trade2_3r_pnl_pct REAL,
            trade2_3r_pnl_usd REAL,
            trade2_4r_result TEXT,
            trade2_4r_realized_r REAL,
            trade2_4r_pnl_pct REAL,
            trade2_4r_pnl_usd REAL,
            trade2_5r_result TEXT,
            trade2_5r_realized_r REAL,
            trade2_5r_pnl_pct REAL,
            trade2_5r_pnl_usd REAL,
            trade2_trail_result TEXT,
            trade2_trail_realized_r REAL,
            trade2_trail_pnl_pct REAL,
            trade2_trail_pnl_usd REAL,
            trade2_early_1r_result TEXT,
            trade2_early_1r_realized_r REAL,
            trade2_early_1r_pnl_pct REAL,
            trade2_early_15r_result TEXT,
            trade2_early_15r_realized_r REAL,
            trade2_early_15r_pnl_pct REAL,
            combined_3r_pct REAL,
            combined_3r_usd REAL,
            combined_4r_pct REAL,
            combined_4r_usd REAL,
            combined_5r_pct REAL,
            combined_5r_usd REAL,
            combined_trail_pct REAL,
            combined_trail_usd REAL,
            combined_early_1r_pct REAL,
            combined_early_15r_pct REAL,
            max_mfe_r REAL,
            max_mae_r REAL,
            adx REAL,
            atr REAL
        )
    """)
    conn.commit()
    conn.close()


def store_trades_sqlite(trades: list[dict], db_path: Path):
    """Guarda trades en SQLite."""
    if not trades:
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cols = [
        "symbol", "worker", "family", "is_primary", "entry_time", "entry_hour", "entry_day", "direction",
        "setup_type", "smc_score", "raw_trade_score", "confirmation_percentage", "trade_grade",
        "structure_break_type", "fvg_confirmed", "chart_pattern_confirmed", "divergence_confirmation",
        "volume_confirmed", "body_ratio", "entry_price", "stop_loss", "risk_price", "spread_price", "spread_ratio",
        "be_price", "tp1_price", "tp2_3r_price", "tp2_4r_price", "tp2_5r_price",
        "trade1_result", "trade1_realized_r", "trade1_pnl_pct", "trade1_pnl_usd", "trade1_bars",
        "trade2_3r_result", "trade2_3r_realized_r", "trade2_3r_pnl_pct", "trade2_3r_pnl_usd",
        "trade2_4r_result", "trade2_4r_realized_r", "trade2_4r_pnl_pct", "trade2_4r_pnl_usd",
        "trade2_5r_result", "trade2_5r_realized_r", "trade2_5r_pnl_pct", "trade2_5r_pnl_usd",
        "trade2_trail_result", "trade2_trail_realized_r", "trade2_trail_pnl_pct", "trade2_trail_pnl_usd",
        "trade2_early_1r_result", "trade2_early_1r_realized_r", "trade2_early_1r_pnl_pct",
        "trade2_early_15r_result", "trade2_early_15r_realized_r", "trade2_early_15r_pnl_pct",
        "combined_3r_pct", "combined_3r_usd", "combined_4r_pct", "combined_4r_usd",
        "combined_5r_pct", "combined_5r_usd", "combined_trail_pct", "combined_trail_usd",
        "combined_early_1r_pct", "combined_early_15r_pct",
        "max_mfe_r", "max_mae_r", "adx", "atr"
    ]
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO smc_step_jump_trades ({','.join(cols)}) VALUES ({placeholders})"
    
    data = []
    for t in trades:
        data.append(tuple(t.get(c) for c in cols))
    cur.executemany(sql, data)
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Analisis SMC 2 Años en Workers STEP y JUMP")
    parser.add_argument("--days", type=int, default=730, help="Dias de historial (default: 730 = 2 años)")
    parser.add_argument("--score", type=float, default=70.0, help="Score minimo SMC (default: 70.0 para capturar todo el universo)")
    parser.add_argument("--max_cores", type=int, default=16, help="Maximo nucleos CPU a utilizar (default: 16)")
    args = parser.parse_args()

    print("=" * 90)
    print("ANALISIS HISTORICO CUANTITATIVO SMC - 2 AÑOS COMPLETO (STEP & JUMP WORKERS)")
    print(f"Periodo: {args.days} dias (~70,000 velas M15 por activo) | Score base: >={args.score}")
    print("Estructura de Riesgo: 1.0% Capital total")
    print("  - Trade 1 (0.5% riesgo): TP1 fijo 1:2 RR (+2.0R = +1.0% capital)")
    print("  - Trade 2 (0.5% riesgo): Runner TP2 (1:3, 1:4, 1:5 RR, Trailing)")
    print("  - Break-Even dinamico: Activado al tocar TP1 (+2.0R), cubriendo spread + 2 pts")
    print("=" * 90)

    if not mt5.initialize():
        print("Error: No se pudo inicializar MetaTrader 5")
        sys.exit(1)

    # Definicion de Universos de los Workers STEP y JUMP
    target_instruments = [
        # Worker STEP
        {"symbol": "Step Index", "worker": "STEP", "family": "STEP", "is_primary": True},
        {"symbol": "Step Index 500", "worker": "STEP", "family": "STEP", "is_primary": True},
        {"symbol": "Step Index 200", "worker": "STEP", "family": "STEP", "is_primary": False},
        {"symbol": "Step Index 300", "worker": "STEP", "family": "STEP", "is_primary": False},
        {"symbol": "Step Index 400", "worker": "STEP", "family": "STEP", "is_primary": False},
        # Worker JUMP
        {"symbol": "Jump 10 Index", "worker": "JUMP", "family": "JUMP", "is_primary": True},
        {"symbol": "Jump 50 Index", "worker": "JUMP", "family": "JUMP", "is_primary": True},
        {"symbol": "Jump 25 Index", "worker": "JUMP", "family": "JUMP", "is_primary": False},
        {"symbol": "Jump 75 Index", "worker": "JUMP", "family": "JUMP", "is_primary": False},
        {"symbol": "Jump 100 Index", "worker": "JUMP", "family": "JUMP", "is_primary": False},
    ]

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=args.days)

    instruments_to_run = []
    print("\nDescargando historial de velas y metadatos de spread desde MT5...")
    for item in target_instruments:
        sym = item["symbol"]
        mt5.symbol_select(sym, True)
        rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start_time, now)
        if rates is None or len(rates) < 200:
            print(f"  [X] {sym}: Datos insuficientes ({0 if rates is None else len(rates)} velas)")
            continue

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        
        info = mt5.symbol_info(sym)
        point = float(info.point) if info and info.point else 0.01
        digits = int(info.digits) if info and info.digits is not None else 2
        spread_points = float(info.spread) if info and info.spread is not None else 10.0
        spread_price = spread_points * point

        instruments_to_run.append({
            **item,
            "candles": df,
            "spread_price": spread_price,
            "point": point,
            "digits": digits,
            "candle_count": len(df),
        })
        primary_label = "PRIMARIO" if item["is_primary"] else "EXTENDIDO"
        print(f"  [+] [{item['worker']}] {sym:18s} ({primary_label:9s}) | Velas: {len(df):6d} | Spread: {spread_price:.4f} ({spread_points:.0f} pts)")

    mt5.shutdown()
    print(f"\nTotal instrumentos listos para procesamiento paralelo: {len(instruments_to_run)}")

    # Base de datos y salidas
    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "step_jump_smc_analysis.db"
    init_database(db_path)

    all_trades = []
    all_summaries = []

    t_start = time.time()
    cores_to_use = min(os.cpu_count() or 4, args.max_cores, len(instruments_to_run))
    print(f"\nIniciando simulación con {cores_to_use} núcleos en paralelo...")

    with ProcessPoolExecutor(max_workers=cores_to_use) as executor:
        futures = {
            executor.submit(
                analyze_single_instrument,
                item["symbol"],
                item["worker"],
                item["family"],
                item["is_primary"],
                item["candles"],
                item["spread_price"],
                item["point"],
                item["digits"],
                args.score,
            ): item["symbol"]
            for item in instruments_to_run
        }

        for future in as_completed(futures):
            sym = futures[future]
            try:
                trades, summary = future.result()
                if summary:
                    all_summaries.append(summary)
                    trades_count = len(trades) if trades else 0
                    print(f"  --> Finalizado {sym:18s} [{summary['worker']}]: {summary['total_candles']} velas, {summary['setups_count']} setups, {trades_count} trades en {summary['elapsed_seconds']}s", flush=True)
                if trades:
                    all_trades.extend(trades)
            except Exception as exc:
                print(f"  [!] Error procesando {sym}: {exc}", flush=True)

    total_time = time.time() - t_start
    print(f"\nSimulacion completada en {total_time:.1f}s ({total_time/60:.2f} minutos).")
    print(f"Total oportunidades detectadas: {len(all_trades)}")

    # Guardar en SQLite, CSV y JSON
    csv_path = out_dir / "step_jump_workers_2y_smc_trades.csv"
    json_path = out_dir / "step_jump_workers_2y_smc_summary.json"

    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df.to_csv(csv_path, index=False)
        store_trades_sqlite(all_trades, db_path)
        print(f"\n[Guardado] CSV de trades: {csv_path}")
        print(f"[Guardado] Base de datos SQLite: {db_path}")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2)
    print(f"[Guardado] Resumen JSON: {json_path}")


if __name__ == "__main__":
    main()
