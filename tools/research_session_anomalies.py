"""Investigación (solo lectura): anomalías de sesión documentadas en Forex, oro e índices — 21-oct-2026.

Reglas fijadas ANTES de ver resultados (sin optimizar), solo velas M15 cerradas, hora del servidor MT5 = UTC,
sesiones con horario de verano real (zoneinfo):

S1 RUPTURA DEL RANGO ASIÁTICO (Forex y metales): rango = máximo/mínimo de 00:00 a 08:00 hora de Londres. Entre las
   08:00 y las 12:00 de Londres, la primera vela M15 que CIERRA fuera del rango dispara la entrada a favor en la
   apertura de la siguiente; SL en la mitad del rango.
   Índices: rango de 00:00 Londres a 09:30 Nueva York; ventana 09:30-11:30 NY.
S2 FALSA RUPTURA (Judas swing): en la misma ventana, la primera vela M15 que supera el rango con la mecha y CIERRA de
   vuelta dentro dispara la entrada en contra (vende si barrió el máximo); SL tras el extremo de esa vela + spread.
   S1 y S2: gestión del contrato (TP1 1R + runner 2R, BE tras TP1), cierre forzoso a las 17:00 NY (Forex/metales) o
   16:00 NY (índices); tope spread/SL 5 %; una operación por día y símbolo y estrategia.
S4 CONTINUACIÓN TRAS FALSA RUPTURA (pre-registrada el 21-oct-2026 en REGISTRO_CAMBIOS_ESTRATEGIA.md): mismo disparo
   que S2 pero entrada A FAVOR de la ruptura en la apertura siguiente, SL en la mitad del rango, misma gestión.
S3 SESGO NOCTURNO (índices): compra en el cierre de las 16:00 NY y venta en la apertura de las 09:30 NY del siguiente
   día hábil. Rentabilidad neta en % (spread + swap real por noche; fin de semana = 3 noches) y comparación con la
   sesión diurna (09:30 → 16:00).

Uso:
    .venv/Scripts/python.exe tools/research_session_anomalies.py --workers 4
Salida: storage/analysis/session_anomalies_trades.csv
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
START = datetime(2024, 10, 1, tzinfo=timezone.utc)
LON, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")
INDICES = ("US Tech 100", "US SP 500", "Wall Street 30")
SPREAD_CAP = 0.05
FOREX = ("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD", "NZDUSD", "GBPCAD", "EURJPY", "GBPJPY", "AUDJPY",
         "EURGBP", "EURCHF", "AUDNZD", "CADCHF", "CHFJPY", "EURAUD", "GBPAUD", "EURCAD", "AUDCAD")
METALS = ("XAUUSD", "XAGUSD")


def _local(day, hour, minute, tz):
    return pd.Timestamp(datetime(day.year, day.month, day.day, hour, minute), tz=tz).tz_convert("UTC")


def session_trades(symbol, m15, spread):
    from tools.replay_msnr_live_faithful import simulate
    idx = pd.DatetimeIndex(pd.to_datetime(m15["time"], utc=True))
    m15.index = idx
    o, h, l, c = (m15[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    t = m15["time"].to_numpy()
    is_index = symbol in INDICES
    rows = []
    for day in sorted(set(idx.tz_convert(LON).date)):
        if pd.Timestamp(day).weekday() >= 5:
            continue
        r0 = _local(day, 0, 0, LON)
        if is_index:
            w0, w1, end = _local(day, 9, 30, NY), _local(day, 11, 30, NY), _local(day, 16, 0, NY)
        else:
            w0, w1, end = _local(day, 8, 0, LON), _local(day, 12, 0, LON), _local(day, 17, 0, NY)
        rng = m15[(idx >= r0) & (idx < w0)]
        if len(rng) < 8:
            continue
        hi, lo = float(rng.high.max()), float(rng.low.min())
        mid = (hi + lo) / 2
        win = np.where((idx >= w0) & (idx < w1))[0]
        stop_i = int(np.searchsorted(idx.values, end.to_datetime64()))
        done = {"S1": False, "S2": False, "S4": False}
        for i in win:
            if i + 1 >= min(stop_i, len(m15)):
                break
            for strat in ("S1", "S2", "S4"):
                if done[strat]:
                    continue
                direction = None
                if strat == "S1":
                    if c[i] > hi:
                        direction, sl = "BUY", mid
                    elif c[i] < lo:
                        direction, sl = "SELL", mid
                elif strat == "S2":
                    if h[i] > hi and c[i] < hi:
                        direction, sl = "SELL", h[i] + spread
                    elif l[i] < lo and c[i] > lo:
                        direction, sl = "BUY", l[i]
                else:
                    if h[i] > hi and c[i] < hi:
                        direction, sl = "BUY", mid
                    elif l[i] < lo and c[i] > lo:
                        direction, sl = "SELL", mid
                if direction is None:
                    continue
                done[strat] = True
                sign = 1 if direction == "BUY" else -1
                fill = o[i + 1] + (spread if sign > 0 else 0.0)
                risk = sign * (fill - sl)
                if risk <= 0 or spread / risk > SPREAD_CAP:
                    continue
                s, e = i + 1, min(stop_i, len(m15))
                rr, out, _ = simulate(direction, fill, sl, fill + sign * risk, fill + sign * 2 * risk,
                                      h[s:e], l[s:e], c[s:e], opens=o[s:e], spreads=np.full(e - s, spread))
                rows.append({"strategy": strat, "symbol": symbol, "time": str(idx[i + 1]), "direction": direction,
                             "rr": rr, "out": out, "spread_sl": spread / risk})
    return rows


def overnight_trades(symbol, m15, spread, swap_long_pct_year, bar=pd.Timedelta(minutes=15)):
    idx = pd.DatetimeIndex(pd.to_datetime(m15["time"], utc=True))
    m = m15.set_index(idx)
    rows = []
    days = sorted(set(idx.tz_convert(NY).date))
    for k, day in enumerate(days[:-1]):
        if pd.Timestamp(day).weekday() >= 5:
            continue
        nxt = next((d for d in days[k + 1:] if pd.Timestamp(d).weekday() < 5), None)
        if nxt is None:
            continue
        t_close, t_open = _local(day, 16, 0, NY) - bar, _local(nxt, 9, 30, NY)  # la última vela cierra a las 16:00
        t_dopen = _local(day, 9, 30, NY)
        if t_close not in m.index or t_open not in m.index or t_dopen not in m.index:
            continue
        p_close, p_open, p_dopen = float(m.loc[t_close, "close"]), float(m.loc[t_open, "open"]), float(m.loc[t_dopen, "open"])
        nights = (pd.Timestamp(nxt) - pd.Timestamp(day)).days
        swap = p_close * (swap_long_pct_year / 100.0) / 360.0 * nights
        gross = (p_open - p_close) / p_close
        net = (p_open - p_close - spread + swap) / p_close
        rows.append({"strategy": "S3_NOCHE", "symbol": symbol, "time": str(t_close), "direction": "BUY",
                     "ret_gross_pct": gross * 100, "ret_net_pct": net * 100, "nights": nights,
                     "day_ret_pct": (p_close - p_dopen) / p_dopen * 100})
    return rows


def run_symbol(symbol, start=None, end=None, timeframe="M15", strategies=("S1", "S2", "S3", "S4")):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return symbol, [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    tf = {"M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30}[timeframe]
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, 99000)
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if rates is None or len(rates) < 1000 or info is None:
        return symbol, [], "SIN_DATOS"
    m15 = pd.DataFrame(rates)
    m15["time"] = pd.to_datetime(m15["time"], unit="s", utc=True)
    m15 = m15[(m15["time"] >= pd.Timestamp(start or START)) & (m15["time"] < pd.Timestamp(end or datetime.now(timezone.utc)))]
    m15 = m15.reset_index(drop=True)
    sp = m15["spread"][m15["spread"] > 0] if "spread" in m15 else pd.Series(dtype=float)
    spread = (float(np.median(sp)) if len(sp) else float(info.spread)) * float(info.point)
    rows = []
    if any(x in strategies for x in ("S1", "S2", "S4")) and timeframe == "M15":
        rows = [r for r in session_trades(symbol, m15.copy(), spread) if r["strategy"] in strategies]
    if "S3" in strategies and symbol in INDICES and int(info.swap_mode) == 5:
        bar = pd.Timedelta(minutes=15 if timeframe == "M15" else 30)
        rows += overnight_trades(symbol, m15.copy(), spread, float(info.swap_long), bar)
    return symbol, rows, "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--start", default="")
    ap.add_argument("--end", default="")
    ap.add_argument("--timeframe", default="M15", choices=("M15", "M30"))
    ap.add_argument("--strategies", default="S1,S2,S3,S4")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    start = pd.Timestamp(args.start, tz="UTC") if args.start else None
    end = pd.Timestamp(args.end, tz="UTC") if args.end else None
    strategies = tuple(x.strip() for x in args.strategies.split(","))
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()] or [*FOREX, *METALS, *INDICES]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_symbol, s, start, end, args.timeframe, strategies): s for s in syms}
        for f in as_completed(futs):
            s, r, status = f.result()
            rows += r
            print(f"{s}: {status} operaciones={len(r)}", flush=True)
    suffix = f"_{args.tag}" if args.tag else ""
    pd.DataFrame(rows).to_csv(OUT / f"session_anomalies_trades{suffix}.csv", index=False)
    print("ok", len(rows))


if __name__ == "__main__":
    main()
