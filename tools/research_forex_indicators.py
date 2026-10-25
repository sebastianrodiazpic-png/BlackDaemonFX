"""Investigación (solo lectura): 3 estrategias de indicadores en Forex con el contrato de dos entradas — 22-oct-2026.

Reglas PRE-REGISTRADAS (fijadas antes de medir; sin optimización). Velas cerradas; precios de las velas = bid;
BUY entra al ask; spread real (mediana causal de 96 velas M15) y swap actual en puntos por noche (aproximación: MT5
no da el histórico del swap). Universo: un contrato por par (sin micro) con spread mediano <= 10 % del ATR H1.

  MOM_D  · Momentum diario: rendimiento de 63 días > 0 y cierre D1 > SMA100; disparo cuando RSI14 D1 cruza 50 al
           alza tras haber estado < 50 (reanudación).  Stop 2 × ATR14 D1.  Regla: cierre D1 < SMA50 o 40 días.
           (El filtro de carry previsto se descarta: sin histórico de swap sería mirar el futuro.)
  ASIA_R · Reversión en la sesión asiática (señal 00:00-05:00 UTC): ADX14 H1 < 25; la vela M15 previa cierra fuera
           de Bollinger(20, 2) con RSI14 fuera de 30/70 y la actual vuelve a cerrar dentro.  Stop 1,5 × ATR14 H1.
           Regla: cierre a las 07:00 UTC (antes de Londres).
  TREND_H· Retroceso en tendencia: H4 EMA50 > EMA200 y ADX14 H4 >= 20; al cierre de la H1, RSI14 H1 < 40 en alguna de
           las 5 H1 previas y cruza 50 al alza.  Stop 2 × ATR14 H1.  Sin señales de 20:00 a 23:59 UTC (rollover).
           Regla: 200 velas M15.
  Espejo exacto para SELL.

Gestión común (contrato del bot): 1 % en dos entradas al 50 %: TP1 1R; runner TP2 2R que pasa a BE al cerrar TP1;
la regla de la estrategia cierra lo que quede. Camino real en M15 (SL primero si coincide). Tope spread/stop 5 %.
Una operación por par y estrategia.

Criterio (3 pruebas), periodo 21-oct-2024 → hoy: R/op > 0 en el año 0 y en el año 1; t >= 2,4 y t agrupado por
día >= 2,0; >= 3 de 4 semestres > 0; p azar < 0,0167 (entradas aleatorias en la misma ventana, misma gestión).
Fuera de muestra (sin tocar nada): 21-oct-2023 → 21-oct-2024 con R/op > 0 y t >= 1,0.

Uso:   .venv/Scripts/python.exe tools/research_forex_indicators.py --workers 3
Salida: storage/analysis/forex_indicators_{trades,random}.csv y forex_indicators_report.md
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_synthetic_indicators as base  # noqa: E402

OUT = ROOT / "storage" / "analysis"
STRATEGIES = ("MOM_D", "ASIA_R", "TREND_H")
OOS_START = pd.Timestamp("2023-10-21", tz="UTC")
START = pd.Timestamp(base.START)
SPLIT = pd.Timestamp(base.SPLIT)
SPREAD_CAP = 0.05
FX_FOLDERS = ("Forex Major", "Forex Minor", "Forex Exotic")
MAX_COST_ATR = 0.10


# ----------------------------------------------------------------------------- gestión
def manage(sign, fill, risk, o, h, l, j0, end):
    """Dos tramos 50/50 (TP1 1R; runner 2R con BE tras TP1) hasta `end`. Precios ya del lado de salida.
    Para SELL se invierten los precios (o, h, l negados y h/l intercambiados), así la lógica es la de un BUY."""
    if sign < 0:
        o, h, l, fill = -o, -l, -h, -fill
    legs = [{"tp": 1.0, "sl": fill - risk, "out": None}, {"tp": 2.0, "sl": fill - risk, "out": None}]
    for i in range(j0, end):
        live = [g for g in legs if g["out"] is None]
        if not live:
            break
        for g in live:
            if i > j0 and o[i] <= g["sl"]:
                g["out"] = (o[i], i)
        tp1_now = False
        for g in [g for g in legs if g["out"] is None]:
            if l[i] <= g["sl"]:
                g["out"] = (g["sl"], i)
            elif h[i] >= fill + g["tp"] * risk:
                g["out"] = (fill + g["tp"] * risk, i)
                tp1_now = tp1_now or g["tp"] == 1.0
        if tp1_now:
            for g in legs:
                if g["out"] is None:
                    g["sl"] = fill
                    if l[i] <= fill:
                        g["out"] = (fill, i)
    for g in legs:
        if g["out"] is None:
            k = min(end, len(o) - 1)
            g["out"] = (o[k], k)
    return [((px - fill) / risk, k) for px, k in (g["out"] for g in legs)]


def trade(sign, j, end, risk, m, spreads, info):
    """Entrada en la apertura de la vela M15 j. Devuelve dict o None / "SPREAD"."""
    if j >= len(m) or not np.isfinite(risk) or risk <= 0:
        return None
    spread = float(spreads[j])
    if spread / risk > SPREAD_CAP:
        return "SPREAD"
    o, h, l = m["open"].to_numpy(float), m["high"].to_numpy(float), m["low"].to_numpy(float)
    sp = spreads
    # salida de un BUY al bid; de un SELL al ask (bid + spread)
    if sign > 0:
        legs = manage(1, o[j] + spread, risk, o, h, l, j, min(end, len(m) - 1))
    else:
        legs = manage(-1, o[j], risk, o + sp, h + sp, l + sp, j, min(end, len(m) - 1))
    rate = float(info.swap_long if sign > 0 else info.swap_short)
    r, last = 0.0, j
    for rr, k in legs:
        nights = max(0, (m["time"].iat[k].normalize() - m["time"].iat[j].normalize()).days)
        r += 0.5 * (rr + nights * rate * float(info.point) / risk)
        last = max(last, k)
    return {"r": float(r), "exit_idx": int(last), "direction": "BUY" if sign > 0 else "SELL",
            "tp1": bool(legs[0][0] >= 1.0 - 1e-9)}


# ----------------------------------------------------------------------------- señales
def build(m15: pd.DataFrame, h1: pd.DataFrame, h4: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    m = m15.copy()
    c = m["close"]
    mid, sd = c.rolling(20).mean(), c.rolling(20).std(ddof=0)
    m["bb_up"], m["bb_lo"], m["rsi"] = mid + 2 * sd, mid - 2 * sd, base.rsi(c)
    m["close_time"] = m["time"] + pd.Timedelta(minutes=15)

    def aligned(df, minutes, cols):
        df = df.copy()
        df["close_time"] = df["time"] + pd.Timedelta(minutes=minutes)
        return df[["close_time", *cols]]

    hh = h1.copy()
    hh["h1_adx"], hh["h1_atr"], hh["h1_rsi"] = base.adx(hh), base.atr(hh), base.rsi(hh["close"])
    hh["h1_rsi_min5"] = hh["h1_rsi"].shift(1).rolling(5).min()
    hh["h1_rsi_max5"] = hh["h1_rsi"].shift(1).rolling(5).max()
    hh["h1_rsi_prev"] = hh["h1_rsi"].shift(1)
    h4c = h4.copy()
    h4c["h4_ema50"], h4c["h4_ema200"], h4c["h4_adx"] = base.ema(h4c["close"], 50), base.ema(h4c["close"], 200), base.adx(h4c)
    dd = d1.copy()
    dc = dd["close"]
    dd["d_ret63"], dd["d_sma100"], dd["d_sma50"] = dc / dc.shift(63) - 1, dc.rolling(100).mean(), dc.rolling(50).mean()
    dd["d_rsi"], dd["d_atr"], dd["d_close"] = base.rsi(dc), base.atr(dd), dc
    dd["d_rsi_prev"] = dd["d_rsi"].shift(1)
    for df, mins, cols in ((hh, 60, ["h1_adx", "h1_atr", "h1_rsi", "h1_rsi_min5", "h1_rsi_max5", "h1_rsi_prev"]),
                           (h4c, 240, ["h4_ema50", "h4_ema200", "h4_adx"]),
                           (dd, 1440, ["d_ret63", "d_sma100", "d_sma50", "d_rsi", "d_rsi_prev", "d_atr", "d_close"])):
        m = pd.merge_asof(m.sort_values("close_time"), aligned(df, mins, cols).sort_values("close_time"),
                          on="close_time", direction="backward")
    h1_close = set(hh["time"] + pd.Timedelta(hours=1))
    d1_close = set(dd["time"] + pd.Timedelta(days=1))
    m["is_h1_close"] = m["close_time"].isin(h1_close)
    m["is_d1_close"] = m["close_time"].isin(d1_close)
    return m.reset_index(drop=True)


def signals(m: pd.DataFrame) -> dict[str, np.ndarray]:
    hour = m["close_time"].dt.hour
    c, c1, r1 = m["close"], m["close"].shift(1), m["rsi"].shift(1)
    mom_b = m.is_d1_close & (m.d_ret63 > 0) & (m.d_close > m.d_sma100) & (m.d_rsi_prev < 50) & (m.d_rsi >= 50)
    mom_s = m.is_d1_close & (m.d_ret63 < 0) & (m.d_close < m.d_sma100) & (m.d_rsi_prev > 50) & (m.d_rsi <= 50)
    asia = (hour >= 0) & (hour < 5) & (m.h1_adx < 25)
    as_b = asia & (c1 < m.bb_lo.shift(1)) & (r1 < 30) & (c > m.bb_lo)
    as_s = asia & (c1 > m.bb_up.shift(1)) & (r1 > 70) & (c < m.bb_up)
    tr_ok = m.is_h1_close & (hour < 20)
    tr_b = tr_ok & (m.h4_ema50 > m.h4_ema200) & (m.h4_adx >= 20) & (m.h1_rsi_min5 < 40) & (m.h1_rsi_prev < 50) & (m.h1_rsi >= 50)
    tr_s = tr_ok & (m.h4_ema50 < m.h4_ema200) & (m.h4_adx >= 20) & (m.h1_rsi_max5 > 60) & (m.h1_rsi_prev > 50) & (m.h1_rsi <= 50)
    s = lambda b, x: np.where(b.fillna(False), 1, np.where(x.fillna(False), -1, 0))
    return {"MOM_D": s(mom_b, mom_s), "ASIA_R": s(as_b, as_s), "TREND_H": s(tr_b, tr_s)}


def exit_index(strat, m, i, sign, ct):
    """Índice M15 en el que la regla cierra lo que quede."""
    if strat == "TREND_H":
        return i + 1 + 200
    if strat == "ASIA_R":
        t = m["close_time"].iat[i]
        target = t.normalize() + pd.Timedelta(hours=7)
        return int(np.searchsorted(ct, target.tz_convert(None).to_datetime64()))
    # MOM_D: primera vela D1 cerrada con cierre contra la SMA50 (o 40 días) -> apertura siguiente
    d_close = m["is_d1_close"].to_numpy()
    days = 0
    for k in range(i + 1, len(m)):
        if d_close[k]:
            days += 1
            against = (m["d_close"].iat[k] < m["d_sma50"].iat[k]) if sign > 0 else (m["d_close"].iat[k] > m["d_sma50"].iat[k])
            if against or days >= 40:
                return k + 1
    return len(m) - 1


def risk_for(strat, m, i):
    return float(2 * m["d_atr"].iat[i] if strat == "MOM_D" else (1.5 if strat == "ASIA_R" else 2.0) * m["h1_atr"].iat[i])


def run_symbol(symbol: str, seed: int):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return symbol, [], [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    fr = {}
    for name, tf, n in (("M15", mt5.TIMEFRAME_M15, 99_000), ("H1", mt5.TIMEFRAME_H1, 30_000),
                        ("H4", mt5.TIMEFRAME_H4, 8_000), ("D1", mt5.TIMEFRAME_D1, 2_000)):
        r = mt5.copy_rates_from_pos(symbol, tf, 0, n)
        if r is None or len(r) < 300:
            mt5.shutdown()
            return symbol, [], [], "SIN_DATOS"
        df = pd.DataFrame(r)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        fr[name] = df
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    m = build(fr["M15"], fr["H1"], fr["H4"], fr["D1"])
    raw = m["spread"].where(m["spread"] > 0)
    spreads = (raw.shift(1).rolling(96, min_periods=1).median().bfill().fillna(float(info.spread)) * float(info.point)).to_numpy(float)
    ct = m["close_time"].values
    valid = (m["close_time"] >= OOS_START).to_numpy()
    rng = np.random.default_rng(seed)
    trades, randoms = [], []
    hour = m["close_time"].dt.hour.to_numpy()
    for strat, sig in signals(m).items():
        busy, n = -1, 0
        for i in np.flatnonzero((sig != 0) & valid):
            if i <= busy:
                continue
            sign = int(sig[i])
            t = trade(sign, i + 1, exit_index(strat, m, i, sign, ct), risk_for(strat, m, i), m, spreads, info)
            if not isinstance(t, dict):
                continue
            busy = t["exit_idx"]
            trades.append({"symbol": symbol, "strategy": strat, "time": m["close_time"].iat[i], **t})
            n += 1
        # azar: misma ventana horaria (diario: cierres D1; Asia: 00-05 UTC; tendencia: cierres H1 antes de las 20)
        if strat == "MOD_D" or strat == "MOM_D":
            window = m["is_d1_close"].to_numpy()
        elif strat == "ASIA_R":
            window = hour < 5
        else:
            window = m["is_h1_close"].to_numpy() & (hour < 20)
        pool = np.flatnonzero(valid[:-300] & window[:-300])
        got = tries = 0
        while n and got < n and tries < 20 * n and len(pool):
            tries += 1
            i = int(rng.choice(pool))
            sign = int(rng.choice((-1, 1)))
            t = trade(sign, i + 1, exit_index(strat, m, i, sign, ct), risk_for(strat, m, i), m, spreads, info)
            if isinstance(t, dict):
                randoms.append({"symbol": symbol, "strategy": strat, "time": m["close_time"].iat[i], "r": t["r"]})
                got += 1
    return symbol, trades, randoms, "OK"


# ----------------------------------------------------------------------------- informe
def stats(g: pd.DataFrame, rn: pd.DataFrame, rng) -> dict:
    t = pd.to_datetime(g["time"], utc=True)
    y0, y1 = g[(t >= START) & (t < SPLIT)], g[t >= SPLIT]
    main = g[t >= START]
    tm = t[t >= START]
    sem = [main[(tm >= START + pd.DateOffset(months=6 * k)) & (tm < START + pd.DateOffset(months=6 * (k + 1)))].r.mean()
           for k in range(4)]
    oos = g[t < START]
    rmain = rn[pd.to_datetime(rn["time"], utc=True) >= START]
    return {"ops": len(main), "r": main.r.mean(), "t": base.tstat(main.r),
            "t_day": base.tstat(main.groupby(tm.dt.date).r.mean()), "wr": (main.r > 0).mean(),
            "tp1": main.tp1.mean(), "y0": y0.r.mean(), "y1": y1.r.mean(), "sem": sem,
            "p": base.chance_p(main, rmain, rng), "oos_n": len(oos), "oos_r": oos.r.mean() if len(oos) else np.nan,
            "oos_t": base.tstat(oos.r), "rnd": rmain.r.mean() if len(rmain) else np.nan}


def passes(s: dict) -> bool:
    sem_pos = sum(1 for v in s["sem"] if np.isfinite(v) and v > 0)
    return bool(s["y0"] > 0 and s["y1"] > 0 and s["t"] >= 2.4 and s["t_day"] >= 2.0 and sem_pos >= 3 and s["p"] < 0.0167)


def row(name, s, verdict=None):
    sem = " / ".join(f"{v:+.3f}" if np.isfinite(v) else "—" for v in s["sem"])
    head = f"| {name} |" + (f" {verdict} |" if verdict is not None else "")
    return (head + f" {s['ops']} | {s['r']:+.4f} | {s['t']:+.2f} | {s['t_day']:+.2f} | {s['wr']:.1%} | {s['tp1']:.0%} | "
            f"{s['y0']:+.4f} | {s['y1']:+.4f} | {sem} | {s['p']:.3f} | {s['rnd']:+.4f} | {s['oos_r']:+.4f} ({s['oos_n']}, t {s['oos_t']:+.1f}) |")


COLS = "| ops | R/op | t | t día | acierto | TP1 | año 0 | año 1 | semestres | p azar | azar R/op | fuera de muestra 23-24 |"
SEP = "|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|"


def write_report(tr, rn, status, path):
    rng = np.random.default_rng(3)
    L = ["# Indicadores en Forex con contrato de dos entradas — replay 2 años + 1 fuera de muestra (22-oct-2026)", "",
         f"Periodo principal {START:%Y-%m-%d} → hoy (año 0 < {SPLIT:%Y-%m-%d} ≤ año 1); fuera de muestra {OOS_START:%Y-%m-%d} → "
         f"{START:%Y-%m-%d}. {len(status)} pares. Criterio: ambos años > 0, t ≥ 2,4, t por día ≥ 2,0, ≥ 3/4 semestres, "
         "p azar < 0,0167; después fuera de muestra R/op > 0 con t ≥ 1.", "",
         "## Global", "", "| estrategia | veredicto " + COLS, "|---|---" + SEP]
    verdicts = {}
    for strat in STRATEGIES:
        g = tr[tr.strategy == strat]
        if g.empty:
            continue
        s = stats(g, rn[rn.strategy == strat], rng)
        ok = passes(s)
        oos_ok = ok and s["oos_r"] > 0 and s["oos_t"] >= 1.0
        verdicts[strat] = "SUPERA" if oos_ok else ("SUPERA 2 AÑOS, FALLA FUERA DE MUESTRA" if ok else "NO SUPERA")
        L.append(row(strat, s, verdicts[strat]))
    L += ["", "## Por par (exploratorio)", ""]
    for strat in STRATEGIES:
        L += [f"### {strat}", "", "| par " + COLS, "|---" + SEP]
        for sym, g in tr[tr.strategy == strat].groupby("symbol"):
            s = stats(g, rn[(rn.strategy == strat) & (rn.symbol == sym)], rng)
            if s["ops"]:
                L.append(row(sym, s))
        L.append("")
    L += ["## Estado de datos", ""] + [f"- {k}: {v}" for k, v in sorted(status.items())]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return verdicts


def universe():
    import MetaTrader5 as mt5
    mt5.initialize()
    out = []
    for x in mt5.symbols_get():
        if x.path.rsplit("\\", 1)[0] not in FX_FOLDERS or x.name.endswith("micro"):
            continue
        mt5.symbol_select(x.name, True)
        m = mt5.copy_rates_from_pos(x.name, mt5.TIMEFRAME_M15, 0, 5000)
        h = mt5.copy_rates_from_pos(x.name, mt5.TIMEFRAME_H1, 0, 1000)
        if m is None or h is None or len(m) < 1000:
            continue
        sp = np.median(m["spread"][m["spread"] > 0]) if (m["spread"] > 0).any() else x.spread
        atr = np.median(h["high"] - h["low"])
        if atr > 0 and sp * x.point / atr <= MAX_COST_ATR:
            out.append(x.name)
    mt5.shutdown()
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()] or universe()
    print(f"{len(syms)} pares: {', '.join(syms)}", flush=True)
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
    tr.to_csv(OUT / f"forex_indicators_trades{sfx}.csv", index=False)
    rn.to_csv(OUT / f"forex_indicators_random{sfx}.csv", index=False)
    print(write_report(tr, rn, status, OUT / f"forex_indicators_report{sfx}.md"))


if __name__ == "__main__":
    main()
