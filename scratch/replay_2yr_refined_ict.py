import sys
sys.path.insert(0, ".")

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import numpy as np
import pandas as pd

from strategy.ict.ict_strategy import ICTSabriMalleStrategy, build_h4_candles_from_h1, compute_atr
from strategy.ict.config import ICTSabriMalleConfig

NEW_YORK = ZoneInfo("America/New_York")

SPREADS = {
    "XAUUSD": 0.59,
    "EURUSD": 0.00015,
    "GBPUSD": 0.00020
}

class FastBacktestProvider:
    def __init__(self, df_h1: pd.DataFrame, spread: float = 0.00015):
        self.df_h1 = df_h1.copy()
        self.df_h1['time'] = pd.to_datetime(self.df_h1['time'], utc=True)
        self.df_h1 = self.df_h1.sort_values('time').reset_index(drop=True)
        self.df_h4 = build_h4_candles_from_h1(self.df_h1)
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


def simulate_trade_m15(signal: dict, df_m15: pd.DataFrame, spread: float, initial_balance: float = 10000.0, risk_pct_total: float = 1.0, max_hold_bars: int = 150):
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

    be_price = entry_price + spread if direction == "BUY" else entry_price - spread
    risk_usd_total = initial_balance * (risk_pct_total / 100.0)
    risk_usd_leg = risk_usd_total / 2.0

    target_rr_1 = signal.get("tp1_rr", 2.0)
    target_rr_2 = signal.get("runner_rr", 3.5)

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


