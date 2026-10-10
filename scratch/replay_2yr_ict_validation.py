import sys
sys.path.insert(0, ".")

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import numpy as np
import pandas as pd

from strategy.ict.ict_strategy import ICTSabriMalleStrategy, build_h4_candles_from_h1, compute_atr, find_active_fvgs_fast
from strategy.ict.config import ICTSabriMalleConfig

NEW_YORK = ZoneInfo("America/New_York")

SPREADS = {
    "XAUUSD": 0.59,
    "EURUSD": 0.00015,
    "GBPUSD": 0.00020
}

class FastBacktestProvider:
    """Proveedor histórico optimizado con H1 y H4 precalculados para máxima velocidad."""
    def __init__(self, df_h1: pd.DataFrame, spread: float = 0.00015):
        self.df_h1 = df_h1.copy()
        self.df_h1['time'] = pd.to_datetime(self.df_h1['time'], utc=True)
        self.df_h1 = self.df_h1.sort_values('time').reset_index(drop=True)
        self.h1_times = self.df_h1['time'].values
        
        # Precalcular H4
        self.df_h4 = build_h4_candles_from_h1(self.df_h1)
        self.h4_times = self.df_h4['time'].values
        
        self.spread = spread
        self.current_idx = 0

    def set_idx(self, idx: int):
        self.current_idx = idx

    def get_candles(self, symbol: str, timeframe: str, count: int = 80) -> pd.DataFrame:
        tf = str(timeframe).upper()
        if tf == "H4":
            cur_t = self.df_h1['time'].iloc[self.current_idx]
            h4_idx = int(self.df_h4['time'].searchsorted(cur_t, side='right'))
            start_i = max(0, h4_idx - count)
            return self.df_h4.iloc[start_i : h4_idx].copy()
        else:
            start_i = max(0, self.current_idx - count + 1)
            return self.df_h1.iloc[start_i : self.current_idx + 1].copy()

    def get_current_tick(self, symbol: str) -> dict:
        c = float(self.df_h1['close'].iloc[self.current_idx])
        return {
            'time': self.df_h1['time'].iloc[self.current_idx],
            'ask': c + self.spread / 2.0,
            'bid': c - self.spread / 2.0,
            'spread': self.spread
        }


