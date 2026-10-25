"""Investigación (solo lectura): brecha demo vs replay en ICT, por operación y por símbolo — 20-oct-2026.

Lee la base viva en solo lectura (trade_journal, DEMO, estrategia ICT) y, por operación lógica (TP1 + RUNNER unidas por
parent_execution_key), descompone el coste de ejecución en R de la SEÑAL (|entrada de la señal − SL|):

- persecución: cuánto se había movido el precio desde la entrada de la señal hasta el ask/bid al enviar (sin spread);
- spread: spread real en el momento del envío;
- deslizamiento: fill real − precio pedido;
y compara el R realizado con el R que el replay fiel dio a la MISMA señal (mercado y límite), emparejando por
símbolo, dirección y hora de la vela M15 de confirmación.

Uso:
    .venv/Scripts/python.exe tools/research_ict_demo_gap.py
Salida: storage/analysis/ict_demo_gap_operations.csv y resumen por símbolo en pantalla.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis"
DB = Path.home() / "AppData" / "Local" / "BlackDaemonFx" / "trading_bot.sqlite3"


def _get(d, *path):
    for key in path:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


def load_operations(db: Path = DB) -> pd.DataFrame:
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    rows = con.execute(
        "select instrument, direction, status, entry_price, stop_loss, net_pnl, risk_amount, strategy_version, "
        "entry_time, details_json from trade_journal where source='DEMO' and strategy_version like 'ict-sabri-malle%'"
    ).fetchall()
    con.close()
    legs = []
    for sym, direction, status, entry, stop, pnl, risk, version, entry_time, details in rows:
        meta = (json.loads(details or "{}") or {}).get("metadata") or {}
        snap = _get(meta, "entry_learning_snapshot", "market_snapshot") or {}
        audit = meta.get("execution_rr_audit") or {}
        legs.append({
            "parent": meta.get("parent_execution_key") or str(meta.get("execution_key") or "").rsplit(":", 1)[0],
            "symbol": sym, "direction": direction, "status": status, "version": version, "entry_time": entry_time,
            "setup_time": _get(meta, "entry_learning_snapshot", "timing", "confirmation_open_at"),
            "signal_entry": snap.get("entry_price"), "spread": snap.get("spread"),
            "planned_entry": audit.get("planned_entry"), "filled_entry": audit.get("filled_entry") or entry,
            "stop": meta.get("initial_stop_loss") or stop, "pnl": pnl or 0.0, "risk": risk or 0.0,
            "virtual_limit": bool(meta.get("ict_virtual_limit") or meta.get("virtual_limit")),
        })
    legs = pd.DataFrame(legs)
    closed = legs[legs.status == "CLOSED"]
    agg = closed.groupby("parent").agg(
        symbol=("symbol", "first"), direction=("direction", "first"), version=("version", "first"),
        entry_time=("entry_time", "min"), setup_time=("setup_time", "first"), signal_entry=("signal_entry", "first"),
        spread=("spread", "first"), planned_entry=("planned_entry", "first"), filled_entry=("filled_entry", "first"),
        stop=("stop", "first"), pnl=("pnl", "sum"), risk=("risk", "sum"), legs=("symbol", "size"),
        virtual_limit=("virtual_limit", "max")).reset_index()
    agg = agg[agg.risk > 0].copy()
    sign = np.where(agg.direction == "BUY", 1.0, -1.0)
    sig_risk = (agg.signal_entry - agg.stop).abs()
    agg["realized_r"] = agg.pnl / agg.risk
    agg["signal_risk"] = sig_risk
    # Precio de mercado "medio" al enviar = pedido ∓ spread/2; persecución = medio − entrada de la señal.
    mid = agg.planned_entry - sign * agg.spread / 2
    agg["chase_r"] = sign * (mid - agg.signal_entry) / sig_risk
    agg["spread_r"] = agg.spread / sig_risk
    agg["slippage_r"] = sign * (agg.filled_entry - agg.planned_entry) / sig_risk
    agg["entry_cost_r"] = sign * (agg.filled_entry - agg.signal_entry) / sig_risk  # total: persecución + spread/2 + desliz.
    agg["spread_sl_fill"] = agg.spread / (agg.filled_entry - agg.stop).abs()
    return agg


def attach_replay(ops: pd.DataFrame) -> pd.DataFrame:
    rep = pd.read_csv(OUT / "ict_limit_entry_signals.csv",
                      usecols=["symbol", "time", "direction", "mkt_rr", "lim_rr", "lim_out", "spread", "lim_risk"])
    rep["setup_time"] = pd.to_datetime(rep.time, utc=True)
    rep = rep.rename(columns={"spread": "replay_spread"})
    ops = ops.copy()
    ops["setup_time"] = pd.to_datetime(ops.setup_time, utc=True, errors="coerce")
    return ops.merge(rep.drop(columns="time"), on=["symbol", "direction", "setup_time"], how="left")


def main():
    ops = attach_replay(load_operations())
    ops.to_csv(OUT / "ict_demo_gap_operations.csv", index=False)
    pd.set_option("display.width", 220)
    m = ops[ops.mkt_rr.notna()]
    print(f"Operaciones ICT cerradas en DEMO: {len(ops)} | emparejadas con el replay: {len(m)}")
    cols = ["realized_r", "chase_r", "spread_r", "slippage_r", "entry_cost_r", "spread_sl_fill"]
    print("\nMedias globales (R de la señal):")
    print(ops[cols].mean().round(3).to_string())
    if len(m):
        print("\nMisma señal: demo vs replay")
        print(f"  demo R/op={m.realized_r.mean():+.3f}  replay mercado={m.mkt_rr.mean():+.3f}  "
              f"replay límite={m.lim_rr.mean():+.3f} (fill límite en {m.lim_rr.notna().mean():.0%})")
    print("\nPor símbolo:")
    t = ops.groupby("symbol").agg(n=("realized_r", "size"), demo_r=("realized_r", "mean"), chase=("chase_r", "mean"),
                                 spread=("spread_r", "mean"), slip=("slippage_r", "mean"),
                                 entry_cost=("entry_cost_r", "mean"), spread_sl=("spread_sl_fill", "median"),
                                 replay_mkt=("mkt_rr", "mean"), replay_lim=("lim_rr", "mean"))
    print(t.sort_values("n", ascending=False).round(3).to_string())


if __name__ == "__main__":
    sys.exit(main())
