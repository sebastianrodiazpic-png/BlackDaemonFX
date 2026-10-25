"""Investigación (solo lectura): 3 estrategias de indicadores en materias primas, contrato de dos entradas — 22-oct-2026.

Universo (spread <= 10 % del ATR H1): XAUUSD, XAGUSD, XAUEUR, XAGEUR, US Oil, UK Brent Oil y Cocoa.
Reglas PRE-REGISTRADAS (sin optimización); velas cerradas; precios bid, BUY al ask; spread real (mediana causal de 96
velas M15) y swap actual en puntos por noche (aproximación: MT5 no da su histórico).

  RSI2_D · RSI(2) diario de Connors en ambos sentidos: BUY si cierre D1 > SMA200 y RSI(2) < 10; SELL si cierre < SMA200
           y RSI(2) > 90.  Stop 2 × ATR14 D1.  Regla: cierre D1 al otro lado de la SMA5 (a favor) o 10 velas D1.
  ST_H4  · Supertrend(10, 3) H4 cambia de sentido con ADX14 H4 >= 20.  Stop 1,5 × ATR14 H4.
           Regla: el Supertrend H4 vuelve a girar en contra, o 60 velas H4.
  GSR_D  · Ratio oro/plata (XAUUSD / XAGUSD, cierres D1): z = (ratio − SMA20) / desviación20.  z > 2 -> plata barata:
           BUY XAGUSD + SELL XAUUSD; z < −2 -> al revés.  Cada pata con el 0,5 % y stop 2 × ATR14 D1 propio;
           R de la operación = media de las dos patas.  Regla: |z| < 0,5 o 20 velas D1.

Gestión común (contrato del bot): cada posición en dos entradas 50/50, TP1 1R y runner TP2 2R con BE tras TP1; la
regla cierra lo que quede. Camino real en M15 (SL primero). Tope spread/stop 5 %. Una operación por símbolo.

Criterio (3 pruebas), periodo 21-oct-2024 → hoy: R/op > 0 en el año 0 y en el año 1; t >= 2,4 y t por día >= 2,0;
>= 3/4 semestres > 0; p azar < 0,0167.  Fuera de muestra 21-oct-2023 → 21-oct-2024 (solo metales tienen datos):
R/op > 0 y t >= 1.

Uso:   .venv/Scripts/python.exe tools/research_commodity_indicators.py
Salida: storage/analysis/commodity_indicators_{trades,random}.csv y commodity_indicators_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_forex_indicators as fx  # noqa: E402
import tools.research_synthetic_indicators as base  # noqa: E402
from tools.research_step_indicators import supertrend_dir  # noqa: E402

OUT = ROOT / "storage" / "analysis"
UNIVERSE = ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "US Oil", "UK Brent Oil", "Cocoa")
STRATEGIES = ("RSI2_D", "ST_H4", "GSR_D")


def load(mt5, sym):
    mt5.symbol_select(sym, True)
    fr = {}
    for name, tf, n in (("M15", mt5.TIMEFRAME_M15, 99_000), ("H4", mt5.TIMEFRAME_H4, 8_000), ("D1", mt5.TIMEFRAME_D1, 2_000)):
        df = pd.DataFrame(mt5.copy_rates_from_pos(sym, tf, 0, n))
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        fr[name] = df
    info = mt5.symbol_info(sym)
    m = fr["M15"].copy()
    m["close_time"] = m["time"] + pd.Timedelta(minutes=15)
    raw = m["spread"].where(m["spread"] > 0)
    spreads = (raw.shift(1).rolling(96, min_periods=1).median().bfill().fillna(float(info.spread)) * float(info.point)).to_numpy(float)
    return fr, m.reset_index(drop=True), spreads, info


def first_bar_after(m, t):
    return int(np.searchsorted(m["time"].values, pd.Timestamp(t).tz_convert(None).to_datetime64()))


def daily_frame(d1):
    d = d1.copy()
    c = d["close"]
    d["sma5"], d["sma200"] = c.rolling(5).mean(), c.rolling(200).mean()
    d["rsi2"], d["atr"] = base.rsi(c, 2), base.atr(d)
    d["close_time"] = d["time"] + pd.Timedelta(days=1)
    return d.reset_index(drop=True)


def h4_frame(h4):
    h = h4.copy()
    h["st"] = supertrend_dir(h)
    h["adx"], h["atr"] = base.adx(h), base.atr(h)
    h["close_time"] = h["time"] + pd.Timedelta(hours=4)
    return h.reset_index(drop=True)


def rsi2_trades(sym, d, m, spreads, info, rng, randoms_out):
    sig = np.where((d.close > d.sma200) & (d.rsi2 < 10), 1, np.where((d.close < d.sma200) & (d.rsi2 > 90), -1, 0))

    def exit_k(i, sign):
        for k in range(i + 1, min(len(d), i + 11)):
            if (sign > 0 and d.close.iat[k] > d.sma5.iat[k]) or (sign < 0 and d.close.iat[k] < d.sma5.iat[k]) or k == i + 10:
                return first_bar_after(m, d.close_time.iat[k])
        return len(m) - 1

    out, busy, n = [], -1, 0
    for i in np.flatnonzero(sig != 0):
        if d.close_time.iat[i] < fx.OOS_START or d.close_time.iat[i] <= (m.time.iat[busy] if busy >= 0 else d.close_time.iat[0]):
            continue
        j = first_bar_after(m, d.close_time.iat[i])
        t = fx.trade(int(sig[i]), j, exit_k(i, int(sig[i])), 2 * float(d.atr.iat[i]), m, spreads, info)
        if isinstance(t, dict):
            busy = t["exit_idx"]
            out.append({"symbol": sym, "strategy": "RSI2_D", "time": d.close_time.iat[i], **t})
            n += 1
    pool = np.flatnonzero(((d.close_time >= fx.OOS_START) & d.sma200.notna()).to_numpy()[:-12])
    for i in (rng.choice(pool, size=n, replace=True) if n and len(pool) else []):
        sign = int(rng.choice((-1, 1)))
        t = fx.trade(sign, first_bar_after(m, d.close_time.iat[i]), exit_k(i, sign), 2 * float(d.atr.iat[i]), m, spreads, info)
        if isinstance(t, dict):
            randoms_out.append({"symbol": sym, "strategy": "RSI2_D", "time": d.close_time.iat[i], "r": t["r"]})
    return out


def st_trades(sym, h, m, spreads, info, rng, randoms_out):
    st, st1 = h["st"], h["st"].shift(1)
    sig = np.where((st == 1) & (st1 == -1) & (h.adx >= 20), 1, np.where((st == -1) & (st1 == 1) & (h.adx >= 20), -1, 0))

    def exit_k(i, sign):
        for k in range(i + 1, min(len(h), i + 61)):
            if h.st.iat[k] != sign or k == i + 60:
                return first_bar_after(m, h.close_time.iat[k])
        return len(m) - 1

    out, busy_t, n = [], None, 0
    for i in np.flatnonzero(sig != 0):
        if h.close_time.iat[i] < fx.OOS_START or (busy_t is not None and h.close_time.iat[i] <= busy_t):
            continue
        j = first_bar_after(m, h.close_time.iat[i])
        t = fx.trade(int(sig[i]), j, exit_k(i, int(sig[i])), 1.5 * float(h.atr.iat[i]), m, spreads, info)
        if isinstance(t, dict):
            busy_t = m.time.iat[t["exit_idx"]]
            out.append({"symbol": sym, "strategy": "ST_H4", "time": h.close_time.iat[i], **t})
            n += 1
    pool = np.flatnonzero((h.close_time >= fx.OOS_START).to_numpy()[:-62])
    for i in (rng.choice(pool, size=n, replace=True) if n and len(pool) else []):
        sign = int(rng.choice((-1, 1)))
        t = fx.trade(sign, first_bar_after(m, h.close_time.iat[i]), exit_k(i, sign), 1.5 * float(h.atr.iat[i]), m, spreads, info)
        if isinstance(t, dict):
            randoms_out.append({"symbol": sym, "strategy": "ST_H4", "time": h.close_time.iat[i], "r": t["r"]})
    return out


def gsr_trades(data, rng, randoms_out):
    (fg, mg, sg, ig), (fs, ms, ss, is_) = data["XAUUSD"], data["XAGUSD"]
    dg, ds = daily_frame(fg["D1"]), daily_frame(fs["D1"])
    r = pd.merge(dg[["time", "close", "atr", "close_time"]], ds[["time", "close", "atr"]], on="time", suffixes=("_g", "_s"))
    r["ratio"] = r.close_g / r.close_s
    r["z"] = (r.ratio - r.ratio.rolling(20).mean()) / r.ratio.rolling(20).std(ddof=0)
    sig = np.where(r.z > 2, 1, np.where(r.z < -2, -1, 0))  # +1: comprar plata y vender oro

    def exit_t(i):
        for k in range(i + 1, min(len(r), i + 21)):
            if abs(r.z.iat[k]) < 0.5 or k == i + 20:
                return r.close_time.iat[k]
        return r.close_time.iat[len(r) - 1]

    def pair(i, sign):
        te = exit_t(i)
        legs = [fx.trade(sign, first_bar_after(ms, r.close_time.iat[i]), first_bar_after(ms, te), 2 * float(r.atr_s.iat[i]), ms, ss, is_),
                fx.trade(-sign, first_bar_after(mg, r.close_time.iat[i]), first_bar_after(mg, te), 2 * float(r.atr_g.iat[i]), mg, sg, ig)]
        if not all(isinstance(t, dict) for t in legs):
            return None
        return {"r": 0.5 * (legs[0]["r"] + legs[1]["r"]), "exit_time": te, "direction": "BUY_XAG" if sign > 0 else "BUY_XAU",
                "tp1": legs[0]["tp1"] or legs[1]["tp1"], "exit_idx": -1}

    out, busy_t, n = [], None, 0
    for i in np.flatnonzero(sig != 0):
        if r.close_time.iat[i] < fx.OOS_START or (busy_t is not None and r.close_time.iat[i] <= busy_t):
            continue
        t = pair(i, int(sig[i]))
        if t:
            busy_t = t.pop("exit_time")
            out.append({"symbol": "XAU/XAG", "strategy": "GSR_D", "time": r.close_time.iat[i], **t})
            n += 1
    pool = np.flatnonzero(((r.close_time >= fx.OOS_START) & r.z.notna()).to_numpy()[:-22])
    for i in (rng.choice(pool, size=n, replace=True) if n and len(pool) else []):
        t = pair(i, int(rng.choice((-1, 1))))
        if t:
            randoms_out.append({"symbol": "XAU/XAG", "strategy": "GSR_D", "time": r.close_time.iat[i], "r": t["r"]})
    return out


def main():
    import MetaTrader5 as mt5
    mt5.initialize()
    rng = np.random.default_rng(17)
    data, trades, randoms, status = {}, [], [], {}
    for sym in UNIVERSE:
        data[sym] = load(mt5, sym)
        fr, m, spreads, info = data[sym]
        trades += rsi2_trades(sym, daily_frame(fr["D1"]), m, spreads, info, rng, randoms)
        trades += st_trades(sym, h4_frame(fr["H4"]), m, spreads, info, rng, randoms)
        status[sym] = f"M15 desde {m.time.iat[0]:%Y-%m-%d}"
        print(sym, "ok", flush=True)
    trades += gsr_trades(data, rng, randoms)
    mt5.shutdown()
    tr, rn = pd.DataFrame(trades), pd.DataFrame(randoms)
    OUT.mkdir(parents=True, exist_ok=True)
    tr.to_csv(OUT / "commodity_indicators_trades.csv", index=False)
    rn.to_csv(OUT / "commodity_indicators_random.csv", index=False)
    fx.STRATEGIES = STRATEGIES
    verdicts = fx.write_report(tr, rn, status, OUT / "commodity_indicators_report.md")
    rep = OUT / "commodity_indicators_report.md"
    rep.write_text(rep.read_text(encoding="utf-8").replace("Indicadores en Forex con contrato de dos entradas",
                                                           "Indicadores en materias primas con contrato de dos entradas")
                   .replace("## Por par (exploratorio)", "## Por símbolo (exploratorio)"), encoding="utf-8")
    print(verdicts)


if __name__ == "__main__":
    main()