def scan_refined_ict_signals(df_h1: pd.DataFrame, df_m15: pd.DataFrame, symbol: str, spread: float, start_date: pd.Timestamp, end_date: pd.Timestamp):
    """
    Estrategia ICT 100% fiel a los 9 videos analizados:
    1. Time & Price (Killzones NY):
       - Sesión Asiática (20:00 - 00:00 NY): define el Asian High y Asian Low (acumulación).
       - Ventana de manipulación y entrada: Londres (02:00 - 05:00 NY) y Nueva York (07:00 - 11:00 NY).
    2. Manipulación (Judas Swing): El precio barre el Asian High o Asian Low en Killzone.
    3. Refinamiento en Temporalidad Menor (M15):
       - Detecta el MSS (Market Structure Shift) en M15: quiebre con cuerpo de vela del último swing antes del sweep.
       - Entrada en Pullback / FVG (Consequent Encroachment 50%): no persigue el cierre alejado de H1.
         Espera el retroceso hacia el FVG generado por la ruptura en M15.
       - Stop Loss ceñido: en el extremo del Judas Swing + spread (un Stop Loss mucho más compacto).
       - Objetivos: TP1 a 1:2.0 RR (liquidez interna / equilibrio), TP2 a 1:3.5 RR (extremo opuesto de liquidez).
    """
    df_h1_c = df_h1.copy()
    df_h1_c['time'] = pd.to_datetime(df_h1_c['time'], utc=True)
    df_h1_c = df_h1_c.sort_values('time').reset_index(drop=True)

    df_m15_c = df_m15.copy()
    df_m15_c['time'] = pd.to_datetime(df_m15_c['time'], utc=True)
    df_m15_c = df_m15_c.sort_values('time').reset_index(drop=True)

    times_ny = df_m15_c['time'].dt.tz_convert(NEW_YORK)
    df_m15_c['ny_hour'] = times_ny.dt.hour
    df_m15_c['ny_date'] = times_ny.dt.date

    df_h4 = build_h4_candles_from_h1(df_h1_c)
    df_h4["ema50"] = df_h4["close"].ewm(span=50, adjust=False).mean()
    df_h4["ema200"] = df_h4["close"].ewm(span=200, adjust=False).mean()

    # Precalcular swings y sesiones asiáticas en M15
    dates = df_m15_c['ny_date'].unique()
    signals = []
    last_trade_time = None

    for d in dates:
        day_m15 = df_m15_c[df_m15_c['ny_date'] == d]
        if len(day_m15) < 15:
            continue

        # 1. Asian Range del día previo/noche (20:00 a 00:00 NY)
        # Buscar en las 24h previas las barras asiáticas
        t_first = day_m15['time'].iloc[0]
        asia_bars = df_m15_c[(df_m15_c['time'] < t_first) & (df_m15_c['time'] >= t_first - pd.Timedelta(hours=14))]
        asia_bars = asia_bars[(asia_bars['ny_hour'] >= 20) | (asia_bars['ny_hour'] == 0)]

        if len(asia_bars) < 4:
            continue

        asian_high = float(asia_bars['high'].max())
        asian_low = float(asia_bars['low'].min())
        asian_range = asian_high - asian_low
        if asian_range <= 0:
            continue

        # 2. Evaluar velas de Killzone: London (02:00 - 05:00) y NY (07:00 - 11:00)
        kz_bars = day_m15[
            ((day_m15['ny_hour'] >= 2) & (day_m15['ny_hour'] <= 5)) |
            ((day_m15['ny_hour'] >= 7) & (day_m15['ny_hour'] <= 11))
        ]
        if kz_bars.empty:
            continue

        # Verificar Macro Bias en H4
        t_ref = kz_bars['time'].iloc[0]
        if t_ref < start_date or t_ref > end_date:
            continue

        h4_idx = int(df_h4['time'].searchsorted(t_ref, side='right')) - 1
        if h4_idx < 10:
            continue
        h4_c = float(df_h4['close'].iloc[h4_idx])
        h4_e50 = float(df_h4['ema50'].iloc[h4_idx])
        h4_e200 = float(df_h4['ema200'].iloc[h4_idx])

        bias_bull = (h4_c > h4_e50) and (h4_e50 >= h4_e200)
        bias_bear = (h4_c < h4_e50) and (h4_e50 <= h4_e200)
        if not (bias_bull or bias_bear):
            continue

        # 3. Detectar Judas Swing (Sweep de Asian High o Low)
        kz_indices = list(kz_bars.index)
        sweep_detected = False
        direction = None
        sweep_idx = None
        sweep_peak = None

        for k_i, idx in enumerate(kz_indices):
            bar = df_m15_c.iloc[idx]
            b_high = float(bar['high'])
            b_low = float(bar['low'])
            b_close = float(bar['close'])
            b_open = float(bar['open'])
            b_range = b_high - b_low + 1e-9

            # Bearish Judas Swing: Barre Asian High y deja rechazo
            if bias_bear and b_high > asian_high:
                upper_wick = b_high - max(b_open, b_close)
                if (upper_wick / b_range) >= 0.30:
                    sweep_detected = True
                    direction = "SELL"
                    sweep_idx = idx
                    sweep_peak = b_high
                    break

            # Bullish Judas Swing: Barre Asian Low y deja rechazo
            elif bias_bull and b_low < asian_low:
                lower_wick = min(b_open, b_close) - b_low
                if (lower_wick / b_range) >= 0.30:
                    sweep_detected = True
                    direction = "BUY"
                    sweep_idx = idx
                    sweep_peak = b_low
                    break

        if not sweep_detected or direction is None:
            continue

        # 4. Refinamiento en M15: Buscar MSS y Entrada en FVG / Pullback (Consequent Encroachment 50%)
        # En las siguientes 8 barras después del sweep:
        post_sweep_bars = df_m15_c.loc[sweep_idx + 1 : min(len(df_m15_c) - 1, sweep_idx + 12)]
        if len(post_sweep_bars) < 3:
            continue

        # Identificar el swing previo que originó el sweep
        if direction == "SELL":
            swing_low_level = float(df_m15_c['low'].loc[max(0, sweep_idx - 4) : sweep_idx - 1].min())
            mss_idx = None
            fvg_level = None

            for p_idx in post_sweep_bars.index:
                c_bar = df_m15_c.loc[p_idx]
                if float(c_bar['close']) < swing_low_level:
                    # Desplazamiento confirmado con cuerpo
                    body = abs(float(c_bar['close']) - float(c_bar['open']))
                    rng = float(c_bar['high']) - float(c_bar['low']) + 1e-9
                    if (body / rng) >= 0.45:
                        mss_idx = p_idx
                        # FVG: High de 2 barras previas > Low actual
                        prev_high = float(df_m15_c['high'].loc[p_idx - 2]) if p_idx >= 2 else float(c_bar['high'])
                        fvg_level = (prev_high + float(c_bar['low'])) / 2.0  # CE 50%
                        break

            if mss_idx is None:
                continue

            # Buscar retesteo / pullback hacia el FVG o nivel roto
            entry_idx = None
            entry_price = None
            retest_window = df_m15_c.loc[mss_idx : min(len(df_m15_c) - 1, mss_idx + 6)]
            for r_idx in retest_window.index:
                r_bar = df_m15_c.loc[r_idx]
                target_retest = fvg_level if fvg_level else swing_low_level
                if float(r_bar['high']) >= target_retest:
                    entry_idx = r_idx
                    entry_price = target_retest
                    break

            if entry_idx is None:
                # Si no llegó exacto al FVG pero rompió con fuerza, entrada al cierre de la vela de ruptura
                entry_idx = mss_idx
                entry_price = float(df_m15_c['close'].loc[mss_idx])

            stop_loss = sweep_peak + spread
            risk = abs(entry_price - stop_loss)
            if risk <= 0 or (spread > 0 and risk < 1.2 * spread):
                continue

            # TP1 a 1:2.0 RR y TP2 a 1:3.5 RR
            tp1_price = entry_price - (2.0 * risk)
            tp2_price = entry_price - (3.5 * risk)

        else:
            swing_high_level = float(df_m15_c['high'].loc[max(0, sweep_idx - 4) : sweep_idx - 1].max())
            mss_idx = None
            fvg_level = None

            for p_idx in post_sweep_bars.index:
                c_bar = df_m15_c.loc[p_idx]
                if float(c_bar['close']) > swing_high_level:
                    body = abs(float(c_bar['close']) - float(c_bar['open']))
                    rng = float(c_bar['high']) - float(c_bar['low']) + 1e-9
                    if (body / rng) >= 0.45:
                        mss_idx = p_idx
                        prev_low = float(df_m15_c['low'].loc[p_idx - 2]) if p_idx >= 2 else float(c_bar['low'])
                        fvg_level = (prev_low + float(c_bar['high'])) / 2.0  # CE 50%
                        break

            if mss_idx is None:
                continue

            entry_idx = None
            entry_price = None
            retest_window = df_m15_c.loc[mss_idx : min(len(df_m15_c) - 1, mss_idx + 6)]
            for r_idx in retest_window.index:
                r_bar = df_m15_c.loc[r_idx]
                target_retest = fvg_level if fvg_level else swing_high_level
                if float(r_bar['low']) <= target_retest:
                    entry_idx = r_idx
                    entry_price = target_retest
                    break

            if entry_idx is None:
                entry_idx = mss_idx
                entry_price = float(df_m15_c['close'].loc[mss_idx])

            stop_loss = sweep_peak - spread
            risk = abs(entry_price - stop_loss)
            if risk <= 0 or (spread > 0 and risk < 1.2 * spread):
                continue

            tp1_price = entry_price + (2.0 * risk)
            tp2_price = entry_price + (3.5 * risk)

        t_entry = df_m15_c['time'].loc[entry_idx]
        if last_trade_time is not None and (t_entry - last_trade_time).total_seconds() < 4 * 3600:
            continue

        sig = {
            "symbol": symbol,
            "direction": direction,
            "entry_time": t_entry.isoformat(),
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "tp1_price": tp1_price,
            "tp2_price": tp2_price,
            "tp1_rr": 2.0,
            "runner_rr": 3.5,
            "risk": risk
        }
        signals.append(sig)
        last_trade_time = t_entry

    return signals


