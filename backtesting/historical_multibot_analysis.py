"""Motor de Análisis Histórico y Optimización Multi-Bot: GOLD (Cuartos) y ORB (Nueva York)

Ejecuta el backtest completo de al menos 2 años (o todo el historial disponible M5/H1)
sobre los instrumentos de los workers GOLD y ORB:
- GOLD: XAUUSD bajo estrategia de Cuartos (GoldQuarterStrategy)
- ORB: XAUUSD, Wall Street 30, US Tech 100, US SP 500, BTCUSD, US Oil, XAGUSD bajo NewYorkORBStrategy

Gestión de Posición Dual (2 Trades / Piernas por oportunidad):
- Riesgo total por setup: 1.0% del capital ($10,000 USD cuenta base -> $100 riesgo)
- Trade 1 (Pierna 1 - TP1): Arriesga 0.5% ($50). Cierra en TP1 asegurando ganancias.
- Trade 2 (Pierna 2 - Corredora): Arriesga 0.5% ($50). Busca TP2.
- Al alcanzar TP1: Trade 2 mueve su SL a Break-Even + spread para reducir al máximo pérdidas.
"""

from __future__ import annotations
import os
import sqlite3
import math
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import numpy as np
import pandas as pd

from scratch.fast_provider import FastHistoricalDataProvider
from strategy.gold_quarters import GoldQuarterStrategy
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig

NEW_YORK = ZoneInfo("America/New_York")

SPREADS = {
    "XAUUSD": 0.59,
    "Wall Street 30": 1.80,
    "US Tech 100": 0.90,
    "BTCUSD": 18.424,
    "US Oil": 0.155,
    "US SP 500": 0.36,
    "XAGUSD": 0.055,
}

ORB_SYMBOLS = [
    "XAUUSD",
    "Wall Street 30",
    "US Tech 100",
    "US SP 500",
    "BTCUSD",
    "US Oil",
    "XAGUSD",
]


