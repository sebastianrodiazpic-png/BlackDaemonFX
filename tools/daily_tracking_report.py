"""Seguimiento diario (solo lectura): resultados DEMO frente a lo que espera el replay fiel — 20-oct-2026.

Por día UTC y acumulado desde --since, por familia de estrategia:
operaciones (TP1 + RUNNER unidas), R total, R/operación, acierto (R > 0) y una comparación con el R/operación
esperado según el replay (z = (media − esperado) / (1,1 / √n); |z| < 2 = en línea con el replay).
Además cuenta los eventos de los filtros nuevos (bloqueos por spread, ocupación fantasma, régimen MSNR, centinela).

Uso:
    .venv/Scripts/python.exe tools/daily_tracking_report.py                  # día UTC de ayer + acumulado
    .venv/Scripts/python.exe tools/daily_tracking_report.py --day 2026-10-20 --since 2026-10-20
Salida: storage/analysis/seguimiento_diario/informe_<día>.md y seguimiento_diario.csv (histórico por día y familia).
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis" / "seguimiento_diario"
DB = Path.home() / "AppData" / "Local" / "BlackDaemonFx" / "trading_bot.sqlite3"
R_STD = 1.1  # desviación típica del R por operación en los replays (2 patas, 1R/2R)

# R/operación esperado según el replay fiel (ver REGISTRO_CAMBIOS_ESTRATEGIA.md, Hallazgos).
EXPECTED = {
    "ICT sintéticos": {"r": 0.03, "rango": "+0,022 / +0,047", "fuente": "replay ICT 2 años con límite, tope 2 % y ocupación fantasma"},
    "MSNR sintéticos": {"r": 0.03, "rango": "+0,007 / +0,054", "fuente": "replay MSNR 2 años, 30 activos (provisional: pendiente el replay con símbolo libre)"},
    "Carry Forex": {"r": 0.225, "rango": "orientativo (swap actual)", "fuente": "replay solo MT5 ene-2025 → oct-2026, top 3 por swap, contrato de dos entradas (prueba demo)"},
    "RSI(2) EE. UU.": {"r": 0.176, "rango": "+0,164 / +0,190", "fuente": "replay 2 años REV_D en los 5 índices US, spread y swap reales (prueba demo; no concluyente por agrupación)"},
    "Ruptura Drift": {"r": 0.086, "rango": "+0,062 / +0,111", "fuente": "replay 2 años C_RUPTURA en Drift Switch 10/20/30 (prueba demo)"},
    "Sesgo nocturno": {"r": 0.033, "rango": "+0,008 / +0,080", "fuente": "replay M30 ene-2024 → oct-2026, stop 1 ATR D1 (prueba demo)"},
    "MSNR Vídeos": {"r": 0.017, "rango": "+0,017 / +0,018", "fuente": "worker MSNR (vídeos): replay H4→H1 2 años con política de dirección (prueba demo)"},
    "MSNR H4→H1": {"r": 0.017, "rango": "+0,017 / +0,018", "fuente": "replay H4→H1 2 años con política de dirección (prueba demo)"},
    "ICT mercados reales": {"r": 0.0, "rango": "≈ 0", "fuente": "replay ICT: sin ventaja demostrada"},
    "ORB": {"r": 0.0, "rango": "no concluyente", "fuente": "prueba demo SWEEP en curso"},
    "Otros": {"r": 0.0, "rango": "—", "fuente": "sin replay de referencia"},
}
TRACKED_EVENTS = ("ICT_SPREAD_LOCK", "MSNR_REGIME_FILTER", "MSNR_REGIME_DEMO_TEST", "MSNR_H4H1_DEMO_TEST", "MSNR_VIDEO_DEMO_TEST", "OVERNIGHT_DEMO_TEST", "OVERNIGHT_TIME_EXIT", "DRIFT_DEMO_TEST", "RSI2_DEMO_TEST", "RSI2_RULE_EXIT", "CARRY_DEMO_TEST", "CARRY_REBALANCE_EXIT", "MARKET_REGIME_OBSERVED",
                  "MARKET_REGIME_BLOCKED", "SYNTHETIC_EXECUTION_SPREAD", "ICT_VIRTUAL_LIMIT")


def family(version: str, symbol: str) -> str:
    from strategy.ict.ict_strategy import is_synthetic_asset
    v = str(version or "").lower()
    synth = is_synthetic_asset(symbol)
    if v.startswith("ict"):
        return "ICT sintéticos" if synth else "ICT mercados reales"
    if v.startswith("overnight"):
        return "Sesgo nocturno"
    if v.startswith("drift-breakout"):
        return "Ruptura Drift"
    if v.startswith("connors-rsi2"):
        return "RSI(2) EE. UU."
    if v.startswith("fx-carry"):
        return "Carry Forex"
    if v.startswith("msnr-video"):
        return "MSNR Vídeos" if synth else "Otros"
    if v.startswith("msnr-h4h1"):
        return "MSNR H4→H1" if synth else "Otros"
    if v.startswith("msnr"):
        return "MSNR sintéticos" if synth else "Otros"
    if v.startswith("orb"):
        return "ORB"
    return "Otros"


def load_operations(con, since: datetime) -> pd.DataFrame:
    rows = con.execute(
        "select instrument, strategy_version, exit_time, net_pnl, risk_amount, execution_key, details_json "
        "from trade_journal where source='DEMO' and status='CLOSED' and exit_time >= ?", (since.strftime("%Y-%m-%d %H:%M:%S"),)
    ).fetchall()
    legs = []
    for sym, version, exit_time, pnl, risk, key, details in rows:
        meta = (json.loads(details or "{}") or {}).get("metadata") or {}
        parent = meta.get("parent_execution_key") or (str(key).rsplit(":", 1)[0] if key else f"{sym}:{exit_time}")
        legs.append({"parent": parent, "symbol": sym, "version": version, "exit_time": exit_time,
                     "pnl": float(pnl or 0.0), "risk": float(risk or 0.0), "worker": meta.get("bot_profile")})
    if not legs:
        return pd.DataFrame(columns=["parent", "symbol", "version", "day", "pnl", "risk", "worker", "R", "family"])
    legs = pd.DataFrame(legs)
    ops = legs.groupby("parent").agg(symbol=("symbol", "first"), version=("version", "first"),
                                     exit_time=("exit_time", "max"), pnl=("pnl", "sum"), risk=("risk", "sum"),
                                     worker=("worker", "first")).reset_index()
    ops = ops[ops.risk > 0].copy()
    ops["R"] = ops.pnl / ops.risk
    ops["day"] = pd.to_datetime(ops.exit_time).dt.date
    ops["family"] = [family(v, s) for v, s in zip(ops.version, ops.symbol)]
    return ops


def summarize(ops: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fam, g in ops.groupby("family"):
        n = len(g)
        mean = g.R.mean()
        exp = EXPECTED.get(fam, EXPECTED["Otros"])["r"]
        z = (mean - exp) / (R_STD / math.sqrt(n)) if n else float("nan")
        verdict = "en línea" if abs(z) < 2 else ("por encima" if z > 0 else "POR DEBAJO")
        rows.append({"familia": fam, "operaciones": n, "R_total": g.R.sum(), "R_op": mean,
                     "acierto": (g.R > 0).mean(), "pnl_usd": g.pnl.sum(), "esperado_R_op": exp, "z": z, "veredicto": verdict})
    return pd.DataFrame(rows).sort_values("operaciones", ascending=False) if rows else pd.DataFrame()


def event_counts(con, day: date) -> pd.DataFrame:
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    rows = []
    for et in TRACKED_EVENTS:  # índice (event_type, event_time)
        for action, n in con.execute(
                "select action, count(*) from daemon_audit_events where event_type=? and event_time>=? and event_time<? group by action",
                (et, start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))):
            rows.append({"evento": et, "accion": action, "n": n})
    return pd.DataFrame(rows)


def _fmt(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_Sin datos._"
    d = df.copy()
    for col in ("R_total", "R_op", "esperado_R_op", "z"):
        if col in d:
            d[col] = d[col].map(lambda x: f"{x:+.3f}" if pd.notna(x) else "—")
    if "acierto" in d:
        d["acierto"] = d["acierto"].map(lambda x: f"{x:.1%}")
    if "pnl_usd" in d:
        d["pnl_usd"] = d["pnl_usd"].map(lambda x: f"{x:+.2f}")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join(lines)


def build_report(db: Path, day: date, since: date) -> tuple[str, pd.DataFrame]:
    con = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)
    try:
        ops = load_operations(con, datetime.combine(since, datetime.min.time()))
        events = event_counts(con, day)
    finally:
        con.close()
    day_ops = ops[ops.day == day] if len(ops) else ops
    upto = ops[ops.day <= day] if len(ops) else ops
    daily = summarize(day_ops)
    cumulative = summarize(upto)
    by_symbol = (day_ops.groupby(["family", "symbol"]).agg(operaciones=("R", "size"), R_total=("R", "sum"))
                 .reset_index().sort_values("R_total") if len(day_ops) else pd.DataFrame())
    lines = [f"# Seguimiento diario — {day.isoformat()} (UTC)", "",
             f"Acumulado desde {since.isoformat()}. R por operación lógica (TP1 + RUNNER). "
             "z = (media − esperado) / (1,1/√n); |z| < 2 = en línea con el replay.", "",
             "## Día", _fmt(daily), "", "## Acumulado", _fmt(cumulative), "",
             "## Referencia del replay", "| familia | R/op esperado | rango | fuente |", "|---|---|---|---|"]
    lines += [f"| {k} | {v['r']:+.3f} | {v['rango']} | {v['fuente']} |" for k, v in EXPECTED.items()]
    lines += ["", "## Símbolos del día (peor a mejor)", _fmt(by_symbol), "",
              "## Filtros del día (eventos de auditoría)", _fmt(events), ""]
    if not daily.empty:
        daily = daily.assign(dia=day.isoformat())
    return "\n".join(lines), daily


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--day", default="", help="día UTC (AAAA-MM-DD); por defecto, ayer")
    ap.add_argument("--since", default="2026-10-20", help="inicio del acumulado (AAAA-MM-DD)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    day = date.fromisoformat(args.day) if args.day else (datetime.now(timezone.utc).date() - timedelta(days=1))
    since = date.fromisoformat(args.since)
    text, daily = build_report(Path(args.db), day, since)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"informe_{day.isoformat()}.md").write_text(text, encoding="utf-8")
    hist = out / "seguimiento_diario.csv"
    if not daily.empty:
        old = pd.read_csv(hist) if hist.exists() else pd.DataFrame()
        if not old.empty:
            old = old[old["dia"] != day.isoformat()]
        pd.concat([old, daily], ignore_index=True).to_csv(hist, index=False)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
