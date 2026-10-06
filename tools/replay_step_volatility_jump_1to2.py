"""Replay Histórico Cuantitativo para STEP, VOLATILITY y JUMP (6 a 12 meses).

Evalúa la estrategia SMC con relación Riesgo:Beneficio mínima 1:2 (RR >= 2.0).
Analiza:
1. Rendimiento estándar 1:2 (TP=+2R, SL=-1R).
2. Rendimiento 1:2 con Break-Even dinámico activado a +1.0R.
3. Análisis de excursión máxima favorable (MFE) en operaciones perdedoras.
4. Diagnóstico de patrones de fallo por activo y familia.

Uso:
    python tools/replay_step_volatility_jump_1to2.py [--days 180] [--symbols ...]
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
from backtesting.trade_simulator import simulate_trade, calculate_realized_rr


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
    "STEP": ["Step Index", "Step Index 500", "Step Index 200"],
    "VOLATILITY": ["Volatility 75 Index", "Volatility 25 Index", "Volatility 50 Index", "Volatility 100 Index"],
    "JUMP": ["Jump 50 Index", "Jump 10 Index", "Jump 25 Index"],
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


def simulate_trade_with_be_and_mfe(
    candles: pd.DataFrame,
    entry_time,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    be_trigger_rr: float = 1.0,
    max_bars: int = 200,
):
    """Simula el trade bar-a-bar midiendo:
    - Resultado directo 1:2 (sin BE)
    - Resultado con Break-Even a +1.0R (BE movido a precio de entrada)
    - Máxima Excursión Favorable (MFE) alcanzada en R antes de salir
    - Máxima Excursión Adversa (MAE) en R
    - Número de barras de permanencia
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

    be_price = entry_price
    be_active = False

    max_mfe_r = 0.0
    max_mae_r = 0.0
    
    direct_result = None
    direct_exit_price = None
    direct_exit_time = None
    direct_bars = 0
    direct_realized_rr = 0.0

    be_result = None
    be_exit_price = None
    be_realized_rr = 0.0

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
            hit_be = be_active and (low <= be_price)
            if bar_mfe >= be_trigger_rr:
                be_active = True
        else:
            bar_mfe = (entry_price - low) / risk
            bar_mae = (high - entry_price) / risk
            hit_tp = low <= take_profit
            hit_sl = high >= stop_loss
            hit_be = be_active and (high >= be_price)
            if bar_mfe >= be_trigger_rr:
                be_active = True

        max_mfe_r = max(max_mfe_r, bar_mfe)
        max_mae_r = max(max_mae_r, bar_mae)

        # 1. Simulación Directa (Sin BE)
        if direct_result is None:
            if hit_sl and hit_tp:
                direct_result = "AMBIGUOUS"
                direct_exit_price = entry_price
                direct_realized_rr = 0.0
                direct_bars = bars_held
                direct_exit_time = c_time
            elif hit_sl:
                direct_result = "LOSS"
                direct_exit_price = stop_loss
                direct_realized_rr = -1.0
                direct_bars = bars_held
                direct_exit_time = c_time
            elif hit_tp:
                direct_result = "WIN"
                direct_exit_price = take_profit
                direct_realized_rr = 2.0
                direct_bars = bars_held
                direct_exit_time = c_time

        # 2. Simulación con BE
        if be_result is None:
            if hit_tp:
                be_result = "WIN"
                be_exit_price = take_profit
                be_realized_rr = 2.0
            elif be_active and hit_be:
                be_result = "BREAK_EVEN"
                be_exit_price = be_price
                be_realized_rr = 0.0
            elif hit_sl:
                be_result = "LOSS"
                be_exit_price = stop_loss
                be_realized_rr = -1.0

        if direct_result is not None and be_result is not None:
            break

    if direct_result is None:
        direct_result = "OPEN"
        direct_realized_rr = 0.0
        direct_bars = len(future)
    if be_result is None:
        be_result = "OPEN"
        be_realized_rr = 0.0

    return {
        "direct_result": direct_result,
        "direct_realized_rr": direct_realized_rr,
        "direct_bars": direct_bars,
        "direct_exit_time": direct_exit_time,
        "be_result": be_result,
        "be_realized_rr": be_realized_rr,
        "max_mfe_r": round(max_mfe_r, 3),
        "max_mae_r": round(max_mae_r, 3),
    }


