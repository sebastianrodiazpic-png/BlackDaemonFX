"""Investigación (solo lectura): gestión del RSI(2) diario de Connors en los 5 índices US — 22-oct-2026.

Mismas entradas que el worker RSI2 (cierre D1 > SMA200 y RSI(2) < 10; entrada en el primer tick del día siguiente
al ask; stop 2 × ATR14 D1; una posición por índice). Se recorre el camino real en velas M15 (SL primero si coincide
en la vela) y se comparan 4 gestiones del 1 % de riesgo:
  A · actual: una posición; salida a la apertura tras el primer cierre D1 > SMA5 o a las 10 velas D1.
  B · dos entradas 50/50: TP1 = 1R; el runner pasa a BE tras TP1 y sale por la regla SMA5 / 10 días.
  C · como B, pero el runner además cierra en TP2 = 2R.
  D · contrato puro: TP1 1R + runner 2R con BE, sin regla; cierre a las 10 velas D1.
Spread y swap reales por tramo. Periodo 21-oct-2024 → hoy.

Uso:   .venv/Scripts/python.exe tools/research_rsi2_management.py
Salida: storage/analysis/rsi2_management_trades.csv y rsi2_management_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.research_synthetic_indicators as base  # noqa: E402
from tools.research_index_indicators import nights_between, swap_r  # noqa: E402
from strategy.connors_rsi2.rsi2_daily import RSI2_DEFAULT_SYMBOLS, daily_indicators  # noqa: E402

OUT = ROOT / "storage" / "analysis"
VARIANTS = ("A_REGLA", "B_TP1_REGLA", "C_TP1_TP2_REGLA", "D_CONTRATO")
MAX_DAYS = 10


def manage(variant, sign, fill, risk, m15, j0, day_end_idx, rule_exit_idx, spread):
    """Recorre las M15 desde j0. Devuelve [(peso, precio_salida, índice_salida)] por tramo."""
    o, h, l = (m15[k].to_numpy(float) for k in ("open", "high", "low"))
    legs = [{"w": 1.0, "tp": None}] if variant == "A_REGLA" else [{"w": 0.5, "tp": 1.0}, {"w": 0.5, "tp": None}]
    if variant in ("C_TP1_TP2_REGLA", "D_CONTRATO"):
        legs[1]["tp"] = 2.0
    for leg in legs:
        leg["sl"] = fill - risk
        leg["out"] = None
    end = rule_exit_idx if variant != "D_CONTRATO" else day_end_idx
    for i in range(j0, end):
        open_legs = [g for g in legs if g["out"] is None]
        if not open_legs:
            break
        for g in open_legs:
            if i > j0 and o[i] <= g["sl"]:
                g["out"] = (o[i], i)
        open_legs = [g for g in legs if g["out"] is None]
        tp1_hit_now = False
        for g in open_legs:
            if l[i] <= g["sl"]:
                g["out"] = (g["sl"], i)
            elif g["tp"] is not None and h[i] >= fill + g["tp"] * risk:
                g["out"] = (fill + g["tp"] * risk, i)
                tp1_hit_now = tp1_hit_now or g["tp"] == 1.0
        if tp1_hit_now:
            for g in legs:
                if g["out"] is None:
                    g["sl"] = fill  # runner a BE tras cerrar TP1
                    if l[i] <= fill:  # orden intravela desconocido: vuelta a BE en la misma vela
                        g["out"] = (fill, i)
    for g in legs:
        if g["out"] is None:
            idx = min(end, len(o) - 1)
            g["out"] = (o[idx], idx)
    return [(g["w"], g["out"][0], g["out"][1]) for g in legs]


def run_symbol(mt5, symbol):
    mt5.symbol_select(symbol, True)
    d1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 5000))
    m15 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 99_000))
    info = mt5.symbol_info(symbol)
    for df in (d1, m15):
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    spread = float(np.median(m15.spread[m15.spread > 0])) * float(info.point)
    d = daily_indicators(d1).reset_index(drop=True)
    mt = m15["time"].values  # datetime64 UTC sin zona
    rows = []
    busy_until = {v: pd.Timestamp(0, tz="UTC") for v in VARIANTS}
    for i in np.flatnonzero(d["signal"].to_numpy()):
        if d.time.iat[i] + pd.Timedelta(days=1) < pd.Timestamp(base.START) or i + 1 >= len(d):
            continue
        day_j = d.time.iat[i + 1]
        j0 = int(np.searchsorted(mt, day_j.tz_convert(None).to_datetime64()))
        if j0 >= len(m15):
            continue
        last_day = min(i + MAX_DAYS, len(d) - 1)          # vela D1 del cierre por tiempo
        rule_day = next((k for k in range(i + 1, last_day + 1) if d.close.iat[k] > d.sma_exit.iat[k]), last_day)
        nxt = lambda k: int(np.searchsorted(mt, (d.time.iat[k] + pd.Timedelta(days=1)).tz_convert(None).to_datetime64()))
        rule_idx, end_idx = nxt(rule_day), nxt(last_day)
        if max(rule_idx, end_idx) >= len(m15):
            continue
        fill = m15.open.iat[j0] + spread
        risk = 2.0 * float(d.atr.iat[i])
        for v in VARIANTS:
            if m15.time.iat[j0] <= busy_until[v]:
                continue
            legs = manage(v, 1, fill, risk, m15, j0, end_idx, rule_idx, spread)
            r = sum(w * ((px - fill) / risk + swap_r(info, 1, fill, risk, nights_between(m15.time.iat[j0], m15.time.iat[k])))
                    for w, px, k in legs)
            busy_until[v] = m15.time.iat[max(k for _, _, k in legs)]
            rows.append({"symbol": symbol, "variant": v, "time": d.time.iat[i] + pd.Timedelta(days=1), "r": r,
                         "tp1": any(w == 0.5 and px >= fill + risk - 1e-9 for w, px, _ in legs[:1]) if v != "A_REGLA" else False})
    return rows


def main():
    import MetaTrader5 as mt5
    mt5.initialize()
    rows = []
    for s in RSI2_DEFAULT_SYMBOLS:
        rows += run_symbol(mt5, s)
        print(s, "ok", flush=True)
    mt5.shutdown()
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "rsi2_management_trades.csv", index=False)
    L = ["# RSI(2) diario en índices US: gestión actual vs dos entradas (replay 2 años, 22-oct-2026)", "",
         "| gestión | ops | R/op | t | t por día | acierto | año 0 | año 1 | TP1 tocado | R total |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for v in VARIANTS:
        g = df[df.variant == v]
        t = pd.to_datetime(g.time, utc=True)
        by_day = g.groupby(t.dt.date).r.mean()
        L.append(f"| {v} | {len(g)} | {g.r.mean():+.4f} | {base.tstat(g.r):+.2f} | {base.tstat(by_day):+.2f} | "
                 f"{(g.r > 0).mean():.1%} | {g[t < base.SPLIT].r.mean():+.4f} | {g[t >= base.SPLIT].r.mean():+.4f} | "
                 f"{g.tp1.mean():.0%} | {g.r.sum():+.1f} |")
    (OUT / "rsi2_management_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("informe: storage/analysis/rsi2_management_report.md")


if __name__ == "__main__":
    main()