class HistoricalEngine:
    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = Path(data_dir)
        self.loaded_data = {}
        self._load_datasets()

    def _load_datasets(self):
        print("Cargando datasets históricos...")
        symbols = set(ORB_SYMBOLS) | {"XAUUSD"}
        for sym in symbols:
            clean = sym.replace(" ", "_")
            m5_path = self.data_dir / f"{clean}_M5.csv"
            h1_path = self.data_dir / f"{clean}_H1.csv"
            
            if not m5_path.exists():
                print(f"  [AVISO] No se encontró {m5_path}")
                continue
                
            df_m5 = pd.read_csv(m5_path)
            df_h1 = pd.read_csv(h1_path) if h1_path.exists() else None
            
            # Formatear datetime UTC
            df_m5['time'] = pd.to_datetime(df_m5['time'], utc=True)
            df_m5 = df_m5.sort_values('time').reset_index(drop=True)
            
            if df_h1 is not None:
                df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
                df_h1 = df_h1.sort_values('time').reset_index(drop=True)
                
            self.loaded_data[sym] = {
                "m5": df_m5,
                "h1": df_h1,
                "spread": SPREADS.get(sym, 0.5)
            }
            print(f"  {sym}: M5={len(df_m5)} barras ({df_m5['time'].iloc[0]} a {df_m5['time'].iloc[-1]}) | H1={len(df_h1) if df_h1 is not None else 0}")

    def scan_gold_quarters_signals(self, tolerance: float = 2.0, min_rr: float = 1.5, adaptive_tolerance: bool = False):
        """Escanea señales para XAUUSD usando GoldQuarterStrategy."""
        print(f"\n[SCAN] GOLD Cuartos (tolerancia={tolerance}, min_rr={min_rr}, adaptativa={adaptive_tolerance})...")
        data = self.loaded_data.get("XAUUSD")
        if not data:
            return []
            
        m5_df = data["m5"]
        h1_df = data["h1"]
        spread = data["spread"]
        
        provider = FastHistoricalDataProvider(m5_df, h1_df, spread=spread)
        gq = GoldQuarterStrategy(provider, increment=25.0, tolerance=tolerance, min_rr=min_rr)
        
        highs = m5_df['high'].values
        lows = m5_df['low'].values
        times = m5_df['time'].values
        n = len(m5_df)
        
        opens = m5_df['open'].values
        closes = m5_df['close'].values
        signals = []
        # Pre-filtro vectorial rápido de velas cerca de niveles de cuartos con rechazo y confirmación
        for i in range(25, n - 1):
            span = highs[i] - lows[i]
            if span <= 0:
                continue
                
            low = lows[i]
            q_low = round(low / 25.0) * 25.0
            dist_l = abs(low - q_low)
            
            high = highs[i]
            q_high = round(high / 25.0) * 25.0
            dist_h = abs(high - q_high)
            
            tol_check = (tolerance * 1.5) if not adaptive_tolerance else 5.0
            
            # Chequeo rápido de rechazo y confirmación
            # BUY: low cerca del cuarto, mecha inferior >= 40% del rango, cierre > nivel, conf cierra alcista y rompe high
            is_buy_cand = False
            if dist_l <= tol_check:
                wick_buy = min(opens[i], closes[i]) - low
                if (wick_buy / span) >= 0.40 and closes[i] > q_low:
                    if closes[i+1] > highs[i] and closes[i+1] > opens[i+1]:
                        is_buy_cand = True
                        
            # SELL: high cerca del cuarto, mecha superior >= 40% del rango, cierre < nivel, conf cierra bajista y rompe low
            is_sell_cand = False
            if dist_h <= tol_check:
                wick_sell = high - max(opens[i], closes[i])
                if (wick_sell / span) >= 0.40 and closes[i] < q_high:
                    if closes[i+1] < lows[i] and closes[i+1] < opens[i+1]:
                        is_sell_cand = True
                        
            if is_buy_cand or is_sell_cand:
                conf_idx = i + 1
                provider.set_index(conf_idx)
                eval_time = pd.Timestamp(times[conf_idx]) + pd.Timedelta(minutes=5)
                
                res = gq.analyze_symbol("XAUUSD", now_utc=eval_time)
                
                # Comprobar señal activa o shadow adaptive
                sig = None
                if res.get("valid"):
                    sig = res["signal"].copy()
                    sig["signal_type"] = "GQ_STRICT"
                elif adaptive_tolerance and "tolerance_shadow" in res:
                    cands = res["tolerance_shadow"].get("candidates", [])
                    for c in cands:
                        if c.get("shadow_conditions_pass"):
                            # Reconstruir señal adaptativa
                            side = c["direction"]
                            entry = float(m5_df['close'].iloc[conf_idx])
                            quarter = c["level"]
                            atr = res["tolerance_shadow"].get("atr", 4.0)
                            sl_buf = max(0.50 * atr, 4.0)
                            stop = float(m5_df['low'].iloc[i]) - sl_buf if side == 'BUY' else float(m5_df['high'].iloc[i]) + sl_buf
                            t1 = quarter + 25.0 if side == 'BUY' else quarter - 25.0
                            t2 = quarter + 50.0 if side == 'BUY' else quarter - 50.0
                            risk = entry - stop if side == 'BUY' else stop - entry
                            if risk > 0 and (abs(t1 - entry) / risk) >= min_rr:
                                sig = {
                                    'strategy_name': 'GOLD_QUARTERS',
                                    'direction': side,
                                    'entry_price': entry,
                                    'stop_loss': stop,
                                    'quarter_target': t1,
                                    'quarter_target_2': t2,
                                    'signal_type': 'GQ_ADAPTIVE_ATR',
                                    'timeframe': 'M5',
                                    'atr': atr,
                                }
                                break
                if sig:
                    sig["symbol"] = "XAUUSD"
                    sig["bar_index"] = conf_idx
                    sig["entry_time"] = pd.Timestamp(times[conf_idx])
                    sig["spread"] = spread
                    signals.append(sig)
                    
        print(f"  -> Total señales GOLD Cuartos encontradas: {len(signals)}")
        return signals

    def scan_orb_signals(self, symbol: str, config: ORBConfig | None = None):
        """Escanea señales ORB para un símbolo en la sesión de Nueva York."""
        data = self.loaded_data.get(symbol)
        if not data:
            return []
            
        m5_df = data["m5"]
        spread = data["spread"]
        cfg = config or ORBConfig()
        
        provider = FastHistoricalDataProvider(m5_df, spread=spread)
        orb = NewYorkORBStrategy(provider, config=cfg)
        
        # Agrupar por sesiones de Nueva York para máxima velocidad y precisión
        times_ny = m5_df['time'].dt.tz_convert(NEW_YORK)
        m5_df['time_ny'] = times_ny
        m5_df['session_date'] = times_ny.dt.date
        m5_df['hour_ny'] = times_ny.dt.hour
        m5_df['min_ny'] = times_ny.dt.minute
        m5_df['weekday_ny'] = times_ny.dt.weekday
        
        # Días laborables (lunes a viernes)
        workdays = m5_df[m5_df['weekday_ny'] < 5]['session_date'].unique()
        print(f"[SCAN] ORB {symbol} (sesiones NY a evaluar: {len(workdays)})...")
        
        signals = []
        for s_date in workdays:
            day_mask = (m5_df['session_date'] == s_date)
            day_df = m5_df[day_mask]
            
            # Velas de apertura (09:30 a 09:44)
            opening = day_df[(day_df['hour_ny'] == 9) & (day_df['min_ny'] >= 30) & (day_df['min_ny'] < 45)]
            if len(opening) < 3:
                continue
                
            orh = float(opening['high'].max())
            orl = float(opening['low'].min())
            if orh <= orl:
                continue
                
            # Velas post-rango (09:45 a 15:55)
            post = day_df[
                ((day_df['hour_ny'] == 9) & (day_df['min_ny'] >= 45)) |
                ((day_df['hour_ny'] >= 10) & (day_df['hour_ny'] < 16))
            ]
            if post.empty:
                continue
                
            post_indices = list(post.index)
            breakout_p_i = None
            for p_i, idx in enumerate(post_indices):
                prev_c = float(m5_df['close'].iloc[post_indices[p_i - 1]]) if p_i > 0 else float(opening['close'].iloc[-1])
                c = float(m5_df['close'].iloc[idx])
                if (prev_c <= orh and c > orh) or (prev_c >= orl and c < orl):
                    breakout_p_i = p_i
                    break
                    
            if breakout_p_i is None:
                continue
                
            # Solo evaluar desde la vela de ruptura hasta la ventana máxima de retest
            eval_window = post_indices[breakout_p_i : min(len(post_indices), breakout_p_i + int(cfg.retest_max_candles) + 1)]
            for idx in eval_window:
                t_bar = m5_df['time'].iloc[idx]
                provider.set_index(idx)
                eval_time = t_bar + pd.Timedelta(minutes=5)
                
                res = orb.analyze_symbol(symbol, now_utc=eval_time)
                if res.get("valid"):
                    sig = res["signal"].copy()
                    sig["symbol"] = symbol
                    sig["bar_index"] = idx
                    sig["entry_time"] = t_bar
                    sig["spread"] = spread
                    sig["session_date"] = str(s_date)
                    signals.append(sig)
                    break  # Una señal confirmada por sesión
                        
        print(f"  -> Total señales ORB {symbol} encontradas: {len(signals)}")
        return signals


