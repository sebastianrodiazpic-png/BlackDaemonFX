"""Investigación (solo lectura): carry en Forex G10 SOLO con datos de MetaTrader 5 — 24-oct-2026 (decisión del usuario).

LIMITACIÓN (orientativo, no concluyente): MT5 no guarda el histórico de tipos ni de swaps. Se usa el swap ACTUAL del
broker como señal y como coste en todo el periodo, lo que solo es razonable en el pasado reciente. Por eso el replay
empieza en ene-2025. La validación fiel es la prueba demo hacia adelante con el swap real en vivo.

Reglas (pre-registradas; rebalanceo al cierre de cada mes):
  Señal: lado del par con swap neto positivo hoy (comprar la divisa de tipo alto); se ordenan los pares por carry
         neto anual (swap / precio × 360).
  C0 · Carry puro: los 3 pares de mayor carry neto.
  C1 · Carry + momentum: los 3 de mayor carry cuyo rendimiento de 63 días va a favor del lado del carry.
  Entrada en la primera vela H1 del mes; stop 3 × ATR20 D1; salida en la primera vela H1 del mes siguiente (regla).
Gestión (contrato del usuario): 1 % dividido en dos entradas al 50 %.
  - Pierna 1: cierra en TP1 = 1R.
  - Pierna 2, objetivo principal TP2 = 2R, en dos variantes:
      FIJA       : cierra en TP2 (2R), con BE tras cerrar TP1.
      PROGRESIVA : al tocar TP2 no cierra: el stop sube a 1,5R y el objetivo pasa a TP4 = 4R; al tocar 3R el stop
                   sube a 2,5R (aproximación de la extensión progresiva TP3/TP4 del motor).
  Swap por noche de calendario con el valor actual; spread mediano M15 del broker.
Azar: mismos meses y misma gestión, par y lado aleatorios entre los 28.

Uso:   .venv/Scripts/python.exe tools/research_fx_carry_mt5.py [--from 2021-11-01] [--tag 5y]
Salida: storage/analysis/fx_carry_mt5_report[_tag].md (añade desglose por año y por par de C0)
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_synthetic_indicators as base  # noqa: E402

OUT = ROOT / "storage" / "analysis"
CCY = ("USD", "EUR", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD")
START = pd.Timestamp("2025-01-01", tz="UTC")
TOP_N = 3
H1_BARS = 20_000


def load(mt5):
    names = {x.name for x in mt5.symbols_get()}
    data = {}
    for s in (a + b for a, b in itertools.permutations(CCY, 2) if a + b in names):
        mt5.symbol_select(s, True)
        i = mt5.symbol_info(s)
        d = pd.DataFrame(mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_D1, 0, 3000))
        h = pd.DataFrame(mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_H1, 0, H1_BARS))
        m = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_M15, 0, 10_000)
        for f in (d, h):
            f["time"] = pd.to_datetime(f["time"], unit="s", utc=True)
        pc = d.close.shift()
        d["atr20"] = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1).rolling(20).mean()
        d["ret63"] = d.close / d.close.shift(63) - 1
        price = float(d.close.iloc[-1])
        long_pct, short_pct = (i.swap_long * i.point / price * 360, i.swap_short * i.point / price * 360)
        data[s] = {"d1": d, "h1": h.reset_index(drop=True), "info": i,
                   "spread": float(np.median(m["spread"][m["spread"] > 0])) * float(i.point),
                   "side": 1 if long_pct > short_pct else -1, "carry": max(long_pct, short_pct)}
    return data


def manage(sign, j, end, risk, inst, progressive):
    """Devuelve R total (dos piernas 50/50) con spread y swap; precios bid; BUY al ask, SELL sale al ask."""
    h = inst["h1"]
    o, hi, lo = h.open.to_numpy(float), h.high.to_numpy(float), h.low.to_numpy(float)
    sp = inst["spread"]
    if sign < 0:   # espejo: precios del lado de salida de un SELL, invertidos para tratarlo como un BUY
        o, hi, lo = -(o + sp), -(lo + sp), -(hi + sp)
        fill = o[j]
    else:
        fill = o[j] + sp
    legs = [{"tp": 1.0, "sl": -1.0, "out": None}, {"tp": 2.0, "sl": -1.0, "out": None, "ext": False}]
    for i in range(j, end):
        for g in legs:
            if g["out"] is not None:
                continue
            stop = fill + g["sl"] * risk
            if i > j and o[i] <= stop:
                g["out"] = ((o[i] - fill) / risk, i); continue
            if lo[i] <= stop:
                g["out"] = (g["sl"], i); continue
            if hi[i] >= fill + g["tp"] * risk:
                if g["tp"] == 1.0:
                    g["out"] = (1.0, i)
                    legs[1]["sl"] = max(legs[1]["sl"], 0.0)            # runner a BE al cerrar TP1
                elif progressive and not g["ext"]:
                    g.update(ext=True, tp=4.0, sl=1.5)                 # TP2 tocado: extensión progresiva
                else:
                    g["out"] = (g["tp"], i)
            if progressive and g.get("ext") and g["out"] is None and hi[i] >= fill + 3.0 * risk:
                g["sl"] = max(g["sl"], 2.5)
    rate = float(inst["info"].swap_long if sign > 0 else inst["info"].swap_short) * float(inst["info"].point)
    total = 0.0
    for g in legs:
        r, k = g["out"] if g["out"] is not None else ((o[min(end, len(o) - 1)] - fill) / risk, min(end, len(o) - 1))
        nights = max(0, (h.time.iat[k].normalize() - h.time.iat[j].normalize()).days)
        total += 0.5 * (r + nights * rate / risk)
    return total


def month_starts(h1):
    t = h1.time[h1.time >= START]
    return t.groupby(t.dt.to_period("M")).min().tolist()


def main():
    global START, H1_BARS
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    if args.start:
        START = pd.Timestamp(args.start, tz="UTC")
        H1_BARS = int((pd.Timestamp.now(tz="UTC") - START).days * 24 * 5 / 7 * 1.15) + 2000
    import MetaTrader5 as mt5
    mt5.initialize()
    data = load(mt5)
    mt5.shutdown()
    ref = data["EURUSD"]["h1"]
    months = month_starts(ref)
    rng = np.random.default_rng(71)
    ranked = sorted(data, key=lambda s: data[s]["carry"], reverse=True)
    rows = []
    for mi in range(len(months) - 1):
        t0, t1 = months[mi], months[mi + 1]
        for strat in ("C0", "C1"):
            chosen = []
            for s in ranked:
                inst = data[s]
                if inst["carry"] <= 0:
                    break
                prev = inst["d1"][inst["d1"].time < t0.normalize()]
                if prev.empty or not np.isfinite(prev.atr20.iat[-1]):
                    continue
                if strat == "C1" and not (np.sign(prev.ret63.iat[-1]) == inst["side"]):
                    continue
                chosen.append(s)
                if len(chosen) == TOP_N:
                    break
            for s in chosen:
                inst = data[s]
                h = inst["h1"]
                j, end = int(np.searchsorted(h.time.values, t0.tz_convert(None).to_datetime64())), int(np.searchsorted(h.time.values, t1.tz_convert(None).to_datetime64()))
                risk = 3 * float(inst["d1"][inst["d1"].time < t0.normalize()].atr20.iat[-1])
                for prog in (False, True):
                    rows.append({"strat": strat, "runner": "PROGRESIVA" if prog else "FIJA", "pair": s, "month": t0, "carry": inst["carry"],
                                 "r": manage(inst["side"], j, end, risk, inst, prog)})
        for _ in range(TOP_N):
            s = str(rng.choice(list(data)))
            inst = data[s]; h = inst["h1"]
            prev = inst["d1"][inst["d1"].time < t0.normalize()]
            j, end = int(np.searchsorted(h.time.values, t0.tz_convert(None).to_datetime64())), int(np.searchsorted(h.time.values, t1.tz_convert(None).to_datetime64()))
            sign = int(rng.choice((-1, 1)))
            for prog in (False, True):
                rows.append({"strat": "AZAR", "runner": "PROGRESIVA" if prog else "FIJA", "pair": s, "month": t0, "carry": np.nan,
                             "r": manage(sign, j, end, 3 * float(prev.atr20.iat[-1]), inst, prog)})
    df = pd.DataFrame(rows)
    L = ["# Carry en Forex G10 solo con MT5 — replay reciente orientativo (24-oct-2026)", "",
         f"Periodo {START:%Y-%m} → hoy ({len(months) - 1} meses). Señal y swap = valor ACTUAL del broker (no hay histórico en MT5): "
         "resultado orientativo; la validación fiel es la prueba demo hacia adelante.", "",
         "Carry actual (top): " + ", ".join(f"{s} {data[s]['carry'] * 100:+.2f}% ({'largo' if data[s]['side'] > 0 else 'corto'})" for s in ranked[:6]), "",
         "| estrategia | runner | ops | R/op | t | acierto | R total | peor mes (R) | meses positivos |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for (st, rn), g in df.groupby(["strat", "runner"]):
        by_m = g.groupby("month").r.sum()
        L.append(f"| {st} | {rn} | {len(g)} | {g.r.mean():+.4f} | {base.tstat(g.r):+.2f} | {(g.r > 0).mean():.0%} | {g.r.sum():+.2f} | {by_m.min():+.2f} | {(by_m > 0).mean():.0%} |")
    L += ["", "## C1 por par (runner progresivo)", "", "| par | ops | R/op |", "|---|---:|---:|"]
    for p, g in df[(df.strat == "C1") & (df.runner == "PROGRESIVA")].groupby("pair"):
        L.append(f"| {p} | {len(g)} | {g.r.mean():+.4f} |")
    c0 = df[(df.strat == "C0") & (df.runner == "PROGRESIVA")].copy()
    rnd = df[(df.strat == "AZAR") & (df.runner == "PROGRESIVA")].copy()
    for f in (c0, rnd):
        f["year"] = pd.to_datetime(f.month).dt.year
    L += ["", "## C0 (runner progresivo) por año frente al azar", "",
          "| año | ops | R/op | acierto | R total | peor mes (R) | azar R/op |", "|---|---:|---:|---:|---:|---:|---:|"]
    for y, g in c0.groupby("year"):
        a = rnd[rnd.year == y].r
        L.append(f"| {y} | {len(g)} | {g.r.mean():+.4f} | {(g.r > 0).mean():.0%} | {g.r.sum():+.2f} | {g.groupby('month').r.sum().min():+.2f} | {a.mean():+.4f} |")
    L += ["", "## C0 (runner progresivo) por par", "", "| par | ops | acierto | R/op | R total |", "|---|---:|---:|---:|---:|"]
    for p_, g in c0.groupby("pair"):
        L.append(f"| {p_} | {len(g)} | {(g.r > 0).mean():.0%} | {g.r.mean():+.4f} | {g.r.sum():+.2f} |")
    eq = c0.groupby("month").r.sum().cumsum()
    L += ["", f"Caída máxima C0 (R, por meses): {(eq - eq.cummax()).min():+.2f}"]
    (OUT / f"fx_carry_mt5_report{'_' + args.tag if args.tag else ''}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
