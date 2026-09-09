"""Reporte de comparación de Win Rate PRE/POST mejoras (v107).

Compara el desempeño real de las operaciones antes y después del despliegue
de las mejoras de win rate implementadas hasta v107:
    1. Break-Even con bloqueo de ganancia real (profit lock). [v106]
    2. Filtro de horas de bajo edge en Sintéticos (con excepción de alta
       confluencia >= 90%). [v106]
    3. Salida por invalidación estructural del análisis, confirmada en velas
       M15 (sin umbral de RR de pérdida). [v106]
    4. `clean_retest` real (rechazo + overshoot acotado) en vez de fijo en
       `True`; patrón chartista y FVG obligatorios en las 4 estrategias. [v107]

La frontera PRE/POST se determina por el campo `strategy_version` de cada
operación: cualquier valor que ya contenga la marca "v107" (o posterior, si
se sigue el mismo esquema de nombres incremental "vNNN...") se considera
POST-despliegue; todo lo demás es PRE.

Uso:
    python tools/winrate_pre_post_report.py [--source DEMO] [--db-path RUTA]

No modifica datos: solo lee la base SQLite configurada del proyecto (o la
ruta indicada por `--db-path` / `DAEMONBLACKFX_DB_PATH`) y agrupa por señal
lógica (TP1 + runner de la misma decisión cuentan como UNA sola operación),
igual que la pantalla /account (`dashboard.account_metrics`).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Windows puede usar cp1252 en consolas/redirecciones. Se fuerza UTF-8 igual
# que en `app/main.py`, para que las tildes/ñ del reporte no se corrompan.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# La clasificación PRE/POST y la reducción a familia de instrumento viven en
# `dashboard.winrate_pre_post` para que este CLI y la pantalla /account
# midan exactamente lo mismo con el mismo criterio.
from dashboard.winrate_pre_post import (  # noqa: E402
    POST_IMPROVEMENT_MIN_VERSION,
    canonical_family as _canonical_bot_profile,
    classify_period,
    win_rate as _win_rate,
)


def _load_trades(db_path: str, source: str):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM trades WHERE source = ? ORDER BY id",
        (source,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def _metadata(trade):
    try:
        details = json.loads(trade.get("details_json") or "{}")
    except Exception:
        details = {}
    return details.get("metadata", {}) if isinstance(details, dict) else {}


def _group_by_logical_signal(trades):
    """Agrupa filas por señal lógica (TP1 + runner = 1 sola operación).

    Replica el criterio de `dashboard.account_metrics.build_account_payload`:
    usa `parent_execution_key` como clave principal, con fallback a
    `execution_key` y, en último caso, un identificador único por fila.
    """
    groups = defaultdict(list)
    for trade in trades:
        meta = _metadata(trade)
        key = meta.get("parent_execution_key") or trade.get("execution_key")
        if not key or str(key).strip().casefold() in {"nan", "none"}:
            key = f"TRADE:{trade.get('id')}"
        groups[str(key)].append(trade)
    return groups


def _signal_outcome(legs):
    """WIN si ninguna pierna perdió, LOSS si ninguna ganó, si no MIXED/BE."""
    results = {leg.get("result") for leg in legs}
    if "WIN" in results and "LOSS" not in results:
        return "WIN"
    if "LOSS" in results and "WIN" not in results:
        return "LOSS"
    if "WIN" in results and "LOSS" in results:
        return "MIXED"
    if "BREAKEVEN" in results:
        return "BREAKEVEN"
    return "OTHER"


def _build_signal_rows(trades):
    """Construye una fila por señal lógica con su periodo, familia y outcome."""
    closed = [
        t for t in trades
        if t.get("result") and t["result"] not in ("OPEN", None)
    ]
    groups = _group_by_logical_signal(closed)
    rows = []
    for key, legs in groups.items():
        first_leg = legs[0]
        strategy_version = first_leg.get("strategy_version")
        meta = _metadata(first_leg)
        rows.append({
            "key": key,
            "period": classify_period(strategy_version),
            "strategy_version": strategy_version,
            "family": _canonical_bot_profile(first_leg.get("instrument"), meta.get("bot_profile")),
            "outcome": _signal_outcome(legs),
            "entry_time": first_leg.get("entry_time"),
            "n_legs": len(legs),
        })
    return rows


def _print_period_summary(period_name, rows):
    counter = Counter(r["outcome"] for r in rows)
    wr, decisive = _win_rate(counter)
    print(f"--- {period_name} ({len(rows)} señales) ---")
    print(f"  {dict(counter)}")
    print(f"  Win Rate (win/(win+loss)) = {wr if wr is not None else 'sin datos'}%  (n decisivas={decisive})")
    if not rows:
        return

    print("  Por familia:")
    by_family = defaultdict(Counter)
    for row in rows:
        by_family[row["family"]][row["outcome"]] += 1
    for family in sorted(by_family):
        fam_counter = by_family[family]
        fam_wr, fam_decisive = _win_rate(fam_counter)
        print(
            f"    {family:12s} {dict(fam_counter)}  "
            f"WR={fam_wr if fam_wr is not None else '—'}%  n={fam_decisive}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="DEMO", help="Origen a reportar (DEMO/REAL/PAPER).")
    parser.add_argument(
        "--db-path",
        default=None,
        help="Ruta explícita al .sqlite3. Si se omite, se resuelve igual que el resto del proyecto.",
    )
    args = parser.parse_args()

    if args.db_path:
        db_path = args.db_path
    else:
        from database.database import DEFAULT_DB_PATH
        db_path = str(DEFAULT_DB_PATH)

    print(f"Base de datos: {db_path}")
    print(f"Origen: {args.source}")
    print(
        f"Frontera PRE/POST: strategy_version con número de versión >= "
        f"{POST_IMPROVEMENT_MIN_VERSION} (esquema smc-vNNN-...) se considera POST.\n"
    )

    trades = _load_trades(db_path, args.source)
    if not trades:
        print("No se encontraron operaciones para este origen.")
        return

    rows = _build_signal_rows(trades)
    pre_rows = [r for r in rows if r["period"] == "PRE"]
    post_rows = [r for r in rows if r["period"] == "POST"]

    _print_period_summary("PRE (antes de las mejoras v107)", pre_rows)
    _print_period_summary("POST (después de las mejoras v107)", post_rows)

    pre_wr, pre_n = _win_rate(Counter(r["outcome"] for r in pre_rows))
    post_wr, post_n = _win_rate(Counter(r["outcome"] for r in post_rows))
    print("=== Resumen comparativo ===")
    print(f"PRE:  WR={pre_wr if pre_wr is not None else '—'}%  (n={pre_n})")
    print(f"POST: WR={post_wr if post_wr is not None else '—'}%  (n={post_n})")
    if pre_wr is not None and post_wr is not None:
        delta = round(post_wr - pre_wr, 1)
        sign = "+" if delta >= 0 else ""
        print(f"Delta: {sign}{delta} puntos porcentuales")
    if post_n < 20:
        print(
            "\nAviso: la muestra POST todavía es pequeña "
            f"(n={post_n}). Con menos de ~20-30 señales decisivas, el WR "
            "puede variar mucho por azar; esperar más operaciones antes de "
            "sacar conclusiones definitivas."
        )


if __name__ == "__main__":
    main()