def simulate_dual_leg_trade(
    signal: dict,
    m5_df: pd.DataFrame,
    spread: float,
    initial_balance: float = 10000.0,
    risk_pct_total: float = 1.0,
    rr_tp1: float = 1.5,
    rr_tp2: float = 2.5,
    use_structural_targets: bool = False,
    max_hold_bars: int = 150
) -> dict:
    """Simula una oportunidad ejecutada en 2 trades / piernas:
    
    - Trade 1 (Pierna 1 - TP1): Arriesga 0.5% del capital. Cierra en TP1.
    - Trade 2 (Pierna 2 - Corredora): Arriesga 0.5% del capital. Busca TP2.
    - Mecánica Break-Even:
      Al tocar TP1, Trade 2 actualiza su Stop Loss a entry_price +- spread.
      Si retrocede, cierra en BE exacto (0.0% PnL neto).
      Si continúa, cierra en TP2 con ganancia completa.
    """
    direction = signal["direction"]
    entry_price = float(signal["entry_price"])
    stop_loss = float(signal["stop_loss"])
    entry_idx = int(signal["bar_index"])
    entry_time = signal["entry_time"]
    symbol = signal["symbol"]
    strategy_name = signal.get("strategy_name", "ORB_NEW_YORK")
    
    risk_distance = abs(entry_price - stop_loss)
    if risk_distance <= 0:
        return None
        
    # Definir TP1 y TP2
    if use_structural_targets and "quarter_target" in signal:
        tp1_price = float(signal["quarter_target"])
        tp2_price = float(signal.get("quarter_target_2", entry_price + (2.0 * risk_distance if direction == "BUY" else -2.0 * risk_distance)))
        target_rr_1 = abs(tp1_price - entry_price) / risk_distance
        target_rr_2 = abs(tp2_price - entry_price) / risk_distance
    else:
        target_rr_1 = rr_tp1
        target_rr_2 = rr_tp2
        tp1_price = entry_price + (risk_distance * target_rr_1) if direction == "BUY" else entry_price - (risk_distance * target_rr_1)
        tp2_price = entry_price + (risk_distance * target_rr_2) if direction == "BUY" else entry_price - (risk_distance * target_rr_2)

    # Nivel de Break-Even con spread cubierto para Trade 2
    be_price = entry_price + spread if direction == "BUY" else entry_price - spread

    # Riesgo en USD: 1.0% total split en 2 piernas de 0.5% cada una
    risk_usd_total = initial_balance * (risk_pct_total / 100.0)
    risk_usd_leg = risk_usd_total / 2.0  # 0.5% por pierna
    
    # Simulación vela a vela
    n_bars = len(m5_df)
    end_idx = min(n_bars, entry_idx + max_hold_bars)
    
    leg1_closed = False
    leg1_outcome = None
    leg1_exit_time = None
    leg1_exit_price = None
    leg1_rr_realized = 0.0
    leg1_pnl_usd = 0.0
    
    leg2_closed = False
    leg2_outcome = None
    leg2_exit_time = None
    leg2_exit_price = None
    leg2_rr_realized = 0.0
    leg2_pnl_usd = 0.0
    leg2_in_be = False
    
    for i in range(entry_idx + 1, end_idx):
        bar = m5_df.iloc[i]
        b_high = float(bar['high'])
        b_low = float(bar['low'])
        b_open = float(bar['open'])
        b_close = float(bar['close'])
        b_time = bar['time']
        
        # 1. GESTIÓN DE PIERNA 1 (si sigue abierta)
        if not leg1_closed:
            # Evaluar SL
            sl_hit = b_low <= stop_loss if direction == "BUY" else b_high >= stop_loss
            # Evaluar TP1
            tp1_hit = b_high >= tp1_price if direction == "BUY" else b_low <= tp1_price
            
            if sl_hit and tp1_hit:
                # Caso extremo ambas cotas en la misma barra: conservadoramente asumimos SL si abrió adverso
                if (direction == "BUY" and b_open < entry_price) or (direction == "SELL" and b_open > entry_price):
                    sl_hit, tp1_hit = True, False
                else:
                    sl_hit, tp1_hit = False, True
                    
            if sl_hit:
                leg1_closed = True
                leg1_outcome = "SL"
                leg1_exit_time = b_time
                leg1_exit_price = stop_loss
                leg1_rr_realized = -1.0
                leg1_pnl_usd = -risk_usd_leg
                
                # Trade 2 también toca SL directo
                leg2_closed = True
                leg2_outcome = "SL"
                leg2_exit_time = b_time
                leg2_exit_price = stop_loss
                leg2_rr_realized = -1.0
                leg2_pnl_usd = -risk_usd_leg
                break  # Fin del setup completo
                
            elif tp1_hit:
                leg1_closed = True
                leg1_outcome = "TP1"
                leg1_exit_time = b_time
                leg1_exit_price = tp1_price
                leg1_rr_realized = target_rr_1
                leg1_pnl_usd = risk_usd_leg * target_rr_1
                
                # ACTIVACIÓN INMEDIATA DE BREAK-EVEN EN CORREDORA (Trade 2)
                leg2_in_be = True

        # 2. GESTIÓN DE PIERNA 2 (CORREDORA)
        if leg1_closed and not leg2_closed:
            # Ahora el SL de la corredora es be_price
            current_sl_leg2 = be_price if leg2_in_be else stop_loss
            
            be_sl_hit = b_low <= current_sl_leg2 if direction == "BUY" else b_high >= current_sl_leg2
            tp2_hit = b_high >= tp2_price if direction == "BUY" else b_low <= tp2_price
            
            if be_sl_hit and tp2_hit:
                if (direction == "BUY" and b_open > current_sl_leg2) or (direction == "SELL" and b_open < current_sl_leg2):
                    tp2_hit, be_sl_hit = True, False
                else:
                    tp2_hit, be_sl_hit = False, True
                    
            if tp2_hit:
                leg2_closed = True
                leg2_outcome = "TP2"
                leg2_exit_time = b_time
                leg2_exit_price = tp2_price
                leg2_rr_realized = target_rr_2
                leg2_pnl_usd = risk_usd_leg * target_rr_2
                break
                
            elif be_sl_hit:
                leg2_closed = True
                leg2_outcome = "BREAK_EVEN" if leg2_in_be else "SL"
                leg2_exit_time = b_time
                leg2_exit_price = current_sl_leg2
                # Al cerrar en be_price (entry +- spread), el PnL neto tras costes de spread es exactamente 0.00
                leg2_rr_realized = 0.0 if leg2_in_be else -1.0
                leg2_pnl_usd = 0.0 if leg2_in_be else -risk_usd_leg
                break

    # Si expira por límite de tiempo/barras
    if not leg1_closed:
        bar = m5_df.iloc[end_idx - 1]
        leg1_outcome = "TIMEOUT"
        leg1_exit_time = bar['time']
        leg1_exit_price = float(bar['close'])
        pnl_diff = (leg1_exit_price - entry_price) if direction == "BUY" else (entry_price - leg1_exit_price)
        leg1_rr_realized = pnl_diff / risk_distance
        leg1_pnl_usd = risk_usd_leg * leg1_rr_realized
        
    if not leg2_closed:
        bar = m5_df.iloc[end_idx - 1]
        leg2_outcome = "TIMEOUT_BE" if leg2_in_be else "TIMEOUT"
        leg2_exit_time = bar['time']
        leg2_exit_price = float(bar['close'])
        pnl_diff = (leg2_exit_price - entry_price) if direction == "BUY" else (entry_price - leg2_exit_price)
        leg2_rr_realized = max(0.0, pnl_diff / risk_distance) if leg2_in_be else pnl_diff / risk_distance
        leg2_pnl_usd = risk_usd_leg * leg2_rr_realized

    total_pnl_usd = leg1_pnl_usd + leg2_pnl_usd
    total_pnl_pct = (total_pnl_usd / initial_balance) * 100.0
    combined_rr = (leg1_rr_realized * 0.5) + (leg2_rr_realized * 0.5)

    return {
        "symbol": symbol,
        "strategy": strategy_name,
        "signal_type": signal.get("signal_type", "STANDARD"),
        "direction": direction,
        "entry_time": str(entry_time),
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "spread": spread,
        "risk_distance": risk_distance,
        "tp1_target": tp1_price,
        "tp2_target": tp2_price,
        "target_rr_1": target_rr_1,
        "target_rr_2": target_rr_2,
        
        # Pierna 1 (TP1)
        "leg1_outcome": leg1_outcome,
        "leg1_exit_time": str(leg1_exit_time),
        "leg1_exit_price": leg1_exit_price,
        "leg1_rr": round(leg1_rr_realized, 2),
        "leg1_pnl_usd": round(leg1_pnl_usd, 2),
        
        # Pierna 2 (Corredora)
        "leg2_outcome": leg2_outcome,
        "leg2_exit_time": str(leg2_exit_time),
        "leg2_exit_price": leg2_exit_price,
        "leg2_rr": round(leg2_rr_realized, 2),
        "leg2_pnl_usd": round(leg2_pnl_usd, 2),
        
        # Resultado Combinado del Setup
        "combined_rr": round(combined_rr, 2),
        "total_pnl_usd": round(total_pnl_usd, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "is_win": total_pnl_usd > 0,
        "is_scratch": abs(total_pnl_usd) < 1e-4,
        "is_loss": total_pnl_usd < -1e-4,
    }


def compute_performance_metrics(trades: list[dict], initial_balance: float = 10000.0) -> dict:
    if not trades:
        return {"total_trades": 0}
        
    df = pd.DataFrame(trades)
    n = len(df)
    
    wins = df[df["total_pnl_usd"] > 0]
    losses = df[df["total_pnl_usd"] < -1e-4]
    scratches = df[df["is_scratch"] == True]
    
    leg1_wins = df[df["leg1_outcome"] == "TP1"]
    leg2_wins = df[df["leg2_outcome"] == "TP2"]
    leg2_bes = df[df["leg2_outcome"] == "BREAK_EVEN"]
    
    total_gain = wins["total_pnl_usd"].sum()
    total_loss = abs(losses["total_pnl_usd"].sum())
    net_pnl = df["total_pnl_usd"].sum()
    profit_factor = (total_gain / total_loss) if total_loss > 0 else (99.0 if total_gain > 0 else 0.0)
    
    # Curva de capital y Drawdown
    equity_curve = [initial_balance]
    for pnl in df["total_pnl_usd"]:
        equity_curve.append(equity_curve[-1] + pnl)
    equity_series = pd.Series(equity_curve)
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak * 100.0
    max_dd = abs(drawdown.min())
    
    win_rate = (len(wins) / n) * 100.0
    leg1_win_rate = (len(leg1_wins) / n) * 100.0
    leg2_win_rate = (len(leg2_wins) / n) * 100.0
    be_rate = (len(leg2_bes) / n) * 100.0
    
    # Sharpe Ratio aproximado anualizado
    returns = df["total_pnl_pct"] / 100.0
    sharpe = (returns.mean() / returns.std() * math.sqrt(252)) if returns.std() > 0 else 0.0
    
    # Expectancy en R
    expectancy_r = df["combined_rr"].mean()
    
    # Rango temporal
    t_series = pd.to_datetime(df["entry_time"], utc=True, format='mixed')
    t_start = t_series.min()
    t_end = t_series.max()
    days = max(1, (t_end - t_start).days)
    trades_per_month = (n / days) * 30.4
    
    return {
        "total_trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "scratches": len(scratches),
        "win_rate_pct": round(win_rate, 2),
        "leg1_win_rate_pct": round(leg1_win_rate, 2),
        "leg2_win_rate_pct": round(leg2_win_rate, 2),
        "leg2_break_even_rate_pct": round(be_rate, 2),
        "total_gain_usd": round(total_gain, 2),
        "total_loss_usd": round(total_loss, 2),
        "net_pnl_usd": round(net_pnl, 2),
        "net_return_pct": round((net_pnl / initial_balance) * 100.0, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "expectancy_r": round(expectancy_r, 2),
        "days_span": days,
        "trades_per_month": round(trades_per_month, 1),
        "start_date": str(t_start.date()) if pd.notna(t_start) else None,
        "end_date": str(t_end.date()) if pd.notna(t_end) else None,
    }


def save_trades_to_storage(trades: list[dict], db_path: str = "storage/analysis/historical_analysis.db", csv_path: str = "storage/analysis/historical_trades_gold_orb.csv"):
    Path("storage/analysis").mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(trades)
    df.to_csv(csv_path, index=False)
    print(f"\n[ALMACENAMIENTO] Guardadas {len(df)} operaciones en CSV: {csv_path}")
    
    conn = sqlite3.connect(db_path)
    df.to_sql("historical_trades_dual_leg", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"[ALMACENAMIENTO] Base de datos SQLite actualizada: {db_path} (tabla: historical_trades_dual_leg)")
