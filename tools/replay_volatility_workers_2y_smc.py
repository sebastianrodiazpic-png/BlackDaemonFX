"""Analisis Historico Cuantitativo de 2 Años en Workers de Volatilidad (VOLATILITY_1 .. 4)

Estrategia: Smart Money Concepts (SMC)
- Riesgo total por oportunidad: 1.0% del capital
- Dividido en 2 trades:
    1. Trade 1: Riesgo 0.5%, Objetivo TP1 con relacion Riesgo:Beneficio 1:2 (+2.0R = +1.0% capital).
    2. Trade 2: Riesgo 0.5%, Corredora (Runner) a TP2 (evaluando 1:3, 1:4 y 1:5 RR),
       con Break-Even (BE) dinamico considerando el spread exacto del activo.
- Analisis comparativo de activacion de BE:
    a) BE activado al llegar a TP1 (+2.0R) [Estrategia Solicitada]
    b) BE activado tempranamente a +1.0R
    c) BE activado intermedio a +1.5R

Persistencia:
- SQLite: storage/analysis/volatility_smc_analysis.db
- CSV: storage/analysis/volatility_workers_2y_smc_trades.csv
- JSON: storage/analysis/volatility_workers_2y_smc_summary.json
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
from app.main import _stable_symbol_shard


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
    - Riesgo total oportunidad: 1.0% de capital ($100 en $10,000)
    - Trade 1: Riesgo 0.5% ($50), TP1 fijo a 1:2 RR (+2.0R = +1.0% / +$100).
    - Trade 2 (Corredora): Riesgo 0.5% ($50).
        - Al llegar el precio a TP1 (+2.0R), SL se mueve a Break-Even considerando spread:
            BUY: entry_price + spread_price + 2 * point
            SELL: entry_price - spread_price - 2 * point
        - Objetivo TP2 evaluado a 1:3 RR y 1:4 RR (+1.5% o +2.0%).
        - Si retrocede y toca BE, sale en 0% neto (spread cubierto).
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

    # Evaluacion alternativa: ¿Que pasaria si activamos BE a +1.0R en vez de a +2.0R?
    be_early_1r_activated = False
    trade2_early_1r_closed = False
    trade2_early_1r_result = None
    trade2_early_1r_realized_r = 0.0

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
            hit_tp2_3r = low <= tp2_3r_price
            hit_tp2_4r = low <= tp2_4r_price
            hit_tp2_5r = low <= tp2_5r_price

        max_mfe_r = max(max_mfe_r, bar_mfe)
        max_mae_r = max(max_mae_r, bar_mae)

        if bar_mfe >= 1.0:
            be_early_1r_activated = True

        # 1. Evaluacion de Trade 1 (Fixed TP1 a 1:2)
        if not trade1_closed:
            if hit_initial_sl and hit_tp1:
                # Caso ambiguo en la misma vela: conservador
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

        if trade1_closed and trade2_3r_closed and trade2_4r_closed and trade2_5r_closed and trade2_early_1r_closed:
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

    # Calculo monetario normalizado sobre $10,000 (Riesgo total 1% = $100)
    # Trade 1 arriesga 0.5% ($50). WIN (+2R) = +$100 (+1.0%), LOSS (-1R) = -$50 (-0.5%)
    t1_pnl_pct = (trade1_realized_r * 0.5) if trade1_closed and trade1_result in ("WIN", "LOSS") else 0.0
    t1_pnl_usd = t1_pnl_pct * 100.0  # $100 por cada 1%

    # Trade 2 (TP2 1:3) arriesga 0.5% ($50). WIN (+3R) = +$150 (+1.5%), BE (0R) = $0, LOSS (-1R) = -$50 (-0.5%)
    t2_3r_pnl_pct = (trade2_3r_realized_r * 0.5) if trade2_3r_closed and trade2_3r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_3r_pnl_usd = t2_3r_pnl_pct * 100.0

    # Trade 2 (TP2 1:4) arriesga 0.5% ($50). WIN (+4R) = +$200 (+2.0%), BE (0R) = $0, LOSS (-1R) = -$50 (-0.5%)
    t2_4r_pnl_pct = (trade2_4r_realized_r * 0.5) if trade2_4r_closed and trade2_4r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_4r_pnl_usd = t2_4r_pnl_pct * 100.0

    # Trade 2 (TP2 1:5) arriesga 0.5% ($50). WIN (+5R) = +$250 (+2.5%), BE (0R) = $0, LOSS (-1R) = -$50 (-0.5%)
    t2_5r_pnl_pct = (trade2_5r_realized_r * 0.5) if trade2_5r_closed and trade2_5r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_5r_pnl_usd = t2_5r_pnl_pct * 100.0

    # Corredora con BE temprano a 1.0R
    t2_early_1r_pnl_pct = (trade2_early_1r_realized_r * 0.5) if trade2_early_1r_closed and trade2_early_1r_result in ("WIN_TP2", "BREAK_EVEN", "LOSS") else 0.0
    t2_early_1r_pnl_usd = t2_early_1r_pnl_pct * 100.0

    combined_3r_pct = round(t1_pnl_pct + t2_3r_pnl_pct, 4)
    combined_3r_usd = round(t1_pnl_usd + t2_3r_pnl_usd, 2)
    combined_4r_pct = round(t1_pnl_pct + t2_4r_pnl_pct, 4)
    combined_4r_usd = round(t1_pnl_usd + t2_4r_pnl_usd, 2)
    combined_5r_pct = round(t1_pnl_pct + t2_5r_pnl_pct, 4)
    combined_5r_usd = round(t1_pnl_usd + t2_5r_pnl_usd, 2)
    combined_early_1r_pct = round(t1_pnl_pct + t2_early_1r_pnl_pct, 4)

    return {
        "risk_price": round(risk_price, digits if digits else 4),
        "spread_price": round(spread_price, digits if digits else 4),
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
        "trade2_early_1r_result": trade2_early_1r_result,
        "trade2_early_1r_realized_r": trade2_early_1r_realized_r,
        "trade2_early_1r_pnl_pct": t2_early_1r_pnl_pct,
        "combined_3r_pct": combined_3r_pct,
        "combined_3r_usd": combined_3r_usd,
        "combined_4r_pct": combined_4r_pct,
        "combined_4r_usd": combined_4r_usd,
        "combined_5r_pct": combined_5r_pct,
        "combined_5r_usd": combined_5r_usd,
        "combined_early_1r_pct": combined_early_1r_pct,
        "max_mfe_r": round(max_mfe_r, 3),
        "max_mae_r": round(max_mae_r, 3),
    }


def analyze_single_instrument(
    symbol: str,
    worker: str,
    candles: pd.DataFrame,
    spread_price: float,
    point: float,
    digits: int,
    min_trade_score: float = 75.0,
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

    # Configuracion optimizada del pipeline SMC
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
        setup_type = str(conf.get("setup_type", ""))

        sim = simulate_two_leg_smc_trade(
            candles=candles,
            entry_time=entry_time,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            spread_price=spread_price,
            point=point,
            digits=digits,
            max_bars=200,
        )
        if sim is None:
            continue

        conf_row = candles[candles["time"] == entry_time]
        adx_val = float(conf_row["adx"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["adx"].iloc[0]) else 0.0
        atr_val = float(conf_row["atr"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["atr"].iloc[0]) else 0.0
        
        # Atributos de fecha/hora para optimizacion
        dt_entry = pd.to_datetime(entry_time)
        entry_hour = dt_entry.hour
        entry_day = dt_entry.day_name()

        rec = {
            "symbol": symbol,
            "worker": worker,
            "entry_time": str(entry_time),
            "entry_hour": entry_hour,
            "entry_day": entry_day,
            "direction": direction,
            "setup_type": setup_type,
            "smc_score": score,
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
    cur.execute("DROP TABLE IF EXISTS smc_historical_trades")
    cur.execute("""
        CREATE TABLE smc_historical_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            worker TEXT,
            entry_time TEXT,
            entry_hour INTEGER,
            entry_day TEXT,
            direction TEXT,
            setup_type TEXT,
            smc_score REAL,
            entry_price REAL,
            stop_loss REAL,
            risk_price REAL,
            spread_price REAL,
            be_price REAL,
            tp1_price REAL,
            tp2_3r_price REAL,
            tp2_4r_price REAL,
            tp2_5r_price REAL,
            trade1_result TEXT,
            trade1_realized_r REAL,
            trade1_pnl_pct REAL,
            trade1_pnl_usd REAL,
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
            trade2_early_1r_result TEXT,
            trade2_early_1r_realized_r REAL,
            trade2_early_1r_pnl_pct REAL,
            combined_3r_pct REAL,
            combined_3r_usd REAL,
            combined_4r_pct REAL,
            combined_4r_usd REAL,
            combined_5r_pct REAL,
            combined_5r_usd REAL,
            combined_early_1r_pct REAL,
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
        "symbol", "worker", "entry_time", "entry_hour", "entry_day", "direction", "setup_type", "smc_score",
        "entry_price", "stop_loss", "risk_price", "spread_price", "be_price",
        "tp1_price", "tp2_3r_price", "tp2_4r_price", "tp2_5r_price",
        "trade1_result", "trade1_realized_r", "trade1_pnl_pct", "trade1_pnl_usd",
        "trade2_3r_result", "trade2_3r_realized_r", "trade2_3r_pnl_pct", "trade2_3r_pnl_usd",
        "trade2_4r_result", "trade2_4r_realized_r", "trade2_4r_pnl_pct", "trade2_4r_pnl_usd",
        "trade2_5r_result", "trade2_5r_realized_r", "trade2_5r_pnl_pct", "trade2_5r_pnl_usd",
        "trade2_early_1r_result", "trade2_early_1r_realized_r", "trade2_early_1r_pnl_pct",
        "combined_3r_pct", "combined_3r_usd", "combined_4r_pct", "combined_4r_usd",
        "combined_5r_pct", "combined_5r_usd", "combined_early_1r_pct",
        "max_mfe_r", "max_mae_r", "adx", "atr"
    ]
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO smc_historical_trades ({','.join(cols)}) VALUES ({placeholders})"
    
    data = []
    for t in trades:
        data.append(tuple(t.get(c) for c in cols))
    cur.executemany(sql, data)
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Analisis SMC 2 Años en Workers Volatility")
    parser.add_argument("--days", type=int, default=730, help="Dias de historial (default: 730 = 2 años)")
    parser.add_argument("--workers", nargs="+", default=["VOLATILITY_1", "VOLATILITY_2", "VOLATILITY_3", "VOLATILITY_4"])
    parser.add_argument("--max_symbols_per_worker", type=int, default=None, help="Limitar activos por worker para pruebas")
    parser.add_argument("--score", type=float, default=75.0, help="Score minimo SMC (default: 75.0)")
    parser.add_argument("--max_cores", type=int, default=12, help="Maximo nucleos CPU a utilizar (default: 12)")
    args = parser.parse_args()

    print("=" * 80)
    print("ANALISIS HISTORICO CUANTITATIVO SMC - 2 AÑOS (VOLATILITY_1 .. 4)")
    print(f"Periodo: {args.days} dias | Riesgo: 1.0% total (0.5% TP1 1:2 + 0.5% Runner con BE + spread)")
    print(f"Workers seleccionados: {args.workers}")
    print("=" * 80)

    if not mt5.initialize():
        print("Error: No se pudo inicializar MetaTrader 5")
        sys.exit(1)

    all_vol_syms = [s.name for s in mt5.symbols_get() if "volatility" in s.name.lower() or "vol " in s.name.lower()]
    shards = {
        "VOLATILITY_1": _stable_symbol_shard(all_vol_syms, 0, 4),
        "VOLATILITY_2": _stable_symbol_shard(all_vol_syms, 1, 4),
        "VOLATILITY_3": _stable_symbol_shard(all_vol_syms, 2, 4),
        "VOLATILITY_4": _stable_symbol_shard(all_vol_syms, 3, 4),
    }

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=args.days)

    # 1. Recolección de datos y metadatos de símbolos en el proceso principal
    instruments_to_run = []
    print("\nDescargando historial de velas y metadatos desde MT5...")
    for worker_name in args.workers:
        worker_syms = shards.get(worker_name, [])
        if args.max_symbols_per_worker:
            worker_syms = worker_syms[:args.max_symbols_per_worker]

        for symbol in worker_syms:
            mt5.symbol_select(symbol, True)
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, start_time, now)
            if rates is None or len(rates) < 200:
                print(f"  [X] {symbol} ({worker_name}): Datos insuficientes ({0 if rates is None else len(rates)} velas)")
                continue

            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
            
            info = mt5.symbol_info(symbol)
            point = float(info.point) if info and info.point else 0.01
            digits = int(info.digits) if info and info.digits is not None else 2
            spread_points = float(info.spread) if info and info.spread is not None else 100.0
            spread_price = spread_points * point

            instruments_to_run.append({
                "symbol": symbol,
                "worker": worker_name,
                "candles": df,
                "spread_price": spread_price,
                "point": point,
                "digits": digits,
                "candle_count": len(df),
            })
            print(f"  [+] {worker_name} -> {symbol:30s} | Velas: {len(df):6d} | Spread: {spread_price:.4f} (pt: {point})")

    mt5.shutdown()
    print(f"\nTotal instrumentos listos para simulación: {len(instruments_to_run)}")

    # 2. Procesamiento paralelo de pipeline SMC y simulación de trades
    all_trades = []
    all_summaries = []

    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "volatility_smc_analysis.db"
    init_database(db_path)

    t_start = time.time()
    cores_to_use = min(os.cpu_count() or 4, args.max_cores)
    print(f"\nIniciando simulación con {cores_to_use} núcleos en paralelo...")

    with ProcessPoolExecutor(max_workers=cores_to_use) as executor:
        futures = {
            executor.submit(
                analyze_single_instrument,
                item["symbol"],
                item["worker"],
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
                    print(f"  --> Finalizado {sym:28s} [{summary['worker']}]: {summary['total_candles']} velas, {summary['setups_count']} setups, {trades_count} trades en {summary['elapsed_seconds']}s", flush=True)
                if trades:
                    all_trades.extend(trades)
            except Exception as exc:
                print(f"  Error procesando {sym}: {exc}", flush=True)

    total_time = time.time() - t_start
    print(f"\nSimulacion completada en {total_time:.1f}s ({total_time/60:.2f} minutos).")
    print(f"Total oportunidades detectadas: {len(all_trades)}")

    # 3. Almacenamiento en CSV, SQLite y JSON
    csv_path = out_dir / "volatility_workers_2y_smc_trades.csv"
    json_path = out_dir / "volatility_workers_2y_smc_summary.json"

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