def simulate_trade_m15(signal: dict, df_m15: pd.DataFrame, spread: float, initial_balance: float = 10000.0, risk_pct_total: float = 1.0, max_hold_bars: int = 200):
    """
    Simulación precisa barra a barra en M15:
    - Pierna 1 (50% riesgo): Sale en TP1.
    - Pierna 2 (50% riesgo): Al tocar TP1 se activa Break-Even. Sale en TP2 o en BE.
    """
    direction = signal["direction"]
    entry_price = float(signal["entry_price"])
    stop_loss = float(signal["stop_loss"])
    tp1_price = float(signal["tp1_price"])
    tp2_price = float(signal["tp2_price"])
    entry_time = pd.to_datetime(signal["entry_time"], utc=True)

    risk_distance = abs(entry_price - stop_loss)
    if risk_distance <= 0:
        return None

    entry_m15_idx = int(df_m15['time'].searchsorted(entry_time, side='right'))
    if entry_m15_idx >= len(df_m15):
        return None

    # BE price con spread cubierto
    be_price = entry_price + spread if direction == "BUY" else entry_price - spread

    risk_usd_total = initial_balance * (risk_pct_total / 100.0)
    risk_usd_leg = risk_usd_total / 2.0

    target_rr_1 = signal.get("tp1_rr", 2.0)
    target_rr_2 = signal.get("runner_rr", 4.0)

    end_idx = min(len(df_m15), entry_m15_idx + max_hold_bars)

    leg1_closed = False
    leg1_outcome = None
    leg1_pnl_usd = 0.0

    leg2_closed = False
    leg2_outcome = None
    leg2_pnl_usd = 0.0
    leg2_in_be = False

    for i in range(entry_m15_idx, end_idx):
        bar = df_m15.iloc[i]
        b_high = float(bar['high'])
        b_low = float(bar['low'])
        b_open = float(bar['open'])
        b_close = float(bar['close'])

        if not leg1_closed:
            sl_hit = b_low <= stop_loss if direction == "BUY" else b_high >= stop_loss
            tp1_hit = b_high >= tp1_price if direction == "BUY" else b_low <= tp1_price

            if sl_hit and tp1_hit:
                if (direction == "BUY" and b_open < entry_price) or (direction == "SELL" and b_open > entry_price):
                    sl_hit, tp1_hit = True, False
                else:
                    sl_hit, tp1_hit = False, True

            if sl_hit:
                leg1_closed = True
                leg1_outcome = "SL"
                leg1_pnl_usd = -risk_usd_leg

                leg2_closed = True
                leg2_outcome = "SL"
                leg2_pnl_usd = -risk_usd_leg
                break

            elif tp1_hit:
                leg1_closed = True
                leg1_outcome = "TP1"
                leg1_pnl_usd = risk_usd_leg * target_rr_1
                leg2_in_be = True

        if leg1_closed and not leg2_closed:
            curr_sl_leg2 = be_price if leg2_in_be else stop_loss
            be_sl_hit = b_low <= curr_sl_leg2 if direction == "BUY" else b_high >= curr_sl_leg2
            tp2_hit = b_high >= tp2_price if direction == "BUY" else b_low <= tp2_price

            if be_sl_hit and tp2_hit:
                if (direction == "BUY" and b_open > curr_sl_leg2) or (direction == "SELL" and b_open < curr_sl_leg2):
                    tp2_hit, be_sl_hit = True, False
                else:
                    tp2_hit, be_sl_hit = False, True

            if tp2_hit:
                leg2_closed = True
                leg2_outcome = "TP2"
                leg2_pnl_usd = risk_usd_leg * target_rr_2
                break
            elif be_sl_hit:
                leg2_closed = True
                leg2_outcome = "BE"
                leg2_pnl_usd = 0.0
                break

    # Si expiró max_hold_bars y sigue abierta alguna pierna
    if not leg1_closed:
        last_close = float(df_m15['close'].iloc[end_idx - 1])
        rr_close = (last_close - entry_price) / risk_distance if direction == "BUY" else (entry_price - last_close) / risk_distance
        leg1_outcome = "EXP_WIN" if rr_close > 0 else "EXP_LOSS"
        leg1_pnl_usd = risk_usd_leg * rr_close
        leg2_outcome = leg1_outcome
        leg2_pnl_usd = leg1_pnl_usd

    elif not leg2_closed:
        last_close = float(df_m15['close'].iloc[end_idx - 1])
        rr_close = (last_close - entry_price) / risk_distance if direction == "BUY" else (entry_price - last_close) / risk_distance
        leg2_outcome = "EXP_WIN" if rr_close > 0 else "EXP_LOSS"
        leg2_pnl_usd = risk_usd_leg * rr_close

    net_pnl = leg1_pnl_usd + leg2_pnl_usd
    overall_outcome = "WIN" if net_pnl > 0 else ("BE" if net_pnl == 0 else "LOSS")

    return {
        "direction": direction,
        "entry_time": entry_time,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "tp1_price": tp1_price,
        "tp2_price": tp2_price,
        "risk_distance": risk_distance,
        "leg1_outcome": leg1_outcome,
        "leg1_pnl": leg1_pnl_usd,
        "leg2_outcome": leg2_outcome,
        "leg2_pnl": leg2_pnl_usd,
        "net_pnl": net_pnl,
        "overall_outcome": overall_outcome,
        "is_win": net_pnl > 0,
        "is_tp1_hit": leg1_outcome == "TP1",
        "is_tp2_hit": leg2_outcome == "TP2",
        "is_be": leg2_outcome == "BE" and leg1_outcome == "TP1",
        "is_full_loss": leg1_outcome == "SL"
    }


