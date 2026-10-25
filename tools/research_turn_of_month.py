"""Investigación (solo lectura): efecto cambio de mes (turn-of-the-month) en índices US — 24-oct-2026.

PRE-REGISTRO (fijado antes de medir). Anomalía documentada (Ariel 1987; Lakonishok y Smidt 1988; McConnell y Xu 2008):
la rentabilidad de la bolsa se concentra entre el último día hábil del mes y los 3 primeros del siguiente.
  Regla: compra en la apertura del último día hábil del mes (apertura de la vela D1) y venta en la apertura del 4.º día
         hábil del mes siguiente (≈ 4 sesiones dentro). Solo largos. Stop de protección 2 × ATR14 D1.
  Gestión principal: contrato de dos entradas (TP1 1R + runner 2R con BE tras TP1); la salida por tiempo cierra lo
         que quede. Informativo: una sola posición sin TP (stop + salida por tiempo).
  Datos: Dukascopy D1 + H1 2021 → sep-2026 (storage/external_data/dukascopy, ya descargado) de US500, USTEC, US30 y
         US2000; spread mediano y swap actual del broker (US SP 500, US Tech 100, Wall Street 30, US Small Cap 2000).
  Criterio: R/op > 0 en 2021-2022, 2023-2024 y 2025-hoy; mejor que el azar con p < 0,05, donde el azar son entradas
         largas en días al azar con la MISMA duración, stop y gestión (así la deriva alcista no cuenta como ventaja).

Uso:   .venv/Scripts/python.exe tools/research_turn_of_month.py
Salida: storage/analysis/turn_of_month_report.md
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
from tools.research_commodity_longrun import extend_daily_with_hourly  # noqa: E402

EXT = ROOT / "storage" / "external_data" / "dukascopy"
OUT = ROOT / "storage" / "analysis"
BROKER = {"US500": "US SP 500", "USTEC": "US Tech 100", "US30": "Wall Street 30", "US2000": "US Small Cap 2000"}
PERIODS = (("2021-2022", "2021-01-01", "2023-01-01"), ("2023-2024", "2023-01-01", "2025-01-01"), ("2025-hoy", "2025-01-01", "2100-01-01"))
fx.SPREAD_CAP = 1.0


def load(name, mt5):
    d1 = pd.read_csv(EXT / f"{name}_daily_bid.csv", parse_dates=["time"])
    h1 = pd.read_csv(EXT / f"{name}_hourly_bid.csv", parse_dates=["time"]).reset_index(drop=True)
    d1 = extend_daily_with_hourly(d1[d1["volume"] > 0].reset_index(drop=True), h1[h1["volume"] > 0])
    d1 = d1[d1.time.dt.weekday < 5].reset_index(drop=True)          # días hábiles (sin las velas de domingo)
    d1["atr"] = base.atr(d1, 14)
    sym = BROKER[name]
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    m = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 20_000)
    spread = float(np.median(m["spread"][m["spread"] > 0])) * float(info.point)
    return {"d1": d1, "h1": h1, "info": info, "spread": spread}


def h1_at(h1, t):
    return int(np.searchsorted(h1["time"].values, pd.Timestamp(t).tz_convert(None).to_datetime64()))


def trade(inst, i_entry, i_exit, risk, single=False):
    """Entrada en la apertura de la vela D1 i_entry y salida en la apertura de i_exit (camino H1)."""
    d, h1 = inst["d1"], inst["h1"]
    j, end = h1_at(h1, d.time.iat[i_entry]), h1_at(h1, d.time.iat[i_exit])
    if j >= len(h1) - 1 or end <= j or not np.isfinite(risk) or risk <= 0:
        return None
    if not single:
        t = fx.trade(1, j, end, risk, h1, np.full(len(h1), inst["spread"]), inst["info"])
        return t["r"] if isinstance(t, dict) else None
    o, lo = h1.open.to_numpy(float), h1.low.to_numpy(float)
    fill = o[j] + inst["spread"]
    sl, px, k = fill - risk, None, end
    for i in range(j, end):
        if lo[i] <= sl:
            px, k = sl, i
            break
    px = o[end] if px is None else px
    nights = max(0, (h1.time.iat[k].normalize() - h1.time.iat[j].normalize()).days)
    return (px - fill) / risk + nights * float(inst["info"].swap_long) * float(inst["info"].point) / risk


def tom_windows(d):
    month = d.time.dt.to_period("M")
    last_idx = d.groupby(month).tail(1).index.to_numpy()      # último día hábil de cada mes
    out = []
    for i in last_idx:
        if i + 4 < len(d) and i >= 20:
            out.append((i, i + 4))                            # sale en la apertura del 4.º día hábil del mes siguiente
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import MetaTrader5 as mt5
    mt5.initialize()
    rng = np.random.default_rng(61)
    rows, rnd = [], []
    for name in BROKER:
        inst = load(name, mt5)
        d = inst["d1"]
        for i, k in tom_windows(d):
            risk = 2 * float(d.atr.iat[i - 1])
            r2, r1 = trade(inst, i, k, risk), trade(inst, i, k, risk, single=True)
            if r2 is not None:
                rows.append({"symbol": name, "time": d.time.iat[i], "r": r2, "r_single": r1})
        n = sum(1 for r in rows if r["symbol"] == name)
        for _ in range(n * 3):
            i = int(rng.integers(20, len(d) - 6))
            risk = 2 * float(d.atr.iat[i - 1])
            r2, r1 = trade(inst, i, i + 4, risk), trade(inst, i, i + 4, risk, single=True)
            if r2 is not None:
                rnd.append({"symbol": name, "time": d.time.iat[i], "r": r2, "r_single": r1})
        print(name, "ok", flush=True)
    mt5.shutdown()
    tr, rn = pd.DataFrame(rows), pd.DataFrame(rnd)
    rng = np.random.default_rng(67)
    L = ["# Efecto cambio de mes en índices US — 5 años de Dukascopy (pre-registro 24-oct-2026)", "",
         "| gestión | ops | R/op | t | 2021-22 | 2023-24 | 2025-hoy | azar R/op | p azar | veredicto |", "|---|---:|---:|---:|---|---|---|---:|---:|---|"]
    for col, label in (("r", "dos entradas (principal)"), ("r_single", "una posición (informativo)")):
        g = tr.rename(columns={col: "rr"})[["symbol", "time", "rr"]].rename(columns={"rr": "r"})
        gr = rn.rename(columns={col: "rr"})[["symbol", "time", "rr"]].rename(columns={"rr": "r"})
        t = pd.to_datetime(g.time, utc=True)
        per = [g[(t >= pd.Timestamp(a, tz="UTC")) & (t < pd.Timestamp(b, tz="UTC"))].r for _, a, b in PERIODS]
        p = base.chance_p(g, gr, rng)
        ok = all(len(x) and x.mean() > 0 for x in per) and p < 0.05
        L.append(f"| {label} | {len(g)} | {g.r.mean():+.4f} | {base.tstat(g.r):+.2f} | " + " | ".join(f"{x.mean():+.3f} ({len(x)})" for x in per)
                 + f" | {gr.r.mean():+.4f} | {p:.3f} | {'SUPERA' if ok and col == 'r' else ('—' if col != 'r' else 'NO SUPERA')} |")
    L += ["", "## Por índice (dos entradas)", "", "| índice | ops | R/op | azar R/op |", "|---|---:|---:|---:|"]
    for s, g in tr.groupby("symbol"):
        L.append(f"| {s} | {len(g)} | {g.r.mean():+.4f} | {rn[rn.symbol == s].r.mean():+.4f} |")
    (OUT / "turn_of_month_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
