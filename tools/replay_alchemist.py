"""Replay FIEL de Alchemist MSNR (pre-registro del 26-oct-2026 en REGISTRO_CAMBIOS_ESTRATEGIA.md). Solo lectura.

- Clase real `AlchemistStrategy` sobre velas cerradas del broker MT5 (M15, H1, H4, D1).
- Precios bid de las velas; ask = bid + spread real de ticks (p75 de --spread-file).
- Variantes: entrada (hombro, CE, OB 50 %) × filtro de confluencia (sí/no) × salida (A, B). Decide solo la principal:
  hombro + confluencia + salida A.
- Azar: misma dirección, SL y objetivo en R con entrada al azar en la sesión del mismo mes (--reps repeticiones).

Uso: python tools/replay_alchemist.py --workers 4 --tag pre
Salida: storage/analysis/alchemist_trades_<tag>.csv y alchemist_summary_<tag>.md
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
SPREAD_FILE = OUT / "real_markets_tick_spread_20261023.json"
UNIVERSE = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "XAUUSD")
PERIODS = (("D", "2023-12-20", "2024-10-25"), ("A", "2024-10-25", "2025-10-25"), ("B", "2025-10-25", "2026-10-25"))
PRIMARY = ("shoulder", True, "A")
VARIANTS = [(e, f, x) for e in ("shoulder", "ce", "ob50") for f in (True, False) for x in ("A", "B")]


def variant_name(entry, confluence, exit_mode):
    return f"{entry}|{'conf' if confluence else 'todo'}|{exit_mode}"


def period_of(ns):
    t = pd.Timestamp(ns, tz="UTC")
    for name, a, b in PERIODS:
        if pd.Timestamp(a, tz="UTC") <= t < pd.Timestamp(b, tz="UTC"):
            return name
    return None


def load_frames(symbol, start, end):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return None, None, "MT5_INIT"
    mt5.symbol_select(symbol, True)
    frames = {}
    for tf, const, warmup in (("M15", mt5.TIMEFRAME_M15, 5), ("H1", mt5.TIMEFRAME_H1, 60),
                              ("H4", mt5.TIMEFRAME_H4, 120), ("D1", mt5.TIMEFRAME_D1, 260)):
        # Por tramos de 300 días: una sola petición supera el límite de velas del terminal (maxbars = 100 000).
        parts, a, stop = [], start - timedelta(days=warmup), end + timedelta(days=3)
        while a < stop:
            b = min(stop, a + timedelta(days=300))
            rates = mt5.copy_rates_range(symbol, const, a.to_pydatetime(), b.to_pydatetime())
            if rates is not None and len(rates):
                parts.append(pd.DataFrame(rates))
            a = b
        if not parts or sum(len(p) for p in parts) < 100:
            mt5.shutdown()
            return None, None, f"SIN_DATOS_{tf}"
        df = pd.concat(parts).drop_duplicates("time").sort_values("time").reset_index(drop=True)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df[["time", "open", "high", "low", "close"]]
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    return frames, info, "OK"


def run_symbol(symbol, spread, reps):
    from strategy.alchemist import AlchemistStrategy
    from strategy.alchemist.simulation import Market, random_baseline, run_variant
    start, end = pd.Timestamp(PERIODS[0][1], tz="UTC"), pd.Timestamp(PERIODS[-1][2], tz="UTC")
    frames, info, status = load_frames(symbol, start, end)
    if frames is None:
        return symbol, [], None, status
    point = float(info.point)
    is_fx = symbol != "XAUUSD"
    pip = point * 10 if is_fx else point
    spread = float(spread) if spread else float(info.spread) * point
    strategy = AlchemistStrategy()
    mk = Market(frames, strategy, spread, pip, is_fx)
    setups = strategy.setups(frames, spread=spread, ctx=mk.ctx)
    rows, primary, funnel = [], [], {}
    for entry, conf, exit_mode in VARIANTS:
        trades = run_variant(mk, setups, entry, conf, exit_mode, start.value, end.value,
                             funnel if (entry, conf, exit_mode) == PRIMARY else None)
        name = variant_name(entry, conf, exit_mode)
        for t in trades:
            rows.append({"symbol": symbol, "variant": name, "period": period_of(t["fill_ns"]),
                         "fill_time": str(pd.Timestamp(t["fill_ns"], tz="UTC")), **t})
        if (entry, conf, exit_mode) == PRIMARY:
            primary = trades
    seed = zlib.crc32(symbol.encode())  # reproducible (hash() cambia entre procesos)
    base = random_baseline(mk, primary, reps=reps, seed=seed) * len(primary) if primary else None
    kinds = {k: sum(1 for x in setups if x.kind == k) for k in ("QML", "QMC")}
    return symbol, rows, base, f"OK setups={len(setups)} {kinds} principal={len(primary)} embudo={funnel}"


def stats(df):
    if df.empty:
        return {"n": 0, "acierto": float("nan"), "r_op": float("nan"), "pf": float("nan"), "racha": 0}
    r = df["rr"].to_numpy()
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    streak = best = 0
    for x in r:
        streak = streak + 1 if x < 0 else 0
        best = max(best, streak)
    return {"n": len(r), "acierto": float((r > 0).mean() * 100), "r_op": float(r.mean()),
            "pf": float(wins / losses) if losses > 0 else float("inf"), "racha": best}


def table(rows, cols):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(x) for x in row) + " |\n" for row in rows)


def fmt(s):
    return [s["n"], f"{s['acierto']:.1f} %", f"{s['r_op']:+.3f}", f"{s['pf']:.2f}", s["racha"]]


def summary(df, base_sum, base_n):
    cols = ["n", "acierto", "R/op", "PF", "racha pérdidas"]
    prim = df[df["variant"] == variant_name(*PRIMARY)]
    out = ["# Replay fiel Alchemist MSNR (pre-registro 26-oct-2026)\n"]
    out.append("## Variante principal (hombro + confluencia + salida A)\n")
    rows = [[p, *fmt(stats(prim[prim["period"] == p]))] for p, _, _ in PERIODS] + [["Total", *fmt(stats(prim))]]
    out.append(table(rows, ["Periodo", *cols]))
    real = prim["rr"].mean() if len(prim) else float("nan")
    if base_n:
        base = base_sum / base_n
        p = float((base >= real).mean())
        out.append(f"\nAzar ({len(base)} repeticiones): media {base.mean():+.3f} R/op, p95 {np.percentile(base, 95):+.3f}; "
                   f"real {real:+.3f}; **p = {p:.3f}**\n")
    else:
        p = float("nan")
    out.append("\n## Principal por instrumento\n")
    out.append(table([[s, *fmt(stats(g))] for s, g in prim.groupby("symbol")], ["Instrumento", *cols]))
    out.append("\n## Principal por tipo de setup\n")
    out.append(table([[k, *fmt(stats(g))] for k, g in prim.groupby("kind")], ["Tipo", *cols]))
    out.append("\n## Principal por resultado\n")
    out.append(table([[k, len(g), f"{g['rr'].mean():+.3f}"] for k, g in prim.groupby("outcome")], ["Resultado", "n", "R/op"]))
    out.append("\n## Variantes exploratorias (no deciden)\n")
    rows = []
    for v in [variant_name(*x) for x in VARIANTS]:
        g = df[df["variant"] == v]
        rows.append([v, *[f"{stats(g[g['period'] == pp])['r_op']:+.3f}" for pp, _, _ in PERIODS], *fmt(stats(g))])
    out.append(table(rows, ["Variante", "R/op D", "R/op A", "R/op B", *cols]))
    s = stats(prim)
    per = [stats(prim[prim["period"] == pp])["r_op"] for pp, _, _ in PERIODS]
    if s["n"] and s["r_op"] <= 0:
        verdict = "DESCARTADA (R/op total ≤ 0)"
    elif s["n"] >= 100 and all(x > 0 for x in per) and s["pf"] >= 1.10 and p < 0.05:
        verdict = "APRUEBA (candidata a worker en prueba demo)"
    elif s["n"]:
        verdict = "NO CONCLUYENTE (R/op > 0 pero falla otra condición → prueba demo con criterio fijado)"
    else:
        verdict = "SIN OPERACIONES"
    out.append(f"\n## Veredicto pre-registrado: **{verdict}**\n")
    return "".join(out), verdict


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--tag", default="pre")
    ap.add_argument("--spread-file", default=str(SPREAD_FILE))
    ap.add_argument("--reps", type=int, default=200)
    args = ap.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()] or list(UNIVERSE)
    spreads = {k: v.get("spread_p75", v["spread"]) for k, v in json.load(open(args.spread_file, encoding="utf-8")).items()}
    rows, base_sum, base_n, statuses = [], None, 0, []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_symbol, s, spreads.get(s), args.reps): s for s in symbols}
        for future in as_completed(futures):
            symbol, trades, base, status = future.result()
            rows += trades
            if base is not None:
                base_sum = base if base_sum is None else base_sum + base
                base_n += sum(1 for t in trades if t["variant"] == variant_name(*PRIMARY))
            print(f"{symbol}: {status}", flush=True)
            statuses.append(f"- {symbol}: {status}")
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"alchemist_trades_{args.tag}.csv", index=False)
    if df.empty:
        print("Sin operaciones")
        return
    text, verdict = summary(df, base_sum, base_n)
    text += "\n## Embudo de la variante principal por instrumento\n" + "\n".join(sorted(statuses)) + "\n"
    (OUT / f"alchemist_summary_{args.tag}.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
