"""Investigación (solo lectura): estrategias de indicadores en los 16 índices bursátiles del broker — 21-oct-2026.

Reglas PRE-REGISTRADAS (fijadas antes de medir; sin optimización). 3 estrategias × 2 ejecuciones = 6 pruebas.
Solo velas cerradas; precios de las velas = bid; BUY entra al ask; spread y swap reales cobrados.

EJECUCIÓN DIARIA (swing, una posición al 1 %, stop de protección 2 × ATR14 D1, salida por regla a la apertura siguiente)
  REV_D  · RSI(2) de Connors, solo largos: cierre D1 > SMA200 D1 y RSI(2) D1 < 10.
           Salida: cierre > SMA5 D1 (o 10 días).
  TREND_D· Tendencia con retroceso: SMA50 > SMA200, ADX14 D1 >= 20, RSI14 D1 < 40 en alguno de los 5 días previos y
           RSI14 cruza 50 al alza.  Salida: cierre < SMA20 (o 30 días).  Espejo para cortos.
  BRK_D  · Ruptura Donchian: cierre > máximo de los 20 días previos.  Salida: cierre < mínimo de 10 días (o 40 días).
           Espejo para cortos.

EJECUCIÓN INTRADÍA (contrato del bot: TP1 1R 50 % + runner 2R 50 % con BE; señales solo en la sesión de contado
del índice, de apertura + 15 min a cierre − 60 min; tope spread/stop 5 %)
  REV_I  · Solo largos: cierre D1 (último cerrado) > SMA200 D1 y RSI(2) H1 < 10 al cierre de la H1.
           Stop 1,5 × ATR14 H1; máximo 200 velas M15.
  TREND_I· H1: EMA50 > EMA200 y ADX14 >= 20; M15: RSI14 < 40 en alguna de las 5 velas previas y cruza 50 al alza.
           Stop 1,5 × ATR14 H1; máximo 200 velas M15.  Espejo para cortos.
  ORB_I  · Rango de apertura = primeros 30 min de la sesión de contado. Primera vela M15 que cierra fuera del rango
           en las 3 h siguientes, del lado correcto del VWAP de sesión (volumen de ticks).  Stop = el otro extremo
           del rango; máximo 26 velas M15 (≈ 6,5 h).  Una operación por sesión.

Criterio (corrección por 6 pruebas): R/op > 0 en el año 0 y en el año 1; t >= 2,7; >= 3 de 4 semestres > 0;
p azar < 0,0083 (entradas aleatorias con la misma gestión y la misma dirección permitida: en REV, largos aleatorios,
de modo que la deriva alcista de los índices no cuenta como ventaja).

Uso:   .venv/Scripts/python.exe tools/research_index_indicators.py --workers 3
Salida: storage/analysis/index_indicators_{trades,random}.csv y index_indicators_report.md
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_synthetic_indicators as base  # noqa: E402

OUT = ROOT / "storage" / "analysis"
STRATEGIES = ("REV_D", "TREND_D", "BRK_D", "REV_I", "TREND_I", "ORB_I")
INTRADAY_SPREAD_CAP = 0.05
US = ("America/New_York", "09:30", "16:00")
EU = ("Europe/Berlin", "09:00", "17:30")
SESSIONS = {
    "US SP 500": US, "US Tech 100": US, "Wall Street 30": US, "US Small Cap 2000": US, "US Mid Cap 400": US,
    "Germany 40": EU, "France 40": EU, "Europe 50": EU, "Netherlands 25": EU, "Spain 35": EU,
    "Swiss 20": ("Europe/Zurich", "09:00", "17:30"), "UK 100": ("Europe/London", "08:00", "16:30"),
    "Japan 225": ("Asia/Tokyo", "09:00", "15:30"), "Australia 200": ("Australia/Sydney", "10:00", "16:00"),
    "Hong Kong 50": ("Asia/Hong_Kong", "09:30", "16:00"), "China H Shares": ("Asia/Hong_Kong", "09:30", "16:00"),
}
REGION = {s: ("EE. UU." if v is US else "Europa" if v[0].startswith("Europe") else "Asia-Pacífico") for s, v in SESSIONS.items()}


# ----------------------------------------------------------------------------- costes
def swap_r(info, sign: int, price: float, risk: float, nights: int) -> float:
    """Swap en R (negativo = coste). Modo 5: % anual sobre el precio; modo 1: puntos por noche."""
    if nights <= 0 or risk <= 0:
        return 0.0
    rate = float(info.swap_long if sign > 0 else info.swap_short)
    if int(info.swap_mode) == 5:
        per_night = price * rate / 100 / 360
    elif int(info.swap_mode) == 1:
        per_night = rate * float(info.point)
    else:
        per_night = 0.0
    return nights * per_night / risk


def nights_between(t0, t1) -> int:
    return max(0, (pd.Timestamp(t1).normalize() - pd.Timestamp(t0).normalize()).days)


# ----------------------------------------------------------------------------- diario
def daily_frame(d1: pd.DataFrame) -> pd.DataFrame:
    d = d1.copy()
    c = d["close"]
    d["sma5"], d["sma20"] = c.rolling(5).mean(), c.rolling(20).mean()
    d["sma50"], d["sma200"] = c.rolling(50).mean(), c.rolling(200).mean()
    d["rsi2"], d["rsi14"] = base.rsi(c, 2), base.rsi(c, 14)
    d["atr"], d["adx"] = base.atr(d), base.adx(d)
    d["hi20"] = d["high"].shift(1).rolling(20).max()
    d["lo20"] = d["low"].shift(1).rolling(20).min()
    d["hi10"] = d["high"].shift(1).rolling(10).max()
    d["lo10"] = d["low"].shift(1).rolling(10).min()
    return d


def daily_signals(d: pd.DataFrame) -> dict[str, np.ndarray]:
    c, r14 = d["close"], d["rsi14"]
    rev = (c > d.sma200) & (d.rsi2 < 10)
    up = (d.sma50 > d.sma200) & (d.adx >= 20) & (r14.shift(1).rolling(5).min() < 40) & (r14.shift(1) < 50) & (r14 >= 50)
    dn = (d.sma50 < d.sma200) & (d.adx >= 20) & (r14.shift(1).rolling(5).max() > 60) & (r14.shift(1) > 50) & (r14 <= 50)
    bu = (c > d.hi20) & d.sma200.notna()
    bd = (c < d.lo20) & d.sma200.notna()
    s = lambda b, x: np.where(b.fillna(False), 1, np.where(x.fillna(False), -1, 0))
    return {"REV_D": s(rev, rev & False), "TREND_D": s(up, dn), "BRK_D": s(bu, bd)}


def daily_exit(strat: str, d: pd.DataFrame, k: int, sign: int) -> bool:
    c = d["close"].iat[k]
    if strat == "REV_D":
        return c > d["sma5"].iat[k]
    if strat == "TREND_D":
        return (c < d["sma20"].iat[k]) if sign > 0 else (c > d["sma20"].iat[k])
    return (c < d["lo10"].iat[k]) if sign > 0 else (c > d["hi10"].iat[k])


MAX_DAYS = {"REV_D": 10, "TREND_D": 30, "BRK_D": 40}


def daily_trade(strat, d, i, sign, spread, info):
    o, h, l = d["open"].to_numpy(), d["high"].to_numpy(), d["low"].to_numpy()
    j = i + 1
    atr = float(d["atr"].iat[i])
    if j >= len(d) or not np.isfinite(atr) or atr <= 0:
        return None
    risk = 2.0 * atr
    ask = spread if sign < 0 else 0.0  # cortos salen al ask
    fill = o[j] + (spread if sign > 0 else 0.0)
    sl = fill - sign * risk
    exit_px, exit_k, how = None, None, None
    for k in range(j, min(len(d), j + MAX_DAYS[strat])):
        if k > j and sign * (o[k] + ask - sl) <= 0:
            exit_px, exit_k, how = o[k] + ask, k, "GAP_SL"
            break
        if (sign > 0 and l[k] <= sl) or (sign < 0 and h[k] + ask >= sl):
            exit_px, exit_k, how = sl, k, "SL"
            break
        if daily_exit(strat, d, k, sign) or k == j + MAX_DAYS[strat] - 1:
            if k + 1 >= len(d):
                return None
            exit_px, exit_k, how = o[k + 1] + ask, k + 1, "REGLA" if k < j + MAX_DAYS[strat] - 1 else "TIEMPO"
            break
    if exit_px is None:
        return None
    nights = nights_between(d["time"].iat[j], d["time"].iat[exit_k])
    r = sign * (exit_px - fill) / risk + swap_r(info, sign, fill, risk, nights)
    return {"time": d["time"].iat[i] + pd.Timedelta(days=1), "direction": "BUY" if sign > 0 else "SELL", "r": float(r),
            "outcome": how, "bars": int(exit_k - j + 1), "exit_idx": int(exit_k), "nights": nights}


# ----------------------------------------------------------------------------- intradía
def session_columns(f: pd.DataFrame, symbol: str) -> pd.DataFrame:
    tz, op, cl = SESSIONS[symbol]
    local_open = f["time"].dt.tz_convert(tz)
    local_close = f["close_time"].dt.tz_convert(tz)
    f["sdate"] = local_open.dt.date
    mins_open = local_open.dt.hour * 60 + local_open.dt.minute
    mins_close = local_close.dt.hour * 60 + local_close.dt.minute
    o_m = int(op[:2]) * 60 + int(op[3:])
    c_m = int(cl[:2]) * 60 + int(cl[3:])
    weekday = local_open.dt.weekday < 5
    f["in_session"] = weekday & (mins_close >= o_m + 15) & (mins_close <= c_m - 60)
    f["or_bar"] = weekday & (mins_open >= o_m) & (mins_open < o_m + 30)
    f["orb_window"] = weekday & (mins_close > o_m + 30) & (mins_close <= o_m + 210)
    sess = weekday & (mins_open >= o_m) & (mins_open < c_m)
    g = f[f.or_bar].groupby("sdate")
    f["or_hi"] = f["sdate"].map(g["high"].max())
    f["or_lo"] = f["sdate"].map(g["low"].min())
    f["or_n"] = f["sdate"].map(g.size()).fillna(0)
    tp = (f["high"] + f["low"] + f["close"]) / 3
    vol = f["tick_volume"].astype(float).where(sess, 0.0)
    key = f["sdate"].astype(str)
    f["vwap"] = (tp * vol).groupby(key).cumsum() / vol.groupby(key).cumsum().replace(0, np.nan)
    return f


def intraday_frame(m15, h1, d1, symbol):
    f = base.features(m15, h1).reset_index(drop=True)
    h = h1.copy()
    h["h_rsi2"] = base.rsi(h["close"], 2)
    h["close_time"] = h["time"] + pd.Timedelta(hours=1)
    f = pd.merge_asof(f, h[["close_time", "h_rsi2"]], on="close_time", direction="backward")
    f["h1_close_now"] = f["close_time"].isin(set(h["close_time"]))
    dd = d1.copy()
    dd["d_sma200"] = dd["close"].rolling(200).mean()
    dd["d_close"] = dd["close"]
    dd["close_time"] = dd["time"] + pd.Timedelta(days=1)
    f = pd.merge_asof(f, dd[["close_time", "d_sma200", "d_close"]], on="close_time", direction="backward")
    return session_columns(f, symbol)


def intraday_signals(f: pd.DataFrame) -> dict[str, np.ndarray]:
    r, r1 = f["rsi"], f["rsi"].shift(1)
    sess = f["in_session"]
    rev = sess & f.h1_close_now & (f.d_close > f.d_sma200) & (f.h_rsi2 < 10)
    up = (f.h_ema50 > f.h_ema200) & (f.h_adx >= 20) & (r.shift(1).rolling(5).min() < 40) & (r1 < 50) & (r >= 50)
    dn = (f.h_ema50 < f.h_ema200) & (f.h_adx >= 20) & (r.shift(1).rolling(5).max() > 60) & (r1 > 50) & (r <= 50)
    c, c1 = f["close"], f["close"].shift(1)
    ok = f.orb_window & (f.or_n >= 2)
    ob = ok & (c > f.or_hi) & ~(c1 > f.or_hi) & (c > f.vwap)
    os_ = ok & (c < f.or_lo) & ~(c1 < f.or_lo) & (c < f.vwap)
    s = lambda b, x: np.where(b.fillna(False), 1, np.where(x.fillna(False), -1, 0))
    return {"REV_I": s(rev, rev & False), "TREND_I": s(sess & up, sess & dn), "ORB_I": s(ob, os_)}


def intraday_trade(strat, f, i, sign, spreads, info):
    o, h, l, c = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    j = i + 1
    if j >= len(f):
        return None
    spread = float(spreads[i])
    fill = o[j] + (spread if sign > 0 else 0.0)
    if strat == "ORB_I":
        stop = float(f["or_lo"].iat[i] if sign > 0 else f["or_hi"].iat[i] + spread)
        risk = sign * (fill - stop)
        max_bars = 26
    else:
        risk = 1.5 * float(f["h_atr"].iat[i])
        max_bars = 200
    if not np.isfinite(risk) or risk <= 0:
        return None
    if spread / risk > INTRADAY_SPREAD_CAP:
        return "SPREAD"
    sl = fill - sign * risk
    end = min(len(f), j + max_bars)
    r, outcome, bars = base.simulate("BUY" if sign > 0 else "SELL", fill, sl, fill + sign * risk, fill + 2 * sign * risk,
                                     h[j:end], l[j:end], c[j:end], opens=o[j:end], spreads=spreads[j:end])
    exit_idx = j + max(int(bars) - 1, 0)
    nights = nights_between(f["time"].iat[j], f["close_time"].iat[exit_idx])
    r = float(r) + swap_r(info, sign, fill, risk, nights)
    return {"time": f["close_time"].iat[i], "direction": "BUY" if sign > 0 else "SELL", "r": r, "outcome": outcome,
            "bars": int(bars), "exit_idx": exit_idx, "nights": nights}


# ----------------------------------------------------------------------------- símbolo
def run_symbol(symbol: str, seed: int):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return symbol, [], [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    frames = {}
    for name, tf in (("M15", mt5.TIMEFRAME_M15), ("H1", mt5.TIMEFRAME_H1), ("D1", mt5.TIMEFRAME_D1)):
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, 99_000)
        if rates is None or len(rates) < 300:
            mt5.shutdown()
            return symbol, [], [], "SIN_DATOS"
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[name] = df
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    rng = np.random.default_rng(seed)
    trades, randoms = [], []
    start = pd.Timestamp(base.START)

    # diario: spread típico de sesión (mediana de las velas M15 de la sesión de contado)
    f = intraday_frame(frames["M15"], frames["H1"], frames["D1"], symbol)
    raw = f["spread"].where(f["spread"] > 0)
    day_spread = float(raw[f["in_session"]].median() if raw[f["in_session"]].notna().any() else info.spread) * float(info.point)
    d = daily_frame(frames["D1"]).reset_index(drop=True)
    dvalid = ((d["time"] + pd.Timedelta(days=1)) >= start).to_numpy()
    for strat, sig in daily_signals(d).items():
        busy, n = -1, 0
        for i in np.flatnonzero((sig != 0) & dvalid):
            if i <= busy:
                continue
            t = daily_trade(strat, d, i, int(sig[i]), day_spread, info)
            if t:
                busy = t["exit_idx"]
                trades.append({"symbol": symbol, "family": REGION[symbol], "strategy": strat, **t})
                n += 1
        pool = np.flatnonzero(dvalid[:-2] & d["sma200"].notna().to_numpy()[:-2])
        for i in (rng.choice(pool, size=min(len(pool), max(n, 0)), replace=True) if n else []):
            sign = 1 if strat == "REV_D" else int(rng.choice((-1, 1)))
            t = daily_trade(strat, d, int(i), sign, day_spread, info)
            if t:
                randoms.append({"symbol": symbol, "family": REGION[symbol], "strategy": strat, "r": t["r"]})

    # intradía
    spreads = (raw.shift(1).rolling(96, min_periods=1).median().bfill().fillna(float(info.spread))
               * float(info.point)).to_numpy(float)
    valid = (f["close_time"] >= start).to_numpy()
    for strat, sig in intraday_signals(f).items():
        busy, n, last_day = -1, 0, None
        for i in np.flatnonzero((sig != 0) & valid):
            if i <= busy or (strat == "ORB_I" and f["sdate"].iat[i] == last_day):
                continue
            t = intraday_trade(strat, f, i, int(sig[i]), spreads, info)
            if not isinstance(t, dict):
                continue
            busy, last_day = t["exit_idx"], f["sdate"].iat[i]
            trades.append({"symbol": symbol, "family": REGION[symbol], "strategy": strat, **t})
            n += 1
        window = f["orb_window"] & (f["or_n"] >= 2) if strat == "ORB_I" else f["in_session"]
        pool = np.flatnonzero(valid[:-2] & window.to_numpy()[:-2])
        got, tries = 0, 0
        while n and got < n and tries < 20 * n and len(pool):
            tries += 1
            i = int(rng.choice(pool))
            sign = 1 if strat == "REV_I" else int(rng.choice((-1, 1)))
            t = intraday_trade(strat, f, i, sign, spreads, info)
            if isinstance(t, dict):
                randoms.append({"symbol": symbol, "family": REGION[symbol], "strategy": strat, "r": t["r"]})
                got += 1
    return symbol, trades, randoms, f"OK spread sesión {day_spread:.2f}"


def passes(s: dict) -> bool:
    sem_pos = sum(1 for v in s["sem"] if np.isfinite(v) and v > 0)
    return bool(s["y0"] > 0 and s["y1"] > 0 and s["t"] >= 2.7 and sem_pos >= 3 and s["p_azar"] < 0.0083)


def write_report(tr: pd.DataFrame, rn: pd.DataFrame, status: dict, path: Path) -> dict:
    rng = np.random.default_rng(5)
    head, sep = base.HEAD.split("\n")
    L = ["# Indicadores en índices bursátiles — replay 2 años (pre-registrado 21-oct-2026)", "",
         f"Periodo {base.START:%Y-%m-%d} → hoy (año 0 < {base.SPLIT:%Y-%m-%d} ≤ año 1); spread y swap reales. "
         "Criterio: R/op > 0 en ambos años, t ≥ 2,7, ≥ 3/4 semestres > 0, p azar < 0,0083.", "",
         "## Global por estrategia", "", "| estrategia | veredicto |" + head[1:], "|---|---" + sep[1:]]
    verdicts = {}
    for strat in STRATEGIES:
        d = tr[tr.strategy == strat]
        if d.empty:
            continue
        s = base.summary(d, rn[rn.strategy == strat], rng)
        verdicts[strat] = passes(s)
        L.append(f"| {strat} | {'SUPERA' if verdicts[strat] else 'NO SUPERA'} " + base.fmt(s))
    L += ["", "## Por región (exploratorio)", "", "| estrategia | región | cumple |" + head[1:], "|---|---|---" + sep[1:]]
    for strat in STRATEGIES:
        for fam, g in tr[tr.strategy == strat].groupby("family"):
            s = base.summary(g, rn[(rn.strategy == strat) & (rn.family == fam)], rng)
            L.append(f"| {strat} | {fam} | {'sí' if passes(s) else 'no'} " + base.fmt(s))
    L += ["", "## R/op por índice: total (año 0 / año 1, ops)", "", "| índice | " + " | ".join(STRATEGIES) + " |",
          "|---|" + "---|" * len(STRATEGIES)]
    t_all = pd.to_datetime(tr["time"], utc=True)
    for sym in sorted(tr.symbol.unique()):
        cells = []
        for strat in STRATEGIES:
            g = tr[(tr.symbol == sym) & (tr.strategy == strat)]
            tg = t_all[g.index]
            a, b = g[tg < base.SPLIT].r, g[tg >= base.SPLIT].r
            cells.append(f"{g.r.mean():+.3f} ({a.mean():+.3f}/{b.mean():+.3f}, {len(g)})" if len(g) else "—")
        L.append(f"| {sym} | " + " | ".join(cells) + " |")
    L += ["", "## Medias de las entradas aleatorias (referencia: deriva + costes)", ""]
    for strat in STRATEGIES:
        g = rn[rn.strategy == strat]
        if len(g):
            L.append(f"- {strat}: {g.r.mean():+.4f} R/op ({len(g)} entradas aleatorias)")
    L += ["", "## Estado de datos", ""] + [f"- {k}: {v}" for k, v in sorted(status.items())]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return verdicts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()] or list(SESSIONS)
    trades, randoms, status = [], [], {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_symbol, s, k) for k, s in enumerate(syms)]
        for done, fut in enumerate(as_completed(futs), 1):
            sym, tr, rn, st = fut.result()
            trades += tr
            randoms += rn
            status[sym] = st
            print(f"[{done}/{len(syms)}] {sym}: {len(tr)} ops {st}", flush=True)
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    sfx = f"_{args.tag}" if args.tag else ""
    OUT.mkdir(parents=True, exist_ok=True)
    tr.to_csv(OUT / f"index_indicators_trades{sfx}.csv", index=False)
    rn.to_csv(OUT / f"index_indicators_random{sfx}.csv", index=False)
    print(write_report(tr, rn, status, OUT / f"index_indicators_report{sfx}.md"))


if __name__ == "__main__":
    main()
