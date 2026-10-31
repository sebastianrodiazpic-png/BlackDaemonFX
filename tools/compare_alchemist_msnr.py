"""Compara Alchemist MSNR (archivada) con Malaysian SNR en el MISMO universo, periodos y costes (solo lectura).

Entradas:
- storage/analysis/alchemist_trades_pre.csv (tools/replay_alchemist.py, variante principal shoulder|conf|A).
- storage/analysis/msnr_variants_signals_cmp_alch_{D,A,B}.csv (tools/replay_msnr_variants.py con spread p75 de ticks,
  tope spread/SL 5 %, --free-busy y cierre forzado de las 16:45 NY); métrica rr_live (TP1 1R + runner 2R con BE).
Azar de Malaysian SNR: misma dirección y riesgo (spread / spread_sl), entrada en la apertura de una vela M15 al azar del
mismo mes y la misma hora UTC, TP1 1R + runner 2R y cierre de las 16:45 NY; --reps repeticiones.

Uso: python tools/compare_alchemist_msnr.py --reps 200
Salida: storage/analysis/compare_alchemist_msnr.md
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
SPREAD_FILE = OUT / "real_markets_tick_spread_20261023.json"


def stats(r):
    r = np.asarray(r, float)
    if not len(r):
        return dict(n=0, acierto=np.nan, r_op=np.nan, pf=np.nan, racha=0, total=0.0)
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    streak = best = 0
    for x in r:
        streak = streak + 1 if x < 0 else 0
        best = max(best, streak)
    return dict(n=len(r), acierto=(r > 0).mean() * 100, r_op=r.mean(), pf=wins / losses if losses else np.inf,
                racha=best, total=r.sum())


def row(label, s):
    return f"| {label} | {s['n']} | {s['acierto']:.1f} % | {s['r_op']:+.3f} | {s['pf']:.2f} | {s['total']:+.1f} | {s['racha']} |"


HEAD = "| {} | n | Acierto | R/op | PF | R total | Peor racha |\n|---|---|---|---|---|---|---|"


def msnr_baseline(trades: pd.DataFrame, spreads: dict, reps: int) -> np.ndarray:
    from tools.replay_alchemist import load_frames
    from tools.replay_msnr_live_faithful import simulate
    from strategy.alchemist.simulation import next_force_flat_ns
    start = pd.Timestamp("2023-12-01", tz="UTC")
    end = pd.Timestamp("2026-10-26", tz="UTC")
    sums = np.zeros(reps)
    for symbol, g in trades.groupby("symbol"):
        frames, _, status = load_frames(symbol, start, end)
        if frames is None:
            print(symbol, status)
            continue
        m = frames["M15"]
        o, h, l, c = (m[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        open_ns = m["time"].to_numpy(dtype="datetime64[ns]").astype("int64")
        months = m["time"].dt.strftime("%Y-%m").to_numpy()
        hours = m["time"].dt.hour.to_numpy()
        spread = float(spreads[symbol])
        rng = np.random.default_rng(zlib.crc32(symbol.encode()))
        pools = {}
        for _, t in g.iterrows():
            key = (t["time"][:7], int(t["hour_utc"]))
            if key not in pools:
                pools[key] = np.flatnonzero((months == key[0]) & (hours == key[1]))[:-2]
        for rep in range(reps):
            for _, t in g.iterrows():
                pool = pools[(t["time"][:7], int(t["hour_utc"]))]
                if not len(pool):
                    continue
                i = int(rng.choice(pool))
                sign = 1 if t["direction"] == "BUY" else -1
                risk = spread / float(t["spread_sl"])
                entry = o[i] + (spread if sign > 0 else 0.0)
                ff = next_force_flat_ns(int(open_ns[i]))
                stop = int(np.searchsorted(open_ns, ff, side="left"))
                rr, _, _ = simulate(t["direction"], entry, entry - sign * risk, entry + sign * risk, entry + sign * 2 * risk,
                                    h[i:stop], l[i:stop], c[i:stop], opens=o[i:stop], spreads=np.full(max(0, stop - i), spread))
                sums[rep] += rr
    return sums / len(trades)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    args = ap.parse_args()
    alch = pd.read_csv(OUT / "alchemist_trades_pre.csv")
    alch = alch[alch["variant"] == "shoulder|conf|A"].sort_values("fill_time")
    parts = []
    for p in ("D", "A", "B"):
        df = pd.read_csv(OUT / f"msnr_variants_signals_cmp_alch_{p}.csv")
        parts.append(df.assign(periodo=p))
    msnr = pd.concat(parts).sort_values("time").reset_index(drop=True)
    msnr = msnr[msnr["spread_sl"] <= 0.05]
    spreads = {k: v.get("spread_p75", v["spread"]) for k, v in json.load(open(SPREAD_FILE, encoding="utf-8")).items()}
    base = msnr_baseline(msnr, spreads, args.reps)
    real = msnr["rr_live"].mean()
    p_msnr = float((base >= real).mean())

    out = ["# Alchemist MSNR frente a Malaysian SNR (mismo universo, periodos y costes)\n"]
    out.append("\n## Global frente al azar\n")
    out.append(HEAD.format("Estrategia"))
    out.append(row("Alchemist (hombro + confluencia + salida A)", stats(alch["rr"])))
    out.append(row("Malaysian SNR (TP1 1R + runner 2R)", stats(msnr["rr_live"])))
    out.append(f"\nAzar Malaysian SNR ({args.reps} rep.): media {base.mean():+.3f}, p95 {np.percentile(base, 95):+.3f} → "
               f"**p = {p_msnr:.3f}**. Azar Alchemist: ver alchemist_summary_pre.md (p = 0,31).\n")
    out.append("\n## Por periodo\n")
    out.append("| Periodo | Alchemist n | Alchemist R/op | MSNR n | MSNR R/op | MSNR acierto |\n|---|---|---|---|---|---|")
    for p in ("D", "A", "B"):
        a, m = stats(alch[alch["period"] == p]["rr"]), stats(msnr[msnr["periodo"] == p]["rr_live"])
        out.append(f"| {p} | {a['n']} | {a['r_op']:+.3f} | {m['n']} | {m['r_op']:+.3f} | {m['acierto']:.1f} % |")
    out.append("\n## Por instrumento\n")
    out.append("| Instrumento | Alchemist n | Alchemist R/op | MSNR n | MSNR R/op | MSNR acierto |\n|---|---|---|---|---|---|")
    for s in sorted(set(alch["symbol"]) | set(msnr["symbol"])):
        a, m = stats(alch[alch["symbol"] == s]["rr"]), stats(msnr[msnr["symbol"] == s]["rr_live"])
        out.append(f"| {s} | {a['n']} | {a['r_op']:+.3f} | {m['n']} | {m['r_op']:+.3f} | {m['acierto']:.1f} % |")
    out.append("\n## Malaysian SNR por escenario\n")
    out.append(HEAD.format("Escenario"))
    for k, g in msnr.groupby("scenario"):
        out.append(row(str(k), stats(g["rr_live"])))
    out.append("\n## Malaysian SNR con otras gestiones (mismas señales)\n")
    out.append(HEAD.format("Gestión"))
    for col, label in (("rr_live", "TP1 1R + runner 2R"), ("rr_r3", "TP1 1R + runner 3R"), ("rr_1r", "todo a 1R"),
                       ("rr_r15", "TP1 1R + runner 1,5R")):
        out.append(row(label, stats(msnr[col])))
    out.append("\n## Perfil de resultados\n")
    out.append("| Estrategia | Resultado | n | R/op |\n|---|---|---|---|")
    for k, g in alch.groupby("outcome"):
        out.append(f"| Alchemist | {k} | {len(g)} | {g['rr'].mean():+.3f} |")
    for k, g in msnr.groupby("rr_live_out"):
        out.append(f"| Malaysian SNR | {k} | {len(g)} | {g['rr_live'].mean():+.3f} |")
    text = "\n".join(out) + "\n"
    (OUT / "compare_alchemist_msnr.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