def run_improved_ict_scanner(df_h1: pd.DataFrame, df_m15: pd.DataFrame, symbol: str, spread: float, start_date: pd.Timestamp, end_date: pd.Timestamp):
    """
    Estrategia ICT Optimizada con los principios de los 9 videos:
    1. Time & Price (Killzones NY):
       - Acumulación: Asian Range (20:00 - 00:00 NY time).
       - Ventana de manipulación y distribución: London (02:00 - 05:00 NY) y New York (07:00 - 11:00 NY).
    2. Rango de Acumulación Real de la sesión asiática (High y Low).
    3. Ruptura / MSS Estricta:
       - Close supera el nivel (sin tolerancia anticipada del 20%).
       - Vela de desplazamiento con cuerpo >= 45% del rango.
    4. Entrada y Stop Loss ceñidos al extremo de la manipulación.
    5. Gestión: TP1 a 1:2.0 RR (liquidez interna), TP2 a 1:3.5 RR (extremo opuesto del rango asiático).
    """
    df = df_h1.copy()
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    # Conversión horaria a New York
    times_ny = df['time'].dt.tz_convert(NEW_YORK)
    df['ny_hour'] = times_ny.dt.hour
    df['ny_date'] = times_ny.dt.date

    df_h4 = build_h4_candles_from_h1(df)
    df_h4["ema50"] = df_h4["close"].ewm(span=50, adjust=False).mean()
    df_h4["ema200"] = df_h4["close"].ewm(span=200, adjust=False).mean()
    h4_times = df_h4['time'].values

    atr_h1 = compute_atr(df, period=14)

    signals = []
    last_trade_time = None

    for i in range(40, len(df)):
        t_bar = df['time'].iloc[i]
        if t_bar < start_date or t_bar > end_date:
            continue

        ny_h = df['ny_hour'].iloc[i]
        
        # 1. Filtro Estricto de Killzones: Solo operar en London (02:00-05:00 NY) o NY (07:00-11:00 NY)
        in_london_kz = (2 <= ny_h <= 5)
        in_ny_kz = (7 <= ny_h <= 11)
        if not (in_london_kz or in_ny_kz):
            continue

        # Evitar señales duplicadas continuas en la misma sesión/día si recién se operó
        if last_trade_time is not None and (t_bar - last_trade_time).total_seconds() < 4 * 3600:
            continue

        # 2. Macro Bias H4
        h4_idx = int(df_h4['time'].searchsorted(t_bar, side='right')) - 1
        if h4_idx < 10:
            continue
        h4_close = float(df_h4["close"].iloc[h4_idx])
        h4_ema50 = float(df_h4["ema50"].iloc[h4_idx])
        h4_ema200 = float(df_h4["ema200"].iloc[h4_idx])

        bias_bull = (h4_close > h4_ema50) and (h4_ema50 >= h4_ema200)
        bias_bear = (h4_close < h4_ema50) and (h4_ema50 <= h4_ema200)
        if not (bias_bull or bias_bear):
            continue

        # 3. Rango Asiático (20:00 a 00:00 NY) de la sesión más reciente
        asian_candles = []
        for look_back in range(1, 24):
            chk_idx = i - look_back
            if chk_idx < 0:
                break
            chk_ny_h = df['ny_hour'].iloc[chk_idx]
            if 20 <= chk_ny_h or chk_ny_h == 0:
                asian_candles.append(df.iloc[chk_idx])
            elif len(asian_candles) > 0:
                break

        if len(asian_candles) < 3:
            slice_prev = df.iloc[max(0, i - 12) : i - 2]
            if len(slice_prev) < 4:
                continue
            range_high = float(slice_prev['high'].max())
            range_low = float(slice_prev['low'].min())
        else:
            df_asian = pd.DataFrame(asian_candles)
            range_high = float(df_asian['high'].max())
            range_low = float(df_asian['low'].min())

        range_height = range_high - range_low
        curr_atr = atr_h1[i] if i < len(atr_h1) else 1.0
        if curr_atr <= 0 or range_height < (0.5 * curr_atr) or range_height > (5.0 * curr_atr):
            continue

        # 4. Manipulación / Judas Swing en las últimas 3 velas de H1
        recent_bars = df.iloc[max(0, i - 3) : i + 1]
        sweep_found = False
        direction = None
        sweep_peak = None
        sweep_bar_idx = None

        for b_sub_idx, (_, bar_row) in enumerate(recent_bars.iterrows()):
            c_high = float(bar_row['high'])
            c_low = float(bar_row['low'])
            c_open = float(bar_row['open'])
            c_close = float(bar_row['close'])
            candle_range = c_high - c_low + 1e-9

            # Bearish Judas Swing: Barre Asian High y deja mecha de rechazo
            if bias_bear and c_high > range_high:
                upper_wick = c_high - max(c_open, c_close)
                if (upper_wick / candle_range) >= 0.35:
                    sweep_found = True
                    direction = "SELL"
                    sweep_peak = c_high
                    sweep_bar_idx = i - len(recent_bars) + b_sub_idx + 1
                    break

            # Bullish Judas Swing: Barre Asian Low y deja mecha de rechazo
            elif bias_bull and c_low < range_low:
                lower_wick = min(c_open, c_close) - c_low
                if (lower_wick / candle_range) >= 0.35:
                    sweep_found = True
                    direction = "BUY"
                    sweep_peak = c_low
                    sweep_bar_idx = i - len(recent_bars) + b_sub_idx + 1
                    break

        if not sweep_found or direction is None:
            continue

        # 5. Ruptura Estructural Estricta (MSS) y Desplazamiento
        last_candle = df.iloc[i]
        curr_close = float(last_candle['close'])
        curr_open = float(last_candle['open'])
        body_size = abs(curr_close - curr_open)
        bar_range = float(last_candle['high']) - float(last_candle['low']) + 1e-9

        # Filtro de vela de desplazamiento (cuerpo >= 45% del rango de la barra)
        if (body_size / bar_range) < 0.45:
            continue

        if direction == "SELL":
            local_support = float(df['low'].iloc[max(0, sweep_bar_idx - 3) : sweep_bar_idx].min())
            if curr_close >= local_support:
                continue
            if (local_support - curr_close) > (0.35 * range_height):
                continue
            entry_price = curr_close
            stop_loss = sweep_peak + spread
            risk = abs(entry_price - stop_loss)
            if risk <= 0:
                continue
            tp1_price = entry_price - (2.0 * risk)
            tp2_price = entry_price - (3.5 * risk)

        else:
            local_resistance = float(df['high'].iloc[max(0, sweep_bar_idx - 3) : sweep_bar_idx].max())
            if curr_close <= local_resistance:
                continue
            if (curr_close - local_resistance) > (0.35 * range_height):
                continue
            entry_price = curr_close
            stop_loss = sweep_peak - spread
            risk = abs(entry_price - stop_loss)
            if risk <= 0:
                continue
            tp1_price = entry_price + (2.0 * risk)
            tp2_price = entry_price + (3.5 * risk)

        sig = {
            "symbol": symbol,
            "direction": direction,
            "entry_time": t_bar.isoformat(),
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "tp1_price": tp1_price,
            "tp2_price": tp2_price,
            "tp1_rr": 2.0,
            "runner_rr": 3.5,
            "risk": risk
        }
        signals.append(sig)
        last_trade_time = t_bar

    return signals


