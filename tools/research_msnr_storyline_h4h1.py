"""Investigación (solo lectura): storyline D1+H4 y confirmación H4→H1 de los vídeos MSNR — 20-oct-2026.

Reglas causales (solo velas cerradas; ver MSNR_VIDEOS_VS_IMPLEMENTACION_20261020.md):

Niveles: A/V del gráfico de líneas (picos y valles de los cierres, radio 2) en D1 y H4; en H1, niveles open-close
(dos velas del mismo color, nivel = cierre de la 1.ª).

Storyline diaria BAJISTA (espejo para alcista):
  1. Una vela D1 abre por debajo de un nivel diario, su máximo lo toca y cierra por debajo (rechazo).
  2. En los 3 días siguientes, una vela H4 cierra por debajo del último mínimo oscilante H4 confirmado (radio 2).
  La storyline empieza al cierre de esa H4 y termina al tocar el siguiente nivel diario por debajo del cierre del
  rechazo, al empezar la contraria o a los 15 días.

Confirmación H4→H1 (escenario nuevo):
  Una vela H4 rechaza un nivel H4 (abre del lado correcto, lo toca y cierra sin cruzarlo). En las 4 velas H1
  siguientes, una H1 cierra rompiendo el último nivel open-close de H1 (30 velas) en el sentido de la operación.
  Entrada en la apertura de la H1 siguiente (BUY al ask), SL tras el extremo de la H4 del rechazo ± 0,1 ATR H1,
  gestión del contrato (TP1 1R + runner 2R con BE tras TP1), tope spread/SL 2 % y una operación por símbolo.

Uso:
    .venv/Scripts/python.exe tools/research_msnr_storyline_h4h1.py --workers 3
Salida: storage/analysis/msnr_storyline_signals.csv (señales MSNR del replay con su storyline) y
        storage/analysis/msnr_h4h1_trades.csv (operaciones del escenario H4→H1).
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
START = datetime(2024, 7, 1, tzinfo=timezone.utc)
SPREAD_CAP = 0.02
TF_DELTA = {"D1": pd.Timedelta(days=1), "H4": pd.Timedelta(hours=4), "H1": pd.Timedelta(hours=1)}


# ----------------------------------------------------------------------------- niveles
def close_levels(df: pd.DataFrame, radius: int = 2) -> pd.DataFrame:
    """Niveles A/V del gráfico de líneas: picos y valles de los cierres (radio 2), disponibles cuando se confirman."""
    c = df["close"].to_numpy(float)
    rows = []
    for i in range(radius, len(df) - radius):
        win = c[i - radius:i + radius + 1]
        if c[i] == win.max() or c[i] == win.min():
            rows.append((df["close_time"].iloc[i + radius], c[i]))
    return pd.DataFrame(rows, columns=["avail", "level"])


def swing_points(df: pd.DataFrame, radius: int = 2):
    """Mínimos/máximos oscilantes confirmados `radius` velas después (causal)."""
    h, l = df["high"].to_numpy(float), df["low"].to_numpy(float)
    lows, highs = [], []
    for i in range(radius, len(df) - radius):
        conf = df["close_time"].iloc[i + radius]
        if l[i] == l[i - radius:i + radius + 1].min():
            lows.append((conf, l[i]))
        if h[i] == h[i - radius:i + radius + 1].max():
            highs.append((conf, h[i]))
    return pd.DataFrame(lows, columns=["conf", "price"]), pd.DataFrame(highs, columns=["conf", "price"])


def _levels_before(levels: pd.DataFrame, t, lookback: int = 120) -> np.ndarray:
    return levels[levels.avail <= t]["level"].to_numpy()[-lookback:]


# ----------------------------------------------------------------------------- storyline D1 + H4
def storyline_events(d1: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    lv = close_levels(d1)
    sw_low, sw_high = swing_points(h4)
    events = []
    for i in range(len(d1)):
        bar = d1.iloc[i]
        lvls = _levels_before(lv, bar["time"])  # niveles formados antes de que abra la vela
        if len(lvls) == 0:
            continue
        for direction in ("SELL", "BUY"):
            if direction == "SELL":
                hit = lvls[(bar.open < lvls) & (bar.high >= lvls) & (bar.close < lvls)]
            else:
                hit = lvls[(bar.open > lvls) & (bar.low <= lvls) & (bar.close > lvls)]
            if len(hit) == 0:
                continue
            rej_close_t = bar["close_time"]
            window = h4[(h4.close_time > rej_close_t) & (h4.close_time <= rej_close_t + pd.Timedelta(days=3))]
            start = None
            for _, hb in window.iterrows():
                pts = (sw_low if direction == "SELL" else sw_high)
                pts = pts[pts.conf <= hb["time"]]
                if pts.empty:
                    continue
                ref = pts["price"].iloc[-1]
                if (direction == "SELL" and hb.close < ref) or (direction == "BUY" and hb.close > ref):
                    start = hb["close_time"]
                    break
            if start is None:
                continue
            others = _levels_before(lv, rej_close_t)
            target = (others[others < bar.close].max() if direction == "SELL" and (others < bar.close).any() else
                      others[others > bar.close].min() if direction == "BUY" and (others > bar.close).any() else np.nan)
            events.append({"start": start, "direction": direction, "target": target, "reject_day": bar["time"]})
    return pd.DataFrame(events).sort_values("start").reset_index(drop=True) if events else pd.DataFrame(
        columns=["start", "direction", "target", "reject_day"])


def storyline_at(events: pd.DataFrame, h4: pd.DataFrame, t) -> str:
    """Storyline vigente en t (BUY / SELL / NONE), sin mirar al futuro."""
    past = events[events.start <= t]
    if past.empty:
        return "NONE"
    ev = past.iloc[-1]
    if t > ev.start + pd.Timedelta(days=15):
        return "NONE"
    if pd.notna(ev.target):
        path = h4[(h4.close_time > ev.start) & (h4.close_time <= t)]
        reached = (path.low <= ev.target).any() if ev.direction == "SELL" else (path.high >= ev.target).any()
        if reached:
            return "NONE"
    return ev.direction


# ----------------------------------------------------------------------------- escenario H4 -> H1
def h4h1_trades(symbol, h4, h1, m15, spread, events, spread_cap=SPREAD_CAP):
    from tools.replay_msnr_live_faithful import simulate
    lv4, lv1 = close_levels(h4), h1.copy()
    o1, c1 = h1["open"].to_numpy(float), h1["close"].to_numpy(float)
    tr = pd.concat([h1.high - h1.low, (h1.high - h1.close.shift()).abs(), (h1.low - h1.close.shift()).abs()], axis=1).max(axis=1)
    atr1 = tr.rolling(14).mean().to_numpy()
    mh, ml, mc, mo = (m15[k].to_numpy(float) for k in ("high", "low", "close", "open"))
    mt = m15["time"].values
    rows, busy_until = [], pd.Timestamp(START)
    for k in range(len(h4)):
        bar = h4.iloc[k]
        if bar["close_time"] <= busy_until:
            continue
        lvls = _levels_before(lv4, bar["time"])
        for direction in ("SELL", "BUY"):
            if direction == "SELL":
                hit = lvls[(bar.open < lvls) & (bar.high >= lvls) & (bar.close < lvls)]
            else:
                hit = lvls[(bar.open > lvls) & (bar.low <= lvls) & (bar.close > lvls)]
            if len(hit) == 0:
                continue
            sign = 1 if direction == "BUY" else -1
            idx = np.searchsorted(h1["time"].values, bar["close_time"].to_datetime64())
            trade = None
            for j in range(idx, min(idx + 4, len(h1) - 1)):
                lo = max(0, j - 30)
                # open-close H1 del lado contrario: pares del mismo color con cierre de la 1.ª vela
                pairs = [c1[m - 1] for m in range(lo + 1, j)
                         if (c1[m - 1] > o1[m - 1]) == (c1[m] > o1[m]) and c1[m - 1] != o1[m - 1]]
                if not pairs:
                    continue
                ref = pairs[-1]
                if (sign < 0 and c1[j] < ref < o1[j]) or (sign > 0 and c1[j] > ref > o1[j]):
                    entry_t = h1["time"].iloc[j + 1]
                    fill = o1[j + 1] + (spread if sign > 0 else 0.0)
                    a = atr1[j] if np.isfinite(atr1[j]) else 0.0
                    sl = (bar.high + 0.1 * a + spread) if sign < 0 else (bar.low - 0.1 * a)
                    risk = sign * (fill - sl)
                    if risk <= 0 or spread / risk > spread_cap:
                        break
                    s = np.searchsorted(mt, entry_t.to_datetime64())
                    if s >= len(mt) - 2:
                        break
                    rr, out, bars = simulate(direction, fill, sl, fill + sign * risk, fill + sign * 2 * risk,
                                             mh[s:], ml[s:], mc[s:], opens=mo[s:], spreads=np.full(len(mh) - s, spread))
                    trade = {"symbol": symbol, "time": entry_t, "direction": direction, "rr": rr, "out": out,
                             "spread_sl": spread / risk, "storyline": storyline_at(events, h4, entry_t)}
                    busy_until = m15["time"].iloc[min(s + bars, len(mt) - 1)]
                    break
            if trade:
                rows.append(trade)
                break
    return rows


# ----------------------------------------------------------------------------- por símbolo
def load(mt5, symbol, tf_name, tf_const):
    rates = mt5.copy_rates_range(symbol, tf_const, START, datetime.now(timezone.utc))
    if rates is None or len(rates) < 50:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    if tf_name in TF_DELTA:
        df["close_time"] = df["time"] + TF_DELTA[tf_name]
    return df


def run_symbol(symbol, signal_rows, spread_cap=SPREAD_CAP):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return symbol, [], [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    frames = {n: load(mt5, symbol, n, c) for n, c in (("D1", mt5.TIMEFRAME_D1), ("H4", mt5.TIMEFRAME_H4),
                                                      ("H1", mt5.TIMEFRAME_H1), ("M15", mt5.TIMEFRAME_M15))}
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if any(f is None for f in frames.values()) or info is None:
        return symbol, [], [], "SIN_DATOS"
    spread = float(info.spread) * float(info.point)
    if "spread" in frames["M15"] and (frames["M15"]["spread"] > 0).any():
        # Spread típico (mediana de las velas M15): el instantáneo depende de la hora (rollover, Asia).
        spread = float(np.median(frames["M15"]["spread"][frames["M15"]["spread"] > 0])) * float(info.point)
    events = storyline_events(frames["D1"], frames["H4"])
    tagged = []
    for r in signal_rows:
        t = pd.Timestamp(r["time"])
        tagged.append({**r, "storyline": storyline_at(events, frames["H4"], t)})
    trades = h4h1_trades(symbol, frames["H4"], frames["H1"], frames["M15"], spread, events, spread_cap)
    return symbol, tagged, trades, f"OK eventos={len(events)}"


def main():
    from config.ict_instrument_policy import MSNR_SYNTHETIC_UNIVERSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--tag", default="", help="sufijo de los CSV de salida")
    ap.add_argument("--spread-cap", type=float, default=SPREAD_CAP, help="tope spread/SL (Forex en vivo: 0.05)")
    args = ap.parse_args()
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()] or list(MSNR_SYNTHETIC_UNIVERSE)
    sig = pd.concat([pd.read_csv(OUT / f"msnr_variants_signals_{y}.csv").assign(year=y) for y in ("y0", "y1")], ignore_index=True)
    sig = sig[sig.symbol.isin(syms) & (sig.spread_sl <= SPREAD_CAP)]
    cols = ["symbol", "time", "direction", "year", "rr_live", "adx", "entry_confirmation", "scenario"]
    tagged, trades = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_symbol, s, sig[sig.symbol == s][cols].to_dict("records"), args.spread_cap): s for s in syms}
        for f in as_completed(futs):
            s, tg, tt, status = f.result()
            tagged += tg
            trades += tt
            print(f"{s}: {status} señales={len(tg)} h4h1={len(tt)}", flush=True)
    suffix = f"_{args.tag}" if args.tag else ""
    pd.DataFrame(tagged).to_csv(OUT / f"msnr_storyline_signals{suffix}.csv", index=False)
    pd.DataFrame(trades).to_csv(OUT / f"msnr_h4h1_trades{suffix}.csv", index=False)
    print("ok", len(tagged), len(trades))


if __name__ == "__main__":
    main()