def analyze_asset_replay(symbol: str, family: str, days: int = 180):
    """Ejecuta el pipeline y replay para un activo individual."""
    print(f"\n[{family}] Analizando {symbol} ({days} días)...", flush=True)

    # Selección de temporalidad según familia:
    # STEP: Confirmación en M15 (aislamiento técnico)
    # VOLATILITY & JUMP: M15 setups + evaluación M15/M5
    if family == "STEP":
        candles = fetch_symbol_candles(symbol, mt5.TIMEFRAME_M15, days)
        eval_tf = "M15"
    else:
        # Para Volatility y Jump usamos M15 para setups estructurales
        candles = fetch_symbol_candles(symbol, mt5.TIMEFRAME_M15, days)
        eval_tf = "M15"

    if candles is None or len(candles) < 200:
        print(f"  --> Sin datos suficientes para {symbol}")
        return None

    # Cálculo de indicadores contextuales (ADX y ATR)
    candles["adx"] = compute_adx(candles, period=14)
    candles["atr"] = compute_atr(candles, period=14)

    # Configuración optimizada de pipeline con RR 1:2
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

    # Procesar en ventanas rodantes para velocidad y escalabilidad
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
    print(f"  Velas: {len(candles)} ({eval_tf}) | Setups: {len(setups)} | Confirmaciones: {len(confirmations)} (Tiempo: {elapsed:.1f}s)", flush=True)

    if confirmations.empty:
        return {
            "symbol": symbol,
            "family": family,
            "total_candles": len(candles),
            "setups": len(setups),
            "total_trades": 0,
            "direct": {"wins": 0, "losses": 0, "win_rate": 0.0, "total_r": 0.0, "expectancy": 0.0},
            "with_be": {"wins": 0, "losses": 0, "be": 0, "win_rate": 0.0, "total_r": 0.0, "expectancy": 0.0},
            "loss_mfe_distribution": {},
        }

    # Simulación de cada confirmación
    trade_records = []
    for _, conf in confirmations.iterrows():
        entry_time = conf["entry_time"]
        direction = conf["direction"]
        entry_price = float(conf["entry_price"])
        stop_loss = float(conf["stop_loss"])
        take_profit = float(conf["take_profit"])

        sim = simulate_trade_with_be_and_mfe(
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

        # Extraer ADX y ATR en el momento de la confirmación
        conf_row = candles[candles["time"] == entry_time]
        adx_val = float(conf_row["adx"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["adx"].iloc[0]) else 0.0
        atr_val = float(conf_row["atr"].iloc[0]) if not conf_row.empty and pd.notna(conf_row["atr"].iloc[0]) else 0.0

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
            **sim
        }
        trade_records.append(rec)

    trades_df = pd.DataFrame(trade_records)
    if trades_df.empty:
        return None

    # 1. Métricas Directas (Sin BE)
    direct_closed = trades_df[trades_df["direct_result"].isin(["WIN", "LOSS"])]
    direct_wins = int((direct_closed["direct_result"] == "WIN").sum())
    direct_losses = int((direct_closed["direct_result"] == "LOSS").sum())
    direct_total = len(direct_closed)
    direct_wr = round((direct_wins / direct_total * 100), 2) if direct_total > 0 else 0.0
    direct_tot_r = round(float(direct_closed["direct_realized_rr"].sum()), 2)
    direct_exp = round(direct_tot_r / direct_total, 3) if direct_total > 0 else 0.0

    # 2. Métricas con Break-Even (+1.0R)
    be_closed = trades_df[trades_df["be_result"].isin(["WIN", "LOSS", "BREAK_EVEN"])]
    be_wins = int((be_closed["be_result"] == "WIN").sum())
    be_losses = int((be_closed["be_result"] == "LOSS").sum())
    be_bes = int((be_closed["be_result"] == "BREAK_EVEN").sum())
    be_total = len(be_closed)
    be_wr = round((be_wins / (be_wins + be_losses) * 100), 2) if (be_wins + be_losses) > 0 else 0.0
    be_tot_r = round(float(be_closed["be_realized_rr"].sum()), 2)
    be_exp = round(be_tot_r / be_total, 3) if be_total > 0 else 0.0

    # 3. Análisis MFE en Pérdidas Directas: ¿Cuánto avanzaron a favor antes de tocar SL?
    losses_df = trades_df[trades_df["direct_result"] == "LOSS"]
    mfe_reached_05 = int((losses_df["max_mfe_r"] >= 0.5).sum()) if not losses_df.empty else 0
    mfe_reached_10 = int((losses_df["max_mfe_r"] >= 1.0).sum()) if not losses_df.empty else 0
    mfe_reached_15 = int((losses_df["max_mfe_r"] >= 1.5).sum()) if not losses_df.empty else 0

    # 4. ADX en Ganadoras vs Perdedoras
    wins_df = trades_df[trades_df["direct_result"] == "WIN"]
    mean_adx_win = round(float(wins_df["adx"].mean()), 1) if not wins_df.empty else 0.0
    mean_adx_loss = round(float(losses_df["adx"].mean()), 1) if not losses_df.empty else 0.0

    result_summary = {
        "symbol": symbol,
        "family": family,
        "total_candles": len(candles),
        "setups": len(setups),
        "total_trades": len(trades_df),
        "direct": {
            "closed": direct_total,
            "wins": direct_wins,
            "losses": direct_losses,
            "win_rate": direct_wr,
            "total_r": direct_tot_r,
            "expectancy_r": direct_exp,
            "avg_bars_held": round(float(direct_closed["direct_bars"].mean()), 1) if not direct_closed.empty else 0.0,
        },
        "with_be": {
            "closed": be_total,
            "wins": be_wins,
            "losses": be_losses,
            "break_evens": be_bes,
            "win_rate_excluding_be": be_wr,
            "total_r": be_tot_r,
            "expectancy_r": be_exp,
            "losses_saved_by_be": be_bes,
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
        "trades": trade_records,
    }

    print(f"  [RESULTADOS {symbol}]")
    print(f"    Directo 1:2:  Trades={direct_total} | Wins={direct_wins} | Losses={direct_losses} | WinRate={direct_wr}% | Total R={direct_tot_r:+.2f}R | Exp={direct_exp:+.3f}R")
    print(f"    Con BE @ 1R:  Trades={be_total} | Wins={be_wins} | BE={be_bes} | Losses={be_losses} | Total R={be_tot_r:+.2f}R | Exp={be_exp:+.3f}R")
    print(f"    Pérdidas que llegaron a +1.0R: {mfe_reached_10} de {len(losses_df)} ({round(mfe_reached_10/len(losses_df)*100, 1) if len(losses_df) > 0 else 0}%)")
    print(f"    ADX Promedio: Wins={mean_adx_win} vs Losses={mean_adx_loss}", flush=True)

    return result_summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Replay histórico Step, Volatility y Jump 1:2 RR")
    parser.add_argument("--days", type=int, default=180, help="Días históricos a analizar (default: 180)")
    parser.add_argument("--family", type=str, default="ALL", help="Familia a analizar (STEP, VOLATILITY, JUMP, ALL)")
    args = parser.parse_args()

    if not mt5.initialize():
        print("Error al inicializar MetaTrader 5:", mt5.last_error())
        sys.exit(1)

    print("=" * 80)
    print(f"REPLAY HISTÓRICO SMC 1:2 RR (ÚLTIMOS {args.days} DÍAS / {args.days//30} MESES)")
    print("=" * 80)

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
    family_aggregates = defaultdict(lambda: {
        "direct_trades": 0, "direct_wins": 0, "direct_losses": 0, "direct_r": 0.0,
        "be_trades": 0, "be_wins": 0, "be_losses": 0, "be_bes": 0, "be_r": 0.0,
        "losses_reaching_1r": 0, "total_losses": 0
    })

    for fam, symbols in selected_families.items():
        print(f"\n>>> INICIANDO FAMILIA {fam} ({len(symbols)} activos) <<<")
        for sym in symbols:
            res = analyze_asset_replay(sym, fam, days=args.days)
            if res:
                all_results[sym] = res
                all_trades.extend(res.pop("trades", []))
                
                # Agregar a métricas de familia
                d = res["direct"]
                b = res["with_be"]
                mfe = res["mfe_loss_analysis"]
                fam_agg = family_aggregates[fam]
                fam_agg["direct_trades"] += d["closed"]
                fam_agg["direct_wins"] += d["wins"]
                fam_agg["direct_losses"] += d["losses"]
                fam_agg["direct_r"] += d["total_r"]
                fam_agg["be_trades"] += b["closed"]
                fam_agg["be_wins"] += b["wins"]
                fam_agg["be_losses"] += b["losses"]
                fam_agg["be_bes"] += b["break_evens"]
                fam_agg["be_r"] += b["total_r"]
                fam_agg["losses_reaching_1r"] += mfe["reached_1_0r_before_loss"]
                fam_agg["total_losses"] += mfe["total_losses"]

    mt5.shutdown()

    # Guardar resultados
    output_dir = PROJECT_ROOT / "storage" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / f"replay_step_vol_jump_{args.days}d_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        csv_path = output_dir / f"replay_step_vol_jump_{args.days}d_trades.csv"
        if csv_path.exists() and args.family.upper() != "ALL":
            try:
                prev_df = pd.read_csv(csv_path)
                curr_families = set(trades_df["family"].unique())
                retained_df = prev_df[~prev_df["family"].isin(curr_families)]
                trades_df = pd.concat([retained_df, trades_df], ignore_index=True)
            except Exception as e:
                print(f"Aviso al combinar CSV: {e}")
        trades_df.to_csv(csv_path, index=False)
        print(f"\nOperaciones guardadas en: {csv_path} (Total acumulado: {len(trades_df)})")

    # Imprimir Tabla Resumen Final
    print("\n" + "=" * 90)
    print("RESUMEN GLOBAL POR FAMILIA - REPLAY SMC 1:2 RR")
    print("=" * 90)
    print(f"{'FAMILIA':<12} | {'DIRECT WR':<10} | {'DIRECT R':<10} | {'EXP (R)':<9} | {'BE WR':<10} | {'BE R':<10} | {'PÉRDIDAS SALVADAS POR BE'}")
    print("-" * 90)
    for fam, agg in family_aggregates.items():
        d_tot = agg["direct_trades"]
        d_wr = round(agg["direct_wins"] / d_tot * 100, 1) if d_tot > 0 else 0.0
        d_exp = round(agg["direct_r"] / d_tot, 3) if d_tot > 0 else 0.0
        
        b_tot = agg["be_wins"] + agg["be_losses"]
        b_wr = round(agg["be_wins"] / b_tot * 100, 1) if b_tot > 0 else 0.0
        b_exp = round(agg["be_r"] / agg["be_trades"], 3) if agg["be_trades"] > 0 else 0.0
        
        pct_saved = round(agg["losses_reaching_1r"] / agg["total_losses"] * 100, 1) if agg["total_losses"] > 0 else 0.0
        
        print(f"{fam:<12} | {d_wr:>8.1f}% | {agg['direct_r']:>+8.2f}R | {d_exp:>+7.3f}R | {b_wr:>8.1f}% | {agg['be_r']:>+8.2f}R | {agg['losses_reaching_1r']} de {agg['total_losses']} ({pct_saved}%)")
    print("=" * 90)


if __name__ == "__main__":
    main()