def run_full_comparison():
    datasets = [
        ("XAUUSD", "data/historical/XAUUSD_H1.csv", "data/historical/XAUUSD_M15.csv", SPREADS["XAUUSD"]),
        ("EURUSD", "data/forex_historical/EURUSD_H1.csv", "data/forex_historical/EURUSD_M15.csv", SPREADS["EURUSD"]),
        ("GBPUSD", "data/forex_historical/GBPUSD_H1.csv", "data/forex_historical/GBPUSD_M15.csv", SPREADS["GBPUSD"])
    ]

    start_date = pd.Timestamp("2024-10-01 00:00:00", tz=timezone.utc)
    end_date = pd.Timestamp("2026-10-01 23:59:59", tz=timezone.utc)

    all_results = {}

    for sym, h1_path, m15_path, spread in datasets:
        print(f"\n==========================================")
        print(f"  PROCESANDO {sym} (Periodo: 2 Años | 2024-2026)")
        print(f"==========================================")

        df_h1 = pd.read_csv(h1_path)
        df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
        df_h1 = df_h1[(df_h1['time'] >= start_date - pd.Timedelta(days=20)) & (df_h1['time'] <= end_date)].sort_values('time').reset_index(drop=True)

        df_m15 = pd.read_csv(m15_path)
        df_m15['time'] = pd.to_datetime(df_m15['time'], utc=True)
        df_m15 = df_m15.sort_values('time').reset_index(drop=True)

        # 1. ESCANEAR Y SIMULAR ESTRATEGIA ACTUAL (BASELINE)
        print(f"[{sym}] 1. Escaneando estrategia actual (Baseline)...")
        provider = FastBacktestProvider(df_h1, spread=spread)
        baseline_strat = ICTSabriMalleStrategy(provider, ICTSabriMalleConfig())
        
        baseline_signals = []
        last_sig_time = None
        for i in range(50, len(df_h1)):
            t_bar = df_h1['time'].iloc[i]
            if t_bar < start_date:
                continue
            if last_sig_time is not None and (t_bar - last_sig_time).total_seconds() < 4 * 3600:
                continue
            provider.set_idx(i)
            res = baseline_strat.analyze_symbol(sym, now_utc=t_bar)
            if res.get("valid"):
                sig = res["signal"]
                baseline_signals.append(sig)
                last_sig_time = t_bar

        print(f"[{sym}] Baseline: {len(baseline_signals)} señales detectadas.")
        baseline_sims = []
        for sig in baseline_signals:
            sim = simulate_trade_m15(sig, df_m15, spread=spread)
            if sim:
                baseline_sims.append(sim)

        # 2. ESCANEAR Y SIMULAR ESTRATEGIA OPTIMIZADA (VIDEOS ICT)
        print(f"[{sym}] 2. Escaneando estrategia optimizada (Killzones + MSS Estricto)...")
        improved_signals = run_improved_ict_scanner(df_h1, df_m15, sym, spread, start_date, end_date)
        print(f"[{sym}] Optimizada: {len(improved_signals)} señales detectadas.")

        improved_sims = []
        for sig in improved_signals:
            sim = simulate_trade_m15(sig, df_m15, spread=spread)
            if sim:
                improved_sims.append(sim)

        all_results[sym] = {
            "baseline": baseline_sims,
            "improved": improved_sims
        }

    return all_results