def run_full_validation():
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
        print(f"  EJECUTANDO REPLAY 2 AÑOS: {sym}")
        print(f"==========================================")

        df_h1 = pd.read_csv(h1_path)
        df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
        df_h1 = df_h1[(df_h1['time'] >= start_date - pd.Timedelta(days=20)) & (df_h1['time'] <= end_date)].sort_values('time').reset_index(drop=True)

        df_m15 = pd.read_csv(m15_path)
        df_m15['time'] = pd.to_datetime(df_m15['time'], utc=True)
        df_m15 = df_m15.sort_values('time').reset_index(drop=True)

        # 1. Estrategia Actual (Baseline)
        print(f"[{sym}] Escaneando Estrategia Actual (Baseline en H1)...")
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

        baseline_sims = []
        for sig in baseline_signals:
            sim = simulate_trade_m15(sig, df_m15, spread=spread)
            if sim:
                baseline_sims.append(sim)

        # 2. Estrategia Optimizada (Videos ICT con Refinamiento M15 / FVG CE 50%)
        print(f"[{sym}] Escaneando Estrategia Optimizada (Killzones + M15 MSS + FVG Pullback)...")
        refined_signals = scan_refined_ict_signals(df_h1, df_m15, sym, spread, start_date, end_date)
        refined_sims = []
        for sig in refined_signals:
            sim = simulate_trade_m15(sig, df_m15, spread=spread)
            if sim:
                refined_sims.append(sim)

        print(f"[{sym}] Finalizado: Baseline={len(baseline_sims)} trades | Optimizada={len(refined_sims)} trades")
        all_results[sym] = {
            "baseline": baseline_sims,
            "refined": refined_sims
        }

    return all_results

if __name__ == "__main__":
    results = run_full_validation()
    print("\n\n>>> COMPARACIÓN FINAL DE MÉTRICAS (2 AÑOS COMPLETOS: OCT 2024 - OCT 2026):")
    
    summary_rows = []
    for sym, res in results.items():
        for model_name, sims in [("Actual (Baseline)", res["baseline"]), ("Optimizada (Refinada ICT)", res["refined"])]:
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
