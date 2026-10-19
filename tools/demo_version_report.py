"""Reporte de resultados reales en la cuenta DEMO por estrategia y versión.

Solo lectura sobre la base de producción. Agrupa las piernas (TP1/RUNNER) de cada
ejecución, calcula R ponderado por riesgo real y evalúa los criterios de promoción:
>= 100 trades cerrados, expectativa > 0 tras costos, PF >= 1.20 y ambas mitades > 0.

Uso:  .venv\\Scripts\\python.exe tools\\demo_version_report.py [--since 2026-10-19] [--db RUTA]
"""
import argparse
import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path


def default_db() -> Path:
    explicit = os.getenv("DAEMONBLACKFX_DB_PATH")
    if explicit:
        return Path(explicit)
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "BlackDaemonFx" / "trading_bot.sqlite3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-19")
    ap.add_argument("--db", default=str(default_db()))
    ap.add_argument("--immutable", action="store_true", help="abrir con immutable=1 (copias o montajes)")
    args = ap.parse_args()
    mode = "immutable=1" if args.immutable else "mode=ro"
    con = sqlite3.connect(f"file:{Path(args.db).as_posix()}?{mode}", uri=True, timeout=30)
    rows = con.execute(
        "SELECT instrument, entry_time, exit_time, net_pnl, risk_amount, execution_key, strategy_version, details_json "
        "FROM trades WHERE source='DEMO' AND entry_time >= ? ORDER BY entry_time", (args.since,)).fetchall()
    groups = defaultdict(list)
    for sym, et, xt, pnl, risk, key, ver, det in rows:
        try:
            meta = (json.loads(det or "{}").get("metadata") or {})
        except Exception:
            meta = {}
        strat = meta.get("strategy_name") or "?"
        groups[(strat, ver or "?", (key or "").rsplit(":", 1)[0])].append((sym, et, xt, pnl or 0.0, risk or 0.0))
    per = defaultdict(list)
    open_count = defaultdict(int)
    for (strat, ver, _), legs in groups.items():
        if any(l[2] is None for l in legs):
            open_count[(strat, ver)] += 1
            continue
        risk = sum(l[4] for l in legs)
        if risk <= 0:
            continue
        per[(strat, ver)].append((min(l[1] for l in legs), sum(l[3] for l in legs) / risk))
    print(f"Desde {args.since} | DB {args.db}")
    print(f"{'Estrategia':18s} {'Versión':36s} {'N':>4s} {'Abiertos':>8s} {'WR%':>6s} {'Exp R':>7s} {'Net R':>7s} {'PF':>5s}  Mitades   Criterio")
    for (strat, ver), items in sorted(per.items()):
        items.sort()
        r = [x for _, x in items]
        n = len(r)
        wins = sum(x > 0.05 for x in r)
        losses = sum(x < -0.05 for x in r)
        gp = sum(x for x in r if x > 0)
        gl = -sum(x for x in r if x < 0)
        pf = gp / gl if gl else float("inf")
        half = n // 2
        a, b = sum(r[:half]), sum(r[half:])
        ok = n >= 100 and sum(r) > 0 and pf >= 1.2 and a > 0 and b > 0
        verdict = "APROBADO" if ok else ("EN CURSO" if n < 100 else "NO CUMPLE")
        wr = 100 * wins / max(1, wins + losses)
        print(f"{strat:18s} {ver:36s} {n:4d} {open_count[(strat, ver)]:8d} {wr:6.1f} {sum(r)/n:+7.3f} {sum(r):+7.2f} {pf:5.2f}  {a:+.1f}/{b:+.1f}  {verdict}")


if __name__ == "__main__":
    main()