if __name__ == "__main__":
    results = run_full_comparison()
    print("\n\n>>> COMPARACIÓN FINAL DE MÉTRICAS (2 AÑOS: OCT 2024 - OCT 2026):")
    
    summary_rows = []
    for sym, res in results.items():
        for model_name, sims in [("Actual (Baseline)", res["baseline"]), ("Optimizada (ICT Videos)", res["improved"])]:
            total_trades = len(sims)
            if total_trades == 0:
                continue
            wins = sum(1 for s in sims if s["is_win"])
            tp1_hits = sum(1 for s in sims if s["is_tp1_hit"])
            tp2_hits = sum(1 for s in sims if s["is_tp2_hit"])
            bes = sum(1 for s in sims if s["is_be"])
            full_losses = sum(1 for s in sims if s["is_full_loss"])
            
            pnl_total = sum(s["net_pnl"] for s in sims)
            gross_profit = sum(s["net_pnl"] for s in sims if s["net_pnl"] > 0)
            gross_loss = abs(sum(s["net_pnl"] for s in sims if s["net_pnl"] < 0))
            profit_factor = round(gross_profit / (gross_loss + 1e-9), 2)
            
            equity = [10000.0]
            for s in sims:
                equity.append(equity[-1] + s["net_pnl"])
            peak = 10000.0
            max_dd = 0.0
            for eq in equity:
                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd

            winrate_effective = round(wins / total_trades * 100.0, 1)
            tp1_hit_rate = round(tp1_hits / total_trades * 100.0, 1)
            tp2_hit_rate = round(tp2_hits / total_trades * 100.0, 1)
            ret_pct = round((equity[-1] - 10000.0) / 10000.0 * 100.0, 1)

            summary_rows.append({
                "Activo": sym,
                "Modelo": model_name,
                "Trades": total_trades,
                "WinRate (TP1)": f"{tp1_hit_rate}%",
                "WinRate (TP2)": f"{tp2_hit_rate}%",
                "WinRate Efectivo": f"{winrate_effective}%",
                "Break-Even %": f"{round(bes / total_trades * 100.0, 1)}%",
                "Full SL %": f"{round(full_losses / total_trades * 100.0, 1)}%",
                "Profit Factor": profit_factor,
                "Retorno Neto": f"{ret_pct}%",
                "Max DD": f"{round(max_dd, 1)}%"
            })

    df_summary = pd.DataFrame(summary_rows)
    print(df_summary.to_string(index=False))
